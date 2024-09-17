from django.shortcuts import render

ships = [
    {
        "id": 1,
        "name": "Starship SN3",
        "description": "Серийный номер Starship 3, или SN3, представлял собой прототип Starship, предназначенный для статических огневых испытаний и полетов на малой высоте. Он был разрушен во время испытаний 3 апреля 2020 года. В баке с жидким кислородом в кормовой части транспортного средства произошла непреднамеренная разгерметизация, в результате чего конструкция рухнула под весом полного метантенка, расположенного выше (который был в центре внимания испытаний). Неповрежденные части прототипа были восстановлены и перепрофилированы для SN4.",
        "production_date": "29.03.2020",
        "image": "http://localhost:9000/images/1.png"
    },
    {
        "id": 2,
        "name": "Starship SN5",
        "description": "У транспортного средства SN5 отсутствует носовой обтекатель, поэтому он немного похож на высокую «летающую водонапорную башню», как и предыдущий испытательный стенд, но он все равно поднимался и опускался со стартовой площадки SpaceX в Бока-Чика, штат Техас.",
        "production_date": "31.09.2020",
        "image": "http://localhost:9000/images/2.png"
    },
    {
        "id": 3,
        "name": "Starship SN4",
        "description": "Серийный номер Starship 4, или SN4, был прототипом Starship, предназначенным для суборбитальных испытаний. Аппарат прошел все контрольные испытания и стал первым прототипом программы Starship, прошедшим статические испытания со времен Starhopper. SN4 был уничтожен 29 мая 2020 года после успешного статического огневого испытания из-за отказа экспериментальной системы 'быстрого отключения' наземного вспомогательного оборудования.",
        "production_date": "17.04.2020",
        "image": "http://localhost:9000/images/3.png"
    },
    {
        "id": 4,
        "name": "Starship SN11",
        "description": "SN11 стал четвертым полностью собранным прототипом Starship, прошедшим летные испытания. Это был последний прототип из первых четырех, поскольку Илон Маск объявил о значительных изменениях для SN15 и отмене SN12-14.",
        "production_date": "05.02.2022",
        "image": "http://localhost:9000/images/4.png"
    },
    {
        "id": 5,
        "name": "Starship SN15",
        "description": "Starship 15 (SN15) был первым прототипом Starship, который успешно завершил полет и благополучно приземлился. Полет состоялся между 17:24 и 17:30 5 мая 2021 года. После его успешной посадки на опорах на краю площадки появились предположения о возможности второго полета в связи с перемещением SN15 на площадку B. Однако позже он был возвращен в Rocket Garden, где 26 июля 2023 года начался демонтаж SN15.",
        "production_date": "05.04.2023",
        "image": "http://localhost:9000/images/5.png"
    }
]

draft_flight = {
    "id": 1,
    "status": "Черновик",
    "date_created": "12 сентября 2024г",
    "launch_cosmodrom": "Уоллопс (США)",
    "arrival_cosmodrom": "Хаммагир (Франция)",
    "estimated_launch_date": "18 сентября 2024г",
    "ships": [
        {
            "id": 3,
            "name": "Starship SN4",
            "description": "Серийный номер Starship 4, или SN4, был прототипом Starship, предназначенным для суборбитальных испытаний. Аппарат прошел все контрольные испытания и стал первым прототипом программы Starship, прошедшим статические испытания со времен Starhopper. SN4 был уничтожен 29 мая 2020 года после успешного статического огневого испытания из-за отказа экспериментальной системы 'быстрого отключения' наземного вспомогательного оборудования.",
            "production_date": "29.03.2020",
            "image": "http://localhost:9000/images/3.png",
            "value": 100
        },
        {
            "id": 4,
            "name": "Starship SN11",
            "description": "SN11 стал четвертым полностью собранным прототипом Starship, прошедшим летные испытания. Это был последний прототип из первых четырех, поскольку Илон Маск объявил о значительных изменениях для SN15 и отмене SN12-14.",
            "production_date": "31.09.2020",
            "image": "http://localhost:9000/images/4.png",
            "value": 150
        },
        {
            "id": 5,
            "name": "Starship SN15",
            "description": "Starship 15 (SN15) был первым прототипом Starship, который успешно завершил полет и благополучно приземлился. Полет состоялся между 17:24 и 17:30 5 мая 2021 года. После его успешной посадки на опорах на краю площадки появились предположения о возможности второго полета в связи с перемещением SN15 на площадку B. Однако позже он был возвращен в Rocket Garden, где 26 июля 2023 года начался демонтаж SN15.",
            "production_date": "17.04.2020",
            "image": "http://localhost:9000/images/5.png",
            "value": 125
        }
    ]
}

def getShipById(ship_id):
    for ship in ships:
        if ship["id"] == ship_id:
            return ship


def searchShips(ship_name):
    res = []

    for ship in ships:
        if ship_name.lower() in ship["name"].lower():
            res.append(ship)

    return res


def getDraftApplication():
    return draft_flight


def getApplicationById(flight_id):
    return draft_flight


def index(request):
    name = request.GET.get("name", "")
    ships = searchShips(name)
    draft_flight = getDraftApplication()

    context = {
        "ships": ships,
        "name": name,
        "ships_count": len(draft_flight["ships"]),
        "draft_flight": draft_flight
    }

    return render(request, "home_page.html", context)


def ship(request, ship_id):
    context = {
        "id": ship_id,
        "ship": getShipById(ship_id),
    }

    return render(request, "ship_page.html", context)


def flight(request, flight_id):
    context = {
        "flight": getApplicationById(flight_id),
    }

    return render(request, "flight_page.html", context)

