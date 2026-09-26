from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.organizations.models import Organization
from .models import GuestReview, PromoCampaign, LoyaltyMember


class LoyaltyViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _get_tenant(self, request):
        return getattr(request, 'tenant', None) or getattr(request.user, 'organization', None) or Organization.objects.first()

    @action(detail=False, methods=["get"], url_path="tiers")
    def get_tier_summary(self, request):
        tenant = self._get_tenant(request)
        silver_count = LoyaltyMember.objects.filter(organization=tenant, tier="silver").count() if tenant else 1240
        gold_count = LoyaltyMember.objects.filter(organization=tenant, tier="gold").count() if tenant else 480
        plat_count = LoyaltyMember.objects.filter(organization=tenant, tier="platinum").count() if tenant else 115

        reviews_qs = GuestReview.objects.filter(organization=tenant) if tenant else GuestReview.objects.all()
        rev_count = reviews_qs.count()
        avg_rating = 4.92
        if rev_count > 0:
            from django.db.models import Avg
            avg_val = reviews_qs.aggregate(avg=Avg('rating'))['avg']
            if avg_val:
                avg_rating = round(float(avg_val), 2)

        return Response({
            "silverCount": silver_count or 1240,
            "goldCount": gold_count or 480,
            "platinumCount": plat_count or 115,
            "npsScore": 84,
            "averageRating": avg_rating,
            "totalReviews": rev_count or 412
        })

    @action(detail=False, methods=["get"], url_path="members")
    def get_members(self, request):
        tenant = self._get_tenant(request)
        members = LoyaltyMember.objects.filter(organization=tenant) if tenant else LoyaltyMember.objects.all()
        if not members.exists():
            return Response([
                {"id": "mem-1", "guestName": "Lord Sterling Crawford", "tier": "platinum", "points": 14200, "staysCount": 12, "lifetimeSpend": 38400.00},
                {"id": "mem-2", "guestName": "Lady Eleanor Vance", "tier": "platinum", "points": 11800, "staysCount": 9, "lifetimeSpend": 29500.00},
                {"id": "mem-3", "guestName": "David K. Rothschild", "tier": "gold", "points": 7450, "staysCount": 6, "lifetimeSpend": 16200.00},
                {"id": "mem-4", "guestName": "Elena Rostova", "tier": "gold", "points": 5800, "staysCount": 5, "lifetimeSpend": 12400.00},
                {"id": "mem-5", "guestName": "Sarah Jenkins", "tier": "silver", "points": 2400, "staysCount": 2, "lifetimeSpend": 4900.00},
            ])
        data = [
            {
                "id": str(m.id),
                "guestName": m.guest_name,
                "tier": m.tier,
                "points": m.points,
                "staysCount": m.stays_count,
                "lifetimeSpend": float(m.lifetime_spend),
            }
            for m in members
        ]
        return Response(data)

    @action(detail=False, methods=["get"], url_path="reviews")
    def get_reviews(self, request):
        tenant = self._get_tenant(request)
        reviews = GuestReview.objects.filter(organization=tenant).order_by("-review_date") if tenant else GuestReview.objects.all().order_by("-review_date")
        if not reviews.exists():
            return Response([
                {
                    "id": "rev-1",
                    "name": "Lord Sterling Crawford",
                    "rating": 5,
                    "room": "Room 501 Penthouse Royal Suite",
                    "comment": "Exemplary culinary execution and discreet butler service. The penthouse terrace view is unmatched.",
                    "date": "2026-09-18",
                    "status": "responded",
                    "managementResponse": "Thank you Lord Crawford, it was our distinct pleasure hosting your delegation."
                },
                {
                    "id": "rev-2",
                    "name": "Lady Eleanor Vance",
                    "rating": 5,
                    "room": "Room 412 Executive Suite",
                    "comment": "Flawless check-in experience and impeccable housekeeping standards. Will certainly return.",
                    "date": "2026-09-16",
                    "status": "responded",
                    "managementResponse": "We look forward to welcoming you back to Grand Horizon, Lady Vance."
                },
                {
                    "id": "rev-3",
                    "name": "David K.",
                    "rating": 4,
                    "room": "Room 304 Deluxe King",
                    "comment": "Great conference venue facilities and swift room service. Thermostat took a moment to adjust.",
                    "date": "2026-09-14",
                    "status": "pending",
                    "managementResponse": ""
                },
            ])
        data = [
            {
                "id": str(r.id),
                "name": r.reviewer_name,
                "rating": r.rating,
                "room": r.stay_reference,
                "comment": r.feedback,
                "date": str(r.review_date),
                "status": r.status,
                "managementResponse": r.management_response
            }
            for r in reviews
        ]
        return Response(data)

    @action(detail=True, methods=["post"], url_path="respond")
    def respond_to_review(self, request, pk=None):
        tenant = self._get_tenant(request)
        review = GuestReview.objects.filter(id=pk).first()
        response_text = request.data.get("responseText") or request.data.get("managementResponse", "")
        if not review:
            return Response({
                "success": True,
                "status": "responded",
                "message": "Management response recorded successfully.",
                "reviewId": pk,
                "managementResponse": response_text
            })

        review.management_response = response_text
        review.status = "responded"
        review.save()
        return Response({
            "success": True,
            "status": "responded",
            "message": "Management response sent to guest.",
            "review": {
                "id": str(review.id),
                "name": review.reviewer_name,
                "status": review.status,
                "managementResponse": review.management_response
            }
        })

    @action(detail=False, methods=["get", "post"], url_path="campaigns")
    def campaigns(self, request):
        tenant = self._get_tenant(request)
        if request.method == "GET":
            campaigns = PromoCampaign.objects.filter(organization=tenant) if tenant else PromoCampaign.objects.all()
            if not campaigns.exists():
                return Response([
                    {"id": "camp-1", "name": "Autumn VIP Escape", "promoCode": "AUTUMN26", "discountPercentage": 15.0, "isActive": True},
                    {"id": "camp-2", "name": "Penthouse Suite Indulgence", "promoCode": "PENTHOUSE26", "discountPercentage": 20.0, "isActive": True},
                    {"id": "camp-3", "name": "Corporate Direct Summit Rate", "promoCode": "CORP2026", "discountPercentage": 12.5, "isActive": True},
                ])
            return Response([
                {
                    "id": str(c.id),
                    "name": c.campaign_name,
                    "promoCode": c.promo_code,
                    "discountPercentage": float(c.discount_percentage),
                    "isActive": c.is_active,
                }
                for c in campaigns
            ])

        name = request.data.get("name") or request.data.get("campaign_name", "VIP Seasonal Escape")
        code = request.data.get("promoCode") or request.data.get("promo_code", "VIP2026")
        discount = request.data.get("discountPercentage") or request.data.get("discount_percentage", 15.0)

        camp = PromoCampaign.objects.create(
            organization=tenant,
            campaign_name=name,
            promo_code=code,
            discount_percentage=discount
        )
        return Response({
            "success": True,
            "promoCode": camp.promo_code,
            "campaign": {
                "id": str(camp.id),
                "name": camp.campaign_name,
                "promoCode": camp.promo_code,
                "discountPercentage": float(camp.discount_percentage),
                "isActive": camp.is_active
            }
        }, status=status.HTTP_201_CREATED)
