from django.conf.urls import include
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from accounts import views

app_name = 'accounts'
urlpatterns = [
    path('', views.user_account, name='account'),
    path('account-detail/<uuid:account_uuid>/', views.account_details, name='account-detail'),
    path('email-validation/<uuid:account_uuid>/<str:token>/', views.email_validation, name='email-validation'),
    path('send-validation/<uuid:account_uuid>/', views.send_validation, name='send-validation'),
    path('update/<uuid:account_uuid>/', views.account_update, name='update'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('password-change/', views.password_change_views, name='password-change'),
    path('password-change-done/', views.password_change_done_views, name='password-change-done'),
    path('password-reset/', auth_views.PasswordResetView.as_view(success_url=reverse_lazy('accounts:password-reset-done')), name='password-reset'),
    path('password-reset-done/', auth_views.PasswordResetDoneView.as_view(), name='password-reset-done'),
    path('register/', views.register, name='register'),
    path('registration-complete/<uuid:account_uuid>/', views.registration_complete, name='registration-complete'),
    path('registration-complete/', views.registration_complete, name='registration-complete'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('accounts:password-reset-complete')), name='password-reset-confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password-reset-complete'),
]
