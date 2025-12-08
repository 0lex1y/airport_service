from django.db import models, transaction
from rest_framework.exceptions import ValidationError

from airport_service import settings

POSITION_CHOICES = ["pilot", "co-pilot", "mechanic"]


# Airport

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="cities")

    class Meta:
        verbose_name_plural = "cities"
        unique_together = ("name", "country")
        ordering = ["name", "country__name"]

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class Airport(models.Model):
    code = models.CharField(max_length=10, unique=True, help_text="IATA or ISAO")
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="airports_city")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="airports_country")

    class Meta:
        verbose_name_plural = "Airports"
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.city})"


class Route(models.Model):
    source = models.ForeignKey(Airport,
                               on_delete=models.CASCADE,
                               related_name="departures")
    destination = models.ForeignKey(Airport,
                                    on_delete=models.CASCADE,
                                    related_name="arrivals")
    distance = models.PositiveIntegerField(help_text="Distance traveled between source and destination")

    class Meta:
        verbose_name_plural = "Routes"
        unique_together = ("source", "destination")

    def __str__(self):
        return f"{self.source.name} -> {self.destination.name}"

    def clean(self):
        super().clean()
        if self.source.name == self.destination.name:
            raise ValidationError("Source and destination must be different")


# Airplane

class AirplaneType(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="jet or superjet etc.")

    class Meta:
        verbose_name = "Airplane Type"
        verbose_name_plural = "Airplane Types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=100)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(AirplaneType,
                                      on_delete=models.PROTECT,
                                      related_name="airplanes")

    class Meta:
        unique_together = ("name",)
        verbose_name = "Airplane"
        verbose_name_plural = "Airplanes"
        ordering = ["name"]

    def clean(self):
        super().clean()
        if self.seats_in_row < 1:
            raise ValidationError("Seats must be greater than 1")
        if self.rows < 1:
            raise ValidationError("Row must be greater than 1")
        if self.airplane_type is None:
            raise ValidationError("Airplane type must be specified")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return f"{self.name} ({self.airplane_type})"


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, choices=POSITION_CHOICES, blank=True)

    class Meta:
        verbose_name = "Crew"
        verbose_name_plural = "Crews"
        unique_together = ("first_name", "last_name")
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# Flight

class Flight(models.Model):
    route = models.ForeignKey(Route,
                              on_delete=models.CASCADE,
                              related_name="flights")
    airplane = models.ForeignKey(Airplane,
                                 on_delete=models.CASCADE,
                                 related_name="flights")
    crew = models.ManyToManyField(Crew, related_name="flights", blank=True)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["departure_time", "airplane"]
        indexes = [
            models.Index(fields=["departure_time"]),
            models.Index(fields=["arrival_time"]),
            models.Index(fields=["airplane", "arrival_time"]),
            models.Index(fields=["departure_time", "airplane"]),
        ]
        verbose_name = "Flight"
        verbose_name_plural = "Flights"

    def __str__(self):
        return (f"{self.airplane} | {self.route} |"
                f"{self.departure_time.strftime('%d/%m/%Y %H:%M')} -> "
                f"{self.arrival_time.strftime('%d/%m/%Y %H:%M')}")

    def clean(self):
        if self.arrival_time <= self.departure_time:
            raise ValidationError("Arrival time must be later than departure time")
        if self.pk:
            conflict = Flight.objects.filter(
                airplane=self.airplane,
                departure_time__lt=self.departure_time,
                arrival_time__gt=self.arrival_time
            ).exclude(pk=self.pk)
        else:
            conflict = Flight.objects.filter(
                airplane=self.airplane,
                departure_time__lt=self.departure_time,
                arrival_time__gt=self.arrival_time
            )
        if conflict.exists():
            raise ValidationError("Flight already exists")

    def save(self, *args, **kwargs):
        self.full_clean()
        super.save(*args, **kwargs)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", ("Pending",)
        COMPLETED = "completed", ("Completed",)
        CANCELED = "canceled", ("Canceled",)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name="orders")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.pk} | {self.user}, {self.status}"

    def complete(self):
        self.status = self.Status.COMPLETED
        self.save(update_fields=["status"])

    def cancel(self):
        self.status = self.Status.CANCELED
        self.save(update_fields=["status"])


class Ticket(models.Model):
    row = models.IntegerField(help_text="Row number (1, 2, 3...)")
    seat = models.CharField(max_length=1, help_text="Seat letter (A, B, C, D, E, F)")
    flight = models.ForeignKey(Flight,
                               on_delete=models.CASCADE,
                               related_name="tickets")
    order = models.ForeignKey(Order,
                              on_delete=models.CASCADE,
                              related_name="tickets")

    class Meta:
        unique_together = ("flight", "row", "seat")
        ordering = ["row", "seat", "flight"]
        indexes = [
            models.Index(fields=["row", "seat", "flight"]),
        ]

    def __str__(self):
        return f"{self.flight} (row: {self.row}, seat: {self.seat.upper()})"

    def clean(self):
        airplane = self.flight.airplane
        if self.row < 1 or self.row > airplane.rows:
            raise ValidationError({"row": f"Row must be between 1 and {airplane.rows}"})
        if self.seat.upper() not in "ABCDEFGH":
            raise ValidationError({"seat": "Seat must be letter in (A-F)"})
        if self.pk is None:
            with transaction.atomic():
                locked_flight = Flight.objects.select_for_update().get(pk=self.flight.pk)
                if Ticket.objects.filter(
                        flight=locked_flight,
                        row=self.row,
                        seat__iexact=self.seat).exists():
                    raise ValidationError("Ticket already exists")

    def save(self, *args, **kwargs):
        self.seat = self.seat.upper()
        self.full_clean()
        super().save(*args, **kwargs)

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
