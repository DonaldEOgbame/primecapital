from django.db import models
from django.conf import settings
import uuid
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    # Existing fields
    referral_code = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_verified = models.BooleanField(default=False, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = uuid.uuid4().hex[:8]  # Generate a unique referral code
        super().save(*args, **kwargs)

    def is_identity_verified(self):
        """
        Checks if the user's identity has been verified.
        Returns True if verified, False otherwise.
        """
        try:
            verification = IdentityVerification.objects.get(user=self)
            return verification.is_verified
        except IdentityVerification.DoesNotExist:
            return False


class InvestmentPackage(models.Model):
    name = models.CharField(max_length=100)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 15% as 15.00
    min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in hours")  # e.g., 12, 24, 48, 72
    currency = models.CharField(max_length=10, default='USDT')  # USDT as the only payment method

    def __str__(self):
        return self.name


class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
        ('completed', 'Completed')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USDT')
    to_address = models.CharField(max_length=42, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Withdrawal request by {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.to_address:
            user_profile, created = Profile.objects.get_or_create(user=self.user)
            self.to_address = user_profile.usdt_trc20_wallet_address

        if self.status == 'completed':
            user_balance, created = UserBalance.objects.get_or_create(user=self.user)
            if user_balance.balance < self.amount:
                raise ValueError("Withdrawal amount exceeds available balance")

        super().save(*args, **kwargs)

        if self.status == 'completed':
            update_user_balance(self.user, -self.amount)


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('earning', 'Earning'),
        ('referral', 'Referral Commission'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tx_hash = models.CharField(max_length=100, unique=True)
    currency = models.CharField(max_length=10, default='USDT')  # USDT as the only payment method
    status = models.CharField(max_length=20, default='pending')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)

    withdrawal_request = models.ForeignKey(WithdrawalRequest, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update user balance after saving the transaction
        if self.transaction_type == 'deposit':
            update_user_balance(self.user, self.amount)
        elif self.transaction_type == 'withdrawal':
            update_user_balance(self.user, -self.amount)  # Subtract withdrawal amount


class UserInvestment(models.Model):
    user = models.ForeignKey('investments.CustomUser', on_delete=models.CASCADE)
    package = models.ForeignKey(InvestmentPackage, on_delete=models.CASCADE)
    amount_invested = models.DecimalField(max_digits=10, decimal_places=2)
    investment_date = models.DateTimeField(auto_now_add=True)
    earnings_calculated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.package.name}"


class UserBalance(models.Model):
    user = models.OneToOneField('investments.CustomUser', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Balance"


class UserEarning(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    earning_date = models.DateTimeField(auto_now_add=True)
    from_investment = models.ForeignKey('UserInvestment', on_delete=models.CASCADE)

    def __str__(self):
        return f"Earning for {self.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update user balance after saving the earning
        update_user_balance(self.user, self.amount)


class ReferralCommission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commission for {self.user.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update user balance after saving the referral commission
        update_user_balance(self.user, self.amount)


class Referral(models.Model):
    referred_by = models.ForeignKey('investments.CustomUser', related_name='referrals_made', on_delete=models.CASCADE)
    referred_user = models.ForeignKey('investments.CustomUser', related_name='referred_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referred_user.username} referred by {self.referred_by.username}"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    usdt_erc20_wallet_address = models.CharField(max_length=42, blank=True)

    def __str__(self):
        return self.user.username


class IdentityVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ssn = models.CharField(max_length=11) # Modify based on your requirements
    zip_code = models.CharField(max_length=10)
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    state = models.CharField(max_length=50)
    document_type = models.CharField(max_length=50)
    document_front = models.ImageField(upload_to='identity_documents/front/')
    document_back = models.ImageField(upload_to='identity_documents/back/')
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


def update_user_balance(user, amount):
    try:
        balance = UserBalance.objects.get(user=user)
        balance.balance += amount
        balance.save()
    except UserBalance.DoesNotExist:
        UserBalance.objects.create(user=user, balance=amount)


class ProcessedTransaction(models.Model):
    tx_hash = models.CharField(max_length=100, unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tx_hash
