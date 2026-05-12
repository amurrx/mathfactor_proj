"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from platform_app.views import dashboard, student_detail, update_lesson_status, toggle_homework, trainer_task, index, logout_view 

admin.site.site_header = "MathFactor Панель Управления"
admin.site.site_title = "Админка MathFactor"
admin.site.index_title = "Добро пожаловать, Артур"

urlpatterns = [
    path('admin/', admin.site.urls),
    # Все запросы, которые начинаются не с admin/, 
    # Django отправит в файл urls.py внутри приложения platform_app
    path('auth/login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('', include('platform_app.urls')), 
    
    # Если у тебя есть авторизация в приложении users, добавь и его
    path('auth/', include('django.contrib.auth.urls')),
]