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

    @property
    def is_teacher(self):
        return self.role == User.TEACHER

    @property
    def is_student(self):
        return self.role == User.STUDENT
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{10,11}$',
        message="Номер телефона должен быть в формате: '8 999 999 9999'."
    )
    phone = models.CharField(validators=[phone_regex], max_length=11, blank=True)

    def __str__(self):
        full_name = self.get_full_name()
        display_name = full_name if full_name else self.username
        return f"{display_name} ({self.get_role_display()})"