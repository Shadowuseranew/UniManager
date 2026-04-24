from django.urls import path
from . import views

urlpatterns = [
    # Guruhlar (Groups)
    path('groups/', views.group_list, name='group_list'),
    path('groups/add/', views.group_add, name='group_add'),
    # path('groups/edit/<int:pk>/', views.group_edit, name='group_edit'), # Agar viewsda bo'lsa oching

    # Fanlar (Subjects)
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path('subjects/edit/<int:pk>/', views.subject_edit, name='subject_edit'),
    path('subjects/delete/<int:pk>/', views.subject_delete, name='subject_delete'),

    # Xonalar (Classrooms)
    path('classrooms/', views.classroom_list, name='classroom_list'),
    path('classrooms/add/', views.classroom_add, name='classroom_add'),
    path('classrooms/edit/<int:pk>/', views.classroom_edit, name='classroom_edit'),
    path('classrooms/delete/<int:pk>/', views.classroom_delete, name='classroom_delete'),

 
    path('timetable/', views.timetable_view, name='timetable_view'), 
    path('timetable/add/', views.timetable_add, name='timetable_add'),
    path('timetable/edit/<int:pk>/', views.timetable_edit, name='timetable_edit'),
    path('timetable/delete/<int:pk>/', views.timetable_delete, name='timetable_delete'),

    # Jurnallar va Dashboardlar
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('journal/<int:lesson_id>/', views.journal_view, name='journal_view'),
    path('subject/<int:subject_id>/journal/', views.grade_journal, name='grade_journal'),
]