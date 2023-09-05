from django.contrib import admin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name',
                    'last_name', 'email', 'role', 'admin')
    search_fields = ('username', 'email')
    list_filter = ('username', 'email',)
    empty_value_display = '-empty-'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author',)
