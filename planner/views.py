from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.utils import timezone
from .forms import ProposalForm
from django.db.models import Q
from host.models import Event, Proposal
from utils.pagination import paginate_queryset  # your global paginator


class PlannerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'planner' and self.request.user.is_approved
    def handle_no_permission(self):
        messages.warning(self.request, 'You must be a logged-in and approved Planner to access this page.')
        return redirect('home')

class PlannerDashboardView(LoginRequiredMixin, PlannerRequiredMixin, ListView):
    model = Proposal
    template_name = 'planner/dashboard.html'
    context_object_name = 'proposals'

    def get_queryset(self):
        return Proposal.objects.filter(planner=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Count of all future events that do NOT have an accepted proposal yet
        open_events = Event.objects.filter(
            start_date__gt=timezone.now()
        ).exclude(
            proposals__status='accepted'
        ).distinct().count()
        context['open_events_count'] = open_events
        return context

class AvailableEventsView(LoginRequiredMixin, PlannerRequiredMixin, ListView):
    model = Event
    template_name = 'planner/available_events.html'
    context_object_name = 'events'
    paginate_by = 6

    def get_queryset(self):
        # Open future events without accepted proposal
        return Event.objects.filter(
            start_date__gt=timezone.now()
        ).exclude(
            proposals__status='accepted'
        ).distinct().order_by('start_date')

class ProposalCreateView(LoginRequiredMixin, PlannerRequiredMixin, CreateView):
    model = Proposal
    form_class = ProposalForm
    template_name = 'planner/proposal_form.html'

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
        form.instance.planner = self.request.user
        form.instance.event = event
        form.instance.status = 'pending'
        messages.success(self.request, 'Proposal submitted successfully! Await host review.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('planner:proposal_list')

class ProposalListView(LoginRequiredMixin, PlannerRequiredMixin, ListView):
    model = Proposal
    template_name = 'planner/proposal_list.html'
    context_object_name = 'proposals'

    def get_queryset(self):
        return Proposal.objects.filter(planner=self.request.user).order_by('-created_at')

class ProposalUpdateView(LoginRequiredMixin, PlannerRequiredMixin, UpdateView):
    model = Proposal
    form_class = ProposalForm
    template_name = 'planner/proposal_form.html'

    def get_queryset(self):
        return Proposal.objects.filter(planner=self.request.user, status='pending')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.object.event
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Proposal updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('planner:proposal_list')

class ProposalDeleteView(LoginRequiredMixin, PlannerRequiredMixin, DeleteView):
    model = Proposal
    template_name = 'planner/proposal_confirm_delete.html'
    success_url = reverse_lazy('planner:proposal_list')

    def get_queryset(self):
        return Proposal.objects.filter(planner=self.request.user, status='pending')

    def delete(self, request, *args, **kwargs):
        messages.error(request, 'Proposal deleted successfully.')
        return super().delete(request, *args, **kwargs)

class ProposalDetailView(LoginRequiredMixin, PlannerRequiredMixin, DetailView):
    model = Proposal
    template_name = 'planner/proposal_detail.html'
    context_object_name = 'proposal'

    def get_queryset(self):
        return Proposal.objects.filter(planner=self.request.user)