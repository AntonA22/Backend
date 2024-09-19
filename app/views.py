from django.contrib.auth.models import User 
from django.db import connection
from django.shortcuts import render, redirect
from django.utils import timezone

from app.models import Ship, Flight, ShipFlight


def index(request):
    name = request.GET.get("name", "")
    ships = Ship.objects.filter(name__icontains=name).filter(status=1)
    draft_flight = get_draft_flight()

    context = {
        "name": name,
        "ships": ships
    }

    if draft_flight:
        context["ships_count"] = len(draft_flight.get_ships())
        context["draft_flight"] = draft_flight

    return render(request, "home_page.html", context)


def add_ship_to_draft_flight(request, ship_id):
    ship = Ship.objects.get(pk=ship_id)

    draft_flight = get_draft_flight()

    if draft_flight is None:
        draft_flight = Flight.objects.create()
        draft_flight.owner = get_current_user()
        draft_flight.date_created = timezone.now()
        draft_flight.save()

    if ShipFlight.objects.filter(flight=draft_flight, ship=ship).exists():
        return redirect("/")

    item = ShipFlight(
        flight=draft_flight,
        ship=ship
    )
    item.save()

    return redirect("/")


def ship_details(request, ship_id):
    context = {
        "ship": Ship.objects.get(id=ship_id)
    }

    return render(request, "ship_page.html", context)


def delete_flight(request, flight_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE flights SET status = 5 WHERE id = %s", [flight_id])

    return redirect("/")


def flight(request, flight_id):
    context = {
        "flight": Flight.objects.get(id=flight_id),
    }

    return render(request, "flight_page.html", context)


def get_draft_flight():
    return Flight.objects.filter(status=1).first()


def get_current_user():
    return User.objects.filter(is_superuser=False).first()