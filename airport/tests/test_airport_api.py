import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import (
    Airplane,
    Route,
    Flight,
    AirplaneType,
    Country,
    City,
    Airport,
    Crew,
    Order,
    Ticket,
)

ORDER_URL = reverse("airport:order-list")
FLIGHTS_URL = reverse("airport:flight-list")


class UnauthenticatedMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ORDER_URL)
        print(res.content)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "testuser@example.com",
            "testpassword",
        )
        self.admin_user = get_user_model().objects.create_superuser(
            "admin@example.com",
            "testpassword",
        )

        self.country = Country.objects.create(name="Test Country", code="TC")
        self.city = City.objects.create(name="Test City", country=self.country)

        self.airport_source = Airport.objects.create(
            code="AAA", name="Airport A", city=self.city, country=self.country
        )

        self.airport_destination = Airport.objects.create(
            code="BBB", name="Airport B", city=self.city, country=self.country
        )

        self.route = Route.objects.create(
            source=self.airport_source,
            destination=self.airport_destination,
            distance=500,
        )

        self.airplane_type = AirplaneType.objects.create(name="Test Type")

        self.airplane = Airplane.objects.create(
            name="Plane X",
            rows=30,
            seats_in_row=6,
            airplane_type=self.airplane_type,
        )

        self.flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time=timezone.now(),
            arrival_time=timezone.now() + datetime.timedelta(hours=1),
        )

        self.flight.crew.add(
            Crew.objects.create(first_name="Ivan", last_name="Ivanov")
        )

    def test_create_order(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("airport:order-list")
        payload = {
            "tickets": [{"flight": self.flight.id, "row": 28, "seat": "A"}]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_cannot_take_one_place_twice(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("airport:order-list")
        payload_1 = {
            "tickets": [{"flight": self.flight.id, "row": 28, "seat": "A"}]
        }
        self.client.post(url, payload_1, format="json")
        payload_2 = {
            "tickets": [{"flight": self.flight.id, "row": 28, "seat": "A"}]
        }
        response = self.client.post(url, payload_2, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "The fields flight, row, seat must make a unique set.",
            str(response.data),
        )

    def test_filter_orders_by_status(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("airport:order-list")
        self.client.post(
            url,
            {"tickets": [{"flight": self.flight.id, "row": 28, "seat": "A"}]},
            format="json",
        )
        response = self.client.get(url + "?status=pending", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_flight_schema(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("airport:order-list")
        payload = {
            "tickets": [
                {"flight": self.flight.id, "row": 12, "seat": "A"},
                {"flight": self.flight.id, "row": 12, "seat": "B"},
            ]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        seats_url = reverse(
            "airport:flight-seats", kwargs={"pk": self.flight.id}
        )
        response = self.client.get(seats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["total"], 180)
        self.assertEqual(data["available"], 178)
        self.assertIn("12A", data["taken"])
        self.assertIn("12B", data["taken"])
        self.assertIn("layout", data)

    def test_airport_search(self):
        self.client.force_authenticate(user=self.user)
        Airport.objects.create(
            code="KBP",
            name="Boryspil",
            city=self.city,
            country=self.city.country,
        )
        Airport.objects.create(
            code="WAW",
            name="Chopin",
            city=self.city,
            country=self.city.country,
        )

        response = self.client.get(
            reverse("airport:airports-list") + "?code=KBP"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["code"], "KBP")
