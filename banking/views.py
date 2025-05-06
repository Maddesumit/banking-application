from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserProfileForm
from .models import Account, Transaction
from decimal import Decimal
from django.contrib.admin.views.decorators import staff_member_required

def home(request):
    return render(request, 'banking/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'banking/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        profile_form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'banking/profile.html', {'profile_form': profile_form})

@login_required
def dashboard(request):
    # Get all accounts for the logged-in user
    accounts = Account.objects.filter(owner=request.user)
    
    # Calculate total balance across all accounts
    total_balance = sum(account.balance for account in accounts)
    
    # Get recent transactions (limit to 5)
    recent_transactions = Transaction.objects.filter(
        account__owner=request.user
    ).order_by('-timestamp')[:5]
    
    context = {
        'accounts': accounts,
        'total_balance': total_balance,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'banking/dashboard.html', context)

@login_required
def account_detail(request, account_id):
    # Get the account, ensuring it belongs to the logged-in user
    account = get_object_or_404(Account, id=account_id, owner=request.user)
    
    # Get transactions for this account
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')
    
    context = {
        'account': account,
        'transactions': transactions,
    }
    
    return render(request, 'banking/account_detail.html', context)

@login_required
def create_account(request):
    if request.method == 'POST':
        account_type = request.POST.get('account_type')
        if account_type in [choice[0] for choice in Account.ACCOUNT_TYPES]:
            account = Account.objects.create(
                owner=request.user,
                account_type=account_type,
                balance=0.00
            )
            messages.success(request, f'Your new {account.get_account_type_display()} has been created!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid account type selected.')
    
    return render(request, 'banking/create_account.html', {'account_types': Account.ACCOUNT_TYPES})

@login_required
def transaction_history(request):
    # Get all accounts for the logged-in user
    accounts = Account.objects.filter(owner=request.user)
    
    # Get filter parameters from request
    account_id = request.GET.get('account')
    transaction_type = request.GET.get('type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Start with all transactions for the user's accounts
    transactions = Transaction.objects.filter(account__owner=request.user)
    
    # Apply filters if provided
    if account_id:
        transactions = transactions.filter(account_id=account_id)
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if date_from:
        transactions = transactions.filter(timestamp__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(timestamp__lte=date_to)
    
    # Order by timestamp (newest first)
    transactions = transactions.order_by('-timestamp')
    
    context = {
        'transactions': transactions,
        'accounts': accounts,
        'transaction_types': Transaction.TRANSACTION_TYPES,
        'selected_account': account_id,
        'selected_type': transaction_type,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'banking/transaction_history.html', context)

@login_required
def deposit(request, account_id):
    account = get_object_or_404(Account, id=account_id, owner=request.user)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Amount must be positive.')
            else:
                account.deposit(amount)
                messages.success(request, f'${amount} has been deposited to your account.')
                return redirect('account_detail', account_id=account.id)
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount.')
    
    return render(request, 'banking/deposit.html', {'account': account})

@login_required
def withdraw(request, account_id):
    account = get_object_or_404(Account, id=account_id, owner=request.user)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Amount must be positive.')
            elif amount > account.balance:
                messages.error(request, 'Insufficient funds.')
            else:
                account.withdraw(amount)
                messages.success(request, f'${amount} has been withdrawn from your account.')
                return redirect('account_detail', account_id=account.id)
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount.')
    
    return render(request, 'banking/withdraw.html', {'account': account})

@login_required
def transfer(request):
    # Get all accounts for the logged-in user
    accounts = Account.objects.filter(owner=request.user)
    
    # Get the from_account from query parameter if provided
    from_account_id = request.GET.get('from_account')
    from_account = None
    if from_account_id:
        try:
            from_account = Account.objects.get(id=from_account_id, owner=request.user)
        except Account.DoesNotExist:
            pass
    
    if request.method == 'POST':
        from_account_id = request.POST.get('from_account')
        to_account_number = request.POST.get('to_account_number')  # Changed to accept account number
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')  # Optional description field
        
        try:
            from_account = Account.objects.get(id=from_account_id, owner=request.user)
            # Find the destination account by account number instead of ID
            to_account = Account.objects.get(account_number=to_account_number)
            amount = Decimal(amount)
            
            if from_account.account_number == to_account.account_number:
                messages.error(request, 'Cannot transfer to the same account.')
            elif amount <= 0:
                messages.error(request, 'Amount must be positive.')
            elif amount > from_account.balance:
                messages.error(request, 'Insufficient funds.')
            else:
                # Withdraw from source account
                from_account.balance -= amount
                from_account.save()
                
                # Deposit to destination account
                to_account.balance += amount
                to_account.save()
                
                # Create a transfer transaction record
                Transaction.objects.create(
                    account=from_account,
                    amount=amount,
                    transaction_type='TRANSFER',
                    description=description or f"Transfer to account {to_account.account_number}",
                    sender=from_account,
                    receiver=to_account
                )
                
                # Create a corresponding record for the receiving account
                Transaction.objects.create(
                    account=to_account,
                    amount=amount,
                    transaction_type='DEPOSIT',
                    description=description or f"Transfer from account {from_account.account_number}",
                    sender=from_account,
                    receiver=to_account
                )
                
                messages.success(request, f'₹{amount} has been transferred successfully to {to_account.account_number}.')
                return redirect('dashboard')
        except Account.DoesNotExist:
            messages.error(request, 'Account not found. Please check the account number.')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid transfer details.')
    
    context = {
        'accounts': accounts,
        'from_account': from_account,
    }
    
    return render(request, 'banking/transfer.html', context)


from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_topup(request):
    if request.method == 'POST':
        account_number = request.POST.get('account_number')
        amount = request.POST.get('amount')
        description = request.POST.get('description', 'System top-up')
        
        try:
            account = Account.objects.get(account_number=account_number)
            amount = Decimal(amount)
            
            if amount <= 0:
                messages.error(request, 'Amount must be positive.')
            else:
                # Update account balance
                account.balance += amount
                account.save()
                
                # Create a transaction record
                Transaction.objects.create(
                    account=account,
                    amount=amount,
                    transaction_type='DEPOSIT',
                    description=description or "System top-up",
                    sender=None,  # No sender for system top-ups
                    receiver=account
                )
                
                messages.success(request, f'₹{amount} has been added to account {account_number} successfully.')
                return redirect('admin_topup')
        except Account.DoesNotExist:
            messages.error(request, 'Account not found. Please check the account number.')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount.')
    
    # Get all accounts for the admin view
    accounts = Account.objects.all().order_by('owner__username', 'account_number')
    
    context = {
        'accounts': accounts,
    }
    
    return render(request, 'banking/admin_topup.html', context)
