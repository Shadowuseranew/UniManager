from django.contrib import admin
from .models import Classroom, Group, Student, Subject, Lesson # Classroom ni qo'shing

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

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'course_number', 'student_count')
    list_filter = ('course_number', 'faculty')

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "Talabalar soni"