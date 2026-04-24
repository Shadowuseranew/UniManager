from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subject, Student, Lesson, Enrollment, Grade, Attendance, Timetable, Classroom, Group  # Lesson modelini qo'shdik
from .forms import SubjectForm, LessonForm, TimetableForm, ClassroomForm, GroupForm
from users.decorators import admin_only
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden

# Asosiy sahifa
def index(request):
    return render(request, 'index.html')

# Fanlar ro'yxati (Hamma ko'ra oladi)
@login_required
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'academy/subject_list.html', {'subjects': subjects})

# Fan qo'shish (Faqat Admin)
@login_required
@admin_only
def subject_add(request):
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request, 'academy/subject_form.html', {'form': form})

# Fan o'chirish (Faqat Admin)
@login_required
@admin_only
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        subject.delete()
        return redirect('subject_list')
    return render(request, 'academy/subject_confirm_delete.html', {'subject': subject})

@login_required
def timetable_view(request):
    # 1. Talabaning profili va guruhlarini aniqlash
    try:
        # related_name='student_profile' orqali talaba ma'lumotlarini olamiz
        student = request.user.student_profile
        student_groups = student.groups.all()
        
        # Faqat talaba a'zo bo'lgan guruhlarning darslarini olamiz
        # .distinct() bir xil darslar takrorlanishini oldini oladi
        lessons = Timetable.objects.filter(
            group__in=student_groups
        ).select_related('group', 'subject', 'teacher', 'classroom').distinct().order_by('day_of_week', 'start_time')
        
        print(f"DEBUG: Talaba {request.user.username} uchun {lessons.count()} ta dars topildi.")
        
    except (AttributeError, Student.DoesNotExist):
        # Agar foydalanuvchi talaba bo'lmasa (admin yoki o'qituvchi), barcha darslar chiqadi
        lessons = Timetable.objects.select_related('group', 'subject', 'teacher', 'classroom').all().order_by('day_of_week', 'start_time')
        print("DEBUG: Talaba profili topilmadi, barcha darslar ko'rsatilmoqda.")

    # 2. Haftalik kunlar lug'ati
    days_names = {
        1: 'Dushanba', 2: 'Seshanba', 3: 'Chorshanba',
        4: 'Payshanba', 5: 'Juma', 6: 'Shanba'
    }
    schedule = {name: [] for name in days_names.values()}
    
    # 3. Darslarni kunlar bo'yicha taqsimlash
    for lesson in lessons:
        day_name = days_names.get(lesson.day_of_week)
        if day_name:
            schedule[day_name].append(lesson)
            
    # 4. Yakuniy natijani yuborish
    return render(request, 'academy/timetable.html', {'schedule': schedule})

@login_required
def timetable_add(request):
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Sizda dars qo'shish huquqi yo'q!")
        return redirect('timetable_view')

    if request.method == "POST":
        # DIQQAT: LessonForm emas, TimetableForm ishlatamiz
        form = TimetableForm(request.POST) 
        if form.is_valid():
            try:
                lesson = form.save(commit=False)
                # Modelda xona bandligini tekshirish uchun full_clean chaqiramiz
                lesson.full_clean() 
                lesson.save()
                messages.success(request, "Dars muvaffaqiyatli qo'shildi!")
                return redirect('timetable_view')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        # BU YERDA HAM: TimetableForm
        form = TimetableForm()
    
    return render(request, 'academy/timetable_form.html', {'form': form})

