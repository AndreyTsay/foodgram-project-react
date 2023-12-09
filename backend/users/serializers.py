import re

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from djoser.conf import settings
from djoser.serializers import TokenCreateSerializer
from rest_framework import serializers

from recipes.models import Recipe
from recipes.serializers import RecipeContextSerializer
from users import constants

from .models import User, Subscription


class SubscriptionStatusField(serializers.BooleanField):
    def to_representation(self, value):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            author=self.parent.instance,
            user=request.user
        ).exists()


class ValidateSubscriptionMixin:
    def validate_subscription(self, author):
        request = self.context.get('request')
        if Subscription.objects.filter(
                user=request.user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.')
        elif request.user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')


class UserRecipesSerializer(
        serializers.ModelSerializer, ValidateSubscriptionMixin):
    is_subscribed = SubscriptionStatusField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes',
                  'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            author=obj, user=request.user
        ).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.id)
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeContextSerializer(
            recipes,
            many=True,
            read_only=True
        )
        return serializer.data

    def validate(self, data):
        author = data['author']

        if data.get('is_subscribed'):
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.')

        if self.context['request'].user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')

        self.validate_subscription(author)

        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=constants.MAX_LENGTH_USERNAME, required=True)
    email = serializers.EmailField(
        max_length=constants.MAX_EMAIL_LENGTH, required=True)
    first_name = serializers.CharField(
        max_length=constants.MAX_FIRST_NAME_LENGTH, required=True)
    last_name = serializers.CharField(
        max_length=constants.MAX_LAST_NAME_LENGTH, required=True)
    password = serializers.CharField(
        max_length=constants.MAX_LENGTH_PASSWORD,
        required=True,
        write_only=True
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'password')

    def validate_username(self, value):
        error_list = []
        username = value
        for symbol in username:
            if not re.search(r'^[\w.@+-]+$', symbol):
                error_list.append(symbol)
        if error_list:
            raise serializers.ValidationError(
                f'Символы {"".join(error_list)} запрещены!'
            )
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(f"Имя {value} уже занято!")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "На этот адрес эл. почты уже зарегистрирован аккаунт!"
            )
        return value

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=make_password(validated_data.get('password'))
        )
        return user


class CustomTokenCreateSerializer(TokenCreateSerializer):
    password = serializers.CharField(required=False,
                                     style={"input_type": "password"})

    default_error_messages = {
        "invalid_credentials":
        settings.CONSTANTS.messages.INVALID_CREDENTIALS_ERROR,
        "inactive_account":
        settings.CONSTANTS.messages.INACTIVE_ACCOUNT_ERROR,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.fields[settings.LOGIN_FIELD] = serializers.CharField(
            required=False)

    def validate(self, attrs):
        password = attrs.get("password")
        params = {settings.LOGIN_FIELD: attrs.get(settings.LOGIN_FIELD)}
        self.user = authenticate(
            request=self.context.get("request"), **params, password=password
        )
        if not self.user:
            self.user = User.objects.filter(**params).first()
            if self.user and not self.user.check_password(password):
                raise serializers.ValidationError(
                    {'Ошибка': 'Неправильный пароль.'}
                )
        if self.user and self.user.is_active:
            return attrs
        raise serializers.ValidationError(
            {'Ошибка': 'Неправильный адрес эл. почты.'}
        )


class UserInfoSerializer(serializers.ModelSerializer):
    is_subscribed = SubscriptionStatusField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')


class UserShortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')


class NewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=150, required=True)
    current_password = serializers.CharField(max_length=150, required=True)
