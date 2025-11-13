from django.urls import path
from . import views

app_name = 'guest'

urlpatterns = [
    path('', views.GuestDashboardView.as_view(), name='dashboard'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('events/<int:pk>/book/', views.BookingCreateView.as_view(), name='book_event'),
    path('payment/<uuid:booking_id>/', views.PaymentSimulationView.as_view(), name='payment_simulation'),
    path('bookings/', views.BookingListView.as_view(), name='booking_list'),
    path('bookings/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'), 
    path('eticket/<uuid:booking_id>/', views.ETicketView.as_view(), name='eticket'),
    path('events/', views.EventListView.as_view(), name='event_list'),

]