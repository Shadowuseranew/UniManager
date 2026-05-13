from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Subject, Student, Enrollment, Grade, Attendance, Timetable, Classroom, Group, LessonJournal, JournalGrade, Payment, StudyMaterial, Exam, Notification, Holiday, Semester, ChatMessage
from .forms import SubjectForm, TimetableForm, ClassroomForm, GroupForm, PaymentForm, ExamForm, StudyMaterialForm, NotificationForm, SemesterForm
from .chat_assistant import Assistant
from .audit_logger import log_action
from users.decorators import admin_only, parent_only, admin_or_teacher
from users.forms import StudentAddForm, TeacherAddForm, AdminAddForm
from django.utils import timezone
from datetime import time, timedelta
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden, HttpResponse
from users.models import User, TeacherProfile
from django.db.models import Avg, Count, Q, Sum
import openpyxl
from collections import defaultdict

@login_required
def dashboard(request):
    role_templates = {
        'teacher': 'academy/teacher_dashboard.html',
        'student': 'academy/student_dashboard.html',
        'parent': 'academy/parent_dashboard.html',
    }
    template = role_templates.get(request.user.role, 'academy/dashboard.html')

    if request.user.role == 'admin':
        context = request.user.dashboard_context()
    elif request.user.role == 'teacher':
        context = {
            'lessons': Timetable.objects.filter(teacher=request.user).select_related('subject', 'group', 'classroom'),
        }
    elif request.user.role == 'student':
        profile = getattr(request.user, 'student_profile', None)
        context = {'subject_data': profile.subject_data() if profile else []}
    elif request.user.role == 'parent':
        context = {'children_data': request.user.parent_children_data()}
    else:
        context = {}

    return render(request, template, context)

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
            obj = form.save()
            log_action(request, 'create', 'Subject', obj, f"Fan qo'shildi: {obj.name}")
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request, 'academy/subject_form.html', {'form': form})

# Fan tahrirlash (Faqat Admin)
@login_required
@admin_only
def subject_edit(request, uuid):
    subject = get_object_or_404(Subject, uuid=uuid)
    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            log_action(request, 'update', 'Subject', subject, f"Fan tahrirlandi: {subject.name}")
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'academy/subject_form.html', {'form': form, 'edit_mode': True})

# Fan o'chirish (Faqat Admin)
@login_required
@admin_only
def subject_delete(request, uuid):
    subject = get_object_or_404(Subject, uuid=uuid)
    if request.method == "POST":
        log_action(request, 'delete', 'Subject', subject, f"Fan o'chirildi: {subject.name}")
        subject.delete()
        return redirect('subject_list')
    return render(request, 'academy/subject_confirm_delete.html', {'subject': subject})

