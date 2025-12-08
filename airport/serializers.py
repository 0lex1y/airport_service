from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from airport.models import (AirplaneType, Airplane, Crew, Airport, Route,
                            Flight, Ticket, Order, Country, City)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name", "code")
        read_only_fields = ("id",)


# For list reading
class CityListSerializer(serializers.ModelSerializer):
    country = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = City
        fields = ("id", "name", "country")
        read_only_fields = ("id",)

# For retrieve reading
class CityDetailSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = City
        fields = ("id", "name", "country")
        read_only_fields = ("id",)

# For City post
class CityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "country")

    def validate(self, attrs):
        name = attrs.get("name")
        country = attrs.get("country")
        if City.objects.filter(name__iexact=name, country=country).exists():
            if self.instance and self.instance.name.lower() == name.lower() and self.instance.country == country:
                return attrs
            raise serializers.ValidationError("City already exists")
        return attrs


# For list reading
class AirportListSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source="city.name", read_only=True)
    country = serializers.CharField(source="country.name", read_only=True)

    class Meta:
        model = Airport
        fields = ("id", "code", "name", "city", "country")
        read_only_fields = ("id",)

# For retrieve reading
class AirportDetailSerializer(serializers.ModelSerializer):
    city = CityListSerializer(many=False, read_only=True)
    country = CountrySerializer(many=False, read_only=True)

    class Meta:
        model = Airport
        fields = ("id", "code", "name", "city", "country")
        read_only_fields = ("id",)


# For Airport Post
class AirportCreateSerializer(serializers.ModelSerializer):
    city = PrimaryKeyRelatedField(queryset=City.objects.all(),
                                  error_messages={"does_not_exist": "City with this id dosnt exist"})

    class Meta:
        model = Airport
        fields = ("id", "code", "name", "city", "country")

    def validate_code(self, value):
        value = value.upper().strip()
        if Airport.objects.filter(code__iexact=value).exists():
            if self.instance and self.instance.name.lower() == value:
                return value
            raise serializers.ValidationError("Airport already exists")
        return value


# For Route list reading
class RouteListSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name", read_only=True)
    destination = serializers.CharField(source="destination.name", read_only=True)
    source_code = serializers.CharField(read_only=True, source="source.code")
    destination_code = serializers.CharField(read_only=True, source="destination.code")

    class Meta:
        model = Route
        fields = ("id",
                  "source", "source_code",
                  "destination", "destination_code",
                  "distance"
                  )
        read_only_fields = ("id",)

# For Route list reading
class RouteDetailSerializer(serializers.ModelSerializer):
    source = AirportDetailSerializer(read_only=True)
    destination = AirportDetailSerializer(read_only=True)
    source_code = serializers.CharField(read_only=True, source="source.code")
    destination_code = serializers.CharField(read_only=True, source="destination.code")

    class Meta:
        model = Route
        fields = ("id",
                  "source", "source_code",
                  "destination", "destination_code",
                  "distance"
                  )
        read_only_fields = ("id",)


# For Route post
class RouteCreateSerializer(serializers.ModelSerializer):
    source = PrimaryKeyRelatedField(queryset=Airport.objects.all(),
                                    error_messages={"does_not_exist": "Source airport dosnt exist"})
    destination = PrimaryKeyRelatedField(queryset=Airport.objects.all(),
                                         error_messages={"does_not_exist": "Destination airport dosnt exist"})

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")

# Airplane

class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class CrewSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


# For airplane read
class AirplaneSerializer(serializers.ModelSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row",
                  "airplane_type", "capacity")
        read_only_fields = ("id", "capacity")


# For airplane post
class AirplaneCreateSerializer(serializers.ModelSerializer):
    airplane_type = serializers.PrimaryKeyRelatedField(
        queryset=AirplaneType.objects.all()
    )

    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type")

    def validate(self, attrs):
        rows = attrs.get("rows")
        seats = attrs.get("seats_in_row")
        if rows is not None and rows < 1:
            raise serializers.ValidationError("Row must be greater than 1")
        if seats is not None and seats < 1:
            raise serializers.ValidationError("Seats must be greater than 1")
        return attrs


# For Flight list reading
class FlightListSerializer(serializers.ModelSerializer):
    route_city = serializers.CharField(read_only=True, source="route.source.city.name")
    destination_city = serializers.CharField(read_only=True, source="route.destination.city.name")
    airplane = serializers.CharField(read_only=True, source="airplane.name")
    crew = serializers.CharField(read_only=True, source="crew.full_name")
    available_seats = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = ("id", "route_city", "destination_city", "airplane", "arrival_time", "departure_time",
                  "crew", "available_seats")

# For Flight detail reading
class FlightDetailSerializer(serializers.ModelSerializer):
    route = RouteDetailSerializer(read_only=True)
    airplane = AirplaneSerializer(read_only=True)
    crew = CrewSerializer(read_only=True, many=True)
    available_seats = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "arrival_time", "departure_time",
                  "crew", "available_seats")

# For Flight post
class FlightCreateSerializer(serializers.ModelSerializer):
    route = serializers.PrimaryKeyRelatedField(queryset=Route.objects.all())
    airplane = serializers.PrimaryKeyRelatedField(queryset=Airplane.objects.all())
    crew = serializers.PrimaryKeyRelatedField(queryset=Crew.objects.all(),
                                              many=True, required=False)

    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "departure_time", "arrival_time", "crew")

    def validate(self, attrs):
        arrival_time = attrs.get("arrival_time")
        departure_time = attrs.get("departure_time")
        if arrival_time <= departure_time:
            raise serializers.ValidationError("Arrival time must be later than departure time")
        return attrs

    def create(self, validated_data):
        crew = validated_data.pop("crew", [])
        flight = Flight.objects.create(**validated_data)
        if crew:
            flight.crew.set(crew)
        return flight

    def update(self, instance, validated_data):
        crew = validated_data.pop("crew")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            instance.save()
        if crew is not None:
            instance.crew.set(crew)
        return instance


# Orders

class TicketSerializer(serializers.ModelSerializer):
    flight = serializers.CharField(read_only=True, source="flight_id")

    class Meta:
        model = Ticket
        fields = ("id", "flight", "row", "seat", "order")


class TicketCreateSerializer(serializers.ModelSerializer):
    flight = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all())

    class Meta:
        model = Ticket
        fields = ("flight", "row", "seat")

    def validate(self, attrs):
        flight = attrs.get("flight")
        airplane = flight.airplane

        if not (1 <= attrs["row"] <= airplane.rows):
            raise serializers.ValidationError({"row": f"Row must be between 1 and {airplane.rows}"})
        if Ticket.objects.filter(
                airplane=airplane,
                flight=flight).exists():
            raise serializers.ValidationError({"flight": f"Flight {flight} already exists"})
        return attrs



class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "created_at", "status", "tickets")
        read_only_fields = ("id", "created_at", "status")
