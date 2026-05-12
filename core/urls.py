from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from academy import views as academy_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Universitet tizimining barcha funksiyalari 'academy/' prefiksi ostida bo'ladi
    path('academy/', include('academy.urls')),
    
    # Foydalanuvchilar va avtentifikatsiya (login, logout, list, add...)
    path('auth/', include('users.urls')),
    
    # REST API
    path('api/', include('academy.api_urls')),
    
    # Dashboard (bosh sahifa)
    path('', academy_views.dashboard, name='dashboard'), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)