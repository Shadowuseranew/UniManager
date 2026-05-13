from django.core.management.base import BaseCommand
from users.models import User, TeacherProfile
from academy.models import Student, Group, Subject, Classroom, Semester, Faculty, AcademicYear
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Malumotlar bilan toldirish: 40 oqituvchi, 400 talaba'

    def handle(self, *args, **options):
        fake = Faker('uz_UZ')
        self.stdout.write("Malumotlar yaratilmoqda...")

        if Subject.objects.count() == 0:
            subjects = [
                ('Matematika', 'MATH101', 4),
                ('Fizika', 'PHY101', 4),
                ('Kimyo', 'CHM101', 3),
                ('Biologiya', 'BIO101', 3),
                ('Informatika', 'INF101', 5),
                ('Ingliz tili', 'ENG101', 3),
                ('Tarix', 'HST101', 3),
                ('Adabiyot', 'LIT101', 3),
                ('Iqtisodiyot', 'ECO101', 4),
                ('Huquqshunoslik', 'LAW101', 3),
            ]
            for name, code, credits in subjects:
                Subject.objects.create(name=name, code=code, credits=credits)
            self.stdout.write(f"  {len(subjects)} ta fan yaratildi")

        if Classroom.objects.count() == 0:
            for i in range(1, 21):
                room_type = random.choice(['lecture', 'lab', 'practice'])
                Classroom.objects.create(
                    number=f"{random.randint(1,5)}0{i:02d}",
                    capacity=random.choice([30, 40, 50, 100]),
                    room_type=room_type,
                )
            self.stdout.write("  20 ta xona yaratildi")

        if Faculty.objects.count() == 0:
            faculties = [
                ('Axborot texnologiyalari', 'IT'),
                ('Iqtisodiyot', 'IQ'),
                ('Huquqshunoslik', 'HQ'),
                ('Filologiya', 'FL'),
                ('Matematika', 'MT'),
            ]
            for name, code in faculties:
                Faculty.objects.create(name=name, code=code)
            self.stdout.write(f"  {len(faculties)} ta fakultet yaratildi")

        if AcademicYear.objects.count() == 0:
            AcademicYear.objects.create(
                name="2025-2026",
                start_date="2025-09-01",
                end_date="2026-06-30",
                is_active=True,
            )
            self.stdout.write("  1 ta o'quv yili yaratildi")

        if Semester.objects.count() == 0:
            academic_year = AcademicYear.objects.filter(is_active=True).first()
            Semester.objects.create(
                name="2025-2026 Bahorgi semestr",
                academic_year=academic_year,
                start_date="2025-02-01",
                end_date="2025-06-15",
                is_active=True,
            )
            self.stdout.write("  1 ta semestr yaratildi")

        teachers_count = User.objects.filter(role='teacher').count()
        if teachers_count < 5:
            to_create = 5 - teachers_count
            for i in range(to_create):
                first = fake.first_name()
                last = fake.last_name()
                username = f"teacher{teachers_count + i + 1}"
                user = User.objects.create_user(
                    username=username,
                    password='teacher123',
                    first_name=first,
                    last_name=last,
                    role='teacher',
                )
                profile = user.teacher_profile
                profile.specialization = random.choice([
                    'Matematika', 'Fizika', 'Kimyo', 'Informatika',
                    'Filologiya', 'Tarix', 'Huquq', 'Iqtisodiyot'
                ])
                profile.bio = f"{first} {last} - tajribali oqituvchi"
                profile.save()
            self.stdout.write(f"  {to_create} ta oqituvchi yaratildi")

        students_count = User.objects.filter(role='student').count()
        if students_count < 10:
            to_create = 10 - students_count
            for i in range(to_create):
                first = fake.first_name()
                last = fake.last_name()
                username = f"student{students_count + i + 1}"
                user = User.objects.create_user(
                    username=username,
                    password='student123',
                    first_name=first,
                    last_name=last,
                    role='student',
                )
                course = ((students_count + i) // 100) + 1
                student = user.student_profile
                student.student_id = f"ST-{2026-course:04d}{(students_count + i + 1):04d}"
                student.course = course
                student.save()
            self.stdout.write(f"  {to_create} ta talaba yaratildi")

        self.stdout.write(self.style.SUCCESS("Barcha malumotlar muvaffaqiyatli yaratildi!"))
