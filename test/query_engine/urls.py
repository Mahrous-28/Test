from django.urls import path
from .views import GenerateAdvertView

urlpatterns = [
    path('generate/', GenerateAdvertView.as_view(), name='generate-advert'),
]