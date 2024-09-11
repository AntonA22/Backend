from django.shortcuts import render

ships = [
    {
        "id": 1,
        "name": "Starship SN3",
        "description": "Серийный номер Starship 3, или SN3, представлял собой прототип Starship, предназначенный для статических огневых испытаний и полетов на малой высоте. Он был разрушен во время испытаний 3 апреля 2020 года. В баке с жидким кислородом в кормовой части транспортного средства произошла непреднамеренная разгерметизация, в результате чего конструкция рухнула под весом полного метантенка, расположенного выше (который был в центре внимания испытаний). Неповрежденные части прототипа были восстановлены и перепрофилированы для SN4.",
        "launch_date": "16 августа 2024г",
        "image": "http://localhost:9000/images/1.png"
    },
    {
        "id": 2,
        "name": "Starship SN5",
        "description": "У транспортного средства SN5 отсутствует носовой обтекатель, поэтому он немного похож на высокую «летающую водонапорную башню», как и предыдущий испытательный стенд, но он все равно поднимался и опускался со стартовой площадки SpaceX в Бока-Чика, штат Техас.",
        "launch_date": "2 июня 2021г",
        "image": "http://localhost:9000/images/2.png"
    },
    {
        "id": 3,
        "name": "Starship SN4",
        "description": "Серийный номер Starship 4, или SN4, был прототипом Starship, предназначенным для суборбитальных испытаний. Аппарат прошел все контрольные испытания и стал первым прототипом программы Starship, прошедшим статические испытания со времен Starhopper. SN4 был уничтожен 29 мая 2020 года после успешного статического огневого испытания из-за отказа экспериментальной системы 'быстрого отключения' наземного вспомогательного оборудования.",
        "launch_date": "25 июля 2023г",
        "image": "http://localhost:9000/images/3.png"
    },
    {
        "id": 4,
        "name": "Starship SN11",
        "description": "SN11 стал четвертым полностью собранным прототипом Starship, прошедшим летные испытания. Это был последний прототип из первых четырех, поскольку Илон Маск объявил о значительных изменениях для SN15 и отмене SN12-14.",
        "launch_date": "9 сентября 2022г",
        "image": "http://localhost:9000/images/4.png"
    },
    {
        "id": 5,
        "name": "Starship SN15",
        "description": "Starship 15 (SN15) был первым прототипом Starship, который успешно завершил полет и благополучно приземлился. Полет состоялся между 17:24 и 17:30 5 мая 2021 года. После его успешной посадки на опорах на краю площадки появились предположения о возможности второго полета в связи с перемещением SN15 на площадку B. Однако позже он был возвращен в Rocket Garden, где 26 июля 2023 года начался демонтаж SN15.",
        "launch_date": "22 июля 2024г",
        "image": "http://localhost:9000/images/5.png"
    }
]

draft_order = {
    "id": 1,
    "ships": [
        {
            "id": 3,
            "name": "Starship SN4",
            "description": "Серийный номер Starship 4, или SN4, был прототипом Starship, предназначенным для суборбитальных испытаний. Аппарат прошел все контрольные испытания и стал первым прототипом программы Starship, прошедшим статические испытания со времен Starhopper. SN4 был уничтожен 29 мая 2020 года после успешного статического огневого испытания из-за отказа экспериментальной системы 'быстрого отключения' наземного вспомогательного оборудования.",
            "launch_date": "25 июля 2023г",
            "image": "http://localhost:9000/images/3.png",
            "queue": "2"
        },
        {
            "id": 4,
            "name": "Starship SN11",
            "description": "SN11 стал четвертым полностью собранным прототипом Starship, прошедшим летные испытания. Это был последний прототип из первых четырех, поскольку Илон Маск объявил о значительных изменениях для SN15 и отмене SN12-14.",
            "launch_date": "9 сентября 2022г",
            "image": "http://localhost:9000/images/4.png",
            "queue": "1"
        },
        {
            "id": 5,
            "name": "Starship SN15",
            "description": "Starship 15 (SN15) был первым прототипом Starship, который успешно завершил полет и благополучно приземлился. Полет состоялся между 17:24 и 17:30 5 мая 2021 года. После его успешной посадки на опорах на краю площадки появились предположения о возможности второго полета в связи с перемещением SN15 на площадку B. Однако позже он был возвращен в Rocket Garden, где 26 июля 2023 года начался демонтаж SN15.",
            "launch_date": "22 июля 2024г",
            "image": "http://localhost:9000/images/5.png",
            "queue": "3"
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


def getDraftOrder():
    return draft_order


def getOrderById(order_id):
    return draft_order


def index(request):   #  функция обработки страницы после поиска
    query = request.GET.get("query", "")
    ships = searchShips(query)

    context = {
        "ships": ships,
        "query": query,
        "draft_order": getDraftOrder()
    }

    return render(request, "home_page.html", context)


def ship(request, ship_id): 
    context = {
        "id": ship_id,
        "ship": getShipById(ship_id),
    }

    return render(request, "ship_page.html", context)


def order(request, order_id):
    context = {
        "order": getOrderById(order_id),
    }

    return render(request, "order_page.html", context)

