# users/views.py
from django.shortcuts import render
from rest_framework import viewsets, permissions, generics, status
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, CarSerializer, AdminUserSerializer, 
    OwnerRegistrationSerializer, ClientRegistrationSerializer,
    MyTokenObtainPairSerializer
)
from .models import Car
from .permissions import IsAdminGeneral, IsOwner, IsClient, IsOwnerOfObject
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import datetime

from .models import SolicitudAccesoOwner
from .serializers import SolicitudAccesoOwnerSerializer, SolicitudRevisionSerializer
from django.core.mail import send_mail
from django.conf import settings
import secrets
import string
import logging
import traceback

from django.db.models import Q  

User = get_user_model()
logger = logging.getLogger(__name__)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RegisterClientView(generics.CreateAPIView):
    """Registro para clientes normales"""
    queryset = User.objects.all()
    serializer_class = ClientRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class RegisterOwnerView(generics.CreateAPIView):
    """Registro para dueños de estacionamientos"""
    queryset = User.objects.all()
    serializer_class = OwnerRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """Vista general para usuarios - Acceso limitado según rol"""
    queryset = User.objects.filter(eliminado=False)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class AdminUserViewSet(UserViewSet):
    """Vista para administradores - Acceso total a usuarios"""
    permission_classes = [permissions.IsAuthenticated, IsAdminGeneral]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        return User.objects.all()

