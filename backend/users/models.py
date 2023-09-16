from django.contrib.auth.models import AbstractUser
from django.db import models

SUBSCRIPTION_MESSAGE = "{subcriber} subscribed on {subscribing}"


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    email = models.EmailField(
        'email',
        max_length=254,
        unique=True,
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


class Subscription(models.Model):
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
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_pair_subscriber_subscribing'
            )
        ]

    def __str__(self):
        return SUBSCRIPTION_MESSAGE.format(
            subscriber=self.user.username, subscribing=self.author.username)
