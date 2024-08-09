# myapp/models.py
from django.db import models


class UploadedImage(models.Model):
    image = models.ImageField(upload_to='images/')
    task_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='processing')
    model_data = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    glb_file = models.FileField(upload_to='models/', null=True, blank=True)
    usdz_file = models.FileField(upload_to='models/', null=True, blank=True)

    def __str__(self):
        return self.task_id