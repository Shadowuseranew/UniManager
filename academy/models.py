from django.db import models
from users.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Subject(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    credits = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Classroom(models.Model):
    ROOM_TYPES = (
        ('lecture', "Ma'ruza"),
        ('lab', 'Laboratoriya'),
        ('practice', 'Amaliyot'),
    )
    number = models.CharField(max_length=10)
    capacity = models.PositiveIntegerField()
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)

    def __str__(self):
        return f"{self.number} ({self.get_room_type_display()})"
     
class Enrollment(models.Model):
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.name}"
    
class Grade(models.Model):
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='given_grades', limit_choices_to={'role': 'teacher'})
    score = models.FloatField(default=0)
    date_graded = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.name}: {self.score}"

    @staticmethod
    def average_for(queryset):
        avg = queryset.aggregate(avg=models.Avg('score'))['avg']
        return round(avg, 1) if avg else 0

    @staticmethod
    def subject_averages(queryset):
        return list(queryset.values('subject__name').annotate(avg=models.Avg('score')).order_by('-avg')[:10])
    
class Attendance(models.Model):
    ATTENDANCE_STATUS = (
        ('present', 'Bor'),
        ('absent', "Yo'q"),
        ('late', 'Kechikdi'),
    )
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    timetable = models.ForeignKey('Timetable', on_delete=models.CASCADE, null=True)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS, default='present')

    class Meta:
        unique_together = ('student', 'timetable', 'date')

    def __str__(self):
        subject_name = self.timetable.subject.name if self.timetable else "Noma'lum dars"
        return f"{self.student.username} - {subject_name} ({self.date})"

    @staticmethod
    def stats_for(queryset, date=None):
        qs = queryset
        if date:
            qs = qs.filter(date=date)
        stats = qs.aggregate(
            total=models.Count('id'),
            present=models.Count('id', filter=models.Q(status='present')),
            absent=models.Count('id', filter=models.Q(status='absent')),
            late=models.Count('id', filter=models.Q(status='late')),
        )
        percent = round((stats['present'] / stats['total'] * 100) if stats['total'] else 0, 1)
        return {**stats, 'percent': percent}

DAYS_OF_WEEK = [
    (1, 'Dushanba'),
    (2, 'Seshanba'),
    (3, 'Chorshanba'),
    (4, 'Payshanba'),
    (5, 'Juma'),
    (6, 'Shanba'),
]

class Faculty(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Fakultet nomi")
    code = models.CharField(max_length=20, unique=True, verbose_name="Fakultet kodi")

    class Meta:
        verbose_name = "Fakultet"
        verbose_name_plural = "Fakultetlar"
        ordering = ['name']

    def __str__(self):
        return self.name

class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="O'quv yili")
    start_date = models.DateField(verbose_name="Boshlanish sanasi")
    end_date = models.DateField(verbose_name="Tugash sanasi")
    is_active = models.BooleanField(default=False, verbose_name="Faol")

    class Meta:
        verbose_name = "O'quv yili"
        verbose_name_plural = "O'quv yillari"
        ordering = ['-start_date']

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Guruh nomi")
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=True, verbose_name="Fakultet")
    course_number = models.PositiveSmallIntegerField(verbose_name="Kurs")
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        limit_choices_to={'role': 'teacher'},
        related_name='led_groups', verbose_name="Guruh rahbari"
    )
    subjects = models.ManyToManyField('Subject', related_name='groups', verbose_name="Fanlar")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.course_number}-kurs)"

    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"

class Timetable(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    date = models.DateField(null=True, blank=True, verbose_name="Sana")

    def __str__(self):
        return f"{self.group.name if self.group else ''} - {self.subject.name} ({self.get_day_of_week_display()})"


    def clean(self):
        filter_kwargs = {
            'day_of_week': self.day_of_week,
            'classroom': self.classroom,
            'start_time__lt': self.end_time,
            'end_time__gt': self.start_time,
        }
        if self.date:
            filter_kwargs['date'] = self.date
        conflicts = Timetable.objects.filter(
            **filter_kwargs
        ).exclude(pk=self.pk)
        if conflicts.exists():
            raise ValidationError(f"{self.classroom} xonasi bu vaqtda band!")
class Student(models.Model):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='student_profile')
    groups = models.ManyToManyField(Group, blank=True, related_name='students', verbose_name="Guruhlari")
    student_id = models.CharField(max_length=20, unique=True, verbose_name="Talaba ID")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Telefon raqami")
    course = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Kurs")
    parent = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children', limit_choices_to={'role': 'parent'},
        verbose_name="Ota-ona"
    )

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} ({self.student_id})"

    @property
    def enrollment_count(self):
        return Enrollment.objects.filter(student=self.user).count()

    @property
    def grade_average(self):
        return Grade.average_for(Grade.objects.filter(student=self.user))

    @property
    def attendance_stats(self):
        return Attendance.stats_for(Attendance.objects.filter(student=self.user))

    @property
    def today_lessons_count(self):
        today = timezone.localdate()
        return Timetable.objects.filter(
            models.Q(date=today) | models.Q(date__isnull=True, day_of_week=today.isoweekday()),
            group__in=self.groups.all()
        ).count()

    def subject_grades_map(self):
        ids = self.enrollments.values_list('subject_id', flat=True)
        return {g.subject_id: g.score for g in Grade.objects.filter(student=self.user, subject_id__in=ids)}

    def subject_attendance_map(self):
        ids = self.enrollments.values_list('subject_id', flat=True)
        att_map = {}
        qs = Attendance.objects.filter(student=self.user, timetable__subject_id__in=ids).values(
            'timetable__subject_id'
        ).annotate(total=models.Count('id'), present=models.Count('id', filter=models.Q(status='present')))
        for a in qs:
            sid = a['timetable__subject_id']
            tot = a['total']
            att_map[sid] = round((a['present'] / tot * 100) if tot else 0, 1)
        return att_map

    def subject_data(self):
        enrollments = Enrollment.objects.filter(student=self.user).select_related('subject')
        grade_map = self.subject_grades_map()
        att_map = self.subject_attendance_map()
        return [{
            'subject': en.subject.name,
            'grade': grade_map.get(en.subject_id, 0),
            'attendance_percent': att_map.get(en.subject_id, 0),
        } for en in enrollments]

    def today_timetable(self):
        today = timezone.localdate()
        return Timetable.objects.filter(
            models.Q(date=today) | models.Q(date__isnull=True, day_of_week=today.isoweekday()),
            group__in=self.groups.all()
        ).select_related('subject', 'teacher', 'classroom', 'group').order_by('start_time')

    def recent_payments(self, limit=5):
        return Payment.objects.filter(student=self.user).order_by('-created_at')[:limit]

    class Meta:
        verbose_name = "Talaba"
        verbose_name_plural = "Talabalar"

