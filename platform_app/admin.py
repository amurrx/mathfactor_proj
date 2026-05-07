from django.contrib import admin
from .models import Topic, Task, Lesson, Homework

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('student', 'start_time', 'status', 'countdown_text')
    autocomplete_fields = ['student', 'teacher']
    list_filter = ('status', 'teacher', 'student')
    list_editable = ('status',)

admin.site.register(Topic)
admin.site.register(Task)
admin.site.register(Homework)