from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.core.mail import send_mail
from .forms import *
from django.conf import settings
from django.views.generic import ListView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from guest.models import Booking
from host.models import *
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from accounts.models import CustomUser
from utils.pagination import paginate_queryset  # your global paginator

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
    # remove/ignore paginate_by because we use the global paginate_queryset DEFAULT_PER_PAGE

    def get_queryset(self):
        # keep your original queryset logic intact
        return (
            Event.objects.all()
            .prefetch_related('proposals')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # get the *full* queryset, then paginate it using the shared helper
        full_qs = self.get_queryset()
        page_obj, page_list = paginate_queryset(self.request, full_qs)

        # Provide variables the pagination partial expects
        context['page_obj'] = page_obj
        context['paginator'] = page_obj.paginator
        context['is_paginated'] = page_obj.has_other_pages()

        # keep context_object_name 'events' pointing to the current page's objects
        context['events'] = page_list

        # current datetime (needed for end_date comparison)
        context['now'] = timezone.now()

        # attach accepted proposal for each event on the current page only
        for event in context['events']:
            event.accepted_proposal = event.proposals.filter(status='accepted').first()

        return context



def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)

    # block past events
    if event.end_date <= timezone.now():
        messages.error(request, "Past events cannot be deleted.")
        return redirect('adminpanel:event_list')

    event.delete()
    messages.success(request, f'Event "{event.name}" deleted successfully.')
    return redirect('adminpanel:event_list')





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

        context['pending_approvals'] = CustomUser.objects.filter(
            role__in=['guest', 'planner'],
            is_approved=False,
            is_active=False
        ).count()

        context['recent_registrations'] = CustomUser.objects.filter(
            date_joined__gte=thirty_days_ago
        ).count()

        context['total_events'] = Event.objects.count()

        # Total confirmed tickets
        context['total_tickets'] = Booking.objects.filter(
            status='confirmed'
        ).aggregate(total=Sum('ticket_quantity'))['total'] or 0

        return context

class TicketHistoryView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'adminpanel/ticket_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = Booking.objects.select_related(
            'guest', 'event'
        ).order_by('-created_at')

        # Apply global pagination
        page_obj, paginated_queryset = paginate_queryset(self.request, queryset)

        context['ticket_history'] = paginated_queryset
        context['page_obj'] = page_obj     # Required by your pagination template

        return context


class PendingApprovalsView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'adminpanel/pending_approvals.html'

    def get(self, request, *args, **kwargs):
        queryset = CustomUser.objects.filter(
            role__in=['guest', 'planner'],
            is_approved=False,
            is_active=False
        ).order_by('-date_joined')

        # Use your global pagination function
        page_obj, users = paginate_queryset(request, queryset)

        return render(request, self.template_name, {
            'users': users,
            'page_obj': page_obj,  # required by partial
        })


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'adminpanel/user_list.html'
    context_object_name = 'users'
    paginate_by = None  # disable Django's built-in paginator

    def get_queryset(self):
        role = self.kwargs.get('role')
        if role in ['host', 'guest', 'planner']:
            return CustomUser.objects.filter(role=role).order_by('-date_joined')
        raise ValueError('Invalid role')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = self.get_queryset()
        page_obj, users_page = paginate_queryset(self.request, queryset)

        context['users'] = users_page
        context['page_obj'] = page_obj
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