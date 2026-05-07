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
from django.urls import path
from platform_app.views import dashboard
from platform_app.views import dashboard, student_detail, update_lesson_status, toggle_homework, trainer_task, index, logout_view 


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('dashboard/', dashboard, name='dashboard'),

    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    
    path('student/<int:student_id>/', student_detail, name='student_detail'),
    path('lesson/<int:lesson_id>/status/<str:status>/', update_lesson_status, name='update_lesson_status'),
    path('homework/<int:homework_id>/toggle/', toggle_homework, name='toggle_homework'),
    path('trainer/<int:topic_id>/', trainer_task, name='trainer_task'),
    # path('logout/', LogoutView.as_view(next_page='dashboard'), name='logout'),
]