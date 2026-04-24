from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Login va Logout
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Universitet tizimining barcha funksiyalari 'academy/' prefiksi ostida bo'ladi
    path('academy/', include('academy.urls')),
    
    # Saytga kirganda avtomat akademiya sahifasiga yuborish
    path('', RedirectView.as_view(url='/academy/subjects/')), 

    path('users/', include('users.urls'))
]