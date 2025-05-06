from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from django.utils import timezone

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    id_verification = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create or update user profile when user is created or updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()

# Account model for banking functionality
class Account(models.Model):
    ACCOUNT_TYPES = (
        ('SAVINGS', 'Savings Account'),
        ('CHECKING', 'Checking Account'),
        ('FIXED', 'Fixed Deposit Account'),
    )
    
    account_number = models.CharField(max_length=20, unique=True, editable=False)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    creation_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.account_type} - {self.account_number}"
    
    def save(self, *args, **kwargs):
        # Generate a unique account number if not already set
        if not self.account_number:
            self.account_number = f"ACC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.save()
            # Create a transaction record
            Transaction.objects.create(
                account=self,
                amount=amount,
                transaction_type='DEPOSIT',
                description=f"Deposit to account {self.account_number}"
            )
            return True
        return False
    
    def withdraw(self, amount):
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            self.save()
            # Create a transaction record
            Transaction.objects.create(
                account=self,
                amount=amount,
                transaction_type='WITHDRAWAL',
                description=f"Withdrawal from account {self.account_number}"
            )
            return True
        return False

# Transaction model to track all financial activities
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER', 'Transfer'),
    )
    
    transaction_id = models.CharField(max_length=20, unique=True, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    sender = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_transactions')
    receiver = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transactions')
    
    def __str__(self):
        return f"{self.transaction_type} - {self.transaction_id}"
    
    def save(self, *args, **kwargs):
        # Generate a unique transaction ID if not already set
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
