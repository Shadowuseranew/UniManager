from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import User, TeacherProfile
from .forms import UserCreationForm, AdminAddForm, TeacherAddForm, StudentAddForm, ParentAddForm
from .decorators import admin_only
from academy.models import Student
from django.contrib import messages
from django.db.models import Q
from academy.audit_logger import log_action

@login_required
@admin_only
def user_add_choice(request):
    """Foydalanuvchi turini tanlash sahifasi"""
    return render(request, 'users/user_add_choice.html')

@login_required
@admin_only
def admin_add(request):
    if request.method == "POST":
        form = AdminAddForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'admin'
            user.save()
            log_action(request, 'create', 'User', user, f"Admin qo'shildi: {user.username}")
            messages.success(request, "Admin muvaffaqiyatli qo'shildi.")
            return redirect('user_list')
    else:
        form = AdminAddForm()
    return render(request, 'users/user_form.html', {'form': form, 'title': "Admin qo'shish"})

@login_required
@admin_only
def teacher_add(request):
    if request.method == "POST":
        form = TeacherAddForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'teacher'
            user.save()
            # Signal PROFILE_REGISTRY orqali TeacherProfile avtomat yaratiladi,
            # shuning uchun faqat forma ma'lumotlarini yangilaymiz
            profile = user.teacher_profile
            profile.specialization = form.cleaned_data.get('specialization')
            profile.bio = form.cleaned_data.get('bio')
            profile.save()
            log_action(request, 'create', 'User', user, f"O'qituvchi qo'shildi: {user.username}")
            messages.success(request, "O'qituvchi muvaffaqiyatli qo'shildi.")
            return redirect('user_list')
    else:
        form = TeacherAddForm()
    return render(request, 'users/user_form.html', {'form': form, 'title': "O'qituvchi qo'shish"})

@login_required
@admin_only
def parent_add(request):
    if request.method == "POST":
        form = ParentAddForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'parent'
            user.save()
            log_action(request, 'create', 'User', user, f"Ota-ona qo'shildi: {user.username}")
            messages.success(request, "Ota-ona muvaffaqiyatli qo'shildi.")
            return redirect('user_list')
    else:
        form = ParentAddForm()
    return render(request, 'users/user_form.html', {'form': form, 'title': "Ota-ona qo'shish"})

@login_required
@admin_only
def student_add(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.save()
            
            student = user.student_profile
            student.student_id = form.cleaned_data.get('student_id')
            student.course = form.cleaned_data.get('course')
            student.parent = form.cleaned_data.get('parent')
            student.save()
            
            groups = form.cleaned_data.get('groups')
            if groups:
                student.groups.set(groups)
                
            log_action(request, 'create', 'User', user, f"Talaba qo'shildi: {user.username}")
            messages.success(request, "Talaba muvaffaqiyatli qo'shildi.")
            return redirect('user_list')
    else:
        form = StudentAddForm()
    return render(request, 'users/user_form.html', {'form': form, 'title': "Talaba qo'shish"})

@login_required
@admin_only
def user_add(request):
    return redirect('user_add_choice')

@login_required
@admin_only
def user_edit(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    
    # Foydalanuvchiga tegishli talaba profilini olish (agar bo'lsa)
    student_profile = getattr(user_obj, 'student_profile', None)
    
    if request.method == "POST":
        form = UserCreationForm(request.POST, instance=user_obj)
        if form.is_valid():
            # 1. Asosiy User ma'lumotlarini saqlaymiz
            user = form.save()
            
            # 2. Agar foydalanuvchi roli 'student' bo'lsa, profilni yangilaymiz
            if user.role == 'student':
                # Agar profil mavjud bo'lmasa (masalan, oldin admin bo'lgan bo'lsa), yangi ochamiz
                if not student_profile:
                    student_profile = Student.objects.create(
                        user=user,
                        student_id=form.cleaned_data.get('student_id')
                    )
                else:
                    student_profile.student_id = form.cleaned_data.get('student_id')
                    student_profile.course = form.cleaned_data.get('course')
                    student_profile.parent = form.cleaned_data.get('parent')
                    student_profile.save()

                selected_groups = form.cleaned_data.get('groups')
                if selected_groups is not None:
                    student_profile.groups.set(selected_groups)
            
            return redirect('user_list')
    else:
        # Tahrirlash sahifasi ochilganda eski ma'lumotlar formada ko'rinishi uchun:
        initial_data = {}
        if student_profile:
            initial_data['student_id'] = student_profile.student_id
            initial_data['course'] = student_profile.course
            initial_data['groups'] = student_profile.groups.all()
            initial_data['parent'] = student_profile.parent
            
        form = UserCreationForm(instance=user_obj, initial=initial_data)
    
    return render(request, 'users/user_form.html', {'form': form, 'edit_mode': True})

@login_required
@admin_only
def user_detail(request, pk):
    """Foydalanuvchi haqida batafsil ma'lumot sahifasi"""
    user_obj = get_object_or_404(User.objects.prefetch_related('student_profile__groups'), pk=pk)
    return render(request, 'users/user_detail.html', {'user_obj': user_obj})

@login_required
@admin_only
def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    
    if request.method == "POST":
        log_action(request, 'delete', 'User', user_obj, f"Foydalanuvchi o'chirildi: {user_obj.username}")
        user_obj.delete()
        return redirect('user_list')
        
    return render(request, 'users/user_confirm_delete.html', {'user_obj': user_obj})

@login_required
@admin_only
def user_list(request):
    # 1. Boshlang'ich so'rov
    users = User.objects.all().prefetch_related('student_profile__groups').order_by('-id')
    
    # 2. Qidiruv (Search) qismini olish
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) | 
            Q(username__icontains=search_query)
        )
    
    # 3. Guruh bo'yicha filtr (faqat talabalar uchun)
    group_filter = request.GET.get('group', '')
    if group_filter:
        users = users.filter(student_profile__groups__id=group_filter)

    # 4. Rollar bo'yicha ajratish (optimallashgan variant)
    users_list = list(users)
    admins = [u for u in users_list if u.role == 'admin']
    teachers = [u for u in users_list if u.role == 'teacher']
    students = [u for u in users_list if u.role == 'student']
    parents = [u for u in users_list if u.role == 'parent']
    
    # Filtrda ko'rsatish uchun barcha guruhlarni olamiz
    from academy.models import Group
    all_groups = Group.objects.all()

    context = {
        'admins': admins,
        'teachers': teachers,
        'students': students,
        'parents': parents,
        'total_count': len(users_list),
        'all_groups': all_groups,
        'search_query': search_query,
        'selected_group': group_filter,
    }
    return render(request, 'users/user_list.html', context)