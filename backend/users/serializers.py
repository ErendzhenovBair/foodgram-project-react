import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, ValidationError

from users.models import Subscription

SELF_FOLLOW_ERROR = "You can't subscribe to yourself"

User = get_user_model()
log = logging.getLogger(__name__)


class CustomUserCreateSerializer(UserCreateSerializer):
    """User model (create user) Serializer."""
    password = serializers.CharField(
        style={
            'input_type': 'password'
        },
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )


class CustomUserSerializer(UserSerializer):
    """User model Serializer."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('user')
        if user is not None and not user.is_anonymous:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False


class SetPasswordSerializer(serializers.Serializer):
    """Set password for User model Serializer."""
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate(self, data):
        new_password = data.get('new_password')
        try:
            validate_password(new_password)
        except exceptions.ValidationError as err:
            raise serializers.ValidationError(
                {'new_password': err.messages}
            )
        return super().validate(data)

    def update(self, instance, validated_data):
        current_password = validated_data.get('current_password')
        new_password = validated_data.get('new_password')
        if not instance.check_password(current_password):
            raise serializers.ValidationError(
                {
                    'current_password': 'Wrong password'
                }
            )
        if current_password == new_password:
            raise serializers.ValidationError(
                {
                    'new_password': 'The new password must be different from '
                                    'the current password'
                }
            )
        instance.set_password(new_password)
        instance.save()
        return validated_data


class SubscriptionCreateDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['user', 'author']
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
                message='You have already subscribed to this author'
            )
        ]

    def validate_following(self, value):
        if value == self.context['request'].user:
            raise ValidationError(SELF_FOLLOW_ERROR)
        return value
