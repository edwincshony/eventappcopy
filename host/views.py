from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Event, Proposal
from .forms import EventForm, ProposalAcceptForm
from accounts.models import CustomUser
from utils.pagination import paginate_queryset  # your global paginator


class HostRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'host'
    def handle_no_permission(self):
        messages.warning(self.request, 'You must be a logged-in Host to access this page.')
        return redirect('accounts:home')



class HostDashboardView(LoginRequiredMixin, HostRequiredMixin, ListView):
    model = Event
    template_name = 'host/dashboard.html'
    context_object_name = 'events'

    def get_queryset(self):
        return Event.objects.filter(host=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_guests'] = CustomUser.objects.filter(role='guest', is_approved=True).count()
        context['total_planners'] = CustomUser.objects.filter(role='planner', is_approved=True).count()
        context['pending_proposals'] = Proposal.objects.filter(event__host=self.request.user, status='pending').count()
        return context

class EventListView(LoginRequiredMixin, HostRequiredMixin, ListView):
    model = Event
    template_name = 'host/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        # Only show events hosted by current user
        return Event.objects.filter(host=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        # Apply global pagination
        page_obj, paginated_events = paginate_queryset(self.request, queryset)
        context['page_obj'] = page_obj
        context['events'] = paginated_events  # override context_object_name with paginated data

        return context

class EventCreateView(LoginRequiredMixin, HostRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'host/event_form.html'
    success_url = reverse_lazy('host:event_list')

    def form_valid(self, form):
        form.instance.host = self.request.user
        messages.success(self.request, 'Event created successfully!')
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, HostRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'host/event_form.html'
    success_url = reverse_lazy('host:event_list')

    def get_queryset(self):
        return Event.objects.filter(host=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Event updated successfully.')
        return super().form_valid(form)


from django.views.decorators.http import require_POST

@require_POST
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk, host=request.user)
    event.delete()
    messages.error(request, 'Event deleted successfully.')
    return redirect('host:event_list')


class EventDetailView(LoginRequiredMixin, HostRequiredMixin, DetailView):
    model = Event
    template_name = 'host/event_details.html'

    def get_queryset(self):
        return Event.objects.filter(host=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        needs = self.object.needs
        context["needs_list"] = needs.split(",") if needs else []
        
        # Get all confirmed bookings for this event
        bookings = Booking.objects.filter(
            event=self.object,
            status='confirmed'
        ).select_related('guest').order_by('-created_at')
        
        context['bookings'] = bookings
        context['total_registered'] = bookings.count()
        context['total_tickets_sold'] = sum(booking.ticket_quantity for booking in bookings)
        context['total_revenue'] = sum(booking.total_amount for booking in bookings)
        
        return context

class GuestListView(LoginRequiredMixin, HostRequiredMixin, ListView):
    model = CustomUser
    template_name = 'host/guest_list.html'
    context_object_name = 'guests'
    # remove paginate_by here because we're using custom pagination

    def get_queryset(self):
        return CustomUser.objects.filter(role='guest', is_approved=True).order_by('full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        page_obj, guests = paginate_queryset(self.request, queryset)
        context['page_obj'] = page_obj
        context['guests'] = guests  # override context_object_name with paginated list
        return context

class PlannerListView(LoginRequiredMixin, HostRequiredMixin, ListView):
    model = CustomUser
    template_name = 'host/planner_list.html'
    context_object_name = 'planners'
    # remove paginate_by to use custom pagination

    def get_queryset(self):
        return CustomUser.objects.filter(role='planner', is_approved=True).order_by('full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        page_obj, planners = paginate_queryset(self.request, queryset)
        context['page_obj'] = page_obj
        context['planners'] = planners  # override the context_object_name with paginated list
        return context

class ProposalsView(LoginRequiredMixin, HostRequiredMixin, ListView):
    model = Proposal
    template_name = 'host/proposals.html'
    context_object_name = 'proposals'

    def get_queryset(self):
        # Only proposals for events hosted by the current user
        return Proposal.objects.filter(event__host=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        # Apply global pagination
        page_obj, paginated_proposals = paginate_queryset(self.request, queryset)
        context['page_obj'] = page_obj
        context['proposals'] = paginated_proposals  # override context_object_name with paginated results

        return context

from django.utils.http import urlencode

def accept_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk, event__host=request.user)
    status = request.GET.get('status', 'accepted')  # Default to accepted

    if proposal.status != 'pending':  # Prevent re-approving
        messages.warning(request, 'This proposal has already been processed.')
        return redirect('host:proposals')

    if status == 'accepted':
        proposal.status = 'accepted'
        messages.success(request, f'Proposal for "{proposal.event.name}" has been accepted.')
    elif status == 'rejected':
        proposal.status = 'rejected'
        messages.error(request, f'Proposal for "{proposal.event.name}" has been rejected.')
    else:
        messages.warning(request, 'Invalid status.')
        return redirect('host:proposals')

    proposal.save()
    # Optionally: send notification/email to planner here
    return redirect('host:proposals')

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from guest.models import Booking  # Adjust import path if needed

from django.views.generic import TemplateView

class QRScannerView(LoginRequiredMixin, HostRequiredMixin, TemplateView):
    template_name = 'host/qr_scanner.html'


from django.contrib.auth.decorators import login_required

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
import json

@csrf_exempt
@require_POST
def verify_qr_code(request):
    """POST endpoint to verify QR codes scanned by camera."""
    
    try:
        # Check authentication
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)
        
        # Check if user is a host
        if request.user.role != 'host':
            return JsonResponse({
                'success': False,
                'message': 'Only hosts can verify tickets'
            }, status=403)
        
        # Get QR data
        data = request.POST.get('qrdata')
        
        if not data:
            return JsonResponse({
                'success': False,
                'message': 'No QR data received'
            }, status=400)
        
        from guest.models import Booking
        
        # Find booking
        try:
            booking = Booking.objects.select_related('guest', 'event').get(booking_id=data)
        except Booking.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or unknown QR code'
            }, status=200)
        
        # Check if host owns this event
        if booking.event.host != request.user:
            return JsonResponse({
                'success': False,
                'message': 'You are not authorized for this event'
            }, status=200)
        
        # If already used
        if booking.is_used:
            local_time = timezone.localtime(booking.scanned_at)
            return JsonResponse({
                'success': False,
                'already_used': True,
                'message': '❌ Ticket already used',
                'guest': booking.guest.full_name,
                'event': booking.event.name,
                'tickets': booking.ticket_quantity,
                'scanned_at': local_time.strftime('%Y-%m-%d %H:%M:%S'),
                'booking_id': str(booking.booking_id)
            }, status=200)
        
        # Mark as used
        booking.is_used = True
        booking.scanned_at = timezone.now()
        booking.save(update_fields=['is_used', 'scanned_at'])

        local_time = timezone.localtime(booking.scanned_at)
        
        return JsonResponse({
            'success': True,
            'already_used': False,
            'guest': booking.guest.full_name,
            'event': booking.event.name,
            'tickets': booking.ticket_quantity,
            'message': '✅ Entry confirmed. Ticket marked as used.',
            'scanned_at': local_time.strftime('%Y-%m-%d %H:%M:%S')
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=200)
