from rest_framework import serializers
from .models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            'id', 'placa', 'marca', 'modelo', 'color',
            'activo', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']

class CreateVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['placa', 'marca', 'modelo', 'color']

    def create(self, validated_data):
        user = self.context['request'].user
        return Vehicle.objects.create(usuario=user, **validated_data)

    def validate_placa(self, value):
        # Validar formato de placa de automóvil
        value = value.upper().strip()
        if len(value) < 6 or len(value) > 8:
            raise serializers.ValidationError("La placa debe tener entre 6 y 8 caracteres")
        return value