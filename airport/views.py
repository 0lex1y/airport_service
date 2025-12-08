from datetime import timezone

from django.conf.global_settings import Router
from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets

from airport.models import Airport, Order, Flight, Crew, Airplane, Route, Country, City
from airport.serializers import AirportSerializer, OrderSerializer, FlightSerializer, CrewSerializer, \
    AirplaneSerializer, RouteSerializer, AirplaneTypeSerializer, CountrySerializer, CitySerializer, \
    CityCreateSerializer, AirportCreateSerializer, RouteCreateSerializer, AirplaneCreateSerializer, \
    FlightCreateSerializer

# Airport
class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    search_fields = ('name', "code")
    ordering_fields = ('name', "code")


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.select_related("country").all()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CitySerializer
        else:
            return CityCreateSerializer
    search_fields = ('name', "country__name")
    ordering_fields = ('name', "country__name")


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.select_related("city__country").all()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AirportSerializer
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
        if self.action in ("list", "retrieve"):
            return RouteSerializer
        else:
            return RouteCreateSerializer
    search_fields = ("source__code", "destination__code")
    ordering_fields = ("distance", "source__code")

# Airplane
class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

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


# Flight
class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.select_related("route__source__city__country",
                                             "route__destination__city__country",
                                             "airplane__airplane_type").prefetch_related("crew").all()


    def get_queryset(self):
        queryset = super().get_queryset()

        date = self.request.query_params.get("date")
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")
        if date:
            day = timezone.datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time__date=day)
        if source:
            queryset = queryset.filter(route__source__code__iexact=source)
        if destination:
            queryset = queryset.filter(route__destination__code__iexact=destination)
        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return FlightSerializer
        else:
            return FlightCreateSerializer