@login_required
def timetable_view(request):
    view_type = request.GET.get('view', 'weekly')
    today = timezone.localdate()
    now = timezone.localtime().time()

    if request.user.role == 'student':
        try:
            student = request.user.student_profile
            student_groups = student.groups.all()
            base = Timetable.objects.filter(group__in=student_groups)
        except (AttributeError, Student.DoesNotExist):
            base = Timetable.objects.none()
    elif request.user.role == 'teacher':
        base = Timetable.objects.filter(teacher=request.user)
    else:
        base = Timetable.objects.all()

    base = base.select_related('group', 'subject', 'teacher', 'classroom')
    week_days = ['', 'Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    month_names = ['', 'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr']

    ctx = {'view_type': view_type, 'today': today, 'week_days': week_days, 'month_names': month_names}

    if view_type == 'daily':
        dow = today.isoweekday()
        if dow == 7:
            dow = 6
        lessons = base.filter(Q(date=today) | Q(date__isnull=True, day_of_week=dow)).order_by('start_time')
        lessons = [l for l in lessons if l.end_time > now]
        ctx.update({'lessons': lessons})

    elif view_type == 'weekly':
        monday = today - timedelta(days=today.weekday())
        dates = [monday + timedelta(days=i) for i in range(6)]
        q = Q()
        for d in dates:
            dow = d.isoweekday()
            q |= Q(date=d)
            if dow <= 6:
                q |= Q(date__isnull=True, day_of_week=dow)
        lessons = base.filter(q).order_by('date', 'start_time')
        schedule = {d: [] for d in dates}
        for l in lessons:
            key = l.date if l.date else monday + timedelta(days=l.day_of_week - 1)
            if key in schedule:
                schedule[key].append(l)
        ctx.update({'schedule': schedule, 'monday': monday})

    elif view_type == 'monthly':
        month_start = today.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year+1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month+1, day=1) - timedelta(days=1)
        lessons = base.filter(date__gte=month_start, date__lte=month_end).order_by('date', 'start_time')
        ctx.update({'lessons': lessons, 'month_start': month_start, 'month_end': month_end})

    elif view_type == 'semester':
        sem = Semester.objects.filter(is_active=True).first()
        if sem:
            lessons = base.filter(date__gte=sem.start_date, date__lte=sem.end_date).order_by('date', 'start_time')
        else:
            lessons = base.filter(date__isnull=False).order_by('date', 'start_time')
        ctx.update({'lessons': lessons, 'semester': sem})

    else:
        lessons = base.filter(date__isnull=True).order_by('day_of_week', 'start_time')
        days_map = {1: 'Dushanba', 2: 'Seshanba', 3: 'Chorshanba', 4: 'Payshanba', 5: 'Juma', 6: 'Shanba'}
        schedule = {n: [] for n in days_map.values()}
        for l in lessons:
            dn = days_map.get(l.day_of_week)
            if dn:
                schedule[dn].append(l)
        ctx.update({'schedule': schedule})
        view_type = 'weekly_template'

    ctx['view_type'] = view_type
    return render(request, 'academy/timetable.html', ctx)

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
                log_action(request, 'create', 'Timetable', lesson, f"Dars qo'shildi: {lesson.subject.name}")
                messages.success(request, "Dars muvaffaqiyatli qo'shildi!")
                return redirect('timetable_view')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        # BU YERDA HAM: TimetableForm
        form = TimetableForm()
    
    return render(request, 'academy/timetable_form.html', {'form': form})

TIME_SLOTS = [
    (1, '09:00', '10:15'),
    (2, '10:25', '11:40'),
    (3, '11:50', '13:05'),
    (4, '13:50', '15:05'),
    (5, '15:15', '16:30'),
    (6, '16:40', '17:55'),
]
DAYS_OF_WEEK_LIST = [
    (1, 'Dushanba'), (2, 'Seshanba'), (3, 'Chorshanba'),
    (4, 'Payshanba'), (5, 'Juma'), (6, 'Shanba'),
]

@login_required
def timetable_batch_add(request):
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Sizda huquq yo'q!")
        return redirect('timetable_view')

    groups = Group.objects.all()
    subjects = Subject.objects.all()
    teachers = User.objects.filter(role='teacher')
    classrooms = Classroom.objects.all()

    if request.method == "POST":
        group_id = request.POST.get('group')
        group = get_object_or_404(Group, pk=group_id)
        created_count = 0

        for day_num, _ in DAYS_OF_WEEK_LIST:
            for slot_num, start_str, end_str in TIME_SLOTS:
                subject_id = request.POST.get(f'subject_{day_num}_{slot_num}')
                teacher_id = request.POST.get(f'teacher_{day_num}_{slot_num}')
                classroom_id = request.POST.get(f'classroom_{day_num}_{slot_num}')
                if subject_id and teacher_id:
                    start_time = time.fromisoformat(start_str)
                    end_time = time.fromisoformat(end_str)
                    Timetable.objects.get_or_create(
                        group=group,
                        subject_id=subject_id,
                        teacher_id=teacher_id,
                        day_of_week=day_num,
                        start_time=start_time,
                        end_time=end_time,
                        classroom_id=classroom_id or None,
                    )
                    created_count += 1

        messages.success(request, f"{group.name} uchun {created_count} ta dars qo'shildi!")
        return redirect('timetable_view')

    semester = Semester.objects.filter(is_active=True).first()
    return render(request, 'academy/timetable_batch.html', {
        'time_slots': TIME_SLOTS,
        'days': DAYS_OF_WEEK_LIST,
        'groups': groups,
        'subjects': subjects,
        'teachers': teachers,
        'classrooms': classrooms,
        'semester': semester,
        'holidays': Holiday.objects.all(),
    })

