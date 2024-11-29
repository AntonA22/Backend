from django.contrib.auth import authenticate
from django.utils.dateparse import parse_datetime
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .redis import session_storage
from rest_framework.permissions import AllowAny
from django.db.models.functions import Lower
import uuid
from .minio import *
import random
from rest_framework.parsers import FormParser

from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
    parser_classes,
)
from .permissions import *
from .serializers import *

def get_draft_flight(request):
    user = request.user

    if user is None:
        return None

    flight = Flight.objects.filter(owner=user).filter(status=1).first()

    return flight

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'ship_name',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ]
)
@api_view(["GET"])
@permission_classes([AllowAny])
def search_ships(request):
    ship_name = request.GET.get("ship_name", "")

    ships = Ship.objects.filter(status=1)

    if ship_name:
        ships = ships.filter(name__icontains=ship_name)
    
    ships = ships.order_by('id')

    serializer = ShipSerializer(ships, many=True)

    draft_flight = None
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            draft_flight = Flight.objects.get(status=1, owner=request.user)
        except Flight.DoesNotExist:
            draft_flight = None

    if draft_flight:
        ships_count = len(draft_flight.get_ships())
    else:
        ships_count = 0

    resp = {
        "ships": serializer.data,
        "ships_count": ships_count,
        "draft_flight_id": draft_flight.pk if draft_flight else None
    }

    return Response(resp)

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            name="ship_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID искомого космолета"
        )
    ],
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="космолет, найденный по ID",
        ),
        status.HTTP_404_NOT_FOUND: "космолет не найден",
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_ship_by_id(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)
    serializer = ShipSerializer(ship)

    return Response(serializer.data)


@swagger_auto_schema(
    method="put",
    request_body=ShipSerializer,
    manual_parameters=[
        openapi.Parameter(
            name="ship_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID обновляемого космолета"
        )
    ],
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Обновленные данные космолета",
        ),
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
        status.HTTP_404_NOT_FOUND: "космолет не найден",
        status.HTTP_400_BAD_REQUEST: "Неверные данные",
    },
)
@api_view(["PUT"])
@permission_classes([IsManagerAuth])
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

@swagger_auto_schema(
    method="post",
    request_body=ShipSerializer,
    responses={
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Созданный космолет",
        ),
        status.HTTP_400_BAD_REQUEST: "Неверные данные",
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
    },
)
@api_view(["POST"])
@permission_classes([IsManagerAuth])
def create_ship(request):
    ship_data = request.data.copy()
    ship_data.pop("image", None)  

    serializer = ShipSerializer(data=ship_data)
    if serializer.is_valid(raise_exception=True):
        new_ship = serializer.save() 

        return Response(ShipSerializer(new_ship).data, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method="delete",
    manual_parameters=[
        openapi.Parameter(
            name="ship_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID удаляемого космолета"
        )
    ],
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_OBJECT),
            description="Обновленный список космолетов после удаления",
        ),
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
        status.HTTP_404_NOT_FOUND: "Космолет не найден",
    },
)
@api_view(["DELETE"])
@permission_classes([IsManagerAuth])
def delete_ship(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)
    ship.status = 2
    ship.save()

    ship = Ship.objects.filter(status=1)
    serializer = ShipSerializer(ship, many=True)

    return Response(serializer.data)

