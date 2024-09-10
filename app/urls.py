from django.urls import path
from .views import *

urlpatterns = [
    path('', index),
    path('ships/<int:ship_id>/', ship),
    path('orders/<int:order_id>/', order),
]