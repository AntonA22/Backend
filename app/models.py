from django.db import models
from django.utils import timezone

from django.contrib.auth.models import User

from app.utils import STATUS_CHOICES


class Ship(models.Model):
    STATUS_CHOICES = (
        (1, 'Действует'),
        (2, 'Удалена'),
    )

    name = models.CharField(max_length=100, verbose_name="Название")
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    image = models.ImageField(default="images/default.png")
    description = models.TextField(verbose_name="Описание", blank=True)
    production_date = models.CharField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Космический корабль"
        verbose_name_plural = "Космические корабли"
        db_table = "ships"


class Flight(models.Model):
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    date_created = models.DateTimeField(default=timezone.now(), verbose_name="Дата создания")
    date_formation = models.DateTimeField(verbose_name="Дата формирования", blank=True, null=True)
    date_complete = models.DateTimeField(verbose_name="Дата завершения", blank=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", null=True, related_name='owner')
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Модератор", null=True, related_name='moderator')

    def __str__(self):
        return "Перелет №" + str(self.pk)

    def get_ships(self):
        res = []

        for item in ShipFlight.objects.filter(flight=self):
            tmp = item.ship
            tmp.value = item.value
            res.append(tmp)

        return res

    def get_status(self):
        return dict(STATUS_CHOICES).get(self.status)

    class Meta:
        verbose_name = "Перелет"
        verbose_name_plural = "Перелеты"
        ordering = ('-date_formation', )
        db_table = "flights"


class ShipFlight(models.Model):
    ship = models.ForeignKey(Ship, models.CASCADE, blank=True, null=True)
    flight = models.ForeignKey(Flight, models.CASCADE, blank=True, null=True)
    value = models.IntegerField(verbose_name="Поле м-м", blank=True, null=True)

    def __str__(self):
        return "м-м №" + str(self.pk)

    class Meta:
        verbose_name = "м-м"
        verbose_name_plural = "м-м"
