import uuid
from django.db import models
from apps.organizations.models import Organization


class LoyaltyTier(models.TextChoices):
    SILVER = "silver", "Silver Tier"
    GOLD = "gold", "Gold Tier"
    PLATINUM = "platinum", "Platinum Tier"


class LoyaltyMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="loyalty_members")
    guest_name = models.CharField(max_length=150)
    guest_email = models.EmailField(blank=True)
    tier = models.CharField(max_length=20, choices=LoyaltyTier.choices, default=LoyaltyTier.SILVER)
    points = models.IntegerField(default=1000)
    stays_count = models.IntegerField(default=1)
    lifetime_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-points']

    def __str__(self):
        return f"{self.guest_name} ({self.tier.upper()} - {self.points} pts)"


class GuestReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="guest_reviews")
    reviewer_name = models.CharField(max_length=150)
    rating = models.IntegerField(default=5)
    stay_reference = models.CharField(max_length=100)
    feedback = models.TextField()
    review_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, default="pending")  # pending, responded
    management_response = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-review_date']

    def __str__(self):
        return f"{self.reviewer_name} ({self.rating} stars) - {self.stay_reference}"


class PromoCampaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="promo_campaigns")
    campaign_name = models.CharField(max_length=150)
    promo_code = models.CharField(max_length=50)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.campaign_name} ({self.promo_code} - {self.discount_percentage}%)"
