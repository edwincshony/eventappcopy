from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('add-host/', views.AddHostView.as_view(), name='add_host'),  # Admin-only
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', views.CustomPasswordChangeView.as_view(), name='password_change_done'),  # Redirects
    path('password/reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]