from django.urls import path
from . import views


app_name = 'host'

urlpatterns = [
    path('', views.HostDashboardView.as_view(), name='dashboard'),
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('events/add/', views.EventCreateView.as_view(), name='event_add'),
    path('events/<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_edit'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('guests/', views.GuestListView.as_view(), name='guest_list'),
    path('planners/', views.PlannerListView.as_view(), name='planner_list'),
    path('proposals/', views.ProposalsView.as_view(), name='proposals'),
    path('proposals/<int:pk>/accept/', views.accept_proposal, name='accept_proposal'),
    path('qr-scanner/', views.QRScannerView.as_view(), name='qr_scanner'),
    path('verify-qr/', views.verify_qr_code, name='verify_qr'),
]