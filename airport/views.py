import datetime

from django.db import transaction
from django.db.models import Q, Count, F
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from airport.models import (Airport, Order, Flight, Crew, Airplane, Route,
                            Country, City, AirplaneType)
from airport.serializers import (AirportListSerializer, OrderSerializer, FlightListSerializer,
                                 CrewSerializer, AirplaneSerializer, RouteListSerializer,
                                 AirplaneTypeSerializer, CountrySerializer, CityListSerializer,
                                 CityCreateSerializer, AirportCreateSerializer, RouteCreateSerializer,
                                 AirplaneCreateSerializer, FlightCreateSerializer, TicketSerializer,
                                 CityDetailSerializer, AirportDetailSerializer, RouteDetailSerializer,
                                 FlightDetailSerializer
                                 )


# Airport
class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    search_fields = ('name', "code")
    ordering_fields = ('name', "code")


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.select_related("country").all()

    def get_serializer_class(self):
        if self.action == "list":
            return CityListSerializer
        elif self.action == "retrieve":
            return CityDetailSerializer
        else:
            return CityCreateSerializer

    search_fields = ('name', "country__name")
    ordering_fields = ('name', "country__name")


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.select_related("city__country").all()

    def get_serializer_class(self):
        if self.action == "list":
            return AirportListSerializer
        elif self.action == "retrieve":
            return AirportDetailSerializer
        else:
            return AirportCreateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        code = self.request.query_params.get("code")
        city = self.request.query_params.get("city")
        country = self.request.query_params.get("country")
        if code:
            queryset = queryset.filter(code__iexact=code)
        if city:
            queryset = queryset.filter(city__name__icontains=city)
        if country:
            queryset = queryset.filter(country__name__icontains=country)
        return queryset

    search_fields = ('name', "code", "city__name")
    ordering_fields = ('name', "code")


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source__city__country",
                                            "destination__city__country").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")
        city = self.request.query_params.get("city")
        if source:
            queryset = queryset.filter(source__code__iexact=source)
        if destination:
            queryset = queryset.filter(destination__code__iexact=destination)
        if city:
            queryset = queryset.filter(
                Q(source__city__name__icontains=city) |
                Q(destination__city__name__icontains=city))
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "retrieve":
            return RouteDetailSerializer
        else:
            return RouteCreateSerializer

    search_fields = ("source__code", "destination__code")
    ordering_fields = ("distance", "source__code")


# Airplane
class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type").all()
    serializer_class = AirplaneSerializer

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AirplaneSerializer
        else:
            return AirplaneCreateSerializer

    search_fields = ('airplane_type__name', "name")
    ordering_fields = ('capacity', "name")


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("tickets__flight")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        tickets_data = request.data.get("tickets")
        if not tickets_data:
            return Response({"tickets": ["This field is required"]},
                            status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=request.user)
        for ticket_data in tickets_data:

            serializer = TicketSerializer(data=ticket_data)
            serializer.is_valid(raise_exception=True)
            serializer.save(order=order)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=["post"])
    def complete(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != "pending":
            return Response({"error": "Order already completed"},
                            status=status.HTTP_400_BAD_REQUEST)
        order.complete()
        return Response({"status": "completed"})
    @action(detail=True, methods=["post"])
    def cancel(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status == "completed":
            return Response({"error": "Cannot  cancel completed order"},
                            status=status.HTTP_400_BAD_REQUEST)
        order.cancel()
        return Response({"status": "cancelled"})

# Flight
class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.select_related("route__source__city__country",
                                             "route__destination__city__country",
                                             "airplane__airplane_type").prefetch_related("crew").all()

    def get_queryset(self):
        queryset = super().get_queryset()
        # Calculate available seats but only in pending or completed status
        queryset = queryset.annotate(
            booked_seats=Count("tickets",
                               filter=Q(tickets__order__status__in=["pending", "completed"]),
                               distinct=True),
            available_seats=F("airplane__rows") * F("airplane__seats_in_row") - F("booked_seats"),
        ).select_related("airplane", "airplane__airplane_type")
        # Filters

        date = self.request.query_params.get("date")
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")
        if date:
            day = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time__date=day)
        if source:
            queryset = queryset.filter(route__source__code__iexact=source)
        if destination:
            queryset = queryset.filter(route__destination__code__iexact=destination)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightDetailSerializer
        else:
            return FlightCreateSerializer
