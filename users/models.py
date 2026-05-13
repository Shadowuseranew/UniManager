from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Foydalanuvchi rollarini belgilaymiz
    USER_ROLES = (
        ('admin', 'Admin'),
        ('teacher', 'O\'qituvchi'),
        ('student', 'Talaba'),
        ('parent', 'Ota-ona'),
    )
    role = models.CharField(max_length=10, choices=USER_ROLES, default='admin')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Rasm")

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    bio = models.TextField(blank=True)
    specialization = models.CharField(max_length=100)

