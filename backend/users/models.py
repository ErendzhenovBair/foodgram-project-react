from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint
from django.utils.translation import gettext_lazy as _

from foodgram.settings import EMAIL_LENGTH


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    email = models.EmailField(
        'email',
        max_length=EMAIL_LENGTH,
        unique=True,
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Subscription model"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Subscriber',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Recipe Author',
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='check_user_not_subscribe_to_self',
            ),
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_pair_subscriber_subscribing'
            )
        ]

    def __str__(self):
        return f'{self.user} subscribed to: {self.author}'

    def clean(self):
        if self.user == self.author:
            raise ValidationError(
                {'user': _('You cannot subscribe to yourself!')}
            )