@login_required
def timetable_semester_generate(request):
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Sizda huquq yo'q!")
        return redirect('timetable_view')

    groups = Group.objects.all()
    subjects = Subject.objects.all()
    teachers = User.objects.filter(role='teacher')
    classrooms = Classroom.objects.all()
    semesters = Semester.objects.all()
    holidays = set(Holiday.objects.values_list('date', flat=True))

    if request.method == "POST":
        group_id = request.POST.get('group')
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher')
        classroom_id = request.POST.get('classroom')
        semester_id = request.POST.get('semester')
        selected_days = request.POST.getlist('days')
        selected_slots = request.POST.getlist('slots')

        if not all([group_id, subject_id, teacher_id, semester_id, selected_days, selected_slots]):
            messages.error(request, "Barcha maydonlarni to'ldiring!")
            return redirect('timetable_semester_generate')

        group = get_object_or_404(Group, pk=group_id)
        subject = get_object_or_404(Subject, pk=subject_id)
        teacher = get_object_or_404(User, pk=teacher_id)
        semester = get_object_or_404(Semester, pk=semester_id)
        classroom = Classroom.objects.filter(pk=classroom_id).first() if classroom_id else None

        selected_days = [int(d) for d in selected_days]
        selected_slots = [int(s) for s in selected_slots]

        created_count = 0
        skipped_holiday = 0
        skipped_exists = 0
        current = semester.start_date

        slot_map = {sn: (st, en) for sn, st, en in TIME_SLOTS}

        while current <= semester.end_date:
            dow = current.isoweekday()
            if dow == 7:
                current += timedelta(days=1)
                continue
            if current in holidays:
                current += timedelta(days=1)
                skipped_holiday += 1
                continue
            if dow in selected_days:
                for sn in selected_slots:
                    st, en = slot_map[sn]
                    start_time = time.fromisoformat(st)
                    end_time = time.fromisoformat(en)
                    exists = Timetable.objects.filter(
                        date=current, group=group, start_time=start_time
                    ).exists()
                    if exists:
                        skipped_exists += 1
                        continue
                    Timetable.objects.create(
                        subject=subject,
                        teacher=teacher,
                        group=group,
                        classroom=classroom,
                        day_of_week=dow,
                        start_time=start_time,
                        end_time=end_time,
                        date=current,
                    )
                    created_count += 1
            current += timedelta(days=1)

        msg = f"{semester.name} uchun {created_count} ta dars yaratildi."
        if skipped_holiday:
            msg += f" {skipped_holiday} ta bayram kuni o'tkazib yuborildi."
        if skipped_exists:
            msg += f" {skipped_exists} ta allaqachon mavjud edi."
        messages.success(request, msg)
        return redirect('timetable_view')

    return render(request, 'academy/timetable_semester.html', {
        'groups': groups,
        'subjects': subjects,
        'teachers': teachers,
        'classrooms': classrooms,
        'semesters': semesters,
        'time_slots': TIME_SLOTS,
        'days': DAYS_OF_WEEK_LIST,
    })

