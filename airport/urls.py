from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.authentication import JWTAuthentication

from airport.views import (OrderViewSet, FlightViewSet, AirplaneViewSet,
                           CrewViewSet, RouteViewSet, AirplaneTypeViewSet,
                           CountryViewSet, CityViewSet, AirportViewSet)

router = DefaultRouter()
# Airport
router.register("countries", CountryViewSet, basename="countries")
router.register("cities", CityViewSet, basename="cities")
router.register("airports", AirportViewSet, basename="airports")
router.register("routes", RouteViewSet, basename="routes")

# Airplane
router.register("airplane_types", AirplaneTypeViewSet)
router.register("crew", CrewViewSet)
router.register("airplanes", AirplaneViewSet)

# Orders
router.register("orders", OrderViewSet)

# Flights
router.register("flights", FlightViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
router.authentication_classes = [JWTAuthentication]
app_name = "airport"
