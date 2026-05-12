from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

class User(AbstractUser):
    TEACHER = 'TEACHER'
    STUDENT = 'STUDENT'
    
    ROLE_CHOICES = (
        (TEACHER, 'Учитель'),
        (STUDENT, 'Ученик'),
    )
    
    def get_avatar_color(self):
        colors = ['#e0e7ff', '#fef3c7', '#dcfce7', '#fee2e2', '#f3e8ff']
        return colors[self.id % len(colors)]

    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default=STUDENT,
        db_index=True
        )
    
    grade = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Класс")

    phone_regex = RegexValidator(
        regex=r'^(\+7|8)\d{10}$',
        message="Номер телефона должен быть в формате: '+79999999999'."
    )
    phone = models.CharField(validators=[phone_regex], max_length=12, blank=True)

    @property
    def is_teacher(self):
        return self.role == User.TEACHER

    @property
    def is_student(self):
        return self.role == User.STUDENT
    
    def __str__(self):
        full_name = self.get_full_name()
        display_name = full_name if full_name else self.username
        return f"{display_name} ({self.get_role_display()})"