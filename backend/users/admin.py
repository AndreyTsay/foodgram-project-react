from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name',
                    'last_name', 'password',)
    search_fields = ('username',)
    list_filter = ('username', 'email',)
    list_editable = ('password',)
    empty_value_display = '-пусто-'


admin.site.register(User, CustomUserAdmin)
