from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'), # Новый эндпоинт
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('update-lesson/<int:lesson_id>/<str:status>/', views.update_lesson_status, name='update_lesson_status'),
    path('toggle-homework/<int:homework_id>/', views.toggle_homework, name='toggle_homework'),
    path('trainer/<int:topic_id>/', views.trainer_task, name='trainer_task'),
]