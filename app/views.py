from django.contrib.auth import authenticate
from django.utils.dateparse import parse_datetime
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .jwt_helper import *
from .permissions import *
from .serializers import *
from .utils import identity_user


def get_draft_flight(request):
    user = identity_user(request)

    if user is None:
        return None

    flight = Flight.objects.filter(owner=user).filter(status=1).first()

    return flight


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'query',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ]
)
@api_view(["GET"])
def search_ships(request):
    ship_name = request.GET.get("ship_name", "")

    ships = Ship.objects.filter(status=1)

    if ship_name:
        ships = ships.filter(name__icontains=ship_name)

    serializer = ShipSerializer(ships, many=True)

    draft_flight = get_draft_flight(request)

    resp = {
        "ships": serializer.data,
        "ships_count": ShipFlight.objects.filter(flight=draft_flight).count() if draft_flight else None,
        "draft_flight_id": draft_flight.pk if draft_flight else None
    }

    return Response(resp)


@api_view(["GET"])
def get_ship_by_id(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)
    serializer = ShipSerializer(ship)

    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsModerator])
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
@permission_classes([IsModerator])
def create_ship(request):
    ship = Ship.objects.create()

    serializer = ShipSerializer(ship)

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsModerator])
def delete_ship(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)
    ship.status = 2
    ship.save()

    ship = Ship.objects.filter(status=1)
    serializer = ShipSerializer(ship, many=True)

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_ship_to_flight(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)

    draft_flight = get_draft_flight(request)

    if draft_flight is None:
        draft_flight = Flight.objects.create()
        draft_flight.date_created = timezone.now()
        draft_flight.owner = identity_user(request)
        draft_flight.save()

    if ShipFlight.objects.filter(flight=draft_flight, ship=ship).exists():
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    item = ShipFlight.objects.create()
    item.flight = draft_flight
    item.ship = ship
    item.save()

    serializer = FlightSerializer(draft_flight)
    return Response(serializer.data["ships"])


@api_view(["POST"])
@permission_classes([IsModerator])
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
@permission_classes([IsAuthenticated])
def search_flights(request):
    status_id = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    flights = Flight.objects.exclude(status__in=[1, 5])

    user = identity_user(request)
    if not user.is_staff:
        flights = flights.filter(owner=user)

    if status_id > 0:
        flights = flights.filter(status=status_id)

    if date_formation_start and parse_datetime(date_formation_start):
        flights = flights.filter(date_formation__gte=parse_datetime(date_formation_start))

    if date_formation_end and parse_datetime(date_formation_end):
        flights = flights.filter(date_formation__lt=parse_datetime(date_formation_end))

    serializer = FlightsSerializer(flights, many=True)

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_flight_by_id(request, flight_id):
    user = identity_user(request)

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)
    serializer = FlightSerializer(flight)

    return Response(serializer.data)


@swagger_auto_schema(method='put', request_body=FlightSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_flight(request, flight_id):
    user = identity_user(request)

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)
    serializer = FlightSerializer(flight, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_status_user(request, flight_id):
    user = identity_user(request)

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)

    flight.status = 2
    flight.date_formation = timezone.now()
    flight.save()

    serializer = FlightSerializer(flight)

    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsModerator])
def update_status_admin(request, flight_id):
    if not Flight.objects.filter(pk=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    request_status = int(request.data["status"])

    if request_status not in [3, 4]:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    flight = Flight.objects.get(pk=flight_id)

    if flight.status != 2:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    flight.status = request_status
    flight.date_complete = timezone.now()
    flight.moderator = identity_user(request)
    flight.save()

    serializer = FlightSerializer(flight)

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_flight(request, flight_id):
    user = identity_user(request)

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)

    if flight.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    flight.status = 5
    flight.save()

    return Response(status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_ship_from_flight(request, flight_id, ship_id):
    user = identity_user(request)

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not ShipFlight.objects.filter(flight_id=flight_id, ship_id=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = ShipFlight.objects.get(flight_id=flight_id, ship_id=ship_id)
    item.delete()

    flight = Flight.objects.get(pk=flight_id)

    serializer = FlightSerializer(flight)
    ships = serializer.data["ships"]

    if len(ships) == 0:
        flight.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(ships)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_ship_flight(request, flight_id, ship_id):
    user = identity_user(request)

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not ShipFlight.objects.filter(ship_id=ship_id, flight_id=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = ShipFlight.objects.get(ship_id=ship_id, flight_id=flight_id)

    serializer = ShipFlightSerializer(item)

    return Response(serializer.data)


@swagger_auto_schema(method='PUT', request_body=ShipFlightSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_ship_in_flight(request, flight_id, ship_id):
    user = identity_user(request)

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not ShipFlight.objects.filter(ship_id=ship_id, flight_id=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = ShipFlight.objects.get(ship_id=ship_id, flight_id=flight_id)

    serializer = ShipFlightSerializer(item, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(method='post', request_body=UserLoginSerializer)
@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    access_token = create_access_token(user.id)

    serializer = UserSerializer(user)

    response = Response(serializer.data, status=status.HTTP_201_CREATED)

    response.set_cookie('access_token', access_token, httponly=True)

    return response


@swagger_auto_schema(method='post', request_body=UserRegisterSerializer)
@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    access_token = create_access_token(user.id)

    serializer = UserSerializer(user)

    response = Response(serializer.data, status=status.HTTP_201_CREATED)

    response.set_cookie('access_token', access_token, httponly=True)

    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    access_token = get_access_token(request)

    if access_token not in cache:
        cache.set(access_token, settings.JWT["ACCESS_TOKEN_LIFETIME"])

    return Response(status=status.HTTP_200_OK)


@swagger_auto_schema(method='PUT', request_body=UserSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    if not User.objects.filter(pk=user_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    user = identity_user(request)

    if user.pk != user_id:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    serializer.save()

    return Response(serializer.data, status=status.HTTP_200_OK)
