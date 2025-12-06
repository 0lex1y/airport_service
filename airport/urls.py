from django.urls import path, include
from rest_framework.routers import DefaultRouter

from airport.views import OrderViewSet, FlightViewSet, AirplaneViewSet, CrewViewSet, RouteViewSet, AirplaneTypeViewSet

router = DefaultRouter()
router.register("orders", OrderViewSet)
router.register("flights", FlightViewSet)
router.register("airports", FlightViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("crews", CrewViewSet)
router.register("routes", RouteViewSet)
router.register("airplane_types", AirplaneTypeViewSet)
urlpatterns = [
    path("", include(router.urls)),
]

app_name = "airport"

