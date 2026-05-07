from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Добавляем наши поля в список отображения в админке
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    
    # Добавляем поля в форму редактирования в админке
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'phone')}),
    )
    # Добавляем поля в форму создания нового пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('role', 'phone')}),
    )

admin.site.register(User, CustomUserAdmin)