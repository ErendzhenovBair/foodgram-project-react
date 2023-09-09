import base64
import logging

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
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
    is_favourited = serializers.BooleanField(read_only=True)
    shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = ['id', 'tags', 'author', 'ingredients', 'is_favourited',
                  'shopping_cart', 'name', 'image', 'text',
                  'cooking_time', ]
        read_only_fields = ['id', 'author', ]


class RecipeWriteSerializer(RecipeSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )

    @staticmethod
    def save_ingredients(recipe, ingredients):
        ingredients_list = []
        for ingredient in ingredients:
            current_ingredient = ingredient['ingredient']['id']
            current_amount = ingredient.get('amount')
            ingredients_list.append(
                IngredientsAmount(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=current_amount
                )
            )
        IngredientsAmount.objects.bulk_create(ingredients_list)

    def validate(self, data):
        cooking_time = data.get('cooking_time')
        if cooking_time <= 0:
            raise serializers.ValidationError(
                {
                    'error': 'Cooking time cannot be less than minutes'
                }
            )
        ingredients_list = []
        ingredients_amount = data.get('ingredients_amount')
        for ingredient in ingredients_amount:
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    {
                        'error': 'The ingredients number cannot be less than 1'
                    }
                )
            ingredients_list.append(ingredient['ingredient']['id'])
        if len(ingredients_list) > len(set(ingredients_list)):
            raise serializers.ValidationError(
                {
                    'error': 'Ingredients should not be repeated'
                }
            )
        return data

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients = validated_data.pop('ingredients_amount')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=author)
        recipe.tags.add(*tags)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        ingredients = validated_data.pop('ingredients_amount')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.add(*tags)
        instance.ingredients.clear()
        recipe = instance
        self.save_ingredients(recipe, ingredients)
        instance.save()
        return instance


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