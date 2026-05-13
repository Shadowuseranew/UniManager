from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Foydalanuvchi rollarini belgilaymiz
    USER_ROLES = (
        ('admin', 'Admin'),
        ('teacher', 'O\'qituvchi'),
        ('student', 'Talaba'),
        ('parent', 'Ota-ona'),
    )
    role = models.CharField(max_length=10, choices=USER_ROLES, default='admin')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Rasm")

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

    def dashboard_context(self):
        from django.utils import timezone
        from django.db.models import Avg, Count, Q
        from academy.models import Subject, Student, Enrollment, Grade, Attendance, Timetable, Group, Payment

        today = timezone.localdate()
        ctx = {}

        if self.role == 'admin':
            att_stats = Attendance.stats_for(Attendance.objects.all())
            today_att = Attendance.stats_for(Attendance.objects.all(), date=today)
            ctx.update({
                'students_count': User.objects.filter(role='student').count(),
                'teachers_count': User.objects.filter(role='teacher').count(),
                'subjects_count': Subject.objects.count(),
                'groups_count': Group.objects.count(),
                'pending_payments': Payment.objects.filter(status='pending').count(),
                'today_lessons': Timetable.objects.filter(date=today).count(),
                'grade_avg': Grade.average_for(Grade.objects.all()),
                'att_percent': att_stats['percent'],
                'subject_grades': Grade.subject_averages(Grade.objects.all()),
                'today_att': {'p': today_att['present'], 'a': today_att['absent'], 'l': today_att['late']},
            })

        elif self.role == 'teacher':
            my_groups = Group.objects.filter(teacher=self)
            my_lessons = Timetable.objects.filter(teacher=self)
            att_stats = Attendance.stats_for(Attendance.objects.filter(timetable__teacher=self))
            ctx.update({
                'my_groups_count': my_groups.count(),
                'my_subjects_count': Subject.objects.filter(groups__teacher=self).distinct().count(),
                'my_students_count': Student.objects.filter(groups__in=my_groups).distinct().count(),
                'today_lessons': my_lessons.filter(date=today).count(),
                'grade_avg': Grade.average_for(Grade.objects.filter(teacher=self)),
                'att_percent': att_stats['percent'],
                'subject_grades': Grade.subject_averages(Grade.objects.filter(teacher=self)),
            })

        elif self.role == 'student':
            try:
                profile = self.student_profile
            except:
                profile = None
            ctx.update({
                'enrollments_count': profile.enrollment_count if profile else 0,
                'grade_avg': profile.grade_average if profile else 0,
                'att_percent': profile.attendance_stats['percent'] if profile else 0,
                'today_lessons': profile.today_lessons_count if profile else 0,
                'subject_grades': [],
            })

        elif self.role == 'parent':
            children = Student.objects.filter(parent=self).select_related('user')
            ctx.update({'children_count': children.count()})

        return ctx

    def parent_children_data(self):
        from academy.models import Student, Enrollment, Grade
        children = Student.objects.filter(parent=self).select_related('user')
        result = []
        for child in children:
            enrollments = Enrollment.objects.filter(student=child.user).select_related('subject')
            grade_map = {}
            ids = enrollments.values_list('subject_id', flat=True)
            for g in Grade.objects.filter(student=child.user, subject_id__in=ids):
                grade_map[g.subject_id] = g.score
            result.append({
                'student': child,
                'enrollments': enrollments,
                'grade_avg': child.grade_average,
                'att_stats': child.attendance_stats,
                'grade_map': grade_map,
            })
        return result

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    bio = models.TextField(blank=True)
    specialization = models.CharField(max_length=100)

