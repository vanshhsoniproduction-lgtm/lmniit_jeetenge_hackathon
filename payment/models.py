import uuid
from django.db import models

class PaymentRequest(models.Model):
    TYPES = [
        ('STATIC', 'Static QR'),
        ('DYNAMIC', 'Dynamic QR')
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('EXPIRED', 'Expired')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_type = models.CharField(max_length=10, choices=TYPES, default='DYNAMIC')
    amount_mon = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    note = models.TextField(blank=True, null=True)
    receiver_wallet = models.CharField(max_length=42)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.request_type} - {self.amount_mon} MON ({self.status})"

class PaymentTransaction(models.Model):
    request = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, related_name='transactions')
    payer_wallet = models.CharField(max_length=42)
    tx_hash = models.CharField(max_length=66, unique=True)
    chain_id = models.CharField(max_length=10, default='11155111') # Sepolia ID
    amount_mon = models.DecimalField(max_digits=20, decimal_places=8)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tx_hash} - {self.amount_mon}"
