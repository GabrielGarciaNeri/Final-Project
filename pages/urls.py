from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import register_view


urlpatterns = [
    #public pages
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

    #AI pages
    path('learn/', views.learn_view, name='learn'),
    path('history/', views.quiz_history, name='quiz_history'),

    #login/logout/register pages
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('register/', register_view, name='register'),

    #password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='forgot-password/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='forgot-password/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='forgot-password/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='forgot-password/password_reset_complete.html'), name='password_reset_complete'),
]




