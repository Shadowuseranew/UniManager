from django.urls import path
from django.contrib.auth.views import LogoutView
from academy import views as academy_views
from . import views

urlpatterns = [
    path('login/', views.RoleBasedLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', academy_views.register, name='register'),
    path('list/', views.user_list, name='user_list'),
    path('add/', views.user_add_choice, name='user_add'),
    path('add/admin/', views.admin_add, name='admin_add'),
    path('add/teacher/', views.teacher_add, name='teacher_add'),
    path('add/student/', views.student_add, name='student_add'),
    path('add/parent/', views.parent_add, name='parent_add'),
    path('edit/<uuid:uuid>/', views.user_edit, name='user_edit'),
    path('delete/<uuid:uuid>/', views.user_delete, name='user_delete'),
    path('detail/<uuid:uuid>/', views.user_detail, name='user_detail'),
]