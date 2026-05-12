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
    path('students/add/', views.create_student, name='create_student'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('trainer/', views.trainer_list, name='trainer_list'), # Основная страница
    path('api/get-tasks/<int:topic_id>/', views.get_tasks_api, name='get_tasks_api'),
    path('api/check-task/', views.check_task_api, name='check_task_api'),
    path('api/get-topics/<str:subject_name>/', views.get_topics_api, name='get_topics_api'),
]