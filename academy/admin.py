from django.contrib import admin
from .models import Classroom, Group, Student, Subject, Timetable, LessonJournal, JournalGrade, Payment, StudyMaterial, Exam, Notification, Holiday, Semester, Faculty, AcademicYear

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('number', 'room_type', 'capacity') # Ro'yxatda ko'rinadigan ustunlar
    list_filter = ('room_type',) # Yon tomonda filtr qilish uchun
    search_fields = ('number',) # Qidiruv maydoni

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    # Ro'yxatda nimalar ko'rinsin
    list_display = ('get_full_name', 'student_id', 'get_groups', 'phone_number')
    # Qidiruv maydonlari
    search_fields = ('user__first_name', 'user__last_name', 'student_id')
    # ManyToMany uchun qulay tanlagich (Box ko'rinishida)
    filter_horizontal = ('groups',)

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = "Talaba ismi"

    def get_groups(self, obj):
        # Talaba a'zo bo'lgan barcha guruhlarni sanab beradi
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = "Guruhlari"

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'course_number', 'student_count')
    list_filter = ('course_number', 'faculty')

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "Talabalar soni"

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'credits')
    search_fields = ('name', 'code')

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('group', 'subject', 'teacher', 'day_of_week', 'start_time')
    list_filter = ('day_of_week', 'group', 'teacher')

@admin.register(LessonJournal)
class LessonJournalAdmin(admin.ModelAdmin):
    list_display = ('timetable', 'date', 'topic')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'status', 'paid_at')
    list_filter = ('status',)

@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'uploaded_by', 'uploaded_at')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('subject', 'group', 'exam_type', 'date', 'start_time')
    list_filter = ('exam_type', 'subject')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'sender', 'recipient', 'is_read', 'created_at')
    list_filter = ('is_read',)

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'description')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'start_date', 'end_date', 'is_active')
    list_filter = ('academic_year',)