from rest_framework import generics, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Vehicle
from .serializers import VehicleSerializer, CreateVehicleSerializer

class UserVehicleListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateVehicleSerializer
        return VehicleSerializer

    def get_queryset(self):
        return Vehicle.objects.filter(usuario=self.request.user, activo=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class UserVehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vehicle.objects.filter(usuario=self.request.user)

    def perform_destroy(self, instance):
        # Soft delete
        instance.activo = False
        instance.save()