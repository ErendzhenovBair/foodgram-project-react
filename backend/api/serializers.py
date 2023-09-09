import base64
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, ValidationError

from recipes.models import (Favourite, Ingredient, IngredientsAmount, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription, User
from users.serializers import CustomUserSerializer

SELF_FOLLOW_ERROR = "You can't subscribe to yourself"

User = get_user_model()
log = logging.getLogger(__name__)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientsAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        read_only=True,
        many=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsAmountSerializer(
        many=True,
        source='ingredients_amount'
    )
    image = Base64ImageField(
        required=False,
        allow_null=True
    )
    shopping_cart = serializers.SerializerMethodField()
    is_favourited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'tags', 'author', 'ingredients', 'is_favourited',
                  'shopping_cart', 'name', 'image', 'text',
                  'cooking_time', ]
        read_only_fields = ['id', 'author', ]

    def get_is_favourited(self, recipe):
        user = self.context.get('user')
        return (
            user
            and Favourite.objects.filter(
                who_favourited__id=user.id, favourited_recipe=recipe).exists()
        )

    def get_shopping_cart(self, recipe) -> bool:
        user = self.context.get('user')
        return (
            not user.is_anonymous
            and ShoppingCart.objects.filter(
                user=user, recipe_in_cart=recipe).exists()
        )

    def get_author(self, obj):
        if 'user' in self.context:
            return self.context['user']
        return None

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = self.initial_data.get('tags')
        user = self.context['user']
        if user.is_authenticated:
            instance = Recipe.objects.create(author=user, **validated_data)
            instance.tags.set(tags)
            instance.save()
            batch = []
            for ingredient in ingredients:
                batch.append(IngredientsList(
                    ingredient_id=ingredient['id'],
                    recipe_id=instance.id,
                    amount=ingredient['amount']))
            IngredientsList.objects.bulk_create(batch)
            return instance

    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.tags.set(self.initial_data.get('tags'))
        IngredientsList.objects.filter(recipe=instance).all().delete()
        batch = []
        for ingredient in validated_data.get('ingredients'):
            batch.append(IngredientsList(
                ingredient_id=ingredient['id'],
                recipe_id=instance.id,
                amount=ingredient['amount']))
        IngredientsList.objects.bulk_create(batch)
        validated_data.pop('ingredients')
        super().update(instance, validated_data)
        return instance

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'you need at least one ingredient'
                                'for the recipe'})
        ingredient_list = set()
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient_item['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ingredients should be unique')
            ingredient_list.add(ingredient)
            if int(ingredient_item['amount']) < 0:
                raise serializers.ValidationError({
                    'ingredients': ('Make sure that the value of the '
                                    'ingredient quantity is greater than 0')
                })
        data['ingredients'] = ingredients
        return data


class RecipeLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'image',
            'cooking_time'
        ]


class FavouriteSerializer(RecipeLightSerializer):
    who_favourited = serializers.SerializerMethodField()
    favourited_recipe = serializers.SerializerMethodField()

    def get_who_favourited(self, obj):
        if "who_favourited" in self.context:
            return self.context["who_favourited"].id
        return None

    def get_favourited_recipe(self, obj):
        if "favourited_recipe" in self.context:
            return self.context["favourited_recipe"].id
        return None

    class Meta:
        model = Favourite
        fields = ['who_favourited', 'favourited_recipe']

    def create(self, validated_data):
        user_id = self.context["who_favourited"].id
        recipe_id = self.context["favourited_recipe"].id
        if Favourite.objects.filter(who_favourited_id=user_id,
                                    favourited_recipe_id=recipe_id):
            raise serializers.ValidationError('You cannot add the recipe'
                                              'to favourites twice')
        favourite_recipe = Favourite.objects.create(
            who_favourited_id=user_id,
            favourited_recipe_id=recipe_id)
        favourite_recipe.save()
        return favourite_recipe


class ShoppingCartSerializer(RecipeLightSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
    )
    recipe_in_cart = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe_in_cart')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='You have already added the recipe to shopping cart'
            )
        ]


class SubscriptionCreateDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['user', 'author']
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
                message='You have already subscribed to this author'
            )
        ]

    def validate_following(self, value):
        if value == self.context['request'].user:
            raise ValidationError(SELF_FOLLOW_ERROR)
        return value


class SubscriptionListSerializer(serializers.ModelSerializer):
    recipes = RecipeLightSerializer(many=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count']

    def get_is_subscribed(self, author) -> bool:
        user = self.context.get('user')
        return (
            user
            and Subscription.objects.filter(author=author,
                                            user=user).exists()
        )

    def get_recipes_count(self, author) -> int:
        return Recipe.objects.filter(author=author).count()

    def get_is_favourited(self, recipe) -> bool:
        user = self.context.get('user')
        return (
            user
            and Favourite.objects.filter(
                who_favourited__id=user.id, favourited_recipe=recipe).exists()
        )