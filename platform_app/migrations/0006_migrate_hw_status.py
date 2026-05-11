from django.db import migrations

def transfer_status(apps, schema_editor):
    # Получаем модель через apps.get_model, чтобы миграция была стабильной
    Homework = apps.get_model('platform_app', 'Homework')
    
    for hw in Homework.objects.all():
        if hw.is_completed:
            hw.status = 'DONE' # Ставим статус "Выполнено"
        else:
            hw.status = 'TODO' # Или любой другой по умолчанию
        hw.save()

def reverse_transfer(apps, schema_editor):
    # Логика для отката миграции (если захотим вернуться к Boolean)
    Homework = apps.get_model('platform_app', 'Homework')
    for hw in Homework.objects.all():
        hw.is_completed = (hw.status == 'DONE')
        hw.save()

class Migration(migrations.Migration):
    dependencies = [
        ('platform_app', '0005_alter_lesson_options_homework_status_and_more'), # Django подставит сам
    ]

    operations = [
        migrations.RunPython(transfer_status, reverse_transfer),
    ]