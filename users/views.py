import secrets
import string

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse
from .models import User, TeacherProfile
from .forms import UserCreationForm, AdminAddForm, TeacherAddForm, StudentAddForm, ParentAddForm
from .decorators import admin_only
from academy.models import Student
from django.contrib import messages
from django.db.models import Q
from django.utils.safestring import mark_safe
from academy.audit_logger import log_action


def _generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def _create_user_with_password(form, role):
    raw_password = form.cleaned_data.get('password') or _generate_password()
    user = form.save(commit=False)
    user.role = role
    user.set_password(raw_password)
    user.login_password = raw_password
    user.save()
    form.save_m2m()
    return user, raw_password

class RoleBasedLoginView(LoginView):
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse('dashboard')


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
            user, password = _create_user_with_password(form, 'admin')
            request.session[f'new_pwd_{user.id}'] = password
            log_action(request, 'create', 'User', user, f"Admin qo'shildi: {user.username}")
            messages.success(request, mark_safe(f"Admin qo'shildi. Parol: <strong>{password}</strong>"))
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
            user, password = _create_user_with_password(form, 'teacher')
            request.session[f'new_pwd_{user.id}'] = password
            profile = user.teacher_profile
            profile.specialization = form.cleaned_data.get('specialization')
            profile.bio = form.cleaned_data.get('bio')
            profile.save()
            log_action(request, 'create', 'User', user, f"O'qituvchi qo'shildi: {user.username}")
            messages.success(request, mark_safe(f"O'qituvchi qo'shildi. Parol: <strong>{password}</strong>"))
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
            user, password = _create_user_with_password(form, 'parent')
            request.session[f'new_pwd_{user.id}'] = password
            log_action(request, 'create', 'User', user, f"Ota-ona qo'shildi: {user.username}")
            messages.success(request, mark_safe(f"Ota-ona qo'shildi. Parol: <strong>{password}</strong>"))
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
            user, password = _create_user_with_password(form, 'student')
            request.session[f'new_pwd_{user.id}'] = password
            student = user.student_profile
            student.course = form.cleaned_data.get('course')
            student.parent = form.cleaned_data.get('parent')
            student.save()
            groups = form.cleaned_data.get('groups')
            if groups:
                student.groups.set(groups)
            log_action(request, 'create', 'User', user, f"Talaba qo'shildi: {user.username}")
            messages.success(request, mark_safe(f"Talaba qo'shildi. Parol: <strong>{password}</strong>"))
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
def user_edit(request, uuid):
    user_obj = get_object_or_404(User, uuid=uuid)
    
    # Foydalanuvchiga tegishli talaba profilini olish (agar bo'lsa)
    student_profile = getattr(user_obj, 'student_profile', None)
    
    if request.method == "POST":
        form = UserCreationForm(request.POST, instance=user_obj)
        if form.is_valid():
            user = form.save(commit=False)
            raw_password = form.cleaned_data.get('password')
            if raw_password:
                user.set_password(raw_password)
                user.login_password = raw_password
            user.save()
            
            if user.role == 'student':
                if not student_profile:
                    student_profile = Student.objects.create(user=user)
                else:
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
            initial_data['course'] = student_profile.course
            initial_data['groups'] = student_profile.groups.all()
            initial_data['parent'] = student_profile.parent
            
        form = UserCreationForm(instance=user_obj, initial=initial_data)
    
    return render(request, 'users/user_form.html', {'form': form, 'edit_mode': True})

@login_required
@admin_only
def user_detail(request, uuid):
    """Foydalanuvchi haqida batafsil ma'lumot sahifasi"""
    user_obj = get_object_or_404(User.objects.prefetch_related('student_profile__groups'), uuid=uuid)
    return render(request, 'users/user_detail.html', {'user_obj': user_obj})

@login_required
@admin_only
def user_delete(request, uuid):
    user_obj = get_object_or_404(User, uuid=uuid)
    
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