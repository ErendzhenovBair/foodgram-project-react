from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import (Favourite, Ingredient, IngredientAmount, Recipe,
                     ShoppingCart, Tag)

from foodgram.settings import ZERO_VALUE


class IngredientAmountFormset(BaseInlineFormSet):
    def clean(self):
        super(IngredientAmountFormset, self).clean()
        count = ZERO_VALUE
        for form in self.forms:
            if form.cleaned_data.get('DELETE'):
                count += 1
        if count == len(self.forms):
            raise ValidationError('You cannot delete all ingredients')


class IngredientAmountInline(admin.TabularInline):
    model = IngredientAmount
    formset = IngredientAmountFormset
    extra = 1
    min_num = 1
    autocomplete_fields = ('ingredient',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author',
                    'added_in_favorites')
    inlines = (IngredientAmountInline,)
    readonly_fields = ('added_in_favorites',)
    list_filter = ('author', 'name', 'tags',)
    empty_value_display = '-пусто-'

    def added_in_favorites(self, obj):
        return obj.favourites.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'
    search_fields = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    empty_value_display = '-пусто-'
    list_filter = ('name',)
    search_fields = ('name',)


class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    empty_value_display = '-пусто-'


class IngredientAmountADmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
    empty_value_display = '-пусто-'


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    empty_value_display = '-пусто-'
    list_filter = ('user',)
    search_fields = ('user',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Favourite, FavouriteAdmin)
admin.site.register(IngredientAmount, IngredientAmountADmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
