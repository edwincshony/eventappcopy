from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('pending-approvals/', views.PendingApprovalsView.as_view(), name='pending_approvals'),
    path('users/<str:role>/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/approve/', views.approve_user, name='approve_user'),
    path('users/<int:pk>/reject/', views.reject_user, name='reject_user'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('activities/', views.ActivitiesView.as_view(), name='activities'),
    # Placeholder for events
    # path('events/', views.EventListView.as_view(), name='event_list'),
]