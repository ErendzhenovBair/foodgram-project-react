import logging

from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Recipe
from users.models import Subscription

User = get_user_model()
log = logging.getLogger(__name__)


class CustomUserCreateSerializer(UserCreateSerializer):
    """User model (create user) Serializer."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {"password": {"write_only": True}}

        def validate(self, data):
            if User.objects.filter(username=data.get('username')):
                raise serializers.ValidationError(
                    'A user with this username already exists!'
                )
            if User.objects.filter(email=data.get('email')):
                raise serializers.ValidationError(
                    'A user with this email already exists!'
                )
            return data


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user is not None and not user.is_anonymous:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    """Subscrtion model Serializer."""
    class Meta:
        model = Subscription
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='You have already subscribed to this author!'
            )
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'You cannot subscribe to yourself!'
            )
        return data


class SubscriptionRecipeShortSerializer(serializers.ModelSerializer):
    """Subscrtion model (for displaying recipes in subscription) Serializer."""
    class Meta:
        model = Recipe
        fields = (
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionShowSerializer(CustomUserSerializer):
    """"Subscription Display Sterilizer."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, author):
        return Recipe.objects.filter(author=author).count()

    def get_recipes_count(self, object):
        return object.recipes.count()