# 3. Darsni tahrirlash (Edit)
@login_required
def timetable_edit(request, pk):
    lesson = get_object_or_404(Timetable, pk=pk)
    
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Sizda tahrirlash huquqi yo'q!")
        return redirect('timetable_view')

    if request.method == "POST":
        form = TimetableForm(request.POST, instance=lesson)
        if form.is_valid():
            try:
                updated_lesson = form.save(commit=False)
                updated_lesson.full_clean()
                updated_lesson.save()
                log_action(request, 'update', 'Timetable', lesson, f"Dars tahrirlandi: {lesson.subject.name}")
                messages.success(request, "Dars muvaffaqiyatli yangilandi!")
                return redirect('timetable_view')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = TimetableForm(instance=lesson)
    
    return render(request, 'academy/timetable_form.html', {'form': form, 'edit_mode': True})

# 4. Darsni o'chirish (Delete)
@login_required
def timetable_delete(request, pk):
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Sizda o'chirish huquqi yo'q!")
        return redirect('timetable_view')

    lesson = get_object_or_404(Timetable, pk=pk)
    if request.method == "POST":
        log_action(request, 'delete', 'Timetable', lesson, f"Dars o'chirildi: {lesson.subject.name}")
        lesson.delete()
        messages.warning(request, "Dars jadvaldan o'chirildi.")
    
    return redirect('timetable_view')

