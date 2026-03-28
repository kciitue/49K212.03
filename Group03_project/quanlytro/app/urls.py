from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import CustomPasswordResetForm

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
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
    path('add_invoice/<int:room_id>/', views.add_invoice, name='add_invoice'),
    path('invoice_detail/<int:invoice_id>/', views.invoice_detail, name = 'invoice_detail'),
    path('invoice/<int:invoice_id>/confirm/', views.confirm_invoice, name='confirm_invoice'),
    path('invoice/<int:invoice_id>/cancel/', views.cancel_invoice, name='cancel_invoice'),
    path('invoice_management/', views.invoice_management, name='invoice_management'),
    path('invoice_edit/<int:invoice_id>/', views.edit_invoice, name='edit_invoice'),
    path('invoice_view/<int:invoice_id>/', views.view_invoice, name='view_invoice'),
    path('quick-search/', views.quick_invoice_search, name='quick_invoice_search'),
    path('invoice/guest/<int:invoice_id>/', views.guest_invoice_detail, name='guest_invoice_detail'),
    path('invoice_confirm/<int:invoice_id>/', views.confirm_invoice, name='confirm_invoice'),
    path('api/sepay-webhook/', views.sepay_webhook, name='sepay_webhook'),
    path('api/invoice/<int:invoice_id>/status/', views.check_invoice_status, name='check_invoice_status'),
    path('report/', views.report, name='report'),
]
