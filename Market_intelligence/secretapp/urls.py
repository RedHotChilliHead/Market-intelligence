from django.urls import path, include
from .views import GenerateAPIView, SecretAPIView

app_name = "secretapp"

urlpatterns = [
    path('generate/', GenerateAPIView.as_view(), name='generate'),
    path('secrets/<str:secret_key>/', SecretAPIView.as_view(), name='secret'),
]