@login_required
def grade_students(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    # Ushbu fanga yozilgan talabalar
    enrollments = Enrollment.objects.filter(subject=subject).select_related('student')
    
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
        return redirect('dashboard')

    return render(request, 'academy/grade_form.html', {
        'subject': subject,
        'enrollments': enrollments
    })

@login_required
def journal_view(request, lesson_id):
    lesson = get_object_or_404(Timetable, pk=lesson_id)
    # Ushbu fanga yozilgan talabalar
    enrollments = Enrollment.objects.filter(subject=lesson.subject).select_related('student')
    
    if request.method == "POST":
        for en in enrollments:
            student_id = en.student.id
            
            # 1. Davomatni saqlash
            status = request.POST.get(f'attendance_{student_id}')
            Attendance.objects.update_or_create(
                student=en.student,
                timetable=lesson,
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
        
        return redirect('dashboard')

    default_date = lesson.date or timezone.now().date()
    attendance_records = Attendance.objects.filter(timetable=lesson, date=default_date)
    att_map = {a.student_id: a.status for a in attendance_records}
    for en in enrollments:
        en.attendance_status = att_map.get(en.student.id, 'present')
    return render(request, 'academy/journal.html', {
        'lesson': lesson,
        'enrollments': enrollments,
        'today': timezone.now().date(),
        'default_date': default_date,
    })

@login_required
@parent_only
def parent_student_detail(request, uuid):
    student = get_object_or_404(Student.objects.select_related('user'), uuid=uuid, parent=request.user)
    return render(request, 'academy/parent_student_detail.html', {
        'student': student,
        'enrollments': Enrollment.objects.filter(student=student.user).select_related('subject'),
        'grade_map': student.subject_grades_map(),
        'att_map': student.subject_attendance_map(),
        'timetable': student.today_timetable(),
        'payments': student.recent_payments(),
    })

@login_required
def classroom_list(request):
    if request.user.role == 'student':
        return redirect('dashboard')
    rooms = Classroom.objects.all()
    return render(request, 'academy/classroom_list.html', {'rooms': rooms})

@login_required
@admin_only
def classroom_add(request):
    if request.method == "POST":
        form = ClassroomForm(request.POST)
        if form.is_valid():
            obj = form.save()
            log_action(request, 'create', 'Classroom', obj, f"Xona qo'shildi: {obj.number}")
            return redirect('classroom_list')
    else:
        form = ClassroomForm()
    return render(request, 'academy/classroom_form.html', {'form': form})

# Tahrirlash (Update)
@login_required
@admin_only
def classroom_edit(request, pk):
    room = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        form = ClassroomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            log_action(request, 'update', 'Classroom', room, f"Xona tahrirlandi: {room.number}")
            return redirect('classroom_list')
    else:
        form = ClassroomForm(instance=room)
    return render(request, 'academy/classroom_form.html', {'form': form, 'edit_mode': True})

# O'chirish (Delete)
@login_required
@admin_only
def classroom_delete(request, pk):
    room = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        log_action(request, 'delete', 'Classroom', room, f"Xona o'chirildi: {room.number}")
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
            group = form.save()
            log_action(request, 'create', 'Group', group, f"Guruh qo'shildi: {group.name}")
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
def grade_journal(request, uuid):
    subject = get_object_or_404(Subject, uuid=uuid)
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
        return redirect('grade_journal', uuid=subject.uuid)

    return render(request, 'academy/grade_journal.html', {
        'subject': subject,
        'enrollments': enrollments
    })

def group_detail(request, uuid):
    group = get_object_or_404(Group, uuid=uuid)
    students = group.students.all().select_related('user')
    
    if request.method == "POST" and request.user.role in ['admin', 'teacher']:
        student_ids = request.POST.getlist('add_students')
        if student_ids:
            added = Student.objects.filter(id__in=student_ids)
            for s in added:
                s.groups.add(group)
            messages.success(request, f"{len(added)} ta talaba guruhga qo'shildi!")
        return redirect('group_detail', uuid=group.uuid)
    
    # Guruhga kirmagan talabalar
    available_students = Student.objects.exclude(groups=group).select_related('user')
    
    return render(request, 'academy/group_detail.html', {
        'group': group,
        'students': students,
        'student_count': students.count(),
        'available_students': available_students,
    })

@login_required
@admin_only
def group_edit(request, uuid):
    group = get_object_or_404(Group, uuid=uuid)
    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            log_action(request, 'update', 'Group', group, f"Guruh tahrirlandi: {group.name}")
            messages.success(request, f"{group.name} guruhi tahrirlandi!")
            return redirect('group_list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'academy/group_form.html', {'form': form, 'edit_mode': True})

@login_required
@admin_only
def group_delete(request, uuid):
    group = get_object_or_404(Group, uuid=uuid)
    if request.method == "POST":
        log_action(request, 'delete', 'Group', group, f"Guruh o'chirildi: {group.name}")
        group.delete()
        messages.success(request, "Guruh o'chirildi!")
        return redirect('group_list')
    return render(request, 'academy/group_confirm_delete.html', {'group': group})

@login_required
def payment_list(request):
    if request.user.role == 'admin':
        payments = Payment.objects.all().select_related('student')
    elif request.user.role == 'student':
        payments = Payment.objects.filter(student=request.user)
    else:
        return redirect('dashboard')
    return render(request, 'academy/payment_list.html', {'payments': payments})

@login_required
@admin_only
def payment_add(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            if payment.status == 'paid':
                payment.paid_at = timezone.now()
            payment.save()
            log_action(request, 'create', 'Payment', payment, f"To'lov qo'shildi: {payment.amount} so'm")
            messages.success(request, "To'lov qo'shildi!")
            return redirect('payment_list')
    else:
        form = PaymentForm()
    return render(request, 'academy/payment_form.html', {'form': form})

@login_required
def exam_list(request):
    if request.user.role == 'admin':
        exams = Exam.objects.all().select_related('subject', 'group', 'created_by')
    elif request.user.role == 'teacher':
        exams = Exam.objects.filter(created_by=request.user)
    elif request.user.role == 'student':
        exams = Exam.objects.filter(group__students=request.user.student_profile)
    else:
        return redirect('dashboard')
    return render(request, 'academy/exam_list.html', {'exams': exams})

@login_required
@admin_only
def exam_add(request):
    if request.method == "POST":
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            log_action(request, 'create', 'Exam', exam, f"Imtihon qo'shildi: {exam.subject.name}")
            messages.success(request, "Imtihon qo'shildi!")
            return redirect('exam_list')
    else:
        form = ExamForm()
    return render(request, 'academy/exam_form.html', {'form': form})

@login_required
def semester_list(request):
    semesters = Semester.objects.all().order_by('-start_date')
    return render(request, 'academy/semester_list.html', {'semesters': semesters})

@login_required
def semester_add(request):
    if request.user.role != 'admin' and not request.user.is_staff:
        messages.error(request, "Sizda huquq yo'q!")
        return redirect('timetable_view')
    if request.method == "POST":
        form = SemesterForm(request.POST)
        if form.is_valid():
            sem = form.save()
            log_action(request, 'create', 'Semester', sem, f"Semestr qo'shildi: {sem.name}")
            messages.success(request, "Semestr muvaffaqiyatli qo'shildi!")
            return redirect('semester_list')
    else:
        form = SemesterForm()
    return render(request, 'academy/semester_form.html', {'form': form})

@login_required
def material_list(request):
    materials = StudyMaterial.objects.all().select_related('subject', 'uploaded_by')
    return render(request, 'academy/material_list.html', {'materials': materials})

@login_required
def material_add(request):
    if request.user.role == 'student':
        return redirect('dashboard')
    if request.method == "POST":
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.uploaded_by = request.user
            material.save()
            log_action(request, 'create', 'StudyMaterial', material, f"Material qo'shildi: {material.title}")
            messages.success(request, "Material qo'shildi!")
            return redirect('material_list')
    else:
        form = StudyMaterialForm()
    return render(request, 'academy/material_form.html', {'form': form})

@login_required
def material_delete(request, pk):
    if request.user.role == 'student':
        return redirect('material_list')
    material = get_object_or_404(StudyMaterial, pk=pk, uploaded_by=request.user) if request.user.role != 'admin' else get_object_or_404(StudyMaterial, pk=pk)
    if request.method == "POST":
        log_action(request, 'delete', 'StudyMaterial', material, f"Material o'chirildi: {material.title}")
        material.delete()
        messages.success(request, "Material o'chirildi!")
        return redirect('material_list')
    return render(request, 'academy/material_confirm_delete.html', {'material': material})

@login_required
def notification_list(request):
    if request.user.role == 'student':
        return redirect('dashboard')
    notifications = Notification.objects.filter(recipient=request.user)
    return render(request, 'academy/notification_list.html', {'notifications': notifications})

@login_required
def notification_send(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    if request.method == "POST":
        title = request.POST.get('title')
        message = request.POST.get('message')
        recipient_group = request.POST.get('recipient_group')

        recipients = []
        if recipient_group == 'all_students':
            recipients = User.objects.filter(role='student')
        elif recipient_group == 'all_teachers':
            recipients = User.objects.filter(role='teacher')
        elif recipient_group == 'everyone':
            recipients = User.objects.all()
        elif recipient_group == 'by_group':
            group_ids = request.POST.getlist('group_ids')
            if group_ids:
                student_ids = Student.objects.filter(groups__in=group_ids).values_list('user_id', flat=True)
                recipients = User.objects.filter(id__in=student_ids)
        elif recipient_group == 'single':
            recipient_ids = request.POST.getlist('recipients')
            if recipient_ids:
                recipients = User.objects.filter(pk__in=recipient_ids)

        if title and message and recipients:
            for user in recipients:
                Notification.objects.create(
                    sender=request.user,
                    recipient=user,
                    title=title,
                    message=message,
                )
            log_action(request, 'create', 'Notification', None, f"Xabar jo'natildi: {title} -> {len(recipients)} kishiga")
            messages.success(request, f"Xabar {len(recipients)} kishiga jo'natildi!")
            return redirect('notification_list')
        else:
            messages.error(request, "Xabar yoki qabul qiluvchi topilmadi!")
    all_users = User.objects.all().order_by('role', 'username')
    groups = Group.objects.all()
    return render(request, 'academy/notification_form.html', {'all_users': all_users, 'groups': groups})

@login_required
def notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    return redirect('notification_list')

@login_required
def calendar_view(request):
    base = Timetable.objects.all()
    if request.user.role == 'teacher':
        base = Timetable.objects.filter(teacher=request.user)
    elif request.user.role == 'student':
        try:
            base = Timetable.objects.filter(group__in=request.user.student_profile.groups.all())
        except:
            base = Timetable.objects.none()
    group_id = request.GET.get('group')
    if group_id:
        base = base.filter(group_id=group_id)
    timetables = base.select_related('group', 'subject', 'teacher', 'classroom').order_by('date', 'start_time')
    groups = Group.objects.all()
    return render(request, 'academy/calendar.html', {
        'timetables': timetables,
        'groups': groups,
    })

@login_required
def export_grades(request, uuid):
    subject = get_object_or_404(Subject, uuid=uuid)
    enrollments = Enrollment.objects.filter(subject=subject).select_related('student', 'student__student_profile')

    grade_map = {}
    for g in Grade.objects.filter(subject=subject, student_id__in=enrollments.values_list('student_id', flat=True)):
        grade_map[g.student_id] = g

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = subject.name
    ws.append(['Talaba', 'Talaba ID', 'Baho'])

    for en in enrollments:
        grade = grade_map.get(en.student_id)
        ws.append([
            en.student.get_full_name(),
            en.student.student_profile.student_id if hasattr(en.student, 'student_profile') else '',
            grade.score if grade else ''
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{subject.name}_baholar.xlsx"'
    wb.save(response)
    return response

def register(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.save()
            student = user.student_profile
            student.student_id = form.cleaned_data.get('student_id')
            student.save()
            groups = form.cleaned_data.get('groups')
            if groups:
                student.groups.set(groups)
            messages.success(request, "Ro'yxatdan o'tdingiz! Tizimga kiring.")
            return redirect('login')
    else:
        form = StudentAddForm()
    return render(request, 'registration/register.html', {'form': form})

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

@login_required
def fill_journal(request, timetable_id):
    timetable = get_object_or_404(Timetable, id=timetable_id)
    # Ushbu guruhdagi barcha talabalarni olamiz
    students = User.objects.filter(student_profile__groups=timetable.group).select_related('student_profile')

    if request.method == "POST":
        # 1. Dars kunini yaratamiz
        journal_entry = LessonJournal.objects.create(
            timetable=timetable,
            topic=request.POST.get('topic')
        )

        # 2. Har bir talaba uchun davomat va bahoni saqlaymiz
        for student in students:
            is_present = request.POST.get(f'present_{student.id}') == 'on'
            score = request.POST.get(f'score_{student.id}')
            
            JournalGrade.objects.create(
                lesson=journal_entry,
                student=student,
                is_present=is_present,
                score=score if score else None
            )
        
        messages.success(request, "Jurnal muvaffaqiyatli saqlandi!")
        return redirect('dashboard')

    return render(request, 'academy/fill_journal.html', {
        'timetable': timetable,
        'students': students
    })

@login_required
def chat_assistant(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    assistant = Assistant(request.user)
    
    if request.method == "POST":
        user_msg = request.POST.get('message', '').strip()
        if user_msg:
            ChatMessage.objects.create(
                user=request.user, role='user', text=user_msg
            )
            bot_reply = assistant.answer(user_msg)
            ChatMessage.objects.create(
                user=request.user, role='bot', text=bot_reply
            )
        return redirect('chat_assistant')
    
    messages_list = ChatMessage.objects.filter(user=request.user).values('role', 'text', 'created_at')
    messages = [{
        'role': m['role'],
        'text': m['text'],
        'time': timezone.localtime(m['created_at']).strftime('%H:%M %d.%m.%Y')
    } for m in messages_list]
    
    return render(request, 'academy/chat.html', {'messages': messages})
