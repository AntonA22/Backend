from django.urls import path
from .views import *

urlpatterns = [
    # Набор методов для услуг
    path('api/ships/', search_ships),  # GET
    path('api/ships/<int:ship_id>/', get_ship_by_id),  # GET
    path('api/ships/<int:ship_id>/update/', update_ship),  # PUT
    path('api/ships/<int:ship_id>/update_image/', update_ship_image),  # POST
    path('api/ships/<int:ship_id>/delete/', delete_ship),  # DELETE
    path('api/ships/create/', create_ship),  # POST
    path('api/ships/<int:ship_id>/add_to_flight/', add_ship_to_flight),  # POST

    # Набор методов для заявок
    path('api/flights/', search_flights),  # GET
    path('api/flights/<int:flight_id>/', get_flight_by_id),  # GET
    path('api/flights/<int:flight_id>/update/', update_flight),  # PUT
    path('api/flights/<int:flight_id>/update_status_user/', update_status_user),  # PUT
    path('api/flights/<int:flight_id>/update_status_admin/', update_status_admin),  # PUT
    path('api/flights/<int:flight_id>/delete/', delete_flight),  # DELETE

    # Набор методов для м-м
    path('api/flights/<int:flight_id>/ships/<int:ship_id>/', get_ship_flight),  # GET
    path('api/flights/<int:flight_id>/update_ship/<int:ship_id>/', update_ship_in_flight),  # PUT
    path('api/flights/<int:flight_id>/delete_ship/<int:ship_id>/', delete_ship_from_flight),  # DELETE

    # Набор методов для аутентификации и авторизации
    path("api/users/register/", register),  # POST
    path("api/users/login/", login),  # POST
    path("api/users/logout/", logout),  # POST
    path("api/users/<int:user_id>/update/", update_user)  # PUT
]
