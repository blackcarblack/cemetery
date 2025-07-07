# serializers.py
from rest_framework import serializers
from .models import GoITeens

class GoITeensSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoITeens
        fields = ('id', 'name')
