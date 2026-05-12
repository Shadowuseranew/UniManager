import re
import django.db.models.deletion
from django.db import migrations, models


def migrate_group_faculty(apps, schema_editor):
    Group = apps.get_model('academy', 'Group')
    Faculty = apps.get_model('academy', 'Faculty')
    seen_codes = set()
    for group in Group.objects.all():
        faculty_name = group.faculty_old or "Noma'lum"
        code = re.sub(r'[^a-zA-Z0-9]', '', faculty_name)[:18].upper()
        while code in seen_codes or Faculty.objects.filter(code=code).exists():
            code += '_'
        seen_codes.add(code)
        faculty_obj, _ = Faculty.objects.get_or_create(
            name=faculty_name,
            defaults={'code': code}
        )
        group.faculty = faculty_obj
        group.save(update_fields=['faculty'])


class Migration(migrations.Migration):

    dependencies = [
        ('academy', '0017_academicyear_faculty_semester_academic_year_auditlog'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='faculty',
            new_name='faculty_old',
        ),
        migrations.AddField(
            model_name='group',
            name='faculty',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='academy.faculty', verbose_name='Fakultet'),
        ),
        migrations.RunPython(migrate_group_faculty, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='group',
            name='faculty_old',
        ),
    ]
