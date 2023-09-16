import base64
import logging

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, ReadOnlyField
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favourite, Ingredient, IngredientsAmount, Recipe, ShoppingCart, Tag)
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


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsInRecipeWriteSerializer(ModelSerializer):
    id = IntegerField(write_only=True)
    amount = IntegerField(required=True)
    name = SerializerMethodField()
    measurement_unit = SerializerMethodField()

    class Meta:
        model = IngredientsAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_measurement_unit(self, ingredient):
        return ingredient.ingredient.measurement_unit

    def get_name(self, ingredient):
        return ingredient.ingredient.name


class IngredientsAmountSerializer(ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = ReadOnlyField(source="ingredient.name")
    measurement_unit = ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = IngredientsAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGETSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsAmountSerializer(many=True)
    is_favourited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favourited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favourited(self, object):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.favourites.filter(
            favourited_recipe=object
        ).exists()

    def get_is_in_shopping_cart(self, object):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.shopping_cart.filter(recipe=object).exists()


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsAmountSerializer(many=True)
    image = Base64ImageField(use_url=True, max_length=None)
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )

    def validate_ingredients(self, ingredients):
        ingredients_data = [
            ingredient.get('id') for ingredient in ingredients
        ]
        if len(ingredients_data) != len(set(ingredients_data)):
            raise serializers.ValidationError(
                'Ингредиенты рецепта должны быть уникальными'
            )
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            if amount is not None and amount < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента не может быть меньше 1'
                )
            if amount is not None and amount > 400:
                raise serializers.ValidationError(
                    'Количество ингредиента не может быть больше 400'
                )
        return ingredients

    def validate_tags(self, tags):
        """Проверяем, что рецепт содержит уникальные теги."""
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги рецепта должны быть уникальными'
            )
        return tags

    @staticmethod
    def add_ingredients(ingredients_data, recipe):
        """Добавляет ингредиенты."""
        IngredientsAmount.objects.bulk_create([
            IngredientsAmount(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        author = self.context.get('request').user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self.add_ingredients(ingredients_data, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        recipe = instance
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.name)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.tags.clear()
        instance.ingredients.clear()
        tags_data = validated_data.get('tags')
        instance.tags.set(tags_data)
        ingredients_data = validated_data.get('ingredients')
        IngredientsAmount.objects.filter(recipe=recipe).delete()
        self.add_ingredients(ingredients_data, recipe)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGETSerializer(
            instance, context=context).data


class RecipeLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'image',
            'cooking_time'
        ]


class FavouriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favourite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favourite.objects.all(),
                fields=('who_favourited', 'favourited_recipe'),
                message='Have you already added this recipe to your favorites'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Have you already added this recipe to your card'
            )
        ]
