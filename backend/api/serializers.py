import base64
import logging

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer, ReadOnlyField
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favourite, Ingredient, IngredientAmount,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()
log = logging.getLogger(__name__)


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

        def validate(self, data):
            if data.get('username') == 'me':
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
            return obj.subscriber.filter(user=user).exists()
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
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='You have already subscribed to this user.'
            )
        ]

    def validate(self, data):
        if data['user'] == data['author']:
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
        author_recipes = object.recipes.all()
        return SubscriptionRecipeShortSerializer(
            author_recipes, many=True
        ).data

    def get_recipes_count(self, object):
        return object.recipes.count()


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
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class IngredientsInRecipeWriteSerializer(ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class IngredientFullSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGETSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientFullSerializer(many=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        return (
            False if user.is_anonymous
            else user.who_favourited.filter(recipe=recipe).exists()
        )

    def get_is_in_shopping_cart(self, object):
        return (self.context.get('request').user.is_authenticated
                and ShoppingCart.objects.filter(
                    user=self.context.get('request').user,
                    recipe=object
        ).exists())


class RecipeSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                  many=True)
    ingredients = IngredientsInRecipeWriteSerializer(many=True)
    image = Base64ImageField(use_url=True, max_length=None)
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError({
                'ingredients': 'At least one ingredient is needed!'
            })
        ingredients_list = [
            ingredient.get('id') for ingredient in value
        ]
        if len(ingredients_list) != len(set(ingredients_list)):
            raise ValidationError({
                'ingredients': 'The ingredients must be unique!'
            })
        for ingredient in value:
            if int(ingredient['amount']) <= 0:
                raise ValidationError({
                    'amount': 'The amount must be greater than 0!'
                })
        return value

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'At least one tag is required!'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'The tags must be unique!'
            )
        return tags

    def create_ingredients_amounts(self, ingredients, recipe):
        IngredientAmount.objects.bulk_create(
            [IngredientAmount(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    @transaction.atomic
    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(recipe, ingredients)
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
        tags = validated_data.get('tags')
        instance.tags.set(tags)
        ingredients = validated_data.get('ingredients')
        self.create_ingredients_amounts(recipe, ingredients)
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['recipe'] = RecipeLightSerializer(instance.recipe).data
        return representation


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favourite
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favourite.objects.all(),
                fields=('user', 'recipe'),
                message='Have you already added this recipe to your favorites'
            )
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['recipe'] = RecipeLightSerializer(instance.recipe).data
        return representation
