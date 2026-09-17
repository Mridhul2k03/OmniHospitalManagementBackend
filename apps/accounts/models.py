"""
Custom User model supporting UUID primary key, organization multi-tenancy,
and enterprise RBAC roles.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ORG_ADMIN', 'Organization Admin'),
        ('PRESIDENT', 'President'),
        ('VICE_PRESIDENT', 'Vice President'),
        ('CEO', 'CEO'),
        ('OPERATIONS_DIRECTOR', 'Operations Director'),
        ('SHAREHOLDER', 'Shareholder'),
        ('PROPERTY_MANAGER', 'Property Manager'),
        ('FRONT_DESK', 'Front Desk'),
        ('HOUSEKEEPING', 'Housekeeping'),
        ('RESTAURANT_POS', 'Restaurant / POS'),
        ('CHEF_KITCHEN', 'Chef / Kitchen'),
        ('MAINTENANCE', 'Maintenance'),
        ('ACCOUNTANT', 'Accountant'),
        ('HR', 'HR Staff'),
        ('SECURITY_STAFF', 'Security / Gate Staff'),
        ('TRANSPORT_DISPATCHER', 'Transport Dispatcher'),
        ('DRIVER', 'Driver'),
        ('TRANSPORT_VENDOR', 'Transport Vendor'),
        ('GUEST', 'Guest'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        help_text="Organization/tenant to which this user belongs"
    )
    
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default='GUEST', db_index=True)
    phone_number = models.CharField(max_length=32, blank=True)
    
    # Privileged Role 2FA
    is_2fa_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=64, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
