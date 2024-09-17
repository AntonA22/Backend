from django.urls import path
from .views import *

urlpatterns = [
    path('', index),
    path('ships/<int:ship_id>/', ship),
    path('flights/<int:flight_id>/', flight),
]