from django.urls import path
from . import views

app_name = 'planner'

urlpatterns = [
    path('', views.PlannerDashboardView.as_view(), name='dashboard'),
    path('available-events/', views.AvailableEventsView.as_view(), name='available_events'),
    path('events/<int:pk>/submit-proposal/', views.ProposalCreateView.as_view(), name='submit_proposal'),
    path('proposals/', views.ProposalListView.as_view(), name='proposal_list'),
    path('proposals/<int:pk>/edit/', views.ProposalUpdateView.as_view(), name='proposal_edit'),
    path('proposals/<int:pk>/delete/', views.ProposalDeleteView.as_view(), name='proposal_delete'),
    path('proposals/<int:pk>/', views.ProposalDetailView.as_view(), name='proposal_detail'),
]