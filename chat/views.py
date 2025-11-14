from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from .models import Room, Message
from .forms import MessageForm
from notifications.models import Notification
from accounts.models import CustomUser
from utils.pagination import paginate_queryset  # your global paginator


# Get the User model
User = get_user_model()

# Admin restriction mixin
class NonAdminRequiredMixin:
    '''Restricts admins/superusers from accessing chat features'''
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin'):
            messages.warning(request, 'Admins cannot participate in chats.')
            return redirect('accounts:home')
        return super().dispatch(request, *args, **kwargs)

class ChatListView(LoginRequiredMixin, NonAdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'chat/room_list.html'
    context_object_name = 'users'
    paginate_by = None  # disable ListView pagination to use global system

    def get_queryset(self):
        return CustomUser.objects.filter(
            is_active=True,
            is_approved=True
        ).exclude(
            Q(id=self.request.user.id) |
            Q(is_superuser=True) |
            Q(role='admin')
        ).order_by('full_name', 'username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Apply global pagination
        page_obj, paginated_users = paginate_queryset(self.request, context['users'])
        context['page_obj'] = page_obj
        context['users'] = paginated_users
        context['is_paginated'] = page_obj.paginator.num_pages > 1

        # Get rooms for this user
        user_rooms = Room.objects.filter(participants=self.request.user)

        # Map: user_id → room object
        room_map = {}
        for room in user_rooms:
            other_participants = room.participants.exclude(id=self.request.user.id)
            for participant in other_participants:
                room_map[participant.id] = room
        
        context['room_map'] = room_map
        context['my_rooms'] = user_rooms

        # Add unread counts
        for room in user_rooms:
            room.unread_count = room.messages.filter(
                is_read=False
            ).exclude(sender=self.request.user).count()

        return context

class RoomDetailView(LoginRequiredMixin, NonAdminRequiredMixin, DetailView):
    model = Room
    template_name = 'chat/room_detail.html'
    context_object_name = 'room'

    def get_queryset(self):
        return Room.objects.filter(participants=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages_qs = self.object.messages.all()
        
        # Mark unread messages as read
        unread = messages_qs.filter(is_read=False).exclude(sender=self.request.user)
        for msg in unread:
            msg.is_read = True
            msg.save(update_fields=['is_read'])
        
        context['messages'] = messages_qs
        context['message_form'] = MessageForm()
        
        # Get the other participant's name
        other_participants = self.object.participants.exclude(id=self.request.user.id)
        if other_participants.exists():
            context['other_user'] = other_participants.first()
        
        return context

@require_http_methods(["POST"])
def send_message(request, pk):
    if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin'):
        return JsonResponse({'status': 'error', 'message': 'Admins cannot send messages.'}, status=403)
    
    room = get_object_or_404(Room, pk=pk, participants=request.user)
    form = MessageForm(request.POST)
    
    if form.is_valid():
        content = form.cleaned_data['content']
        message = Message.objects.create(
            room=room,
            sender=request.user,
            content=content
        )
        
        for participant in room.participants.exclude(id=request.user.id):
            Notification.objects.create(
                recipient=participant,
                notification_type='general',
                message=f'New message from {request.user.full_name} in chat.',
                related_object_id=message.id,
                related_model='chat.message'
            )
        
        return JsonResponse({
            'status': 'success',
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': request.user.username,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

def load_messages(request, pk):
    if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin'):
        return JsonResponse({'status': 'error', 'message': 'Admins cannot access chats.'}, status=403)
    
    room = get_object_or_404(Room, pk=pk, participants=request.user)
    messages = room.messages.all().values('id', 'content', 'sender__username', 'timestamp', 'is_read')
    return JsonResponse({'messages': list(messages)})

def get_or_create_room(request, other_user_id):
    # Block if current user is admin
    if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin'):
        messages.warning(request, 'Admins cannot participate in chats.')
        return redirect('accounts:home')
    
    # FIXED: Use User model instead of settings.AUTH_USER_MODEL string
    other_user = get_object_or_404(User, pk=other_user_id)
    
    # Block if other user is admin
    if other_user.is_superuser or (hasattr(other_user, 'role') and other_user.role == 'admin'):
        messages.warning(request, 'Cannot create chat with admin users.')
        return redirect('chat:room_list')
    
    # Find existing room with exactly these two participants
    existing_room = None
    for room in Room.objects.filter(participants=request.user):
        room_participants = list(room.participants.all())
        if len(room_participants) == 2 and other_user in room_participants:
            existing_room = room
            break
    
    if existing_room:
        messages.info(request, f'Continuing chat with {other_user.full_name}.')
        return redirect('chat:room_detail', pk=existing_room.pk)
    
    # Create new room
    room = Room.objects.create(
        name=f'{request.user.full_name} & {other_user.full_name}'
    )
    room.participants.add(request.user, other_user)
    messages.success(request, f'Chat started with {other_user.full_name}.')
    return redirect('chat:room_detail', pk=room.pk)
