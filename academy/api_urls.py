from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api

router = DefaultRouter()
router.register(r'subjects', api.SubjectViewSet)
router.register(r'classrooms', api.ClassroomViewSet)
router.register(r'groups', api.GroupViewSet)
router.register(r'students', api.StudentViewSet)
router.register(r'timetables', api.TimetableViewSet)
router.register(r'grades', api.GradeViewSet)
router.register(r'attendance', api.AttendanceViewSet)
router.register(r'payments', api.PaymentViewSet)
router.register(r'exams', api.ExamViewSet)
router.register(r'materials', api.StudyMaterialViewSet)
router.register(r'notifications', api.NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
