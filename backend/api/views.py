from datetime import datetime
import logging

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .permissions import IsAuthorOrAdminReadOnly
from recipes.models import (
    Favourite, Ingredient, IngredientsAmount,
    Recipe, ShoppingCart, Tag
)
from .filters import IngredientFilter, RecipeFilter
from .serializers import (
    IngredientSerializer, RecipeLightSerializer, RecipeGETSerializer,
    RecipeSerializer, ShoppingCartSerializer, TagSerializer)

User = get_user_model()

logging.basicConfig(format='%(message)s')
log = logging.getLogger(__name__)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name', )
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrAdminReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def add_to(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response(
                {'errors': 'The recipe has already been added!'},
                status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeLightSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'The recipe has already been deleted!'},
            status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        url_name='favorite',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_to(Favourite, request.user, pk)
        else:
            return self.delete_from(Favourite, request.user, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def get_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'user': request.user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            shopping_cart_serializer = RecipeLightSerializer(recipe)
            return Response(
                shopping_cart_serializer.data, status=status.HTTP_201_CREATED
            )
        shopping_cart_recipe = get_object_or_404(
            ShoppingCart, user=request.user, recipe=recipe
        )
        shopping_cart_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ingredients = IngredientsAmount.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        today = datetime.today()
        shopping_cart = (
            f'Shopping cart for: {user.get_full_name()}\n\n'
            f'Date: {today:%Y-%m-%d}\n\n'
        )
        shopping_cart += '\n'.join(
            [
                f'- {ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]})'
                f' - {ingredient["amount"]}'
                for ingredient in ingredients
            ]
        )
        shopping_cart += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_cart.txt'
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGETSerializer
        return RecipeSerializer