class LessonJournal(models.Model):
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    topic = models.CharField(max_length=255, verbose_name="Dars mavzusi")

    def __str__(self):
        return f"{self.timetable.subject.name} - {self.date}"

class JournalGrade(models.Model):
    lesson = models.ForeignKey(LessonJournal, on_delete=models.CASCADE, related_name='grades')
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    is_present = models.BooleanField(default=True, verbose_name="Qatnashdi")
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name="Baho")
    comment = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('lesson', 'student')

class Payment(models.Model):
    PAYMENT_STATUS = (
        ('paid', "To'langan"),
        ('pending', "Kutilmoqda"),
        ('overdue', "Muddati o'tgan"),
    )
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, verbose_name="Talaba")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Summa")
    description = models.CharField(max_length=255, verbose_name="Izoh")
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending', verbose_name="Holat")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="To'lov sanasi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.amount} so'm ({self.get_status_display()})"

class StudyMaterial(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='materials', verbose_name="Fan")
    title = models.CharField(max_length=255, verbose_name="Mavzu")
    file = models.FileField(upload_to='materials/', verbose_name="Fayl")
    uploaded_by = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name="Yuklagan")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuklangan sana")

    class Meta:
        verbose_name = "O'quv materiali"
        verbose_name_plural = "O'quv materiallari"
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

class Exam(models.Model):
    EXAM_TYPES = (
        ('midterm', 'Oraliq nazorat'),
        ('final', 'Yakuniy nazorat'),
        ('quiz', 'Test'),
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams', verbose_name="Fan")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='exams', verbose_name="Guruh")
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPES, verbose_name="Imtihon turi")
    date = models.DateField(verbose_name="Sana")
    start_time = models.TimeField(verbose_name="Boshlanish vaqti")
    end_time = models.TimeField(verbose_name="Tugash vaqti")
    max_score = models.PositiveIntegerField(default=100, verbose_name="Maksimal ball")
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name="Yaratuvchi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Imtihon"
        verbose_name_plural = "Imtihonlar"
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.subject.name} ({self.get_exam_type_display()}) - {self.date}"

class Notification(models.Model):
    sender = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sent_notifications', verbose_name="Jo'natuvchi")
    recipient = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='received_notifications', verbose_name="Qabul qiluvchi")
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    message = models.TextField(verbose_name="Xabar")
    is_read = models.BooleanField(default=False, verbose_name="O'qilgan")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class AuditLog(models.Model):
    ACTION_TYPES = (
        ('create', 'Qo\'shish'),
        ('update', 'Tahrirlash'),
        ('delete', 'O\'chirish'),
    )
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, verbose_name="Foydalanuvchi")
    action = models.CharField(max_length=10, choices=ACTION_TYPES, verbose_name="Amal")
    model_name = models.CharField(max_length=50, verbose_name="Model")
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Objekt ID")
    object_repr = models.CharField(max_length=255, blank=True, verbose_name="Objekt nomi")
    details = models.TextField(blank=True, verbose_name="Tafsilot")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sana")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Audit log"
        verbose_name_plural = "Audit loglar"

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} {self.model_name}"

class ChatMessage(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('bot', 'Bot')])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} - {self.role}: {self.text[:50]}"

class Holiday(models.Model):
    date = models.DateField(unique=True, verbose_name="Sana")
    description = models.CharField(max_length=255, verbose_name="Izoh")

    class Meta:
        verbose_name = "Bayram kuni"
        verbose_name_plural = "Bayram kunlari"
        ordering = ['date']

    def __str__(self):
        return f"{self.date} - {self.description}"

class Semester(models.Model):
    name = models.CharField(max_length=100, verbose_name="Semestr nomi")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, verbose_name="O'quv yili", null=True, blank=True)
    start_date = models.DateField(verbose_name="Boshlanish sanasi")
    end_date = models.DateField(verbose_name="Tugash sanasi")
    is_active = models.BooleanField(default=False, verbose_name="Faol")

    class Meta:
        verbose_name = "Semestr"
        verbose_name_plural = "Semestrlar"

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
