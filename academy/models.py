from django.db import models
from users.models import User
from django import forms

class Subject(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    credits = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Classroom(models.Model):
    ROOM_TYPES = (
        ('lecture', 'Ma\'ruza'),
        ('lab', 'Laboratoriya'),
        ('practice', 'Amaliyot'),
    )
    number = models.CharField(max_length=10)
    capacity = models.PositiveIntegerField()
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)

    def __str__(self):
        return f"{self.number} ({self.get_room_type_display()})"
     
class Lesson(models.Model):
    DAYS_OF_WEEK = (
        (1, 'Dushanba'),
        (2, 'Seshanba'),
        (3, 'Chorshanba'),
        (4, 'Payshanba'),
        (5, 'Juma'),
        (6, 'Shanba'),
    )

    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE)
    group_name = models.CharField(max_length=50) # Masalan: "IF-21"
    
    day = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.subject.name} - {self.group_name} ({self.get_day_display()})"

    # Professional tekshiruv (Conflict Detection)
    def clean(self):
        from django.core.exceptions import ValidationError
        # Bir vaqtda bir xonada ikkita dars bo'lmasligi kerak
        conflicts = Lesson.objects.filter(
            day=self.day,
            classroom=self.classroom,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)
        
        if conflicts.exists():
            raise ValidationError(f"{self.classroom} xonasi bu vaqtda band!")
        
class Enrollment(models.Model):
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True) # Yakuniy baho uchun joy

    class Meta:
        unique_together = ('student', 'subject') # Talaba bir fanga ikki marta yozila olmaydi

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.name}"
    
class Grade(models.Model):
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='given_grades', limit_choices_to={'role': 'teacher'})
    
    score = models.FloatField(default=0) # Masalan, 0 dan 100 gacha
    date_graded = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject') # Bir fandan bir marta baholash (yoki semestr uchun)

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject.name}: {self.score}"
    
class Attendance(models.Model):
    ATTENDANCE_STATUS = (
        ('present', 'Bor'),
        ('absent', 'Yo\'q'),
        ('late', 'Kechikdi'),
    )

    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True) # Bugungi sana
    status = models.CharField(max_length=10, choices=ATTENDANCE_STATUS, default='present')

    class Meta:
        # Bir talaba uchun bir darsda bir kunda faqat bitta belgi qo'yish mumkin
        unique_together = ('student', 'lesson', 'date')

    def __str__(self):
        return f"{self.student.username} - {self.lesson.subject.name} ({self.date})"

DAYS_OF_WEEK = [
    (1, 'Dushanba'),
    (2, 'Seshanba'),
    (3, 'Chorshanba'),
    (4, 'Payshanba'),
    (5, 'Juma'),
    (6, 'Shanba'),
]

class Timetable(models.Model):
    # ... DAYS_OF_WEEK o'zgarishsiz qoladi ...

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    
    # 1. Guruhni qo'shing
    group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True) 
    
    # 2. 'room' o'rniga 'classroom' (ForeignKey) ishlating
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True)
    
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.group.name if self.group else ''} - {self.subject.name}"
    
from django.db import models
from users.models import User  # User modelini import qilamiz

class Group(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Guruh nomi")
    faculty = models.CharField(max_length=100, verbose_name="Fakultet")
    course_number = models.PositiveSmallIntegerField(verbose_name="Kurs")
    
    # 1. Guruh rahbari (O'qituvchi bilan bog'liqlik)
    teacher = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'role': 'teacher'},
        related_name='led_groups',
        verbose_name="Guruh rahbari"
    )
    
    # 2. Guruh o'qiydigan fanlar (Subject bilan bog'liqlik)
    subjects = models.ManyToManyField(
        'Subject', # Subject modeli shu faylda bo'lsa nomini yozish yetarli
        related_name='groups',
        verbose_name="Fanlar"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.course_number}-kurs)"

    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"

# academy/models.py fayliga qo'shing

class Student(models.Model):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='student_profile')
    groups = models.ManyToManyField(Group, blank=True, related_name='students', verbose_name="Guruhlari")
    student_id = models.CharField(max_length=20, unique=True, verbose_name="Talaba ID")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Telefon raqami")

    def __str__(self):
        # ManyToManyField-da self.group endi yo'q, shuning uchun groups.all() ishlatamiz
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} ({self.student_id})"

    class Meta:
        verbose_name = "Talaba"
        verbose_name_plural = "Talabalar"