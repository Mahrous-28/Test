from rest_framework import serializers
from .models import Advertisement

class AdvertisementSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    
    class Meta:
        model = Advertisement
        fields = ['id', 'description', 'image_description', 'generated_content', 'image', 'created_at']
