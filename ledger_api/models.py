from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Q


class Customer(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_summary(self):

        entries = self.ledger_entries.all()
        
        total_credit = entries.filter(type='CREDIT').aggregate(Sum('amount'))['amount__sum'] or 0
        total_debit = entries.filter(type='DEBIT').aggregate(Sum('amount'))['amount__sum'] or 0
        balance = total_credit - total_debit

        return {
            'total_credit': total_credit,
            'total_debit': total_debit,
            'balance': balance
        }


class LedgerEntry(models.Model):

    TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]

    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE, 
        related_name='ledger_entries'
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.TextField(blank=True, null=True)
    entry_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-entry_date', '-created_at']
        indexes = [
            models.Index(fields=['customer', 'entry_date']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.customer.name} - {self.type} - {self.amount}"