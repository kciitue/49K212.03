from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import CustomPasswordResetForm

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home_admin/', views.home_admin, name='home_admin'),
    path('home_customer/', views.home_customer, name='home_customer'),
    path('forgot_password/', auth_views.PasswordResetView.as_view(
        template_name='apartment/forgot password/require_set_password_again.html',
        form_class=CustomPasswordResetForm,  # Dùng form tự chế để check email
        email_template_name='apartment/forgot password/password_reset_email.html'  # Template nội dung mail
    ), name='require_set_password_again'),
    path('sent_email/',
         auth_views.PasswordResetDoneView.as_view(template_name='apartment/forgot password/password_reset_done.html'),
         name='password_reset_done'),
    path('set_new_password/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='apartment/forgot password/set_new_password.html'),
         name='set_new_password'),
    path('change_password/', auth_views.PasswordResetCompleteView.as_view(
        template_name='apartment/forgot password/password_reset_complete.html'), name='password_reset_complete'),
    path('user_management/', views.user_management, name='user_management'),

    path('add_user/', views.add_user, name='add_user'),

    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('edit/<int:user_id>/', views.edit_user, name='edit_user'),

    path('toggle_status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),

    path('add_room/', views.add_room, name='add_room'),
    path('delete_room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('edit_room/<int:room_id>/', views.edit_room, name='edit_room'),
]
