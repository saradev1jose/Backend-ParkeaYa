# reservations/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, datetime
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.db.models import Count, Q
from django.db.models import Count, Sum, Q 

from .permissions import (
    IsAdminGeneral, IsOwner, IsClient, IsAdminOrOwner,
    IsOwnerOfParkingReservation, IsAdminOrOwnerOfReservation, CanManageReservations
)
from .models import Reservation
from .serializers import (
    ReservationClientSerializer, ReservationOwnerSerializer, 
    ReservationAdminSerializer, ReservationDetailSerializer,
    ExtendReservationSerializer, CheckInResponseSerializer,
    CheckOutResponseSerializer, ReservationStatsSerializer,
    ParkingReservationsResponseSerializer
)
from parking.models import ParkingLot
from users.models import Car
from django.shortcuts import render, redirect
from django.conf import settings

# ----------------------------
# VISTAS PARA WEBVIEW MÓVIL
# ----------------------------


def mobile_login_via_token(request):
    """
    Endpoint simple para que la app WebView pueda pasar un token JWT
    en la URL y se establezca como cookie para las siguientes peticiones.

    Uso: /api/reservations/mobile/login/?token=<JWT>&next=/api/reservations/mobile/reservas/
    """
    token = request.GET.get('token')
    next_url = request.GET.get('next') or '/api/reservations/mobile/reservas/'

    response = redirect(next_url)
    if token:
        cookie_name = getattr(settings, 'REST_AUTH', {}).get('JWT_AUTH_COOKIE', 'jwt-auth')
        # Poner cookie no HttpOnly para que JS en WebView pueda leerla y añadir Authorization header
        response.set_cookie(cookie_name, token, httponly=False)
    return response


def mobile_reservas_page(request):
    """Renderiza la pantalla de reservas para WebView.
    La plantilla consumirá la API REST (`/api/reservations/client/mis-reservas/`).
    """
    return render(request, 'reservations/mobile_reservas.html')


def mobile_pago_page(request):
    """Renderiza la pantalla de pago para WebView.

    Espera `?reserva=<uuid>` para preseleccionar la reserva.
    """
    reserva_id = request.GET.get('reserva')
    return render(request, 'reservations/mobile_pago.html', {'reserva_id': reserva_id})

# =============================================================================
# VISTA PRINCIPAL DE RESERVAS
# =============================================================================

