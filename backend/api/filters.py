from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favourited = filters.BooleanFilter(method='get_is_favourited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )
    author = filters.AllValuesMultipleFilter(field_name='author__username')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favourited', 'is_in_shopping_cart')

    def get_is_favourited(self, queryset, name, value):
        if value:
            return queryset.filter(favourites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
