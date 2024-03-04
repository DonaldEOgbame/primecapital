from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.contrib.auth import logout
import secrets
from django.core.mail import send_mail, message
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from .forms import IdentityVerificationForm
from .models import IdentityVerification
from .forms import (
    IdentityVerificationForm,
    CustomUserCreationForm,
    CustomPasswordChangeForm,
    WithdrawalRequestForm,
    CustomAuthenticationForm,
    ProfileForm
)
from .models import (
    IdentityVerification,
    CustomUser,
    Profile,
    UserBalance,
    Transaction,
    Referral,
    ReferralCommission,
    UserEarning,
    InvestmentPackage,
    WithdrawalRequest,
    UserInvestment
)
from .notifications import (
    notify_user_of_referral_commission,
    notify_user_of_transaction,
    notify_user_of_withdrawal_request,
    notify_user_no_package_match,
    send_acknowledgment_email,
    send_verification_status_email
)
from urllib.parse import urlencode


def index(request):
    """
    View for the home page (index.html).
    """
    return render(request, 'index.html')


def investors(request):
    """
    View for the investors page (investors.html).
    """
    return render(request, 'investors.html')


def leaders(request):
    """
    View for the Leaders page (Leaders.html).
    """
    return render(request, 'Leaders.html')


def support(request):
    """
    View for the support page (support.html).
    """
    return render(request, 'support.html')


def customer(request):
    """
    View for the customer support page (customer.html).
    """
    return render(request, 'customer.html')


def market(request):
    """
    View for the market page (market.html).
    """
    return render(request, 'market.html')


@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Save the user first before checking for referral code
            user.save()

            # Check and set referrer if available
            referral_code_from_session = request.session.get('referral_code')
            if referral_code_from_session:
                try:
                    referrer = CustomUser.objects.get(referral_code=referral_code_from_session)
                    user.referrer = referrer

                    # Create referral and commission objects
                    referral = Referral.objects.create(referred_by=referrer, referred_user=user)
                    ReferralCommission.objects.create(user=referrer, amount=10)

                    # Save the user after setting the referrer and creating related objects
                    user.save()

                except CustomUser.DoesNotExist:
                    pass

            # Redirect to login page after successful registration
            return redirect('login')
        else:
            # Display form errors if validation fails
            return render(request, 'registration.html', {'form': form})
    else:
        # Display registration form for GET requests
        form = CustomUserCreationForm()
        return render(request, 'registration.html', {'form': form})


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'login.html'


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
    }
    return render(request, 'profile.html', context)


@login_required
def payment_details(request):
    """
    View for the payment details page (payment_details.html).
    """
    return render(request, 'payment_details.html', {'settings': settings})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user

    try:
        user_balance = UserBalance.objects.get(user=user)
    except UserBalance.DoesNotExist:
        user_balance = UserBalance.objects.create(user=user)

    current_balance = user_balance.balance
    total_deposits = Transaction.objects.filter(user=user, transaction_type='deposit').aggregate(Sum('amount'))['amount__sum'] or 0
    total_withdrawals = Transaction.objects.filter(user=user, transaction_type='withdrawal').aggregate(Sum('amount'))['amount__sum'] or 0
    total_referral_commissions = ReferralCommission.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0
    latest_investment = UserInvestment.objects.filter(user=user).order_by('-investment_date').first()
    last_earning = UserEarning.objects.filter(user=user).order_by('-earning_date').first()

    context = {
        'current_balance': current_balance,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_referral_commissions': total_referral_commissions,
        'latest_investment': latest_investment,
        'last_earning': last_earning,
    }

    return render(request, 'dashboard.html', context)


@login_required
def referrals(request):
    user = request.user
    total_referrals = Referral.objects.filter(referred_by=user).count()
    active_referrals = Referral.objects.filter(referred_by=user, referred_user__userinvestment__isnull=False).distinct().count()

    context = {
        'total_referrals': total_referrals,
        'active_referrals': active_referrals,
    }
    return render(request, 'referrals.html', context)


@login_required
def transactions(request):
    user = request.user
    deposits = Transaction.objects.filter(user=user, transaction_type='deposit')
    earnings = UserEarning.objects.filter(user=user)
    withdrawals = WithdrawalRequest.objects.filter(user=user)

    context = {
        'deposits': deposits,
        'withdrawals': withdrawals,
        'earnings': earnings,
    }
    return render(request, 'transactions.html', context)




@login_required
def request_withdrawal(request):
    """
    View for the request withdrawal page (request_withdrawal.html).
    Handles both submission of new withdrawal requests and listing past requests.
    Verifies if the user's identity is verified before allowing a withdrawal request.
    """
    user = request.user

    try:
        if not user.is_identity_verified():
            return render(request, 'identity_verification_required.html')
    except IdentityVerification.DoesNotExist:
        return render(request, 'identity_verification_required.html')

    if request.method == 'POST':
        form = WithdrawalRequestForm(request.POST)
        if form.is_valid():
            withdrawal_request = form.save(commit=False)
            withdrawal_request.user = user
            withdrawal_request.save()
            return render(request, 'dashboard.html')
    else:
        # Instantiate the form with an instance of WithdrawalRequest
        withdrawal_request = WithdrawalRequest(user=user)
        form = WithdrawalRequestForm(instance=withdrawal_request)

    past_requests = WithdrawalRequest.objects.filter(user=user).order_by('-created_at')

    context = {
        'form': form,
        'past_requests': past_requests,
    }
    return render(request, 'request_withdrawal.html', context)


@login_required
def select_package(request):
    """
    View for the select_package page (select_package.html).
    Displays a list of investment packages from the InvestmentPackage model.
    """
    packages = InvestmentPackage.objects.all()

    context = {
        'packages': packages,
    }
    return render(request, 'select_package.html', context)


@login_required
def submit_verification(request):
    try:
        verification_instance = request.user.identityverification
    except IdentityVerification.DoesNotExist:
        verification_instance = None

    if request.method == 'POST':
        form = IdentityVerificationForm(request.POST, request.FILES, instance=verification_instance)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.save()

            send_acknowledgment_email(request.user.email)
            return redirect('profile')
    else:
        form = IdentityVerificationForm(instance=verification_instance)

    return render(request, 'submit_verification.html', {'form': form})


@login_required
def verification_status(request):
    try:
        verification = request.user.identity_verification
        status = True
    except IdentityVerification.DoesNotExist:
        status = False

    send_verification_status_email(request.user, status)

    return JsonResponse({"status": status, "message": message})


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)


def logout_view(request):
    logout(request)
    return redirect(reverse('login'))
