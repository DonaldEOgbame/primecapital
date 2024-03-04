from django.urls import path
from . import views
from .views import CustomLoginView
from django.conf import settings
from django.conf.urls. static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change-password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('referrals/', views.referrals, name='referrals'),
    path('transactions/', views.transactions, name='transactions'),
    path('investors/', views.investors, name='investors'),
    path('leaders/', views.leaders, name='leaders'),
    path('customer-support/', views.customer, name='customer'),
    path('support/', views.support, name='support'),
    path('market/', views.market, name='market'),
    path('payment-details/', views.payment_details, name='payment_details'),
    path('request-withdrawal/', views.request_withdrawal, name='request-withdrawal'),
    path('select-package/', views.select_package, name='select-package'),
    path('submit-verification/', views.submit_verification, name='submit-verification'),
    path('api/verification-status/', views.verification_status, name='verification_status'),
    path('logout/', views.logout_view, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'),
         name='password_reset'),
    path('password_reset/sent/',
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
         name='password_reset_complete'),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

