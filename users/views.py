from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import User
from .forms import UserCreationForm
from .decorators import admin_only
from academy.models import Student
from django.contrib import messages
from django.db.models import Q

@login_required
@admin_only
def user_list(request):
    # .prefetch_related orqali talabalarning guruhlarini bitta so'rovda olamiz
    # Bu 'Template' ichidagi user_obj.student_profile.groups.all so'rovini tezlashtiradi
    users = User.objects.all().prefetch_related(
        'student_profile__groups'
    ).order_by('-id')
    
    # Python darajasida filtrlash (Bazaga qayta so'rov yubormaslik uchun listga aylantiramiz)
    # Agar foydalanuvchilar juda ko'p bo'lmasa (masalan, < 1000), bu usul tezroq ishlaydi
    users_list = list(users)
    
    admins = [u for u in users_list if u.role == 'admin']
    teachers = [u for u in users_list if u.role == 'teacher']
    students = [u for u in users_list if u.role == 'student']
    
    context = {
        'admins': admins,
        'teachers': teachers,
        'students': students,
        'total_count': len(users_list)
    }
    return render(request, 'users/user_list.html', context)

@login_required
@admin_only
def user_add(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # 1. Userni saqlash (Signals avtomatik ravishda Student profilini yaratadi)
            user = form.save()
            
            # 2. Guruhlarni bog'lash (Many-to-Many)
            # Signal profilni yaratib bo'lgan, shuning uchun biz unga guruhlarni qo'shib qo'yamiz
            if user.role == 'student':
                selected_groups = form.cleaned_data.get('groups')
                if selected_groups:
                    # student_profile signal orqali allaqachon yaratilgan
                    user.student_profile.groups.set(selected_groups)
            
            messages.success(request, f"{user.username} muvaffaqiyatli yaratildi!")
            return redirect('user_list')
        else:
            messages.error(request, "Iltimos, xatoliklarni tekshiring.")
    else:
        form = UserCreationForm()
    
    return render(request, 'users/user_form.html', {'form': form})

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
                    # Mavjud profilni yangilash
                    student_profile.student_id = form.cleaned_data.get('student_id')
                    student_profile.save()
                
                # 3. Many-to-Many guruhlarni yangilash
                selected_groups = form.cleaned_data.get('groups')
                if selected_groups is not None:
                    student_profile.groups.set(selected_groups)
            
            return redirect('user_list')
    else:
        # Tahrirlash sahifasi ochilganda eski ma'lumotlar formada ko'rinishi uchun:
        initial_data = {}
        if student_profile:
            initial_data['student_id'] = student_profile.student_id
            # Eski tanlangan guruhlarni formaga yuklaymiz
            initial_data['groups'] = student_profile.groups.all()
            
        form = UserCreationForm(instance=user_obj, initial=initial_data)
    
    return render(request, 'users/user_form.html', {'form': form, 'edit_mode': True})

@login_required
@admin_only
def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    
    if request.method == "POST":
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
    
    # Filtrda ko'rsatish uchun barcha guruhlarni olamiz
    from academy.models import Group
    all_groups = Group.objects.all()

    context = {
        'admins': admins,
        'teachers': teachers,
        'students': students,
        'total_count': len(users_list),
        'all_groups': all_groups,
        'search_query': search_query,
        'selected_group': group_filter,
    }
    return render(request, 'users/user_list.html', context)