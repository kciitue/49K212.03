from django.contrib import admin
from . import views
from django.urls import path
urlpatterns = [
    path('', views.home_admin, name='home_admin'),
    path('add_room/', views.add_room, name='add_room'),
    path('delete_room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('edit_room/<int:room_id>/', views.edit_room, name='edit_room'),
    path('add_invoice/<int:room_id>/', views.add_invoice, name='add_invoice')
]
