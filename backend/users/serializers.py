import logging

from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers, status
from rest_framework.validators import UniqueTogetherValidator

from foodgram.settings import RECIPES_LIMIT
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

    class Meta:
        model = Subscription
        fields = ['user', 'author']
        read_only_fields = ('email', 'username')
        extra_kwargs = {
            'user': {'required': False},
            'author': {'required': False},
        }

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscription.objects.filter(author=author, user=user).exists():
            raise serializers.ValidationError(
                detail='You have already subscribed to this user!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise serializers.ValidationError(
                'You cannot subscribe to yourself!'
            )
        return data


class SubscriptionRecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionShowSerializer(CustomUserSerializer):
    """"Subscription Model Serializer."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
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

    def get_recipes(self, object):
        author_recipes = object.recipes.all()[:RECIPES_LIMIT]
        return SubscriptionRecipeShortSerializer(
            author_recipes, many=True
        ).data

    def get_recipes_count(self, object):
        return object.recipes.count()
