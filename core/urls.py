from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views
from core.forms import CustomPasswordChangeForm


urlpatterns = [
    ########## Applications ##########
    path('blog/', include('blog.urls')),
    path('admin/', admin.site.urls),

    ########## Core App ##########
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    ########## Dashboard ##########
    path('dashboard/', views.dashboard, name='dashboard'),
    path("login/", views.user_login, name="login"),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/profile/', views.profile, name='profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(form_class=CustomPasswordChangeForm,template_name='core/changepwd.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='core/changepwddone.html'), name='password_change_done'),
    path('dashboard/settings/', TemplateView.as_view(template_name='core/settings.html'), name='settings'),
    path('dashboard/users/', views.users, name='users')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

