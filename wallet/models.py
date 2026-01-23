from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid

class WalletUserManager(BaseUserManager):
    def create_user(self, wallet_address, **extra_fields):
        if not wallet_address:
            raise ValueError('The Wallet Address must be set')
        wallet_address = wallet_address.lower() # Normalize to lowercase
        user = self.model(wallet_address=wallet_address, **extra_fields)
        user.set_unusable_password() # No password needed
        user.save(using=self._db)
        return user

    def create_superuser(self, wallet_address, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(wallet_address, **extra_fields)

class WalletUser(AbstractBaseUser, PermissionsMixin):
    wallet_address = models.CharField(max_length=42, unique=True)
    nonce = models.CharField(max_length=100, default=uuid.uuid4, help_text="Random nonce for security")
    
    # Required fields for Django Auth
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = WalletUserManager()

    USERNAME_FIELD = 'wallet_address'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.wallet_address