from django.contrib.auth.models import User
from rest_framework import serializers
from .models import PolygonFeature 

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password' : {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    

 # Import your model

class PolygonFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolygonFeature
        fields = '__all__'  # Or specify fields like ['id', 'name', 'geom']