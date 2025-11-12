from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.mail import send_mail
from .forms import *
from django.conf import settings
from django.views.generic import ListView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from host.models import *
from datetime import timedelta
from django.utils import timezone
from accounts.models import CustomUser

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser
    def handle_no_permission(self):
        messages.warning(self.request, 'You do not have permission to access this page.')
        return redirect('accounts:home')
    

class AdminEventListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Event
    template_name = 'adminpanel/event_list.html'
    context_object_name = 'events'
    paginate_by = 10

    def get_queryset(self):
        # Prefetch accepted proposals to avoid N+1 queries
        return (
            Event.objects.all()
            .prefetch_related('proposals')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # For convenience, attach each event's accepted proposal (if any)
        for event in context['events']:
            event.accepted_proposal = event.proposals.filter(status='accepted').first()
        return context



class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'adminpanel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        context['total_users'] = CustomUser.objects.count()
        context['total_hosts'] = CustomUser.objects.filter(role='host').count()
        context['total_guests'] = CustomUser.objects.filter(role='guest').count()
        context['total_planners'] = CustomUser.objects.filter(role='planner').count()
        context['pending_approvals'] = CustomUser.objects.filter(role__in=['guest', 'planner'], is_approved=False, is_active=False).count()
        context['recent_registrations'] = CustomUser.objects.filter(date_joined__gte=thirty_days_ago).count()
        # Placeholder for events/tickets (integrate later)
        context['total_events'] = Event.objects.count()

        return context

class PendingApprovalsView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'adminpanel/pending_approvals.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        return CustomUser.objects.filter(role__in=['guest', 'planner'], is_approved=False, is_active=False).order_by('-date_joined')

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'adminpanel/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        role = self.kwargs.get('role')
        if role in ['host', 'guest', 'planner']:
            return CustomUser.objects.filter(role=role).order_by('-date_joined')
        raise ValueError('Invalid role')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.kwargs.get('role', '').title()
        return context

def approve_user(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, role__in=['guest', 'planner'], is_approved=False)
    user.is_approved = True
    user.is_active = True
    user.save(update_fields=['is_approved', 'is_active'])
    send_mail(
        'EventApp Account Approved',
        'Your registration has been approved. You can now log in to the platform.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    messages.success(request, f'User "{user.username}" approved successfully.')
    return redirect(request.META.get('HTTP_REFERER', 'adminpanel:dashboard'))

def reject_user(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, role__in=['guest', 'planner'], is_approved=False)
    send_mail(
        'EventApp Account Rejected',
        'Your registration has been rejected. Please contact support for more details.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    user.delete()  # Or set is_active=False; here delete for simplicity
    messages.error(request, f'User "{user.username}" rejected and deleted.')
    return redirect(request.META.get('HTTP_REFERER', 'adminpanel:dashboard'))

class UserEditView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserEditForm
    template_name = 'adminpanel/user_edit.html'
    success_url = reverse_lazy('adminpanel:dashboard')

    def get_object(self):
        return get_object_or_404(CustomUser, pk=self.kwargs.get('pk'))

    def form_valid(self, form):
        messages.success(self.request, 'User updated successfully.')
        return super().form_valid(form)

class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'adminpanel/user_confirm_delete.html'
    success_url = reverse_lazy('adminpanel:dashboard')

    def get_object(self):
        return get_object_or_404(CustomUser, pk=self.kwargs.get('pk'))

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.error(request, f'User "{user.username}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

class ActivitiesView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'adminpanel/activities.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        context['recent_users'] = CustomUser.objects.filter(date_joined__gte=thirty_days_ago).order_by('-date_joined')[:10]
        context['pending_count'] = CustomUser.objects.filter(role__in=['guest', 'planner'], is_approved=False).count()
        # Placeholder: Recent events, tickets, etc.
        context['recent_events'] = []  # From events app
        return context