import requests
from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import *


def get_draft_flight():
    return Flight.objects.filter(status=1).first()


def get_user():
    return User.objects.filter(is_superuser=False).first()


def get_moderator():
    return User.objects.filter(is_superuser=True).first()


@api_view(["GET"])
def search_ships(request):
    ship_name = request.GET.get("ship_name", "")

    ships = Ship.objects.filter(status=1).filter(name__icontains=ship_name)

    serializer = ShipSerializer(ships, many=True)

    draft_flight = get_draft_flight()

    resp = {
        "ships": serializer.data,
        "draft_flight": draft_flight.pk if draft_flight else None
    }

    return Response(resp)


@api_view(["GET"])
def get_ship_by_id(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)
    serializer = ShipSerializer(ship, many=False)

    return Response(serializer.data)


@api_view(["PUT"])
def update_ship(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)

    image = request.data.get("image")
    if image is not None:
        ship.image = image
        ship.save()

    serializer = ShipSerializer(ship, data=request.data, many=False, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
def create_ship(request):
    ship_data = request.data.copy()
    ship_data.pop("image", None)  

    serializer = ShipSerializer(data=ship_data)
    if serializer.is_valid(raise_exception=True):
        new_ship = serializer.save() 

        pic = request.FILES.get("image")
        if pic is not None:
            new_ship.image = pic  
            new_ship.save() 

        ships = Ship.objects.filter(status=1)
        serializer = ShipSerializer(ships, many=True)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
def delete_ship(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)
    ship.status = 2
    ship.save()

    ships = Ship.objects.filter(status=1)
    serializer = ShipSerializer(ships, many=True)

    return Response(serializer.data)


@api_view(["POST"])
def add_ship_to_flight(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)

    draft_flight = get_draft_flight()

    if draft_flight is None:
        draft_flight = Flight.objects.create()
        draft_flight.owner = get_user()
        draft_flight.date_created = timezone.now()
        draft_flight.save()

    if ShipFlight.objects.filter(flight=draft_flight, ship=ship).exists():
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    item = ShipFlight.objects.create()
    item.flight = draft_flight
    item.ship = ship
    item.save()

    serializer = FlightSerializer(draft_flight, many=False)

    return Response(serializer.data["ships"])


@api_view(["GET"])
def get_ship_image(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)
    response = requests.get(ship.image.url.replace("localhost", "minio"))

    return HttpResponse(response, content_type="image/png")


@api_view(["POST"])
def update_ship_image(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)

    image = request.data.get("image")
    if image is not None:
        ship.image = image
        ship.save()

    serializer = ShipSerializer(ship)

    return Response(serializer.data)


@api_view(["GET"])
def search_flights(request):
    status = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    flights = Flight.objects.exclude(status__in=[1, 5])

    if status > 0:
        flights = flights.filter(status=status)

    if date_formation_start and parse_datetime(date_formation_start):
        flights = flights.filter(date_formation__gte=parse_datetime(date_formation_start))

    if date_formation_end and parse_datetime(date_formation_end):
        flights = flights.filter(date_formation__lt=parse_datetime(date_formation_end))

    serializer = FlightsSerializer(flights, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def get_flight_by_id(request, flight_id):
    if not Flight.objects.filter(pk=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)
    serializer = FlightSerializer(flight, many=False)

    return Response(serializer.data)


@api_view(["PUT"])
def update_flight(request, flight_id):
    if not Flight.objects.filter(pk=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)

    allowed_fields = ['launch_cosmodrom', 'arrival_cosmodrom', 'estimated_launch_date']
    data = {key: value for key, value in request.data.items() if key in allowed_fields}

    if not data:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    serializer = FlightSerializer(flight, data=data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(["PUT"])
def update_status_user(request, flight_id):
    if not Flight.objects.filter(pk=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)

    if flight.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    flight.status = 2
    flight.date_formation = timezone.now()
    flight.save()

    serializer = FlightSerializer(flight, many=False)

    return Response(serializer.data)


@api_view(["PUT"])
def update_status_admin(request, flight_id):
    if not Flight.objects.filter(pk=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    request_status = int(request.data["status"])

    if request_status not in [3, 4]:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    flight = Flight.objects.get(pk=flight_id)

    if flight.status != 2:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    flight.date_complete = timezone.now()
    flight.status = request_status
    flight.moderator = get_moderator()
    flight.save()

    serializer = FlightSerializer(flight, many=False)

    return Response(serializer.data)


@api_view(["DELETE"])
def delete_flight(request, flight_id):
    if not Flight.objects.filter(pk=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)

    if flight.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    flight.status = 5
    flight.save()

    serializer = FlightSerializer(flight, many=False)

    return Response(serializer.data)


@api_view(["DELETE"])
def delete_ship_from_flight(request, flight_id, ship_id):
    if not ShipFlight.objects.filter(flight_id=flight_id, ship_id=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = ShipFlight.objects.get(flight_id=flight_id, ship_id=ship_id)
    item.delete()

    flight = Flight.objects.get(pk=flight_id)

    serializer = FlightSerializer(flight, many=False)
    ships = serializer.data["ships"]

    if len(ships) == 0:
        flight.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(ships)


@api_view(["PUT"])
def update_ship_in_flight(request, flight_id, ship_id):
    if not ShipFlight.objects.filter(ship_id=ship_id, flight_id=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = ShipFlight.objects.get(ship_id=ship_id, flight_id=flight_id)

    serializer = ShipFlightSerializer(item, data=request.data, many=False, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    serializer = UserSerializer(user)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def logout(request):
    return Response(status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_user(request, user_id):
    if not User.objects.filter(pk=user_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    user = User.objects.get(pk=user_id)
    serializer = UserSerializer(user, data=request.data, many=False, partial=True)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    serializer.save()

    return Response(serializer.data)