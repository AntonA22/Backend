import random

from django.core.management.base import BaseCommand
from minio import Minio

from ...models import *
from .utils import random_date, random_timedelta


def add_users():
    User.objects.create_user("user", "user@user.com", "1234")
    User.objects.create_superuser("root", "root@root.com", "1234")

    for i in range(1, 10):
        User.objects.create_user(f"user{i}", f"user{i}@user.com", "1234")
        User.objects.create_superuser(f"root{i}", f"root{i}@root.com", "1234")

    print("Пользователи созданы")


def add_ships():
    Ship.objects.create(
        name="Starship SN3",
        description="Серийный номер Starship 3, или SN3, представлял собой прототип Starship, предназначенный для статических огневых испытаний и полетов на малой высоте. Он был разрушен во время испытаний 3 апреля 2020 года. В баке с жидким кислородом в кормовой части транспортного средства произошла непреднамеренная разгерметизация, в результате чего конструкция рухнула под весом полного метантенка, расположенного выше (который был в центре внимания испытаний).",
        creation_date="29.03.2020",
        image="1.png"
    )

    Ship.objects.create(
        name="Starship SN5",
        description="У транспортного средства SN5 отсутствует носовой обтекатель, поэтому он немного похож на высокую «летающую водонапорную башню», как и предыдущий испытательный стенд, но он все равно поднимался и опускался со стартовой площадки SpaceX в Бока-Чика, штат Техас.",
        creation_date="31.09.2020",
        image="2.png"
    )

    Ship.objects.create(
        name="Starship SN4",
        description="Серийный номер Starship 4, или SN4, был прототипом Starship, предназначенным для суборбитальных испытаний. Аппарат прошел все контрольные испытания и стал первым прототипом программы Starship, прошедшим статические испытания со времен Starhopper. SN4 был уничтожен 29 мая 2020 года после успешного статического огневого испытания из-за отказа экспериментальной системы 'быстрого отключения' наземного вспомогательного оборудования.",
        creation_date="17.04.2020",
        image="3.png"
    )

    Ship.objects.create(
        name="Starship SN11",
        description="SN11 стал четвертым полностью собранным прототипом Starship, прошедшим летные испытания. Это был последний прототип из первых четырех, поскольку Илон Маск объявил о значительных изменениях для SN15 и отмене SN12-14.",
        creation_date="05.02.2022",
        image="4.png"
    )

    Ship.objects.create(
        name="Starship SN15",
        description="Starship 15 (SN15) был первым прототипом Starship, который успешно завершил полет и благополучно приземлился. Полет состоялся между 17:24 и 17:30 5 мая 2021 года. После его успешной посадки на опорах на краю площадки появились предположения о возможности второго полета в связи с перемещением SN15 на площадку B.",
        creation_date="05.04.2023",
        image="5.png"
    )

    Ship.objects.create(
        name="Starship SN20",
        description="Starship 20 - выведенный из эксплуатации iso прототип второй ступени starship, который в настоящее время находится в rocket garden. Первоначально Первоначально Планировавшийся как первый корабль, который совершит орбитальный полет вместе с B4, он был замечен 7 марта 2021 года и проходил сборку, пока в июле 2021 года не завершился этап укладки.",
        creation_date="17.08.2024",
        image="6.png"
    )

    client = Minio("minio:9000", "minio", "minio123", secure=False)
    client.fput_object('images', '1.png', "app/static/images/1.png")
    client.fput_object('images', '2.png', "app/static/images/2.png")
    client.fput_object('images', '3.png', "app/static/images/3.png")
    client.fput_object('images', '4.png', "app/static/images/4.png")
    client.fput_object('images', '5.png', "app/static/images/5.png")
    client.fput_object('images', '6.png', "app/static/images/6.png")
    client.fput_object('images', 'default.png', "app/static/images/default.png")

    print("Услуги добавлены")


def add_flights():
    users = User.objects.filter(is_superuser=False)
    moderators = User.objects.filter(is_superuser=True)

    if len(users) == 0 or len(moderators) == 0:
        print("Заявки не могут быть добавлены. Сначала добавьте пользователей с помощью команды add_users")
        return

    ships = Ship.objects.all()

    for _ in range(30):
        status = random.randint(2, 5)
        add_flight(status, ships, users, moderators)

    add_flight(1, ships, users, moderators)

    print("Заявки добавлены")


def add_flight(status, ships, users, moderators):
    flight = Flight.objects.create()
    flight.status = status

    if flight.status in [3, 4]:
        flight.date_complete = random_date()
        flight.date_formation = flight.date_complete - random_timedelta()
        flight.date_created = flight.date_formation - random_timedelta()
    else:
        flight.date_formation = random_date()
        flight.date_created = flight.date_formation - random_timedelta()

    flight.owner = random.choice(users)
    flight.moderator = random.choice(moderators)

    flight.launch_cosmodrom = "Уоллопс (США)"
    flight.arrival_cosmodrom = "Хаммагир (Франция)"
    flight.estimated_launch_date = random_date()

    for ship in random.sample(list(ships), 3):
        item = ShipFlight(
            flight=flight,
            ship=ship,
            value=random.randint(100, 1000)
        )
        item.save()

    flight.save()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        add_users()
        add_ships()
        add_flights()



















