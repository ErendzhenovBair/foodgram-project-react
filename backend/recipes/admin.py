from django.contrib import admin

from .models import (Favourite, Ingredient, IngredientAmount, Recipe,
                     ShoppingCart, Tag)


class IngredientAmountInline(admin.TabularInline):
    model = IngredientAmount
    min_num = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'get_tags',
                    'get_ingredients', 'added_in_favorites')
    inlines = (IngredientAmountInline,)
    readonly_fields = ('added_in_favorites',)
    list_filter = ('author', 'name', 'tags',)
    empty_value_display = '-пусто-'

    def get_ingredients(sef, obj):
        return '\n'.join(
            (ingredient.name for ingredient in obj.ingredients.all())
        )
    get_ingredients.short_description = 'ingredients'

    def get_tags(self, obj):
        return '\n'.join((tag.name for tag in obj.tags.all()))
    get_ingredients.short_description = 'tags'

    def added_in_favorites(self, obj):
        return obj.favourites.count()
    get_ingredients.short_description = 'favorites'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    empty_value_display = '-пусто-'
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    empty_value_display = '-пусто-'


@admin.register(IngredientAmount)
class IngredientAmountADmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    empty_value_display = '-пусто-'
    list_filter = ('user',)
    search_fields = ('user',)
