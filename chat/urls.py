from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.ChatListView.as_view(), name='room_list'),
    path('room/<int:pk>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('room/<int:pk>/send/', views.send_message, name='send_message'),
    path('room/<int:pk>/load/', views.load_messages, name='load_messages'),
    path('start/<int:other_user_id>/', views.get_or_create_room, name='start_room'),
]