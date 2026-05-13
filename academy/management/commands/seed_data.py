from django.core.management.base import BaseCommand
from users.models import User
from academy.models import Student, Subject, Classroom, Semester, Faculty, AcademicYear, Group, Enrollment, Timetable
import random
from datetime import time

class Command(BaseCommand):
    help = 'Malumotlar bilan toldirish: 40 oqituvchi, 400 talaba'

    def handle(self, *args, **options):
        self.stdout.write("Malumotlar yaratilmoqda...")
        first_names = ['Ali', 'Vali', 'Soli', 'Husan', 'Husan', 'Murod', 'Bobur', 'Jamshid', 'Botir', 'Akmal',
                       'Dilshod', 'Shavkat', 'Rustam', 'Oybek', 'Ulug\'bek', 'Jasur', 'Davron', 'Bahrom', 'Zafar', 'Islom',
                       'Shohruh', 'Temur', 'Sarvar', 'Jahongir', 'Ilyos', 'Bekzod', 'Farrux', 'Ravshan', 'Aziz', 'Nodir',
                       'Nigora', 'Zulfiya', 'Gulnora', 'Dildora', 'Mohigul', 'Nargiza', 'Feruza', 'Maftuna', 'Shahlo', 'Gulbahor',
                       'Maqsuda', 'Saodat', 'Matluba', 'Dilfuza', 'Sabina', 'Zilola', 'Adolat', 'Sitora', 'Malika', 'Hilola']
        last_names = ['Abdullayev', 'Karimov', 'Aliyev', 'Toshmatov', 'Sobirov', 'Murodov', 'Sultonov', 'Mirzayev',
                      'Usmonov', 'Xasanov', 'Raximov', 'Ismoilov', 'Komilov', 'Yusupov', 'Nurmatov', 'Ergashev',
                      'Rashidov', 'Hamidov', 'Tursunov', 'Bekmurodov',
                      'Abdullayeva', 'Karimova', 'Aliyeva', 'Sobirova', 'Raximova', 'Usmonova', 'Sultonova', 'Mirzayeva',
                      'Ismoilova', 'Xasanova', 'Komilova', 'Yusupova', 'Ergasheva', 'Rashidova', 'Hamidova', 'Nurmatova']

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
                first = random.choice(first_names)
                last = random.choice(last_names)
                username = f"teacher{teachers_count + i + 1}"
                user = User.objects.create_user(
                    username=username,
                    password='teacher123',
                    first_name=first,
                    last_name=last,
                    role='teacher',
                )
                user.login_password = 'teacher123'
                user.save(update_fields=['login_password'])
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
                first = random.choice(first_names)
                last = random.choice(last_names)
                username = f"student{students_count + i + 1}"
                user = User.objects.create_user(
                    username=username,
                    password='student123',
                    first_name=first,
                    last_name=last,
                    role='student',
                )
                user.login_password = 'student123'
                user.save(update_fields=['login_password'])
                course = ((students_count + i) // 100) + 1
                student = user.student_profile
                student.student_id = f"ST-{2026-course:04d}{(students_count + i + 1):04d}"
                student.course = course
                student.save()
            self.stdout.write(f"  {to_create} ta talaba yaratildi")

        if Group.objects.count() == 0:
            faculties = list(Faculty.objects.all())
            subjects = list(Subject.objects.all())
            teachers = list(User.objects.filter(role='teacher'))
            group_names = ['Matematika 101', 'Informatika 101', 'Iqtisodiyot 101']
            groups = []
            for i, name in enumerate(group_names):
                g = Group.objects.create(
                    name=name,
                    faculty=faculties[i % len(faculties)],
                    course_number=1,
                    teacher=teachers[i % len(teachers)] if teachers else None,
                )
                g.subjects.set(random.sample(subjects, min(4, len(subjects))))
                groups.append(g)
            self.stdout.write(f"  {len(groups)} ta guruh yaratildi")

        if Enrollment.objects.count() == 0:
            students = list(User.objects.filter(role='student'))
            subjects = list(Subject.objects.all())
            enrolled = 0
            for student in students:
                for subject in random.sample(subjects, min(3, len(subjects))):
                    Enrollment.objects.get_or_create(student=student, subject=subject)
                    enrolled += 1
            self.stdout.write(f"  {enrolled} ta yozuv (Enrollment) yaratildi")

        if Timetable.objects.count() == 0:
            groups = list(Group.objects.all())
            teachers = list(User.objects.filter(role='teacher'))
            classrooms = list(Classroom.objects.all())
            times = [
                (time(9, 0), time(10, 30)),
                (time(10, 45), time(12, 15)),
                (time(13, 0), time(14, 30)),
            ]
            week_days = [1, 2, 3, 4, 5]
            entries = 0
            for group in groups:
                group_subjects = list(group.subjects.all())
                for subj in group_subjects[:2]:
                    day = random.choice(week_days)
                    start, end = random.choice(times)
                    teacher = random.choice(teachers) if teachers else None
                    classroom = random.choice(classrooms) if classrooms else None
                    Timetable.objects.create(
                        subject=subj,
                        teacher=teacher,
                        group=group,
                        classroom=classroom,
                        day_of_week=day,
                        start_time=start,
                        end_time=end,
                    )
                    entries += 1
            self.stdout.write(f"  {entries} ta dars jadvali yaratildi")

        self.stdout.write(self.style.SUCCESS("Barcha malumotlar muvaffaqiyatli yaratildi!"))
