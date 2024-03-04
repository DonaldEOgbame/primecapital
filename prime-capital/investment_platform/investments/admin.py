from django.contrib import admin
from django.utils import timezone
from .models import InvestmentPackage, Transaction, UserInvestment, UserBalance, UserEarning, WithdrawalRequest, Referral, ReferralCommission, CustomUser
from .notifications import notify_user_of_withdrawal_request
from django.contrib.auth.admin import UserAdmin
from .models import IdentityVerification


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)


@admin.register(InvestmentPackage)
class InvestmentPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'interest_rate', 'min_amount', 'max_amount', 'duration', 'currency']
    list_filter = ['currency']
    search_fields = ['name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'status', 'transaction_type', 'transaction_date']
    list_filter = ['transaction_type', 'currency', 'status']
    search_fields = ['user__username', 'tx_hash']


@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'amount_invested', 'investment_date', 'earnings_calculated']
    list_filter = ['package']
    search_fields = ['user__username']


@admin.register(UserBalance)
class UserBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance']
    search_fields = ['user__username']


@admin.register(UserEarning)
class UserEarningAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'earning_date', 'from_investment']
    search_fields = ['user__username']


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'status', 'created_at', 'processed_at']
    list_filter = ['status', 'currency']
    search_fields = ['user__username']
    actions = ['approve_withdrawal', 'reject_withdrawal']

    def approve_withdrawal(self, request, queryset):
        for withdrawal in queryset.filter(status='pending'):
            withdrawal.status = 'approved'
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
            notify_user_of_withdrawal_request(withdrawal)

    def reject_withdrawal(self, request, queryset):
        for withdrawal in queryset.filter(status='pending'):
            withdrawal.status = 'rejected'
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
            notify_user_of_withdrawal_request(withdrawal)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referred_by', 'referred_user', 'created_at']
    search_fields = ['referred_by__username', 'referred_user__username']


@admin.register(ReferralCommission)
class ReferralCommissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'created_at']
    search_fields = ['user__username']


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'state', 'document_type', 'is_verified']
    actions = ['approve_verification', 'reject_verification']

    def approve_verification(self, request, queryset):
        queryset.update(is_verified=True)
    approve_verification.short_description = "Approve selected verifications"

    def reject_verification(self, request, queryset):
        queryset.update(is_verified=False)
    reject_verification.short_description = "Reject selected verifications"
