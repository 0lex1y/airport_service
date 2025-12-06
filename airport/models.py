from django.db import models
from rest_framework.exceptions import ValidationError

from airport_service import settings


class AirplaneType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=100)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(AirplaneType,
                                      on_delete=models.CASCADE,
                                      related_name="airplanes")

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return f"{self.name}"


class Airport(models.Model):
    name = models.CharField(max_length=100)
    closest_big_city = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name="departures")
    destination = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name="arrivals")
    distance = models.IntegerField()

    def __str__(self):
        return f"{self.source.name} -> {self.destination.name}"


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Flight(models.Model):
    route = models.ForeignKey(Route,
                              on_delete=models.CASCADE,
                              related_name="flights")
    airplane = models.ForeignKey(Airplane,
                                 on_delete=models.CASCADE,
                                 related_name="flights")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["departure_time", "arrival_time", "airplane", "route"]

    def __str__(self):
        return f"{self.departure_time} -> {self.arrival_time}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name="orders")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.created_at)


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(Flight,
                               on_delete=models.CASCADE,
                               related_name="tickets")
    order = models.ForeignKey(Order,
                              on_delete=models.CASCADE,
                              related_name="tickets")

    @staticmethod
    def validate_ticket(row, seat, airplane, errors_to_raise):
        for ticket_attr_value, ticket_attr_name, airplane_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(airplane, airplane_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise errors_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                                          f"number must be in valid range: "
                                          f"(1, {airplane_attr_name}): "
                                          f"(1, {count_attrs})"
                    }
                )
    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.flight.airplane,
            ValidationError)

    def save(self,
             *args,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None):
        self.full_clean()
        return super(Ticket,self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields)
    def __str__(self):
        return f"{self.flight} (row: {self.row}, seat: {self.seat})"

    class Meta:
        unique_together = ("flight", "row", "seat")
        ordering = ["row", "seat"]
