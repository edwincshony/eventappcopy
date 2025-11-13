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
        return Event.objects.filter(host=self.request.user)

class EventCreateView(LoginRequiredMixin, HostRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'host/event_form.html'
    success_url = reverse_lazy('host:event_list')

    def form_valid(self, form):
        form.instance.host = self.request.user
        messages.success(self.request, 'Event created successfully! Invite planners to bid.')
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
    template_name = 'host/event_details.html'  # Optional; add if needed

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        needs = self.object.needs
        context["needs_list"] = needs.split(",") if needs else []
        return context

class GuestListView(LoginRequiredMixin, HostRequiredMixin, ListView):
    model = CustomUser
    template_name = 'host/guest_list.html'
    context_object_name = 'guests'
    paginate_by = 10

    def get_queryset(self):
        return CustomUser.objects.filter(role='guest', is_approved=True).order_by('full_name')

class PlannerListView(LoginRequiredMixin, HostRequiredMixin, ListView):
    model = CustomUser
    template_name = 'host/planner_list.html'
    context_object_name = 'planners'
    paginate_by = 10

    def get_queryset(self):
        return CustomUser.objects.filter(role='planner', is_approved=True).order_by('full_name')

class ProposalsView(LoginRequiredMixin, HostRequiredMixin, ListView):
    model = Proposal
    template_name = 'host/proposals.html'
    context_object_name = 'proposals'
    paginate_by = 10

    def get_queryset(self):
        return Proposal.objects.filter(event__host=self.request.user).order_by('-created_at')

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


@csrf_exempt
def verify_qr_code(request):
    """POST endpoint to verify QR codes scanned by camera."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
    
    data = request.POST.get('qrdata')
    
    if not data:
        return JsonResponse({'success': False, 'message': 'No QR data received'}, status=400)
    
    try:
        booking = Booking.objects.get(booking_id=data)
    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid or unknown QR code'}, status=404)
    
    # Check if host owns this event
    if booking.event.host != request.user:
        return JsonResponse({'success': False, 'message': 'You are not authorized for this event'}, status=403)
    
    # Check if already used
    if booking.is_used:
        return JsonResponse({
            'success': False,
            'already_used': True,
            'message': f'❌ Ticket already used',
            'guest': booking.guest.fullname,
            'event': booking.event.name,
            'tickets': booking.ticket_quantity,
            'scanned_at': booking.scanned_at.strftime('%Y-%m-%d %H:%M:%S'),
            'booking_id': str(booking.booking_id)
        })
    
    # Mark as used
    booking.mark_as_used()
    
    return JsonResponse({
        'success': True,
        'already_used': False,
        'guest': booking.guest.fullname,
        'event': booking.event.name,
        'tickets': booking.ticket_quantity,
        'message': '✅ Entry confirmed. Ticket marked as used.',
        'scanned_at': booking.scanned_at.strftime('%Y-%m-%d %H:%M:%S')
    })


