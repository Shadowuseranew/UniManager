from django.urls import path
from . import views

urlpatterns = [
    # Guruhlar (Groups)
    path('groups/', views.group_list, name='group_list'),
    path('groups/add/', views.group_add, name='group_add'),
    path('groups/edit/<uuid:uuid>/', views.group_edit, name='group_edit'),
    path('groups/delete/<uuid:uuid>/', views.group_delete, name='group_delete'),

    # Fanlar (Subjects)
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path('subjects/edit/<uuid:uuid>/', views.subject_edit, name='subject_edit'),
    path('subjects/delete/<uuid:uuid>/', views.subject_delete, name='subject_delete'),

    # Xonalar (Classrooms)
    path('classrooms/', views.classroom_list, name='classroom_list'),
    path('classrooms/add/', views.classroom_add, name='classroom_add'),
    path('classrooms/edit/<int:pk>/', views.classroom_edit, name='classroom_edit'),
    path('classrooms/delete/<int:pk>/', views.classroom_delete, name='classroom_delete'),

 
    path('timetable/', views.timetable_view, name='timetable_view'), 
    path('timetable/add/', views.timetable_add, name='timetable_add'),
    path('timetable/batch/', views.timetable_batch_add, name='timetable_batch'),
    path('timetable/semester/', views.timetable_semester_generate, name='timetable_semester'),
    path('timetable/edit/<int:pk>/', views.timetable_edit, name='timetable_edit'),
    path('timetable/delete/<int:pk>/', views.timetable_delete, name='timetable_delete'),

    # Jurnallar va Dashboardlar
    path('teacher/dashboard/', views.dashboard, name='teacher_dashboard'),
    path('student/dashboard/', views.dashboard, name='student_dashboard'),
    path('journal/<int:lesson_id>/', views.journal_view, name='journal_view'),
    path('subject/<uuid:uuid>/journal/', views.grade_journal, name='grade_journal'),
    path('journal/fill/<int:timetable_id>/', views.fill_journal, name='fill_journal'),
    path('groups/<uuid:uuid>/', views.group_detail, name='group_detail'),
    path('timetable/list/', views.timetable_list, name='timetable_list'),

    # Semestrlar
    path('semesters/', views.semester_list, name='semester_list'),
    path('semesters/add/', views.semester_add, name='semester_add'),

    # Tolovlar
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_add, name='payment_add'),

    # Imtihonlar
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_add, name='exam_add'),

    # Oquv materiallari
    path('materials/', views.material_list, name='material_list'),
    path('materials/add/', views.material_add, name='material_add'),
    path('materials/delete/<int:pk>/', views.material_delete, name='material_delete'),

    # Xabarlar
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/send/', views.notification_send, name='notification_send'),
    path('notifications/read/<int:pk>/', views.notification_read, name='notification_read'),

    # Kalendar
    path('calendar/', views.calendar_view, name='calendar_view'),

    # Hisobot eksport
    path('export/grades/<uuid:uuid>/', views.export_grades, name='export_grades'),



    # Ota-ona (Parent)
    path('parent/dashboard/', views.dashboard, name='parent_dashboard'),
    path('parent/student/<uuid:uuid>/', views.parent_student_detail, name='parent_student_detail'),

    path('chat/', views.chat_assistant, name='chat_assistant'),
]