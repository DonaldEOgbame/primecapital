from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_email(subject, message, recipient):
    """
    Sends an email with the given subject and message to the specified recipient.
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])


def notify_user_of_transaction(user, transaction):
    """
    Notifies a user of a transaction.
    """
    subject = 'Transaction Notification'
    context = {'user': user, 'transaction': transaction}
    message = render_to_string('transaction_notification.html', context)
    send_email(subject, message, [user.email])


def notify_user_of_withdrawal_request(withdrawal):
    """
    Notifies a user of a withdrawal request update.
    """
    subject = 'Withdrawal Request Update'
    context = {'withdrawal': withdrawal}
    message = render_to_string('withdrawal_request_update.html', context)
    send_email(subject, message, [withdrawal.user.email])


def notify_user_of_referral_commission(user, commission):
    """
    Notifies a user of a referral commission earned.
    """
    subject = 'Referral Commission Earned'
    context = {'user': user, 'commission': commission}
    message = render_to_string('referral_commission_earned.html', context)
    send_email(subject, message, [user.email])


def notify_user_no_package_match(user, amount, currency):
    """
    Notifies a user of no available investment package.
    """
    subject = 'No Investment Package Available'
    context = {'user': user, 'amount': amount, 'currency': currency}
    message = render_to_string('no_package_available.html', context)
    send_email(subject, message, [user.email])


def send_acknowledgment_email(user_email):
    """
    Sends an acknowledgment email for a verification request.
    """
    subject = 'Verification Request Acknowledgment'
    message = render_to_string('acknowledgement_email.html')
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user_email])


def send_verification_status_email(user_email, status):
    """
    Sends an email with the verification status update.
    """
    subject = 'Verification Status Update'
    context = {'status': status}
    message = render_to_string('verification_status_email.html', context)
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user_email])
