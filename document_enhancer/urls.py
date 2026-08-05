from django.urls import path
from . import views

app_name = 'document_enhancer'

urlpatterns = [
    path('', views.enhancer_view, name='enhancer'),
]
