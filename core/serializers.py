# myapp/serializers.py
from rest_framework import serializers
from .models import UploadedImage

class UploadedImageSerializer(serializers.ModelSerializer):
    task_id = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    model_data = serializers.JSONField(required=False)

    class Meta:
        model = UploadedImage
        fields = ('id', 'image', 'uploaded_at', 'task_id', 'status', 'model_data')
