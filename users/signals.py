from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from academy.models import Student

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Agar yangi foydalanuvchi yaratilgan bo'lsa (created=True)
    # va uning roli talaba bo'lsa
    if created and instance.role == 'student':
        Student.objects.create(
            user=instance,
            student_id=f"ST-{instance.username}", # Avtomatik ID berish
            phone_number=instance.phone_number or ''
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Foydalanuvchi ma'lumotlari yangilanganda profilni ham yangilash
    if instance.role == 'student' and hasattr(instance, 'student_profile'):
        instance.student_profile.save()