@swagger_auto_schema(
    method="post",
    manual_parameters=[
        openapi.Parameter(
            name="ship_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID космолета, добавляемого в перелет"
        )
    ],
    responses={
        status.HTTP_201_CREATED: openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_OBJECT),
            description="Обновленный список космолетов в перелете-черновике",
        ),
        status.HTTP_404_NOT_FOUND: "космолет не найден",
        status.HTTP_400_BAD_REQUEST: "космолет уже добавлен в черновик",
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "Ошибка при создании связки",
    },
)
@api_view(["POST"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def add_ship_to_flight(request, ship_id):
    if not Ship.objects.filter(pk=ship_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    ship = Ship.objects.get(pk=ship_id)

    draft_flight = get_draft_flight(request)

    if draft_flight is None:
        draft_flight = Flight.objects.create()
        draft_flight.date_created = timezone.now()
        draft_flight.owner = request.user
        draft_flight.save()

    if ShipFlight.objects.filter(flight=draft_flight, ship=ship).exists():
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    item = ShipFlight.objects.create()
    item.flight = draft_flight
    item.ship = ship
    item.save()

    serializer = FlightSerializer(draft_flight)
    return Response(serializer.data["ships"])

@swagger_auto_schema(
    method="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "image": openapi.Schema(type=openapi.TYPE_FILE, description="Новое изображение для космолета"),
        },
        required=["image"]
    ),
    manual_parameters=[
        openapi.Parameter(
            name="ship_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID  космолета, для которой загружается/изменяется изображение"
        )
    ],
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Обновленная информация о космолете с новым изображением",
        ),
        status.HTTP_400_BAD_REQUEST: "Изображение не предоставлено",
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
        status.HTTP_404_NOT_FOUND: "космолет не найден",
    },
)
@api_view(["POST"])
@permission_classes([IsManagerAuth])
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

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            name="status",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            description="Фильтр по статусу отправки",
        ),
        openapi.Parameter(
            name="date_formation_start",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Начальная дата формирования (формат: YYYY-MM-DDTHH:MM:SS)",
        ),
        openapi.Parameter(
            name="date_formation_end",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Конечная дата формирования (формат: YYYY-MM-DDTHH:MM:SS)",
        ),
    ],
    responses={
        status.HTTP_200_OK: FlightSerializer(many=True),
        status.HTTP_400_BAD_REQUEST: "Некорректный запрос",
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему",
    },
)
@api_view(["GET"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def search_flights(request):
    status_id = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    #flights = Flight.objects.exclude(status__in=[1, 5])
    flights = Flight.objects
    if not request.user.is_superuser:
        flights = flights.filter(owner=request.user)
    if status_id > 0:
        flights = flights.filter(status=status_id)

    if date_formation_start and parse_datetime(date_formation_start):
        flights = flights.filter(formation_date__gte=parse_datetime(date_formation_start))

    if date_formation_end and parse_datetime(date_formation_end):
        flights = flights.filter(formation_date__lt=parse_datetime(date_formation_end))

    serializer = FlightsSerializer(flights, many=True)

    return Response(serializer.data)

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            name="flight_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID искомого перелета",
        ),
    ],
    responses={
        status.HTTP_200_OK: FlightSerializer(),
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему",
        status.HTTP_404_NOT_FOUND: "Перелет не найден",
    },
)
@api_view(["GET"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def get_flight_by_id(request, flight_id):
    user = request.user

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)
    serializer = FlightSerializer(flight)

    return Response(serializer.data)

@swagger_auto_schema(
    method="put",
    manual_parameters=[
        openapi.Parameter(
            name="flight_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID изменяемого перелета",
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "launch_cosmodrom": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Космодром отправки:",
            ),
            "arrival_cosmodrom": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Космодром прилета:",
            ),
            "estimated_launch_date": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Предполагаемая дата запуска:",
            ),
        },
    ),
    responses={
        status.HTTP_200_OK: FlightSerializer(),
        status.HTTP_400_BAD_REQUEST: "Нет данных для обновления или поля не разрешены",
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "Перелет не найден",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_flight(request, flight_id):
    user = request.user

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
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

@swagger_auto_schema(
    method="put",
    manual_parameters=[
        openapi.Parameter(
            name="flight_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID перелета, формируемой создателем",
        ),
    ],
    responses={
        status.HTTP_200_OK: FlightSerializer(),
        status.HTTP_400_BAD_REQUEST: "Не заполнены обязательные поля: [поля, которые не заполнены]",
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "Перелет не найден",
        status.HTTP_405_METHOD_NOT_ALLOWED: "Перелет не в статусе 'Черновик'",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_status_user(request, flight_id):
    user = request.user

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)

    if flight.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    flight.status = 2
    flight.date_formation = timezone.now()
    flight.save()

    serializer = FlightSerializer(flight)

    return Response(serializer.data)

@swagger_auto_schema(
    method="put",
    manual_parameters=[
        openapi.Parameter(
            name="flight_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID заявки, обрабатываемой модератором",
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "status": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="Новый статус отправки (3 для завершения, 4 для отклонения)",
            ),
        },
        required=["status"],
    ),
    responses={
        status.HTTP_200_OK: FlightSerializer(),
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
        status.HTTP_404_NOT_FOUND: "Перелет не найдена",
        status.HTTP_405_METHOD_NOT_ALLOWED: "перелет не статусе 'Сформирован'",
    },
)
@api_view(["PUT"])
@permission_classes([IsManagerAuth])
@authentication_classes([AuthBySessionID])
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
    flight.moderator = request.user
    flight.result = random.choice([True, False])
    flight.save()

    serializer = FlightSerializer(flight)

    return Response(serializer.data)

@swagger_auto_schema(
    method="delete",
    manual_parameters=[
        openapi.Parameter(
            name="flight_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID удаляемого перелета",
        ),
    ],
    responses={
        status.HTTP_200_OK: FlightSerializer(),
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "перелет не найден",
        status.HTTP_405_METHOD_NOT_ALLOWED: "Удаление возможно только для перелета в статусе 'Черновик'",
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def delete_flight(request, flight_id):
    user = request.user

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    flight = Flight.objects.get(pk=flight_id)

    if flight.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    flight.status = 5
    flight.save()

    return Response(status=status.HTTP_200_OK)

@swagger_auto_schema(
    method="delete",
    manual_parameters=[
        openapi.Parameter(
            name="ship_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID космолета"
        ),
        openapi.Parameter(
            name="flight_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID перелета"
        ),
    ],
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Обновлённые данные перелета после удаления космолета",
        ),
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "Связь между космолетом и перелетом не найдена",
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def delete_ship_from_flight(request, flight_id, ship_id):
    user = request.user

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

# @swagger_auto_schema(
#     method="put",
#     manual_parameters=[
#         openapi.Parameter(
#             name="ship_flight_id",
#             in_=openapi.IN_PATH,
#             type=openapi.TYPE_INTEGER,
#             description="ID связи между космолетом и перелетом, которую нужно обновить"
#         ),
#     ],
#     request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties={
#             "value": openapi.Schema(
#                 type=openapi.TYPE_INTEGER,
#                 description="Новая полезная нагрузка"
#             ),
#         },
#         required=["value"],
#         description="Обновлённые данные перелета и космодрома"
#     ),
#     responses={
#         status.HTTP_200_OK: openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             description="Обновлённые данные перелета и космодрома",
#         ),
#         status.HTTP_403_FORBIDDEN: "Доступ запрещен",
#         status.HTTP_404_NOT_FOUND: "Связь между космодромом и перелетом не найдена",
#         status.HTTP_400_BAD_REQUEST: "Количество не предоставлено",
#     },
# )
# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def get_ship_flight(request, flight_id, ship_id):
    user = identity_user(request)

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not ShipFlight.objects.filter(ship_id=ship_id, flight_id=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = ShipFlight.objects.get(ship_id=ship_id, flight_id=flight_id)

    serializer = ShipFlightSerializer(item)

    return Response(serializer.data)

@swagger_auto_schema(
    method="put",
    manual_parameters=[
        openapi.Parameter(
            name="ship_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID космолета"
        ),
        openapi.Parameter(
            name="flight_id",
            in_=openapi.IN_PATH,
            type=openapi.TYPE_INTEGER,
            description="ID перелета"
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "value": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="Новая полезная нагрузка"
            ),
        },
        required=["value"],
        description="Обновлённые данные перелета и космодрома"
    ),
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Обновлённые данные перелета и космодрома",
        ),
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "Связь между космодромом и перелетом не найдена",
        status.HTTP_400_BAD_REQUEST: "Количество не предоставлено",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_ship_in_flight(request, flight_id, ship_id):
    user = request.user

    if not Flight.objects.filter(pk=flight_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not ShipFlight.objects.filter(ship_id=ship_id, flight_id=flight_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = ShipFlight.objects.get(ship_id=ship_id, flight_id=flight_id)

    serializer = ShipFlightSerializer(item, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(
    method="post",
    manual_parameters=[
        openapi.Parameter(
            "username",
            type=openapi.TYPE_STRING,
            description="username",
            in_=openapi.IN_FORM,
            required=True,
        ),
        openapi.Parameter(
            "password",
            type=openapi.TYPE_STRING,
            description="password",
            in_=openapi.IN_FORM,
            required=True,
        ),
    ],
)
@api_view(["POST"])
@parser_classes((FormParser,))
@permission_classes([AllowAny])
def login(request):
    username = request.POST.get("username")
    password = request.POST.get("password")
    user = authenticate(username=username, password=password)
    if user is not None:
        session_id = str(uuid.uuid4())
        session_storage.set(session_id, username)
        response = Response(status=status.HTTP_200_OK)
        response.set_cookie("session_id", session_id, samesite="lax")
        return response
    return Response(
        {"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    method="post",
    request_body=UserSerializer,
    responses={
        status.HTTP_201_CREATED: "Created",
        status.HTTP_400_BAD_REQUEST: "Bad Request",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    serializer = UserSerializer(user)

    response = Response(serializer.data, status=status.HTTP_201_CREATED)

    return response


@swagger_auto_schema(
    method="post",
    responses={
        status.HTTP_204_NO_CONTENT: "No content",
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["POST"])
@permission_classes([IsAuth])
def logout(request):
    session_id = request.COOKIES["session_id"]
    if session_storage.exists(session_id):
        session_storage.delete(session_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_403_FORBIDDEN)


@swagger_auto_schema(
    method="put",
    request_body=UserSerializer,
    responses={
        status.HTTP_200_OK: UserSerializer(),
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_user(request, user_id):
    if not User.objects.filter(pk=user_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    user = request.user

    if user.pk != user_id:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    serializer.save()

    return Response(serializer.data, status=status.HTTP_200_OK)
