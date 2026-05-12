from .forms import StudentCreateForm
from django.shortcuts import render
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from .models import Lesson, Homework, Topic, Task
from users.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from django.http import JsonResponse
import json


def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')

def logout_view(request):
    logout(request)
    return redirect('index')

def sync_lesson_statuses(user):
    """Обновляет статусы просроченных уроков для пользователя"""
    now = timezone.now()
    # Находим все запланированные уроки, которые закончились более 5 минут назад
    overdue = Lesson.objects.filter(
        status=Lesson.Status.PLANNED,
        start_time__lte=now - timedelta(minutes=65) # 60 мин урока + 5 мин запас
    )
    if user.is_teacher:
        overdue = overdue.filter(teacher=user)
    else:
        overdue = overdue.filter(student=user)
    
    overdue.update(status=Lesson.Status.COMPLETED)

@login_required
def dashboard(request):
    sync_lesson_statuses(request.user)
    if not request.user.is_teacher:
        lessons = Lesson.objects.filter(student=request.user).order_by('start_time')
        return render(request, 'platform_app/student_dashboard.html', {'lessons': lessons})

    now = timezone.now()
    base_query = Lesson.objects.select_related('student', 'topic').filter(teacher=request.user)

    # 1. Все уроки
    all_lessons = base_query.order_by('-start_time')

    # 2. Предстоящие
    upcoming_all = list(base_query.filter(
        status=Lesson.Status.PLANNED, 
        start_time__gte=now - timezone.timedelta(minutes=60)
    ).order_by('start_time'))
    
    next_lesson = upcoming_all[0] if upcoming_all else None
    upcoming_lessons = upcoming_all[1:] if upcoming_all else []

    # 3. Проведенные
    completed_lessons = base_query.filter(status=Lesson.Status.COMPLETED).order_by('-start_time')

    # 4. Отмененные
    cancelled_lessons = base_query.filter(status=Lesson.Status.CANCELLED).order_by('-start_time')

    return render(request, 'platform_app/teacher_dashboard.html', {
        'all_lessons': all_lessons,
        'next_lesson': next_lesson,
        'upcoming_lessons': upcoming_lessons,
        'completed_lessons': completed_lessons,
        'cancelled_lessons': cancelled_lessons,
    })

@login_required
def trainer_list(request):
    """Главная страница тренажера: подгружает предметы и темы"""
    subjects = Topic.objects.values_list('subject', flat=True).distinct()
    
    current_subject = request.GET.get('subject')
    if not current_subject and subjects:
        current_subject = subjects[0]
        
    topics = Topic.objects.filter(subject=current_subject).order_by('name')
    
    return render(request, 'platform_app/trainer_list.html', {
        'subjects': subjects,
        'current_subject': current_subject,
        'topics': topics
    })

@login_required
def get_tasks_api(request, topic_id):
    """API: Отдает по 15 задач для бесконечного скролла"""
    page_number = request.GET.get('page', 1)
    tasks_queryset = Task.objects.filter(topic_id=topic_id).order_by('id')
    
    paginator = Paginator(tasks_queryset, 15)
    page_obj = paginator.get_page(page_number)
    
    tasks_data = [{'id': t.id, 'text': t.text} for t in page_obj]
        
    return JsonResponse({
        'tasks': tasks_data,
        'has_next': page_obj.has_next(),
        'current_page': page_obj.number
    })

@login_required
def check_task_api(request):
    """API: Проверка ответа без перезагрузки"""
    if request.method == 'POST':
        data = json.loads(request.body)
        task = get_object_or_404(Task, id=data.get('task_id'))
        user_answer = data.get('answer', '').strip().lower()
        is_correct = user_answer == task.answer.strip().lower()
        return JsonResponse({
            'is_correct': is_correct,
            'correct_answer': task.answer,
            'solution': task.solution # Показываем разбор только после проверки
        })

@login_required
def get_topics_api(request, subject_name):
    """API: Отдает список тем для выбранного предмета"""
    topics = Topic.objects.filter(subject=subject_name).values('id', 'name')
    return JsonResponse({'topics': list(topics)})

@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    sync_lesson_statuses(request.user) # Обновляем перед показом
    lesson = get_object_or_404(Lesson, id=lesson_id)
    now = timezone.now()

    # Кнопка активна за 15 минут до начала И всё время, пока идет урок (60 мин)
    lesson_end_time = lesson.start_time + timedelta(minutes=60)
    can_join = (lesson.start_time - timedelta(minutes=15)) <= now <= lesson_end_time
    is_past = now > lesson_end_time


    # Проверка доступа: только учитель этого урока или сам ученик
    if request.user != lesson.teacher and request.user != lesson.student:
        raise PermissionDenied

    # Получаем или создаем объект домашки для этого урока
    homework, created = Homework.objects.get_or_create(lesson=lesson)

    if request.method == 'POST':
        if request.user.is_teacher:
            # Учитель обновляет тему, ссылку на материалы и описание ДЗ
            lesson.status = request.POST.get('status', lesson.status)
            lesson.material_link = request.POST.get('material_link', lesson.material_link)
            lesson.save()
            
            homework.description = request.POST.get('description', homework.description)
            homework.save()
        else:
            # Ученик отправляет отчет
            homework.report = request.POST.get('report', homework.report)
            homework.status = Homework.Status.REVIEW # Автоматически ставим "На проверке"
            homework.save()
            
        return redirect('lesson_detail', lesson_id=lesson.id)

    return render(request, 'platform_app/lesson_detail.html', {
            'lesson': lesson,
            'homework': homework,
            'can_join': can_join,
            'is_past': is_past,
        })

