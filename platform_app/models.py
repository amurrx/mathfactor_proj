from django.db import models
from users.models import User
from django.utils import timezone
from datetime import timedelta

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
    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['-start_time']
        
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Запланировано'
        COMPLETED = 'COMPLETED', 'Проведено'
        CANCELLED = 'CANCELLED', 'Отменено'
        MISSED = 'MISSED', 'Пропущено'

    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='lessons_teacher',
        limit_choices_to={'role': User.TEACHER}, # Добавляем этот фильтр
        verbose_name="Учитель"
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='lessons_student',
        limit_choices_to={'role': User.STUDENT}, # И этот тоже
        verbose_name="Ученик"
    )
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField(verbose_name="Время начала")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PLANNED)
    material_link = models.FileField(blank=True, verbose_name="Ссылка на материалы")
    meeting_link = models.URLField(blank=True, verbose_name="Ссылка на Zoom/Телемост")

    @property
    def countdown_text(self):
        now = timezone.now()
        if self.status != self.Status.PLANNED:
            return self.get_status_display() # Возвращает "Проведено", "Отменено" и т.д.

        diff = self.start_time - now
        total_seconds = int(diff.total_seconds())

        if total_seconds <= 0:
            return "Идет сейчас" if total_seconds > -3600 else "Завершен" # Условно 1 час на урок
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 0:
            return f"{days} дн. {hours} ч."
        if hours > 0:
            return f"{hours} ч. {minutes} мин."
        return f"{minutes} мин." # Округляет вниз
    
    duration = models.PositiveIntegerField(default=60, verbose_name="Длительность (мин)")

    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Запланировано'
        ONGOING = 'ONGOING', 'Идет сейчас' # Добавим новый виртуальный статус
        COMPLETED = 'COMPLETED', 'Проведено'
        CANCELLED = 'CANCELLED', 'Отменено'
        MISSED = 'MISSED', 'Пропущено'

    @property
    def current_status(self):
        """Возвращает актуальный статус с учетом времени"""
        now = timezone.now()
        end_time = self.start_time + timedelta(minutes=self.duration)

        if self.status == self.Status.PLANNED:
            if self.start_time <= now <= end_time:
                return "ONGOING" # Идет сейчас
            elif now > end_time:
                return "NEEDS_CONFIRMATION" # Отработал, но не отмечен
        
        return self.status
    
    @property
    def is_ongoing(self):
        """Идет ли урок прямо сейчас?"""
        now = timezone.now()
        # Урок идет, если время начала прошло, но час еще не кончился
        return self.start_time <= now <= (self.start_time + timedelta(minutes=60))

    @property
    def is_overdue(self):
        """Урок уже закончился, но статус еще 'Запланировано'?"""
        return self.status == self.Status.PLANNED and timezone.now() > (self.start_time + timedelta(minutes=60))

    def __str__(self):
        return f"{self.student.last_name} - {self.start_time.strftime('%d.%m %H:%M')}"


class Homework(models.Model):
    """Домашняя работа, привязанная к уроку"""
    
    class Status(models.TextChoices):
        TODO = 'TODO', 'Не начато'
        REVIEW = 'REVIEW', 'На проверке'
        FIXING = 'FIXING', 'Требует исправления'
        DONE = 'DONE', 'Выполнено'

    lesson = models.OneToOneField(
        'Lesson', 
        on_delete=models.CASCADE, 
        related_name='homework'
    )
    
    description = models.TextField(verbose_name="Что сделать")

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.TODO,
        verbose_name="Статус"
    )
    
    report = models.TextField(blank=True, verbose_name="Отчет ученика/ссылка")

    def __str__(self):
        return f"ДЗ к уроку {self.lesson.id} [{self.get_status_display()}]"