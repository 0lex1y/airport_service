from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField

from airport.models import AirplaneType, Airplane, Crew, Airport, Route, Flight, Ticket, Order, Country, City


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name", "code")
        read_only_fields = ("id",)


# For reading
class CitySerializer(serializers.ModelSerializer):
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


# For read Airport
class AirportSerializer(serializers.ModelSerializer):
    city = CitySerializer(many=False, read_only=True)

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


# For Route reading
class RouteSerializer(serializers.ModelSerializer):
    source = AirportSerializer(read_only=True)
    destination = AirportSerializer(read_only=True)
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

        def validate(self, attrs):
            source = attrs.get("source_id")
            destination = attrs.get("destination_id")
            if source == destination:
                raise serializers.ValidationError("Source and destination must be different")
            if Route.objects.filter(source_id=source,
                                    destination_id=destination).exists():
                raise ValidationError("Source and destination must be different")
            return attrs


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
    airplane_type_id = serializers.PrimaryKeyRelatedField(
        queryset=AirplaneType.objects.all(),
        error_messages={"does_not_exist": "Airplane type does not exist"}
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

# For Flight read
class FlightSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
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


class OrderSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "ticket", "created_at")
