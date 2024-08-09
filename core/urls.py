from django.urls import path
from core.views import ImageStatusView, ImageUploadView


app_name = "core"
urlpatterns = [
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
    path('status/<str:task_id>/', ImageStatusView.as_view(), name='image-status'),
]
