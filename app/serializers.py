from rest_framework import serializers

from .models import *


class ShipSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, ship):
        return ship.image.url.replace("minio", "localhost", 1)
        
    class Meta:
        model = Ship
        fields = "__all__"


class ShipItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField('get_value')

    def get_image(self, ship):
        return ship.image.url.replace("minio", "localhost", 1)

    def get_value(self, ship):
        return self.context.get("value")

    class Meta:
        model = Ship
        fields = ("id", "name", "image", "value")


class FlightsSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    moderator = serializers.SerializerMethodField()

    def get_owner(self, flight):
        return flight.owner.username

    def get_moderator(self, flight):
        if flight.moderator:
            return flight.moderator.username

        return ""

    class Meta:
        model = Flight
        fields = "__all__"


class FlightSerializer(serializers.ModelSerializer):
    ships = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    moderator = serializers.SerializerMethodField()

    def get_owner(self, flight):
        return flight.owner.username

    def get_moderator(self, flight):
        return flight.moderator.username if flight.moderator else ""
    
    def get_ships(self, flight):
        items = ShipFlight.objects.filter(flight=flight)
        return [ShipItemSerializer(item.ship, context={"value": item.value}).data for item in items]
    
    class Meta:
        model = Flight
        fields = "__all__"


class ShipFlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipFlight
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username')


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            name=validated_data['name']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)