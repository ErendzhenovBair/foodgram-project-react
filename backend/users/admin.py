from django import forms
from django.contrib import admin

from .models import Subscription, User


class UserChangeForm(forms.ModelForm):

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserChangeForm
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
    form = UserChangeForm
    list_display = ('id', 'user', 'author',)
