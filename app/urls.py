from django.urls import path
from .views import *

urlpatterns = [
    path('', index),
    path('ships/<int:ship_id>/', ship_details),
    path('ships/<int:ship_id>/add_to_flight/', add_ship_to_draft_flight),
    path('flights/<int:flight_id>/delete/', delete_flight),
    path('flights/<int:flight_id>/', flight)
]