class OwnerUserViewSet(UserViewSet):
    """Vista para dueños de estacionamientos"""
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return User.objects.filter(Q(id=self.request.user.id) | Q(rol='client'))  # ✅ Corregido: 'cliente' a 'client'
    
    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        """Endpoint para obtener y actualizar el perfil del owner actual"""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientUserViewSet(UserViewSet):
    """Vista para clientes - Solo acceso a su propio perfil"""
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.rol == 'admin':
            return User.objects.filter(eliminado=False)
        elif user.rol == 'owner':
            # Los dueños ven sus propios datos y los de sus clientes
            return User.objects.filter(eliminado=False).filter(
                Q(id=user.id) | Q(reservations__estacionamiento__dueno=user)
            ).distinct()
        else:
            # Clientes solo ven sus propios datos
            return User.objects.filter(id=user.id, eliminado=False)

    def get_serializer_class(self):
        if self.request.user.is_superuser or self.request.user.rol == 'admin':
            return AdminUserSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Endpoint para obtener datos del usuario actual"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.instance
        if not self.request.user.is_superuser and not self.request.user.rol == 'admin':
            #  Permitir actualizar todos los campos del perfil
            allowed_fields = {
                'first_name', 'last_name', 'email', 'telefono',
                'tipo_documento', 'numero_documento', 'fecha_nacimiento',
                'direccion', 'codigo_postal', 'pais'
            }
            for field in serializer.validated_data.copy():
                if field not in allowed_fields:
                    serializer.validated_data.pop(field)
        serializer.save()

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        # Solo admins o el propio usuario pueden cambiar la contraseña
        if not (request.user.is_superuser or request.user.id == user.id):
            return Response(
                {'error': 'No tienes permiso para cambiar esta contraseña'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': 'Se requieren ambas contraseñas'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not user.check_password(old_password):
            return Response(
                {'error': 'Contraseña actual incorrecta'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Contraseña actualizada correctamente'})

    @action(detail=True, methods=['post'])
    def soft_delete(self, request, pk=None):
        """Eliminación suave de usuario"""
        user = self.get_object()
        if not request.user.is_superuser and not request.user.rol == 'admin':
            return Response(
                {'error': 'No tienes permiso para realizar esta acción'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.eliminado = True
        user.activo = False
        user.fecha_eliminacion = timezone.now()
        user.save()
        
        return Response({'message': 'Usuario eliminado correctamente'})


class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all().order_by('-created_at')
    serializer_class = CarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin_general:
            # Admin puede ver todos los vehículos
            return Car.objects.all()
        elif user.is_owner:
            # Dueño puede ver vehículos de sus clientes (se implementará cuando tengas las relaciones)
            return Car.objects.all()  # Temporal
        else:
            # Cliente solo ve sus vehículos
            return Car.objects.filter(usuario=user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

# =============================================================================
# VISTAS ESPECÍFICAS PARA EL PANEL WEB
# =============================================================================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_panel_login(request):
    """
    Login específico para el panel administrativo web
    Solo permite acceso a administradores y dueños
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user is not None and user.is_active and not user.eliminado:
        # Verificar que sea admin o owner
        if not user.is_admin_general and not user.is_owner:
            return Response(
                {'error': 'Acceso solo para administradores y dueños'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'rol': user.rol,
                'rol_display': user.get_rol_display(),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_admin': user.is_admin_general,
                'is_owner': user.is_owner
            }
        })
    else:
        return Response(
            {'error': 'Credenciales inválidas o cuenta desactivada'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

# ✅ NUEVA VISTA PARA ACTUALIZAR PERFIL
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_user_profile(request):
    """Vista específica para actualizar el perfil del usuario"""
    user = request.user
    
    # ✅ CAMPOS PERMITIDOS PARA ACTUALIZACIÓN
    allowed_fields = {
        'first_name', 'last_name', 'email', 'telefono',
        'tipo_documento', 'numero_documento', 'fecha_nacimiento',
        'direccion', 'codigo_postal', 'pais'
    }
    
    # Filtrar datos
    data = {k: v for k, v in request.data.items() if k in allowed_fields}
    
    # ✅ PROCESAR FECHA_NACIMIENTO SI VIENE EN FORMATO dd/mm/yyyy
    if 'fecha_nacimiento' in data and data['fecha_nacimiento']:
        try:
            fecha_str = data['fecha_nacimiento']
            # Intentar parsear formato dd/mm/yyyy
            if '/' in fecha_str:
                fecha_obj = datetime.strptime(fecha_str, '%d/%m/%Y').date()
                data['fecha_nacimiento'] = fecha_obj
            # Si ya viene en formato ISO (yyyy-mm-dd), dejarlo como está
            elif '-' in fecha_str:
                data['fecha_nacimiento'] = fecha_str
        except ValueError as e:
            return Response(
                {'error': f'Formato de fecha inválido: {str(e)}. Use dd/mm/yyyy'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Usar el serializer para validar y aplicar cambios
    serializer = UserSerializer(user, data=data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_profile(request):
    """Obtener perfil del usuario actual - SOLO GET"""
    user = request.user
    
    # ✅ USAR EL MÉTODO DEL MODELO PARA OBTENER DATOS COMPLETOS
    return Response(user.obtener_perfil_completo())

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_panel_access(request):
    """Verificar si el usuario tiene acceso al panel administrativo"""
    user = request.user
    has_panel_access = user.is_admin_general or user.is_owner
    
    return Response({
        'has_panel_access': has_panel_access,
        'is_admin': user.is_admin_general,
        'is_owner': user.is_owner,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'rol': user.rol,
            'rol_display': user.get_rol_display()
        }
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminGeneral])
def admin_dashboard_stats(request):
    """Estadísticas para el dashboard del administrador general"""
    total_users = User.objects.filter(eliminado=False).count()
    total_owners = User.objects.filter(rol='owner', eliminado=False).count()
    total_clients = User.objects.filter(rol='client', eliminado=False).count()
    active_users = User.objects.filter(activo=True, eliminado=False).count()
    
    return Response({
        'total_users': total_users,
        'total_owners': total_owners,
        'total_clients': total_clients,
        'active_users': active_users,
        'users_by_role': {
            'admin': User.objects.filter(rol='admin', eliminado=False).count(),
            'owner': total_owners,
            'client': total_clients
        }
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsOwner])
def owner_dashboard_stats(request):
    
    user = request.user
    
    return Response({
        'user_info': {
            'username': user.username,
            'email': user.email,
            'rol': user.rol
        },
        'parking_stats': {
            'total_spots': 0,
            'available_spots': 0,
            'reserved_spots': 0
        },
        'revenue_stats': {
            'today': 0,
            'this_week': 0,
            'this_month': 0
        }
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def client_dashboard_stats(request):
    """Estadísticas para el dashboard del cliente"""
    user = request.user
    
    return Response({
        'user_info': {
            'username': user.username,
            'email': user.email,
            'telefono': user.telefono
        },
        'stats': {
            'total_parkings': 0,  
            'active_reservations': 0,
            'monthly_earnings': 0
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_own_password(request):
    """Permite al usuario autenticado cambiar su propia contraseña.
    Recibe `old_password` y `new_password` en el body (JSON).
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not old_password or not new_password:
        return Response({'error': 'Se requieren la contraseña actual y la nueva.'}, status=status.HTTP_400_BAD_REQUEST)

    if confirm_password is not None and new_password != confirm_password:
        return Response({'error': 'La nueva contraseña y la confirmación no coinciden.'}, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(old_password):
        return Response({'error': 'Contraseña actual incorrecta.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({'message': 'Contraseña actualizada correctamente'})



# solicitud del owner

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def solicitar_acceso_owner(request):
    """
    Endpoint público para solicitar acceso como owner
    Recibe: nombre, email, telefono, empresa, mensaje
    """
    serializer = SolicitudAccesoOwnerSerializer(data=request.data)
    
    if serializer.is_valid():
        # Verificar si ya existe una solicitud pendiente con este email
        email = serializer.validated_data['email']
        solicitud_existente = SolicitudAccesoOwner.objects.filter(
            email=email, 
            estado='pendiente'
        ).exists()
        
        if solicitud_existente:
            return Response(
                {'error': 'Ya tienes una solicitud pendiente con este email'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        solicitud = serializer.save()
        
        #  Enviar email de confirmación de recepción
        try:
            from_email = (getattr(settings, 'DEFAULT_FROM_EMAIL', None) or
                          getattr(settings, 'EMAIL_HOST_USER', None) or
                          'no-reply@parkeaya.com')
            from_email = from_email.strip() if isinstance(from_email, str) else from_email

            send_mail(
                'Solicitud de Registro Recibida - ParkEA',
                f'Hola {solicitud.nombre},\n\n'
                f'Hemos recibido tu solicitud para registrar "{solicitud.empresa}".\n'
                f'Tu solicitud será revisada por nuestro equipo administrativo y te notificaremos el resultado.\n\n'
                f'Gracias por elegir ParkEA.',
                from_email,
                [solicitud.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error enviando email: {e}")
        
        return Response(
            {
                'message': 'Solicitud enviada correctamente. Será revisada por el administrador.',
                'solicitud_id': solicitud.id
            },
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminGeneral])
def listar_solicitudes_pendientes(request):
    """
    Listar solicitudes pendientes para el admin
    """
    estado = request.GET.get('estado', 'pendiente')
    if estado == 'todas':
        solicitudes = SolicitudAccesoOwner.objects.all().order_by('-fecha_solicitud')
    else:
        solicitudes = SolicitudAccesoOwner.objects.filter(estado=estado).order_by('-fecha_solicitud')
    
    serializer = SolicitudAccesoOwnerSerializer(solicitudes, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminGeneral])
def revisar_solicitud_owner(request, solicitud_id):
    """
    Aprobar o rechazar una solicitud
    """
    try:
        solicitud = SolicitudAccesoOwner.objects.get(id=solicitud_id, estado='pendiente')
    except SolicitudAccesoOwner.DoesNotExist:
        return Response(
            {'error': 'Solicitud no encontrada o ya revisada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Envolver lógica en try/except para capturar errores y facilitar debugging
    try:
        print(f"\n=== REVISAR SOLICITUD {solicitud_id} ===")
        print(f"Request data: {request.data}")
        
        serializer = SolicitudRevisionSerializer(data=request.data)

        if serializer.is_valid():
            estado = serializer.validated_data['estado']
            comentarios = serializer.validated_data.get('comentarios_rechazo', '')

            # Normalizar valores (aceptar 'aprobada'/'aprobado')
            if estado in ('aprobada', 'aprobado'):
                estado = 'aprobado'
            elif estado in ('rechazada', 'rechazado'):
                estado = 'rechazado'

            print(f"Estado normalizado: {estado}")
            
            solicitud.estado = estado
            solicitud.comentarios_rechazo = comentarios
            solicitud.fecha_revision = timezone.now()
            solicitud.revisado_por = request.user

            if estado == 'aprobado':
                # Generar usuario y contraseña automáticos
                username = generar_username_unico(solicitud.email)
                password = generar_password_aleatoria()

                print(f"Creando usuario: {username}")
                
                # Crear el usuario owner
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=solicitud.email,
                        password=password,
                        first_name=solicitud.nombre.split(' ')[0],
                        last_name=' '.join(solicitud.nombre.split(' ')[1:]) if len(solicitud.nombre.split(' ')) > 1 else '',
                        telefono=solicitud.telefono,
                        rol='owner'
                    )

                    solicitud.usuario_creado = user
                    print(f"✓ Usuario creado: {username}")

                    # Enviar email con credenciales
                    try:
                        print(f"Enviando email a: {solicitud.email}")
                        from_email = (getattr(settings, 'DEFAULT_FROM_EMAIL', None) or
                                      getattr(settings, 'EMAIL_HOST_USER', None) or
                                      'no-reply@parkeaya.com')
                        from_email = from_email.strip() if isinstance(from_email, str) else from_email

                        try:
                            send_mail(
                                'Solicitud Aprobada - Credenciales ParkeaYa',
                                f'Hola {solicitud.nombre},\n\n'
                                f'¡Felicidades! Tu solicitud para "{solicitud.empresa}" ha sido APROBADA.\n\n'
                                f'Tus credenciales de acceso son:\n'
                                f'Usuario: {username}\n'
                                f'Contraseña: {password}\n\n'
                                f'Puedes acceder a tu panel owner en: {settings.FRONTEND_URL}/owner/login\n\n'
                                f'Te recomendamos cambiar tu contraseña después del primer acceso.\n\n'
                                f'Bienvenido a ParkeaYa!',
                                from_email,
                                [solicitud.email],
                                fail_silently=False,
                            )
                            print(f"✓ Email enviado")
                        except Exception as e:
                            print(f"✗ Error enviando email: {str(e)}")
                            logger.exception(f"Error enviando email para solicitud {solicitud_id}: from={from_email} to={solicitud.email}")
                            try:
                                user.delete()
                            except Exception:
                                pass
                            return Response(
                                {'error': f'Error enviando credenciales por email: {str(e)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                            )
                    except Exception as e:
                        print(f"✗ Error enviando email: {str(e)}")
                        logger.exception(f"Error enviando email para solicitud {solicitud_id}")
                        # Si falla el envío, revertir creación de usuario y devolver error
                        try:
                            user.delete()
                        except Exception:
                            pass
                        return Response(
                            {'error': f'Error enviando credenciales por email: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                except Exception as e:
                    print(f"✗ Error creando usuario: {str(e)}")
                    logger.exception(f"Error creando usuario para solicitud {solicitud_id}")
                    return Response(
                        {'error': f'Error creando usuario: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            else:  # Estado rechazado
                # Enviar email de rechazo
                try:
                    print(f"Enviando email de rechazo a: {solicitud.email}")
                    from_email = (getattr(settings, 'DEFAULT_FROM_EMAIL', None) or
                                  getattr(settings, 'EMAIL_HOST_USER', None) or
                                  'no-reply@parkeaya.com')
                    from_email = from_email.strip() if isinstance(from_email, str) else from_email
                    try:
                        send_mail(
                            'Solicitud Rechazada - ParkEA',
                            f'Hola {solicitud.nombre},\n\n'
                            f'Lamentamos informarte que tu solicitud para "{solicitud.empresa}" ha sido RECHAZADA.\n\n'
                            f'Motivo: {comentarios}\n\n'
                            f'Si tienes alguna pregunta, por favor contacta con nuestro soporte.\n\n'
                            f'Saludos,\nEquipo ParkeaYa',
                            from_email,
                            [solicitud.email],
                            fail_silently=True,
                        )
                        print(f"✓ Email de rechazo enviado")
                    except Exception as e:
                        print(f"✗ Error enviando email de rechazo: {str(e)}")
                        logger.warning(f"Error enviando email de rechazo para solicitud {solicitud_id}: {str(e)} from={from_email} to={solicitud.email}")
                except Exception as e:
                    # log error pero no revertir
                    print(f"✗ Error enviando email de rechazo: {str(e)}")
                    logger.warning(f"Error enviando email de rechazo para solicitud {solicitud_id}: {str(e)}")

            solicitud.save()
            print(f"✓ Solicitud guardada como {estado}")

            return Response({
                'message': f'Solicitud {estado} correctamente',
                'solicitud': SolicitudAccesoOwnerSerializer(solicitud).data
            })

        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as exc:
        tb_str = traceback.format_exc()
        print(f"\n✗✗✗ EXCEPTION EN revisar_solicitud_owner ✗✗✗")
        print(tb_str)
        print(f"✗✗✗ FIN EXCEPTION ✗✗✗\n")
        logger.exception(f"Exception en revisar_solicitud_owner para solicitud {solicitud_id}")
        return Response(
            {'error': 'Internal server error', 'details': str(exc)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def generar_username_unico(email):
    """Genera un username único basado en el email"""
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def generar_password_aleatoria(longitud=12):
    """Genera una contraseña aleatoria segura"""
    caracteres = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Permite al usuario cambiar su contraseña desde el perfil"""
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    print(f" [CAMBIAR CONTRASEÑA] Usuario: {user.username}")
    
    if not all([old_password, new_password]):
        return Response(
            {'error': 'Se requieren la contraseña actual y la nueva'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar confirmación si se proporciona
    if confirm_password and new_password != confirm_password:
        return Response(
            {'error': 'La nueva contraseña y la confirmación no coinciden'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar contraseña actual
    if not user.check_password(old_password):
        print(" [CAMBIAR CONTRASEÑA] Contraseña actual incorrecta")
        return Response(
            {'error': 'Contraseña actual incorrecta'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar longitud de nueva contraseña
    if len(new_password) < 6:
        return Response(
            {'error': 'La nueva contraseña debe tener al menos 6 caracteres'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Cambiar contraseña
    user.set_password(new_password)
    user.save()
    
    print(" [CAMBIAR CONTRASEÑA] Contraseña actualizada exitosamente")
    
    return Response({'message': 'Contraseña actualizada correctamente'})