@login_required
def student_list(request):
    if not request.user.is_teacher:
        raise PermissionDenied

    # Базовый QuerySet: только те, кто связан уроками с этим учителем
    # Или вообще все ученики, если ты хочешь видеть всех зарегистрированных
    student_ids = Lesson.objects.filter(teacher=request.user).values_list('student_id', flat=True).distinct()
    students = User.objects.filter(id__in=student_ids).prefetch_related('lessons_student__homework')

    # Получаем параметры фильтрации
    query = request.GET.get('q', '')
    subject = request.GET.get('subject', '')
    grade = request.GET.get('grade', '')
    hw_status = request.GET.get('hw_status', '')

    # 1. Поиск по имени/фамилии
    if query:
        students = students.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )

    # 2. Фильтр по классу
    if grade:
        students = students.filter(grade=grade)

    # 3. Фильтр по предмету (через связанные уроки)
    if subject:
        students = students.filter(lessons_student__topic__subject=subject)

    if hw_status == 'pending':
        students = students.filter(lessons_student__homework__status='REVIEW')
    elif hw_status == 'missing':
        students = students.filter(lessons_student__homework__status='TODO')
    elif hw_status == 'fixing':
        # Новое: Требует исправления
        students = students.filter(lessons_student__homework__status='FIXING')
    elif hw_status == 'done':
        # Новое: Выполнено
        students = students.filter(lessons_student__homework__status='DONE')

    students = students.distinct()

    # Для выпадающего списка предметов получим все уникальные предметы учителя
    subjects = Lesson.objects.filter(teacher=request.user, topic__isnull=False)\
        .values_list('topic__subject', flat=True).distinct()
    
    # Добавляем подсчет домашних заданий со статусом REVIEW (на проверке) и TODO (не начато)
    students = students.annotate(
        hw_pending_count=Count('lessons_student__homework', filter=Q(lessons_student__homework__status='REVIEW')),
        hw_missing_count=Count('lessons_student__homework', filter=Q(lessons_student__homework__status='TODO'))
    )

    return render(request, 'platform_app/student_list.html', {
        'students': students,
        'query': query,
        'subjects': subjects,
        'selected_subject': subject,
        'selected_grade': grade,
        'selected_hw': hw_status,
    })


@login_required
def student_detail(request, student_id):
    if not request.user.is_teacher:
        raise PermissionDenied # Ограничение доступа

    student = get_object_or_404(User, id=student_id)
    now = timezone.now()

    overdue_lessons = Lesson.objects.filter(
        student = student,
        status  =Lesson.Status.PLANNED,
        start_time__lte = now - timedelta(minutes=60) # Даем 1 час запаса
    )
    overdue_lessons.update(status=Lesson.Status.COMPLETED)

    # Все уроки этого ученика с текущим учителем
    lessons = Lesson.objects.filter(student=student, teacher=request.user).order_by('-start_time')
    homeworks = Homework.objects.filter(lesson__student=student, lesson__teacher=request.user)
    # Статистика
    total_lessons = lessons.count()
    # Используем класс статусов из модели для надежности
    completed_homeworks = homeworks.filter(status=Homework.Status.DONE).count()
    completed_lessons = lessons.filter(status=Lesson.Status.COMPLETED).count()
    missed_lessons = lessons.filter(status=Lesson.Status.MISSED).count()
    
    # Считаем выполненные ДЗ
    # Собираем все ДЗ, привязанные к урокам этого ученика

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
    if not request.user.is_teacher:
        raise PermissionDenied # Ограничение доступа

    lesson = get_object_or_404(Lesson, id=lesson_id, teacher=request.user)
    lesson.status = status
    lesson.save()
    
    # Возвращаемся туда, откуда пришли (на страницу ученика или дашборд)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def toggle_homework(request, homework_id):
    if not request.user.is_teacher:
        raise PermissionDenied # Ограничение доступа

    homework = get_object_or_404(Homework, id=homework_id, lesson__teacher=request.user)

    if homework.status == Homework.Status.DONE:
        homework.status = Homework.Status.TODO
    else:
        homework.status = Homework.Status.DONE

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
        
        task = tasks.order_by('?').first()
        return render(request, 'platform_app/trainer_task.html', {
            'topic': topic,
            'task': task,
        })

@login_required
def create_student(request):
    if not request.user.is_teacher:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentCreateForm()
    
    return render(request, 'platform_app/create_student.html', {'form': form})