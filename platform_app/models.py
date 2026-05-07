from django.db import models
from users.models import User
from django.utils import timezone

class Topic(models.Model):
    """Темы для тренажера и уроков"""
    name = models.CharField(max_length=255, verbose_name="Название темы")
    subject = models.CharField(max_length=100, verbose_name="Предмет")

    def __str__(self):
        return f"{self.subject}: {self.name}"

class Task(models.Model):
    """Банк задач для тренажера"""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tasks')
    text = models.TextField(verbose_name="Условие задачи (Markdown/LaTeX)")
    answer = models.CharField(max_length=255, verbose_name="Правильный ответ")
    solution = models.TextField(verbose_name="Разбор решения")

    def __str__(self):
        return f"Задача #{self.id} ({self.topic.name})"

class Lesson(models.Model):
    """Расписание занятий"""
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Запланировано'
        COMPLETED = 'COMPLETED', 'Проведено'
        CANCELLED = 'CANCELLED', 'Отменено'
        MISSED = 'MISSED', 'Пропущено'

    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='lessons_teacher',
        limit_choices_to={'role': 'TEACHER'}, # Добавляем этот фильтр
        verbose_name="Учитель"
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='lessons_student',
        limit_choices_to={'role': 'STUDENT'}, # И этот тоже
        verbose_name="Ученик"
    )
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField(verbose_name="Время начала")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PLANNED)
    material_link = models.URLField(blank=True, verbose_name="Ссылка на материалы")

    @property
    def countdown_text(self):
        """Логика таймера: 3м 32с -> 3 мин"""
        now = timezone.now()
        if self.start_time <= now:
            return "Идет или завершено"
        
        diff = self.start_time - now
        total_seconds = int(diff.total_seconds())
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            return f"{days} дн. {hours} ч."
        if hours > 0:
            return f"{hours} ч. {minutes} мин."
        return f"{minutes} мин." # Округляет вниз, как ты и просил

    def __str__(self):
        return f"{self.student.last_name} - {self.start_time.strftime('%d.%m %H:%M')}"

class Homework(models.Model):
    """Домашняя работа, привязанная к уроку"""
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='homework')
    description = models.TextField(verbose_name="Что сделать")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    report = models.TextField(blank=True, verbose_name="Отчет ученика/ссылка")

    def __str__(self):
        return f"ДЗ к уроку {self.lesson.id}"