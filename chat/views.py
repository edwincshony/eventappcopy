from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Room, Message
from .forms import MessageForm
from notifications.models import Notification  # Integrate

class ChatListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'chat/room_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        return Room.objects.filter(participants=self.request.user).order_by('-created_at')

class RoomDetailView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = 'chat/room_detail.html'
    context_object_name = 'room'

    def get_queryset(self):
        queryset = Room.objects.filter(participants=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages_qs = self.object.messages.all()
        # Mark unread as read for current user
        unread = messages_qs.filter(is_read=True).exclude(sender=self.request.user)
        for msg in unread:
            msg.is_read = True
            msg.save(update_fields=['is_read'])
        context['messages'] = messages_qs
        context['message_form'] = MessageForm()
        return context

@require_http_methods(["POST"])
def send_message(request, pk):
    room = get_object_or_404(Room, pk=pk, participants=request.user)
    form = MessageForm(request.POST)
    if form.is_valid():
        content = form.cleaned_data['content']
        message = Message.objects.create(
            room=room,
            sender=request.user,
            content=content
        )
        # Notify other participants
        for participant in room.participants.exclude(id=request.user.id):
            Notification.objects.create(
                recipient=participant,
                notification_type='general',
                message=f'New message from {request.user.full_name} in chat room "{room.name}".',
                related_object_id=message.id,
                related_model='chat.message'
            )
        return JsonResponse({'status': 'success', 'message': {
            'id': message.id,
            'content': message.content,
            'sender': request.user.username,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }})
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

def load_messages(request, pk):
    room = get_object_or_404(Room, pk=pk, participants=request.user)
    messages = room.messages.all().values('id', 'content', 'sender__username', 'timestamp', 'is_read')
    return JsonResponse({'messages': list(messages)})

# Helper to get or create room (e.g., for starting chat with specific user)
def get_or_create_room(request, other_user_id):
    other_user = get_object_or_404(settings.AUTH_USER_MODEL, pk=other_user_id)
    if request.user.role == 'admin' or other_user.role == 'admin':
        messages.warning(request, 'Admins cannot participate in chats.')
        return redirect('chat:room_list')
    room, created = Room.objects.get_or_create(
        participants__in=[request.user, other_user],
        defaults={'name': f"Chat with {other_user.username}"}
    )
    if created:
        room.participants.add(request.user, other_user)
        messages.success(request, 'New chat room created.')
    return redirect('chat:room_detail', pk=room.pk)