# 3. Darsni tahrirlash (Edit)
@login_required
def timetable_edit(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Sizda tahrirlash huquqi yo'q!")
        return redirect('timetable_view')

    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            try:
                updated_lesson = form.save(commit=False)
                updated_lesson.full_clean()
                updated_lesson.save()
                messages.success(request, "Dars muvaffaqiyatli yangilandi!")
                return redirect('timetable_view')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = LessonForm(instance=lesson)
    
    return render(request, 'academy/timetable_form.html', {'form': form, 'edit_mode': True})

# 4. Darsni o'chirish (Delete)
@login_required
def timetable_delete(request, pk):
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Sizda o'chirish huquqi yo'q!")
        return redirect('timetable_view')

    lesson = get_object_or_404(Lesson, pk=pk)
    if request.method == "POST":
        lesson.delete()
        messages.warning(request, "Dars jadvaldan o'chirildi.")
    
    return redirect('timetable_view')

@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        return redirect('subject_list') # Admin yoki Talaba bo'lsa boshqa yoqqa
    
    # O'qituvchi dars beradigan fanlar
    my_lessons = Lesson.objects.filter(teacher=request.user)
    return render(request, 'academy/teacher_dashboard.html', {'lessons': my_lessons})

@login_required
def grade_students(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    # Ushbu fanga yozilgan talabalar
    enrollments = Enrollment.objects.filter(subject=subject)
    
    if request.method == "POST":
        for enrollment in enrollments:
            score = request.POST.get(f'grade_{enrollment.student.id}')
            if score:
                # Bahoni yangilash yoki yaratish
                Grade.objects.update_or_create(
                    student=enrollment.student,
                    subject=subject,
                    defaults={'score': score, 'teacher': request.user}
                )
        return redirect('teacher_dashboard')

    return render(request, 'academy/grade_form.html', {
        'subject': subject,
        'enrollments': enrollments
    })

@login_required
def journal_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    # Ushbu fanga yozilgan talabalar
    enrollments = Enrollment.objects.filter(subject=lesson.subject)
    
    if request.method == "POST":
        for en in enrollments:
            student_id = en.student.id
            
            # 1. Davomatni saqlash
            status = request.POST.get(f'attendance_{student_id}')
            Attendance.objects.update_or_create(
                student=en.student,
                lesson=lesson,
                date=request.POST.get('lesson_date'), # Sanani formadan olamiz
                defaults={'status': status}
            )
            
            # 2. Bahoni saqlash (ixtiyoriy)
            score = request.POST.get(f'grade_{student_id}')
            if score:
                Grade.objects.update_or_create(
                    student=en.student,
                    subject=lesson.subject,
                    defaults={'score': score, 'teacher': request.user}
                )
        
        return redirect('teacher_dashboard')

    return render(request, 'academy/journal.html', {
        'lesson': lesson,
        'enrollments': enrollments,
        'today': timezone.now().date()
    })

@login_required
def teacher_dashboard(request):
    # Faqat o'qituvchilarga ruxsat beramiz
    if request.user.role != 'teacher':
        return redirect('subject_list')
    
    # O'qituvchining darslari (timetable'dan olinadi)
    my_lessons = Lesson.objects.filter(teacher=request.user)
    
    return render(request, 'academy/teacher_dashboard.html', {
        'lessons': my_lessons
    })

from django.db.models import Avg, Count, Q

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('teacher_dashboard')
    
    # Talaba yozilgan fanlar
    enrollments = Enrollment.objects.filter(student=request.user).select_related('subject')
    
    # Har bir fan bo'yicha baho va davomat tahlili
    subject_data = []
    for en in enrollments:
        # Baho
        grade = Grade.objects.filter(student=request.user, subject=en.subject).first()
        
        # Davomat (necha marta dars bo'lgan va necha marta qatnashgan)
        attendance_stats = Attendance.objects.filter(
            student=request.user, 
            lesson__subject=en.subject
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present'))
        )
        
        # Davomat foizini hisoblash
        att_percent = 0
        if attendance_stats['total'] > 0:
            att_percent = (attendance_stats['present'] / attendance_stats['total']) * 100
            
        subject_data.append({
            'subject': en.subject.name,
            'grade': grade.score if grade else 0,
            'attendance_percent': round(att_percent, 1)
        })

    return render(request, 'academy/student_dashboard.html', {
        'subject_data': subject_data
    })

from django.shortcuts import render, redirect, get_object_or_404

# Tahrirlash
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'academy/subject_form.html', {'form': form})

# O'chirish
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        subject.delete()
        return redirect('subject_list')
    return render(request, 'academy/subject_confirm_delete.html', {'subject': subject})

@login_required
def classroom_list(request):
    rooms = Classroom.objects.all()
    return render(request, 'academy/classroom_list.html', {'rooms': rooms})

@login_required
def classroom_add(request):
    if request.method == "POST":
        form = ClassroomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('classroom_list')
    else:
        form = ClassroomForm()
    return render(request, 'academy/classroom_form.html', {'form': form})

@login_required
def classroom_add(request):
    if request.method == "POST":
        form = ClassroomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('classroom_list') # Saqlangandan keyin ro'yxatga qaytadi
    else:
        form = ClassroomForm()
    
    return render(request, 'academy/classroom_form.html', {'form': form})

# Tahrirlash (Update)
@login_required
def classroom_edit(request, pk):
    room = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        form = ClassroomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('classroom_list')
    else:
        form = ClassroomForm(instance=room)
    return render(request, 'academy/classroom_form.html', {'form': form, 'edit_mode': True})

# O'chirish (Delete)
@login_required
def classroom_delete(request, pk):
    room = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        room.delete()
        return redirect('classroom_list')
    return render(request, 'academy/classroom_confirm_delete.html', {'room': room})

@login_required
def group_list(request):
    # teacher (One-to-Many) uchun select_related
    # subjects (Many-to-Many) uchun prefetch_related
    groups = Group.objects.all().select_related('teacher').prefetch_related('subjects').order_by('name')
    
    return render(request, 'academy/group_list.html', {'groups': groups})

@login_required
# @admin_only  <-- Agar dekoratoringiz bo'lsa, pastdagi if-check shart emas
def group_add(request):
    # Xavfsizlik tekshiruvi (dekorator bo'lmasa, shu holatda qoladi)
    if request.user.role != 'admin':
        messages.error(request, "Sizda ushbu amalni bajarish uchun ruxsat yo'q.")
        return redirect('group_list') # Forbidden o'rniga redirect qilish yaxshiroq UX
    
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            # Guruhni saqlaymiz (teacher va subjects bilan birga)
            group = form.save()
            messages.success(request, f"{group.name} guruhi muvaffaqiyatli qo'shildi!")
            return redirect('group_list')
        else:
            messages.error(request, "Iltimos, forma xatolarini tekshiring.")
    else:
        form = GroupForm()
    
    return render(request, 'academy/group_form.html', {
        'form': form,
        'title': "Yangi guruh qo'shish" # Sarlavhani dinamik uzatish mumkin
    })

@login_required
def grade_journal(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    # Ushbu fanga yozilgan barcha talabalarni guruhlari bilan olish
    enrollments = Enrollment.objects.filter(subject=subject).select_related('student', 'student__student_profile')

    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith('grade_') and value:
                student_id = key.replace('grade_', '')
                # update_or_create: bor bo'lsa yangilaydi, yo'q bo'lsa yaratadi
                Grade.objects.update_or_create(
                    student_id=student_id,
                    subject=subject,
                    defaults={'score': float(value)}
                )
        messages.success(request, f"{subject.name} fanidan ballar saqlandi!")
        return redirect('grade_journal', subject_id=subject.id)

    return render(request, 'academy/grade_journal.html', {
        'subject': subject,
        'enrollments': enrollments
    })

def group_detail(request, pk):
    # Guruhni topamiz
    group = get_object_or_404(Group, pk=pk)
    
    # Shu guruhga tegishli barcha talabalarni olamiz
    # related_name='students' bo'lgani uchun group.students orqali kiramiz
    students = group.students.all().select_related('user')
    
    return render(request, 'academy/group_detail.html', {
        'group': group,
        'students': students,
        'student_count': students.count()
    })

@login_required
def timetable_list(request):
    group_id = request.GET.get('group')
    
    # select_related orqali bazaga so'rovlar sonini kamaytiramiz
    timetables = Timetable.objects.select_related(
        'group', 'subject', 'teacher', 'classroom'
    ).order_by('day_of_week', 'start_time')

    if group_id:
        timetables = timetables.filter(group_id=group_id)

    groups = Group.objects.all()
    
    return render(request, 'academy/timetable_list.html', {
        'timetables': timetables,
        'groups': groups,
        'selected_group': group_id
    })