from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.db import models
from django.utils import timezone
from .models import Booking
from .forms import BookingForm, PaymentForm
from host.models import Event, Proposal
from utils.pagination import paginate_queryset  # your global paginator


class GuestRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (self.request.user.is_authenticated and 
                self.request.user.role == 'guest' and 
                self.request.user.is_approved)

    def handle_no_permission(self):
        messages.warning(self.request, 'You must be a logged-in and approved Guest to access this page.')
        return redirect('accounts:home')

class GuestDashboardView(LoginRequiredMixin, GuestRequiredMixin, ListView):
    model = Event
    template_name = 'guest/dashboard.html'
    context_object_name = 'events'
    paginate_by = 6

    def get_queryset(self):
        confirmed_events = Event.objects.filter(
            proposals__status='accepted',
            start_date__gt=timezone.now()
        ).distinct()
        return confirmed_events

class EventDetailView(LoginRequiredMixin, GuestRequiredMixin, DetailView):
    model = Event
    template_name = 'guest/event_detail.html'
    context_object_name = 'event'

    def get_queryset(self):
        return Event.objects.filter(
            proposals__status='accepted',
            start_date__gt=timezone.now()
        ).distinct()

class BookingCreateView(LoginRequiredMixin, GuestRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'guest/booking_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['event'] = get_object_or_404(Event, pk=self.kwargs['pk'])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = get_object_or_404(Event, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        event = get_object_or_404(Event, pk=self.kwargs['pk'])
        
        confirmed_bookings = Booking.objects.filter(event=event, status='confirmed')
        total_booked = confirmed_bookings.aggregate(models.Sum('ticket_quantity'))['ticket_quantity__sum'] or 0
        remaining = event.guest_count - total_booked

        if remaining <= 0:
            messages.warning(self.request, f"Bookings for '{event.name}' are full.")
            return redirect('guest:dashboard')

        if form.instance.ticket_quantity > remaining:
            messages.warning(self.request, f"Only {remaining} tickets left for '{event.name}'. Please adjust your quantity.")
            return redirect('guest:book_event', pk=event.pk)


        form.instance.guest = self.request.user
        form.instance.event = event
        form.instance.total_amount = (event.budget / event.guest_count) * form.instance.ticket_quantity
        self.object = form.save()
        messages.success(self.request, 'Booking confirmed! Proceed to payment.')
        return redirect('guest:payment_simulation', booking_id=self.object.booking_id)


class PaymentSimulationView(LoginRequiredMixin, GuestRequiredMixin, TemplateView):
    template_name = 'guest/payment_simulation.html'

    def get_context_data(self, **kwargs):
        booking_id = self.kwargs['booking_id']
        booking = get_object_or_404(Booking, booking_id=booking_id, guest=self.request.user)
        context = super().get_context_data(**kwargs)
        context['booking'] = booking
        context['payment_form'] = PaymentForm()
        context['amount'] = booking.total_amount
        return context

    def post(self, request, *args, **kwargs):
        booking_id = self.kwargs['booking_id']
        booking = get_object_or_404(Booking, booking_id=booking_id, guest=request.user)
        payment_form = PaymentForm(request.POST)
        
        if payment_form.is_valid():
            # FIXED: Generate actual QR code
            booking.generate_qr_code()
            booking.save()
            
            messages.success(request, 'Payment successful! E-ticket generated.')
            return redirect('guest:eticket', booking_id=booking.booking_id)
        else:
            context = self.get_context_data(**kwargs)
            context['payment_form'] = payment_form
            return render(request, self.template_name, context)


class BookingListView(LoginRequiredMixin, GuestRequiredMixin, ListView):
    model = Booking
    template_name = 'guest/booking_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(guest=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        page_obj, paginated_bookings = paginate_queryset(self.request, queryset)
        context['bookings'] = paginated_bookings
        context['page_obj'] = page_obj  # for pagination controls
        return context

def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, guest=request.user, status='confirmed')
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Booking cancelled. Refund processed (simulated).')
        return redirect('guest:booking_list')
    return render(request, 'guest/booking_confirm_cancel.html', {'booking': booking})

# FIXED: ETicketView with proper UUID field handling
class ETicketView(LoginRequiredMixin, GuestRequiredMixin, DetailView):
    model = Booking
    template_name = 'guest/eticket.html'
    context_object_name = 'booking'
    slug_field = 'booking_id'
    slug_url_kwarg = 'booking_id'

    def get_queryset(self):
        return Booking.objects.filter(guest=self.request.user)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Optional: Make downloadable PDF (placeholder HTML printable)
        return response



    # For download: Add PDF response if reportlab
    # def render_to_response(self, context, **response_kwargs):
    #     response = HttpResponse(content_type='application/pdf')
    #     p = canvas.Canvas(response)
    #     p.drawString(100, 100, f"Booking ID: {self.object.booking_id}")
    #     p.save()
    #     response['Content-Disposition'] = f'attachment; filename="eticket_{self.object.booking_id}.pdf"'
    #     return response