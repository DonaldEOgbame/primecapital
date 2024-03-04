import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'investment_platform.settings')
django.setup()

import requests
from decimal import Decimal
from django.conf import settings
from investments.models import Transaction, UserInvestment, CustomUser, update_user_balance, InvestmentPackage, \
    ProcessedTransaction
from django.utils import timezone
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Constants
USDT_DIVISOR = Decimal(1e6)  # USDT decimals divisor


def fetch_usdt_transactions(address):
    """Fetch USDT transactions from Etherscan API."""
    try:
        api_url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}&contractaddress={settings.USDT_CONTRACT_ADDRESS}&page=1&offset=1000&sort=desc&apikey={settings.ETHERSCAN_API_KEY}"
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json().get('result', [])
    except requests.RequestException as e:
        logger.error(f"Error fetching USDT transactions from Etherscan: {e}")
        return []


def process_usdt_transactions(transactions, required_confirmations):
    """Process USDT transactions."""
    for tx in transactions:
        tx_hash = tx.get('hash')
        confirmations = int(tx.get('confirmations', 0))
        if confirmations >= required_confirmations:
            if not ProcessedTransaction.objects.filter(tx_hash=tx_hash).exists():
                amount = Decimal(tx.get('value', 0)) / USDT_DIVISOR
                sender_address = tx.get('from')  # Get sender's address
                user = CustomUser.objects.filter(usdt_erc20_wallet_address=sender_address).first()
                if user:
                    transaction_instance = create_transaction_instance(user, amount, tx_hash)
                    if transaction_instance:
                        create_user_investment(user, amount, transaction_instance)
            else:
                logger.info(f"Skipping transaction {tx_hash} as it has already been processed.")
        else:
            logger.info(f"USDT transaction {tx_hash} has not reached required confirmations.")


def create_transaction_instance(user, amount, tx_hash):
    """Create an instance of the Transaction model."""
    try:
        return Transaction.objects.create(
            user=user,
            amount=amount,
            currency='USDT',
            status='confirmed',
            transaction_type='deposit',
            tx_hash=tx_hash
        )
    except Exception as e:
        logger.error(f"Error creating transaction instance for {tx_hash}: {e}")
        return None


def create_user_investment(user, amount, transaction_instance):
    """Create an instance of the UserInvestment model."""
    package = match_transaction_to_package(amount)
    if package:
        try:
            return UserInvestment.objects.create(
                user=user,
                package=package,
                amount_invested=amount,
                investment_date=timezone.now(),
                earnings_calculated=False,
                transaction=transaction_instance
            )
        except Exception as e:
            logger.error(f"Error creating UserInvestment instance for user {user.username}: {e}")
    else:
        logger.warning(f"No investment package found for the transaction amount: {amount}")


def match_transaction_to_package(amount):
    """Match transaction to investment package."""
    try:
        return InvestmentPackage.objects.filter(
            min_amount__lte=amount,
            max_amount__gte=amount,
            currency='USDT'
        ).first()
    except Exception as e:
        logger.error(f"Error matching transaction to package: {e}")
        return None


def calculate_user_earnings():
    """
    Calculate earnings for user investments when they reach maturity and update user balances accordingly.
    """
    user_investments = UserInvestment.objects.filter(earnings_calculated=False)

    for investment in user_investments:
        maturity_date = investment.investment_date + timezone.timedelta(hours=investment.package.duration)
        current_date = timezone.now()
        if current_date >= maturity_date:
            interest_rate = investment.package.interest_rate / 100
            earnings = investment.amount_invested * interest_rate
            update_user_balance(investment.user, earnings)
            investment.earnings_calculated = True
            investment.save()


def main():
    """Main function."""
    transactions = fetch_usdt_transactions(settings.USDT_WALLET_ADDRESS)
    if transactions:
        process_usdt_transactions(transactions, required_confirmations=25)
        calculate_user_earnings()


if __name__ == "__main__":
    main()
