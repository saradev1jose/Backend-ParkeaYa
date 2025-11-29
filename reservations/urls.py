from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReservationViewSet, 
    CheckInView, 
    CheckOutView, 
    UserActiveReservationsView, 
    ParkingReservationsView,
    ReservationStatsView,
    admin_reservations_stats,
    owner_reservations_stats
)
from .views import mobile_login_via_token, mobile_reservas_page, mobile_pago_page

router = DefaultRouter()
# Registrar el ViewSet en el router con prefijo vacío para que, al incluirse
# en `path('api/reservations/', include(...))` en el archivo principal,
# las rutas queden en `/api/reservations/` (en vez de `/api/reservations/reservations/`).
router.register(r'', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),
    
    # Endpoints específicos de reservas por rol
    path('client/active/', UserActiveReservationsView.as_view(), name='user-active-reservations'),
    path('owner/parking/<int:parking_id>/', ParkingReservationsView.as_view(), name='parking-reservations'),
    path('stats/', ReservationStatsView.as_view(), name='reservation-stats'),
    
    # Endpoints para dashboards
    path('dashboard/admin/stats/', admin_reservations_stats, name='admin-reservations-stats'),
    path('dashboard/owner/stats/', owner_reservations_stats, name='owner-reservations-stats'),
    
    # Endpoints por código de reserva
    path('<uuid:codigo_reserva>/checkin/', CheckInView.as_view(), name='checkin'),
    path('<uuid:codigo_reserva>/checkout/', CheckOutView.as_view(), name='checkout'),
    
    # Endpoints de acciones específicas
    path('<uuid:codigo_reserva>/cancel/', 
         ReservationViewSet.as_view({'post': 'cancel'}), 
         name='cancel-reservation'),
    path('<uuid:codigo_reserva>/extend/', 
         ReservationViewSet.as_view({'post': 'extend'}), 
         name='extend-reservation'),
    path('tipos/', 
         ReservationViewSet.as_view({'get': 'tipos_reserva'}), 
         name='reservation-tipos'),
    
    # Endpoints específicos por rol
    path('client/mis-reservas/', 
         ReservationViewSet.as_view({'get': 'mis_reservas'}), 
         name='mis-reservas'),
    path('owner/reservas/', 
         ReservationViewSet.as_view({'get': 'reservas_estacionamiento'}), 
         name='reservas-estacionamiento'),

    # Páginas para WebView móvil
    path('mobile/login/', mobile_login_via_token, name='mobile-login'),
    path('mobile/reservas/', mobile_reservas_page, name='mobile-reservas'),
    path('mobile/pago/', mobile_pago_page, name='mobile-pago'),
]