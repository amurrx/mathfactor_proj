from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Topic, Task, Lesson, Homework


class HomeworkInline(TabularInline):
    model = Homework
    extra = 0 # Чтобы не создавались пустые формы
    fields = ['description', 'status', 'report']

@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    list_display = ["name", "subject"]
    search_fields = ["name"]

@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = ["id", "topic", "answer"]
    list_filter = ["topic"]
    # Unfold поддерживает Markdown/Rich Text в полях, если настроить

@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    list_display = ('student', 'start_time', 'status', 'get_topic') # Используем метод для темы
    autocomplete_fields = ['student', 'teacher', 'topic']
    list_filter = ('status', 'teacher', 'student')
    list_editable = ('status',)
    inlines = [HomeworkInline] # ДОБАВЛЯЕМ панель домашки сюда

    # Метод, чтобы красиво вывести тему в списке уроков
    def get_topic(self, obj):
        return obj.topic.name if obj.topic else "—"
    get_topic.short_description = "Тема"

@admin.register(Homework)
class HomeworkAdmin(ModelAdmin):    
    # Чтобы вывести студента и тему, нужно обращаться к ним через lesson
    list_display = ('get_student', 'get_topic', 'status')
    list_filter = ('status',)
    
    # Методы для отображения данных из связанной модели Lesson
    def get_student(self, obj):
        return obj.lesson.student.get_full_name()
    get_student.short_description = 'Ученик'

    def get_topic(self, obj):
        return obj.lesson.topic.name if obj.lesson.topic else "—"
    get_topic.short_description = 'Тема'