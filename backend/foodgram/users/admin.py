from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    list_filter = ('is_staff', 'is_superuser', 'is_active',
                   'groups', 'email', 'username')


admin.site.register(User, UserAdmin)
