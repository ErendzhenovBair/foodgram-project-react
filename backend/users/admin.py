from django import forms
from django.contrib import admin

from users.models import Subscription

from .models import Subscription, User


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = '__all__'

    def clean(self):
        if self.cleaned_data.get('user') == self.cleaned_data.get('author'):
            raise forms.ValidationError('You cannot subscribe to yourself!')
        return self.cleaned_data


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
    form = SubscriptionForm
    list_display = ('id', 'user', 'author',)
    search_fields = ('author',)
