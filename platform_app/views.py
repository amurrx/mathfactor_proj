import random
from django.shortcuts import render
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from .models import Lesson, Homework, Topic, Task
from users.models import User
from django.utils import timezone


def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')

def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def dashboard(request):
    # Получаем уроки текущего пользователя (и как учителя, и как ученика)
    if request.user.role == 'TEACHER':
            now = timezone.now()
            # Получаем все будущие уроки учителя
            all_upcoming = Lesson.objects.filter(
                teacher=request.user, 
                start_time__gte=now - timezone.timedelta(minutes=60) # Показываем уроки, которые начались не более часа назад
            ).order_by('start_time')

            next_lesson = all_upcoming.first() # Самый ближайший
            other_lessons = all_upcoming[1:] if all_upcoming.count() > 1 else [] # Все остальные

            student_ids = Lesson.objects.filter(teacher=request.user).values_list('student_id', flat=True).distinct()
            students = User.objects.filter(id__in=student_ids)

            return render(request, 'platform_app/teacher_dashboard.html', {
                'next_lesson': next_lesson,
                'other_lessons': other_lessons,
                'students': students
            })
    else:
         # Логика для ученика
        lessons = Lesson.objects.filter(student=request.user).order_by('start_time')
        topics = Topic.objects.all()

        return render(request, 'platform_app/student_dashboard.html', {
            'lessons': lessons,
            'topics': topics
        })

@login_required
def student_detail(request, student_id):
    if request.user.role != 'TEACHER':
        return render(request, '403.html') # Ограничение доступа

    student = get_object_or_404(User, id=student_id)
    # Все уроки этого ученика с текущим учителем
    lessons = Lesson.objects.filter(student=student, teacher=request.user).order_by('-start_time')
    
    # Статистика
    total_lessons = lessons.count()
    completed_lessons = lessons.filter(status='COMPLETED').count()
    missed_lessons = lessons.filter(status='MISSED').count()
    
    # Считаем выполненные ДЗ
    # Собираем все ДЗ, привязанные к урокам этого ученика
    homeworks = Homework.objects.filter(lesson__student=student, lesson__teacher=request.user)
    completed_homeworks = homeworks.filter(is_completed=True).count()

    context = {
        'student': student,
        'lessons': lessons,
        'stats': {
            'total': total_lessons,
            'completed': completed_lessons,
            'missed': missed_lessons,
            'hw_done': completed_homeworks,
            'hw_total': homeworks.count(),
        }
    }
    return render(request, 'platform_app/student_detail.html', context)

@login_required
def update_lesson_status(request, lesson_id, status):
    if request.user.role != 'TEACHER':
        return render(request, '403.html')
    
    lesson = get_object_or_404(Lesson, id=lesson_id, teacher=request.user)
    lesson.status = status
    lesson.save()
    
    # Возвращаемся туда, откуда пришли (на страницу ученика или дашборд)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def toggle_homework(request, homework_id):
    if request.user.role != 'TEACHER':
        return render(request, '403.html')
    
    homework = get_object_or_404(Homework, id=homework_id, lesson__teacher=request.user)
    homework.is_completed = not homework.is_completed # Переключаем статус
    homework.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

def trainer_task(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    
    if request.method == 'POST':
        # Если это POST, мы не берем рандомную задачу, 
        # а находим ту, которую ученик только что решал
        task_id = request.POST.get('task_id')
        task = get_object_or_404(Task, id=task_id)
        
        user_answer = request.POST.get('user_answer', '').strip()
        is_correct = user_answer.lower() == task.answer.strip().lower()
        
        return render(request, 'platform_app/trainer_task.html', {
            'topic': topic,
            'task': task,
            'is_correct': is_correct,
            'user_answer': user_answer
        })
        
    else:
        # Если это обычный заход на страницу (GET), выбираем рандомную задачу
        tasks = Task.objects.filter(topic=topic)
        if not tasks.exists():
            return render(request, 'platform_app/no_tasks.html', {'topic': topic})
        
        task = random.choice(tasks)
        return render(request, 'platform_app/trainer_task.html', {
            'topic': topic,
            'task': task,
        })

