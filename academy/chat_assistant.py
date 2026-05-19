import re
from datetime import date, timedelta
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from .models import Grade, JournalGrade, Timetable, Exam, Payment, Group, Subject, Enrollment

class Assistant:
    def __init__(self, user):
        self.user = user

    def answer(self, message):
        msg = message.lower()

        if self.user.role == 'student':
            return self._answer_student(msg)
        elif self.user.role == 'teacher':
            return self._answer_teacher(msg)
        else:
            return self._answer_admin(msg)

    def _answer_student(self, msg):
        if any(w in msg for w in ['baho', 'ball', 'grade', 'natija']):
            return self._get_grades()
        if any(w in msg for w in ['davomat', 'qatnash', 'absent', 'kelmadi']):
            return self._get_attendance()
        if any(w in msg for w in ['dars', 'jadval', 'bugun', 'ertaga', 'timetable', 'schedule']):
            return self._get_schedule(msg)
        if any(w in msg for w in ['imtihon', 'exam', 'test']):
            return self._get_exams()
        if any(w in msg for w in ["to'lov", 'tolov', 'payment', 'qarz']):
            return self._get_payments()
        if any(w in msg for w in ['guruh', 'group', 'kurs']):
            return self._get_group_info()
        if any(w in msg for w in ['salom', 'assalom', 'hello', 'hi']):
            return "Assalomu alaykum! Men sizning yordamchingizman. Savollaringizni bering."
        if any(w in msg for w in ['yordam', 'help', 'komanda', 'buyruq']):
            return ("Menga quyidagilarni so'rashingiz mumkin:\n"
                    "- Baholarim / ballarim\n"
                    "- Davomatim\n"
                    "- Bugungi / ertangi darslar\n"
                    "- Imtihonlar jadvali\n"
                    "- To'lovlarim\n"
                    "- Guruh ma'lumotlari")
        return "Kechirasiz, tushunmadim. «Yordam» deb yozib ko'ring."

    def _answer_teacher(self, msg):
        if any(w in msg for w in ['fan', 'subject', 'dars']):
            return self._get_teacher_subjects()
        if any(w in msg for w in ['guruh', 'group', 'talaba', 'student']):
            return self._get_teacher_groups()
        if any(w in msg for w in ['dars', 'jadval', 'bugun', 'timetable']):
            return self._get_schedule(msg)
        if any(w in msg for w in ['salom', 'assalom']):
            return "Assalomu alaykum! Qanday yordam kerak?"
        if any(w in msg for w in ['yordam', 'help']):
            return "Fanlarim, Guruhlarim, Dars jadvali haqida so'rashingiz mumkin."
        return "Kechirasiz, tushunmadim."

    def _answer_admin(self, msg):
        if any(w in msg for w in ['fan', 'subject']):
            subjects = Subject.objects.count()
            return f"Jami {subjects} ta fan mavjud."
        if any(w in msg for w in ['guruh', 'group']):
            groups = Group.objects.count()
            return f"Jami {groups} ta guruh mavjud."
        if any(w in msg for w in ['talaba', 'student']):
            from users.models import User
            count = User.objects.filter(role='student').count()
            return f"Jami {count} ta talaba ro'yxatdan o'tgan."
        if any(w in msg for w in ['oqituvchi', 'teacher', "o'qituvchi"]):
            from users.models import User
            count = User.objects.filter(role='teacher').count()
            return f"Jami {count} ta o'qituvchi ro'yxatdan o'tgan."
        if any(w in msg for w in ['salom', 'assalom']):
            return "Assalomu alaykum! Admin panelga xush kelibsiz."
        if any(w in msg for w in ['yordam', 'help']):
            return "Fanlar, Guruhlar, Talabalar, O'qituvchilar sonini so'rashingiz mumkin."
        return "Kechirasiz, tushunmadim."

    def _get_grades(self):
        grades = Grade.objects.filter(student=self.user).select_related('subject')
        if not grades:
            return "Sizda hali baholar yo'q."
        lines = ["Sizning baholaringiz:"]
        for g in grades:
            lines.append(f"  {g.subject.name}: {g.score}")
        avg = grades.aggregate(Avg('score'))['score__avg']
        lines.append(f"O'rtacha ball: {avg:.1f}" if avg else "")
        return "\n".join(lines)

    def _get_attendance(self):
        stats = JournalGrade.objects.filter(
            student=self.user
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent')),
            late=Count('id', filter=Q(status='late')),
        )
        total = stats['total']
        if total == 0:
            return "Davomat ma'lumotlari yo'q."
        percent = (stats['present'] / total * 100) if total else 0
        return (f"Davomatingiz:\n"
                f"  Kelgan: {stats['present']} ta\n"
                f"  Kechikkan: {stats['late']} ta\n"
                f"  Kelmagan: {stats['absent']} ta\n"
                f"  Foiz: {percent:.1f}%")

    def _get_schedule(self, msg):
        from academy.models import Timetable
        today = timezone.localdate()
        if 'ertaga' in msg:
            target = today + timedelta(days=1)
        else:
            target = today
        dow = target.isoweekday()
        if dow == 7:
            dow = 6
        lessons = Timetable.objects.filter(
            Q(date=target) | Q(date__isnull=True, day_of_week=dow)
        ).select_related('subject', 'teacher', 'classroom', 'group').order_by('start_time')
        if not lessons:
            return f"{target.strftime('%d.%m.%Y')} kuni darslar yo'q."
        lines = [f"{target.strftime('%d.%m.%Y')} ({self._day_name(dow)}):"]
        for l in lessons:
            lines.append(f"  {l.start_time.strftime('%H:%M')}-{l.end_time.strftime('%H:%M')} | {l.subject.name} | {l.teacher.get_full_name()}")
        return "\n".join(lines)

    def _get_exams(self):
        import datetime
        today = date.today()
        exams = Exam.objects.filter(
            Q(group__students=self.user.student_profile)
        ).filter(date__gte=today).order_by('date')[:5]
        if not exams:
            return "Yaqin kunlarda imtihonlar yo'q."
        lines = ["Yaqinlashayotgan imtihonlar:"]
        for e in exams:
            lines.append(f"  {e.date} {e.start_time.strftime('%H:%M')} | {e.subject.name} | {e.get_exam_type_display()}")
        return "\n".join(lines)

    def _get_payments(self):
        payments = Payment.objects.filter(student=self.user)[:5]
        if not payments:
            return "To'lovlar haqida ma'lumot yo'q."
        lines = ["To'lovlaringiz:"]
        for p in payments:
            lines.append(f"  {p.amount} so'm - {p.get_status_display()}")
        return "\n".join(lines)

    def _get_group_info(self):
        try:
            profile = self.user.student_profile
            groups = profile.groups.all()
            if not groups:
                return "Siz guruhga biriktirilmagansiz."
            lines = ["Guruhlaringiz:"]
            for g in groups:
                count = g.students.count()
                lines.append(f"  {g.name} ({g.faculty.name}, {g.course_number}-kurs) - {count} talaba")
            return "\n".join(lines)
        except:
            return "Guruh ma'lumoti topilmadi."

    def _get_teacher_subjects(self):
        subjects = Subject.objects.filter(groups__teacher=self.user).distinct()
        if not subjects:
            return "Sizda fanlar yo'q."
        lines = ["Fanlaringiz:"]
        for s in subjects:
            lines.append(f"  {s.name} ({s.code})")
        return "\n".join(lines)

    def _get_teacher_groups(self):
        groups = Group.objects.filter(teacher=self.user)
        if not groups:
            return "Sizga biriktirilgan guruhlar yo'q."
        lines = ["Guruhlaringiz:"]
        for g in groups:
            count = g.students.count()
            lines.append(f"  {g.name} - {count} talaba")
        return "\n".join(lines)

    def _day_name(self, dow):
        names = {1: "Dushanba", 2: "Seshanba", 3: "Chorshanba", 4: "Payshanba", 5: "Juma", 6: "Shanba", 7: "Yakshanba"}
        return names.get(dow, "")
