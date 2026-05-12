import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from academy.models import Timetable
entries = Timetable.objects.filter(day_of_week=1, classroom__number='101', start_time='11:50:00').order_by('id')[:5]
for e in entries:
    print(f'id={e.id}, date={e.date}, day={e.day_of_week}, time={e.start_time}-{e.end_time}')
print()
print('Total:', Timetable.objects.filter(day_of_week=1, classroom__number='101', start_time='11:50:00').count())
print()
dates = Timetable.objects.filter(day_of_week=1, classroom__number='101').values('date').distinct().order_by('date')
for d in dates:
    print(f'  date={d["date"]}')
