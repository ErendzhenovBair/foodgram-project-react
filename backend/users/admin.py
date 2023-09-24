from django.contrib import admin
from django.core.exceptions import ValidationError

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

    def save_model(self, request, obj, form, change):
        if obj.author == request.user:
            raise ValidationError('You cannot subscribe to yourself!')
        super().save_model(request, obj, form, change)
