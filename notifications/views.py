from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from .models import Notification

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 10

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unread_count = Notification.objects.filter(recipient=self.request.user, is_read=False).count()
        context['unread_count'] = unread_count
        return context

def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    messages.success(request, 'Notification marked as read.')
    return redirect('notifications:notification_list')

class NotificationDetailView(LoginRequiredMixin, DetailView):
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_read:
            self.object.is_read = True
            self.object.save(update_fields=['is_read'])
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)