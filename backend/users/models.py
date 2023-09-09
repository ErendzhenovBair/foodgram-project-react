from django.contrib.auth.models import AbstractUser
from django.db import models

SUBSCRIPTION_MESSAGE = "{subcriber} subscribed on {subscribing}"


class User(AbstractUser):
    USER: str = 'user'
    ADMIN: str = 'admin'
    CHOICES = (
        (USER, 'user'),
        (ADMIN, 'admin'),
    )
    role = models.CharField(choices=CHOICES,
                            default='user',
                            max_length=128)

    class Meta:
        ordering = ['id']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        constraints = [
            models.UniqueConstraint(fields=['username', 'email'],
                                    name='unique_user')
        ]

    def __str__(self):
        return self.username

    @property
    def is_user(self):
        return self.role == self.USER

    @property
    def is_admin(self):
        return self.role == self.ADMIN


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
