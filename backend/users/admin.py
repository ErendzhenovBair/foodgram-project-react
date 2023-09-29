from django.contrib import admin

from users.models import Subscription

from .models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'email',
        'username', 'first_name',
        'last_name', 'password'
    )
    search_fields = ('username', 'email')
    list_filter = ('username', 'email',)
    empty_value_display = '-empty-'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author',)
    search_fields = ('author',)
