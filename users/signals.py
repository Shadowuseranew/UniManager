from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import User, TeacherProfile
from academy.models import Student

@receiver(post_save, sender=User)
def create_user_profiles(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'student':
            Student.objects.create(
                user=instance,
                student_id=f"ST-{instance.username}",
                phone_number=instance.phone_number or ''
            )
        elif instance.role == 'teacher':
            TeacherProfile.objects.create(
                user=instance,
                specialization=''
            )

@receiver(post_save, sender=User)
def save_user_profiles(sender, instance, **kwargs):
    if instance.role == 'student' and hasattr(instance, 'student_profile'):
        instance.student_profile.save()
    elif instance.role == 'teacher' and hasattr(instance, 'teacher_profile'):
        instance.teacher_profile.save()