class ReservationViewSet(viewsets.ModelViewSet):
    """Vista principal de reservas - Comportamiento diferenciado por rol"""
    # Asegurar que el ViewSet acepte tokens JWT además de autenticación por sesión
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    queryset = Reservation.objects.all().select_related(
        'usuario', 'vehiculo', 'estacionamiento'
    ).order_by('-created_at')
    
    @action(detail=False, methods=['get', 'post', 'put', 'patch', 'delete'])
    def reservations(self, request):
        if request.method == 'GET':
            return self.list(request)
        elif request.method == 'POST':
            return self.create(request)
    
    def get_serializer_class(self):
        """Selecciona serializer según el rol del usuario"""
        user = self.request.user
        
        if not user.is_authenticated:
            return ReservationDetailSerializer
            
        if user.is_admin_general:
            return ReservationAdminSerializer
        elif user.is_owner:
            return ReservationOwnerSerializer
        else:
            # PARA CLIENTES: Usar ReservationClientSerializer para CREATE
            if self.action == 'create':
                return ReservationClientSerializer
            return ReservationDetailSerializer

    def get_queryset(self):
        """Filtra reservas según el rol del usuario"""
        user = self.request.user
        
        if not user.is_authenticated:
            return Reservation.objects.none()
            
        if user.is_admin_general:
            return self.queryset
        elif user.is_owner:
            return self.queryset.filter(estacionamiento__dueno=user)
        else:
            return self.queryset.filter(usuario=user)

    def get_permissions(self):
        """Configura permisos según la acción y rol - CORREGIDO"""
        if self.action in ['list', 'retrieve', 'tipos_reserva']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
            # ✅ PERMITIR POST A TODOS LOS USUARIOS AUTENTICADOS
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy', 'cancel', 'extend']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrOwnerOfReservation]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Crear reserva - PARA TODOS LOS USUARIOS AUTENTICADOS
        """
        data = request.data.copy()
        user = request.user

        vehiculo_id = data.get('vehiculo')
        estacionamiento_id = data.get('estacionamiento')
        hora_entrada = data.get('hora_entrada')
        duracion_minutos = int(data.get('duracion_minutos', 60))
        tipo_reserva = data.get('tipo_reserva', 'hora')

        # Validaciones básicas -> devolver errores por campo para el cliente
        errors = {}
        if not vehiculo_id:
            errors['vehiculo'] = ['Este campo es requerido.']
        if not estacionamiento_id:
            errors['estacionamiento'] = ['Este campo es requerido.']
        if not hora_entrada:
            errors['hora_entrada'] = ['Este campo es requerido.']
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # ✅ CORRECCIÓN: Buscar PRIMERO en Vehicle y convertir a Car si es necesario
        vehiculo_car = None
        user_vehicles = []
        user_cars = []
        
        try:
            from vehicles.models import Vehicle as ExternalVehicle
            try:
                # Buscar en Vehicle primero
                vehiculo_external = ExternalVehicle.objects.get(id=vehiculo_id, usuario=user)
                
                # ✅ CONVERTIR: Crear o obtener un Car equivalente
                vehiculo_car, created = Car.objects.get_or_create(
                    placa=vehiculo_external.placa,
                    usuario=user,
                    defaults={
                        'modelo': getattr(vehiculo_external, 'modelo', ''),
                        'marca': getattr(vehiculo_external, 'marca', ''),
                        'tipo': 'auto',
                        'color': getattr(vehiculo_external, 'color', '')
                    }
                )
                
            except ExternalVehicle.DoesNotExist:
                pass
            user_vehicles = list(ExternalVehicle.objects.filter(usuario=user).values('id', 'placa'))
        except ImportError:
            pass

        # Si no encontró en vehicles, intentar en Car directamente
        if not vehiculo_car:
            try:
                vehiculo_car = Car.objects.get(id=vehiculo_id, usuario=user)
            except Car.DoesNotExist:
                pass
            user_cars = list(Car.objects.filter(usuario=user).values('id', 'placa'))

        # Si no encontró en ningún lado, retornar error
        if not vehiculo_car:
            return Response(
                {
                    'vehiculo': ['Vehículo no encontrado o no pertenece al usuario.'],
                    'user_vehicles': user_vehicles,
                    'user_cars': user_cars
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Ahora usar vehiculo_car (que es del modelo Car)
        vehiculo = vehiculo_car

        # Bloquear estacionamiento para evitar overbooking
        try:
            parking = ParkingLot.objects.select_for_update().get(
                pk=estacionamiento_id, 
                aprobado=True, 
                activo=True
            )
        except ParkingLot.DoesNotExist:
            return Response(
                {'estacionamiento': ['Estacionamiento no disponible.']},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar disponibilidad
        if parking.plazas_disponibles <= 0:
            return Response(
                {'estacionamiento': ['No hay plazas disponibles en este momento.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parsear hora de entrada
        try:
            from django.utils.dateparse import parse_datetime
            entrada_dt = parse_datetime(hora_entrada)

            # Fallback: aceptar formatos comunes (espacio y T)
            if entrada_dt is None:
                try:
                    entrada_dt = datetime.strptime(hora_entrada, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    try:
                        entrada_dt = datetime.strptime(hora_entrada, "%Y-%m-%dT%H:%M:%S")
                    except Exception:
                        entrada_dt = None

            if entrada_dt is None:
                raise ValueError("invalid datetime")

            # Normalizar a timezone-aware si es naive (asumir UTC)
            if entrada_dt.tzinfo is None:
                from django.utils.timezone import make_aware
                try:
                    entrada_dt = make_aware(entrada_dt)
                except Exception:
                    # si no se puede hacer aware, dejar como está y comparar en UTC
                    pass

            # Verificar que la reserva no sea en el pasado
            if entrada_dt < timezone.now():
                return Response(
                    {'hora_entrada': ['No se pueden hacer reservas en el pasado.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except ValueError:
            return Response(
                {'hora_entrada': ['Formato de hora_entrada inválido. Use formato ISO (ej: 2025-11-29T04:30:00 o 2025-11-29 04:30:00).']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar tipo de reserva
        if tipo_reserva == 'dia' and not hasattr(parking, 'precio_dia'):
            return Response(
                {'tipo_reserva': ['Este estacionamiento no acepta reservas por día.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif tipo_reserva == 'mes' and not hasattr(parking, 'precio_mes'):
            return Response(
                {'tipo_reserva': ['Este estacionamiento no acepta reservas por mes.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar duración mínima según tipo de reserva
        if tipo_reserva == 'hora' and duracion_minutos < 60:
            return Response(
                {'duracion_minutos': ['La duración mínima para reserva por hora es 60 minutos.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif tipo_reserva == 'dia' and duracion_minutos < 1440:
            return Response(
                {'duracion_minutos': ['La duración mínima para reserva por día es 24 horas.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif tipo_reserva == 'mes' and duracion_minutos < 43200:
            return Response(
                {'duracion_minutos': ['La duración mínima para reserva por mes es 30 días.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar conflictos de reserva para el mismo vehículo
        salida_dt = entrada_dt + timedelta(minutes=duracion_minutos)
        reservas_conflicto = Reservation.objects.filter(
            vehiculo=vehiculo,
            hora_entrada__lt=salida_dt,
            hora_salida__gt=entrada_dt,
            estado__in=['activa', 'confirmada']
        )
        
        if reservas_conflicto.exists():
            return Response(
                {'non_field_errors': ['El vehículo ya tiene una reserva en ese horario.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcular costo (usar tarifa_hora como base)
        precio_por_minuto = float(parking.tarifa_hora) / 60.0
        costo_estimado = round(precio_por_minuto * duracion_minutos, 2)

        # Reducir plazas disponibles
        parking.plazas_disponibles -= 1
        parking.save()

        # Crear reserva
        create_payload = {
            'vehiculo': vehiculo.id,
            'estacionamiento': estacionamiento_id,
            'hora_entrada': entrada_dt,
            'hora_salida': salida_dt,
            'duracion_minutos': duracion_minutos,
            'costo_estimado': costo_estimado,
            'tipo_reserva': tipo_reserva
        }

        serializer = self.get_serializer(data=create_payload)
        serializer.is_valid(raise_exception=True)
        reservation = serializer.save(usuario=user)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancelar reserva
        """
        # ✅ pk contiene el UUID de la reserva
        reservation = self.get_object()
        user = request.user

        # Verificar que se pueda cancelar
        if reservation.estado != 'activa':
            return Response(
                {'detail': 'Solo se pueden cancelar reservas activas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reservation.hora_entrada <= timezone.now():
            return Response(
                {'detail': 'No se puede cancelar una reserva que ya comenzó.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cancelar reserva y liberar plaza
        with transaction.atomic():
            parking = ParkingLot.objects.select_for_update().get(pk=reservation.estacionamiento.id)
            parking.plazas_disponibles += 1
            parking.save()
            
            reservation.estado = 'cancelada'
            reservation.save()

        return Response(
            {'detail': 'Reserva cancelada exitosamente.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        """
        Extender tiempo de reserva
        """
        reservation = self.get_object()
        serializer = ExtendReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        minutos_extra = serializer.validated_data['minutos_extra']
        tipo_reserva_extension = serializer.validated_data.get('tipo_reserva', reservation.tipo_reserva)

        if reservation.estado != 'activa':
            return Response(
                {'detail': 'Solo se pueden extender reservas activas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcular costo extra (usar tarifa_hora como base)
        parking = reservation.estacionamiento
        precio_por_minuto = float(parking.tarifa_hora) / 60.0
        costo_extra = round(precio_por_minuto * minutos_extra, 2)

        with transaction.atomic():
            reservation.hora_salida += timedelta(minutes=minutos_extra)
            reservation.duracion_minutos += minutos_extra
            reservation.costo_estimado += Decimal(str(costo_extra))
            reservation.tipo_reserva = tipo_reserva_extension
            reservation.save()

        response_serializer = self.get_serializer(reservation)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def tipos_reserva(self, request):
        """
        Obtener los tipos de reserva disponibles
        """
        return Response({
            'tipos_reserva': [
                {'value': 'hora', 'label': 'Por Hora', 'duracion_minima': 60},
                {'value': 'dia', 'label': 'Por Día', 'duracion_minima': 1440},
                {'value': 'mes', 'label': 'Por Mes', 'duracion_minima': 43200},
            ]
        })

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsClient])
    def mis_reservas(self, request):
        """
        Reservas del usuario actual (para clientes)
        """
        reservations = self.get_queryset().filter(usuario=request.user)
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsOwner])
    def reservas_estacionamiento(self, request):
        """
        Reservas de los estacionamientos del dueño
        """
        reservations = self.get_queryset().filter(estacionamiento__dueno=request.user)
        
        # Filtros
        estado = request.GET.get('estado')
        fecha = request.GET.get('fecha')
        tipo_reserva = request.GET.get('tipo_reserva')
        
        if estado:
            reservations = reservations.filter(estado=estado)
        if fecha:
            reservations = reservations.filter(hora_entrada__date=fecha)
        if tipo_reserva:
            reservations = reservations.filter(tipo_reserva=tipo_reserva)
            
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)

# =============================================================================
# VISTAS ESPECÍFICAS
# =============================================================================

class CheckInView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwnerOfReservation]

    def post(self, request, codigo_reserva):
        """
        Check-in usando código QR/numérico
        """
        reservation = get_object_or_404(Reservation, codigo_reserva=codigo_reserva)
        
        # Verificar permisos mediante el permission class

        if reservation.estado != 'activa':
            return Response(
                {'detail': 'La reserva no está activa.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que no sea demasiado temprano para check-in
        tiempo_antes = (reservation.hora_entrada - timezone.now()).total_seconds() / 60
        if tiempo_antes > 30:
            return Response(
                {'detail': 'Solo puede hacer check-in hasta 30 minutos antes de la reserva.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Marcar como check-in
        reservation.estado = 'activa'  # Podrías agregar un campo específico para check-in
        reservation.save()

        response_data = {
            'detail': 'Check-in realizado exitosamente.',
            'reserva': ReservationDetailSerializer(reservation).data
        }
        # Devolver directamente el dict serializado para evitar doble-serialización
        return Response(response_data)

class CheckOutView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwnerOfReservation]

    def post(self, request, codigo_reserva):
        """
        Check-out y liberar espacio
        """
        reservation = get_object_or_404(Reservation, codigo_reserva=codigo_reserva)

        if reservation.estado != 'activa':
            return Response(
                {'detail': 'La reserva no está activa.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Liberar espacio en el estacionamiento
            parking = ParkingLot.objects.select_for_update().get(pk=reservation.estacionamiento.id)
            parking.plazas_disponibles += 1
            parking.save()

            # Calcular tiempo real y costo final
            hora_salida_real = timezone.now()
            tiempo_real_minutos = max(0, (hora_salida_real - reservation.hora_entrada).total_seconds() / 60)
            
            # Calcular costo final (usar tarifa_hora como base)
            precio_por_minuto = float(parking.tarifa_hora) / 60.0
            
            # Aplicar política de tolerancia (15 minutos gratis)
            tolerancia_minutos = 15
            if tiempo_real_minutos <= tolerancia_minutos:
                costo_final = Decimal('0.00')
            else:
                tiempo_cobrable = tiempo_real_minutos - tolerancia_minutos
                costo_final = Decimal(str(round(precio_por_minuto * tiempo_cobrable, 2)))

            reservation.hora_salida = hora_salida_real
            reservation.duracion_minutos = int(tiempo_real_minutos)
            reservation.costo_estimado = costo_final
            reservation.estado = 'finalizada'
            reservation.save()

        response_data = {
            'detail': 'Check-out realizado exitosamente.',
            'costo_final': costo_final,
            'tiempo_estacionado_minutos': round(tiempo_real_minutos, 2),
            'tipo_reserva': reservation.tipo_reserva,
            'reserva': ReservationDetailSerializer(reservation).data
        }
        # Devolver directamente el dict serializado para evitar errores en nested fields
        return Response(response_data)

class UserActiveReservationsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClient]

    def get(self, request):
        """
        Obtener reservas activas del usuario (solo para clientes)
        """
        reservations = Reservation.objects.filter(
            usuario=request.user,
            estado='activa',
            hora_salida__gt=timezone.now()
        ).order_by('hora_entrada')
        
        serializer = ReservationDetailSerializer(reservations, many=True)
        return Response(serializer.data)

class ParkingReservationsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get(self, request, parking_id):
        """
        Obtener reservas de un estacionamiento específico (para dueños)
        """
        # Verificar que el parking pertenece al usuario
        parking = get_object_or_404(ParkingLot, id=parking_id, dueno=request.user)

        estado = request.GET.get('estado')
        fecha = request.GET.get('fecha')
        tipo_reserva = request.GET.get('tipo_reserva')
        
        reservations = Reservation.objects.filter(estacionamiento=parking)
        
        if estado:
            reservations = reservations.filter(estado=estado)
        if fecha:
            reservations = reservations.filter(hora_entrada__date=fecha)
        if tipo_reserva:
            reservations = reservations.filter(tipo_reserva=tipo_reserva)
            
        reservations = reservations.order_by('-hora_entrada')
        serializer = ReservationDetailSerializer(reservations, many=True)
        
        response_data = {
            'estacionamiento': parking.nombre,
            'total_reservas': reservations.count(),
            'reservas': serializer.data
        }
        serializer_response = ParkingReservationsResponseSerializer(response_data)
        return Response(serializer_response.data)

class ReservationStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Estadísticas de reservas según el rol del usuario
        """
        user = request.user
        stats = {}

        if user.is_admin_general:
            # Estadísticas para administradores
            reservations = Reservation.objects.all()
            
            stats['total_reservas'] = reservations.count()
            stats['reservas_activas'] = reservations.filter(estado='activa').count()
            stats['reservas_hoy'] = reservations.filter(
                hora_entrada__date=timezone.now().date()
            ).count()
            
            # Por tipo de reserva
            stats['por_tipo_reserva'] = {
                'hora': reservations.filter(tipo_reserva='hora').count(),
                'dia': reservations.filter(tipo_reserva='dia').count(),
                'mes': reservations.filter(tipo_reserva='mes').count(),
            }

            # Por tipo de vehículo
            stats['por_tipo_vehiculo'] = list(reservations.values(
                'vehiculo__tipo'
            ).annotate(total=Count('id')).order_by('-total'))

        elif user.is_owner:
            # Estadísticas para dueños
            user_parkings = ParkingLot.objects.filter(dueno=user)
            reservations = Reservation.objects.filter(estacionamiento__in=user_parkings)
            
            stats['total_reservas'] = reservations.count()
            stats['reservas_activas'] = reservations.filter(estado='activa').count()
            stats['reservas_hoy'] = reservations.filter(
                hora_entrada__date=timezone.now().date()
            ).count()
            
            # Por tipo de reserva
            stats['por_tipo_reserva'] = {
                'hora': reservations.filter(tipo_reserva='hora').count(),
                'dia': reservations.filter(tipo_reserva='dia').count(),
                'mes': reservations.filter(tipo_reserva='mes').count(),
            }

            # Por estacionamiento
            stats['por_estacionamiento'] = list(reservations.values(
                'estacionamiento__nombre'
            ).annotate(total=Count('id')).order_by('-total'))

        else:
            # Estadísticas para clientes
            user_reservations = Reservation.objects.filter(usuario=user)
            
            stats['total_reservas'] = user_reservations.count()
            stats['reservas_activas'] = user_reservations.filter(estado='activa').count()
            stats['reservas_hoy'] = user_reservations.filter(
                hora_entrada__date=timezone.now().date()
            ).count()
            
            # Por tipo de reserva
            stats['por_tipo_reserva'] = {
                'hora': user_reservations.filter(tipo_reserva='hora').count(),
                'dia': user_reservations.filter(tipo_reserva='dia').count(),
                'mes': user_reservations.filter(tipo_reserva='mes').count(),
            }

        serializer = ReservationStatsSerializer(stats)
        return Response(serializer.data)

# =============================================================================
# VISTAS PARA DASHBOARD
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminGeneral])
def admin_reservations_stats(request):
    """Estadísticas de reservas para dashboard de administrador"""
    today = timezone.now().date()
    
    stats = {
        'total_reservas': Reservation.objects.count(),
        'reservas_hoy': Reservation.objects.filter(hora_entrada__date=today).count(),
        'reservas_activas': Reservation.objects.filter(estado='activa').count(),
        'ingresos_hoy': Reservation.objects.filter(
            hora_entrada__date=today,
            estado='finalizada'
        ).aggregate(total=Sum('costo_estimado'))['total'] or 0,
        'reservas_por_tipo': {
            'hora': Reservation.objects.filter(tipo_reserva='hora').count(),
            'dia': Reservation.objects.filter(tipo_reserva='dia').count(),
            'mes': Reservation.objects.filter(tipo_reserva='mes').count(),
        }
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsOwner])
def owner_reservations_stats(request):
    """Estadísticas de reservas para dashboard de dueño"""
    today = timezone.now().date()
    user_parkings = ParkingLot.objects.filter(dueno=request.user)
    reservations = Reservation.objects.filter(estacionamiento__in=user_parkings)
    
    stats = {
        'total_reservas': reservations.count(),
        'reservas_hoy': reservations.filter(hora_entrada__date=today).count(),
        'reservas_activas': reservations.filter(estado='activa').count(),
        'ingresos_hoy': reservations.filter(
            hora_entrada__date=today,
            estado='finalizada'
        ).aggregate(total=Sum('costo_estimado'))['total'] or 0,
        'reservas_por_estacionamiento': list(
            reservations.values('estacionamiento__nombre')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
    }
    
    return Response(stats)