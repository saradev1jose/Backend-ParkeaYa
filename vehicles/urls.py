from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('vehicles/', views.UserVehicleListCreateView.as_view(), name='user-vehicles'),
    path('vehicles/<int:pk>/', views.UserVehicleDetailView.as_view(), name='vehicle-detail'),
]