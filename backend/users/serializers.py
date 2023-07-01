from django.contrib.auth import authenticate
from rest_framework import serializers


class TokenSerializer(serializers.Serializer):
    email = serializers.EmailField(
        label='Адрес электронной почты',
        write_only=True)
    password = serializers.CharField(
        label='Пароль',
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True)
    token = serializers.CharField(
        label='Токен',
        read_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password)
            if not user:
                raise serializers.ValidationError(
                    'Не удалось войти в систему с предоставленными данными',
                    code='authorization')
        else:
            raise serializers.ValidationError(
                'Необходимо указать адрес электронной почты и пароль',
                code='authorization')
        attrs['user'] = user
        return attrs
