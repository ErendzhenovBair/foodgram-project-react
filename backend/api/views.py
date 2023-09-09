import logging

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .pagination import CustomPagination
from .permissions import IsAuthorOrAdminReadOnly, RecipePermission
from recipes.models import (Favourite, Ingredient, Recipe,
                            ShoppingCart, Tag)
from .filters import IngredientFilter
from .serializers import (
    FavouriteSerializer, IngredientSerializer,
    RecipeLightSerializer, RecipeWriteSerializer,
    RecipeSerializer, ShoppingCartSerializer, TagSerializer)

User = get_user_model()

logging.basicConfig(format='%(message)s')
log = logging.getLogger(__name__)


def dict_to_txt(final_list: dict) -> str:
    txt_to_repr = []
    for name, value in final_list.items():
        unit = value.get('measurement_unit')
        amount = value.get('amount')
        if unit and amount:
            txt_to_repr.append(f'{name} ({unit}) — {amount}\n')
    return ''.join(txt_to_repr)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    # filterset_class = RecipeFilter
    permission_classes = [IsAuthorOrAdminReadOnly, ]
    ordering = ['-pub_date']

    def get_serializer_class(self):
        if self.action in ('favourite', 'shopping_cart'):
            return RecipeLightSerializer
        if self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'user': request.user, },
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartCreateDeleteViewSet(
    mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = (RecipePermission,)

    @action(methods=["post"], detail=False)
    def create(self, request, pk=None):
        user = get_object_or_404(User, id=request.user.id)
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = self.get_serializer(
            data=request.data, context={'user': user, 'recipe_in_cart': recipe}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['delete'], detail=False)
    def destroy(self, request, pk=None) -> Response:
        recipe_in_cart = get_object_or_404(
            ShoppingCart, user=request.user.id, recipe_in_cart_id=pk)
        self.perform_destroy(recipe_in_cart)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavouritedCreateDeleteViewSet(
    mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    queryset = Favourite.objects.all()
    serializer_class = FavouriteSerializer
    permission_classes = (RecipePermission,)

    @action(methods=["post"], detail=False)
    def create(self, request, pk=None) -> Response:
        user = get_object_or_404(User, id=request.user.id)
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = self.get_serializer(
            data=request.data,
            context={"who_favourited": user, "favourited_recipe": recipe},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["delete"], detail=False)
    def destroy(self, request, pk=None) -> Response:
        favourited = get_object_or_404(
            Favourite,
            who_favorited_id=request.user.id,
            favourited_recipe_id=pk
        )
        self.perform_destroy(favourited)
        return Response("object deleted", status=status.HTTP_204_NO_CONTENT)
