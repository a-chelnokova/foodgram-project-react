from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser, Subscription


class CustomUserAdmin(UserAdmin):
    list_display = ['pk', 'username', 'email', 'first_name', 'last_name']
    list_filter = ['email', 'username']


@register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_filter = ('user', 'author')
    empty_value_display = '-пусто-'


admin.site.register(CustomUser, CustomUserAdmin)
