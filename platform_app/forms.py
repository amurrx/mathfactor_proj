from django import forms
from users.models import User

class StudentCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password']
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.STUDENT  # Жестко задаем роль
        user.set_password(self.cleaned_data["password"]) # Хешируем пароль
        if commit:
            user.save()
        return user