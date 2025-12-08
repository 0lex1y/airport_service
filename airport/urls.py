from django.urls import path, include
from rest_framework.routers import DefaultRouter

from airport.views import OrderViewSet, FlightViewSet, AirplaneViewSet, CrewViewSet, RouteViewSet, AirplaneTypeViewSet, \
    CountryViewSet, CityViewSet

router = DefaultRouter()
# Airport
router.register("countries", CountryViewSet)
router.register("cities", CityViewSet)
router.register("airports", FlightViewSet)
router.register("routes", RouteViewSet)

# Airplane
router.register("airplane_types", AirplaneTypeViewSet)
router.register("crews", CrewViewSet)
router.register("airplanes", AirplaneViewSet)

# Orders
router.register("orders", OrderViewSet)

# Flights
router.register("flights", FlightViewSet)




urlpatterns = [
    path("", include(router.urls)),
]

app_name = "airport"

