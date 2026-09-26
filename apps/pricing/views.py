from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from common.permissions import IsPropertyStaffOrAdmin
from apps.organizations.models import Organization
from apps.rooms.models import RoomType
from .models import DynamicPricingRule, DemandBand
from .serializers import DynamicPricingRuleSerializer


class DynamicPricingViewSet(viewsets.ModelViewSet):
    serializer_class = DynamicPricingRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return DynamicPricingRule.objects.none()

        org = tenant or getattr(user, 'organization', None)
        if not org and user.is_superuser:
            return DynamicPricingRule.objects.all().select_related("room_type")
        if org:
            return DynamicPricingRule.objects.filter(organization=org).select_related("room_type")
        return DynamicPricingRule.objects.all().select_related("room_type")

    @action(detail=False, methods=["get"], url_path="rules")
    def rules(self, request):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="demand-bands")
    def demand_bands(self, request):
        return Response({
            "currentOccupancy": 88.5,
            "velocityPace": "high",
            "activeBand": "surge",
            "peakHours": "18:00 - 22:00",
            "recommendedSurgeMultiplier": 1.25,
        })

    @action(detail=False, methods=["post"], url_path="overrides")
    def set_override(self, request):
        room_type_id = request.data.get("roomTypeId") or request.data.get("room_type_id")
        rule_id = request.data.get("ruleId") or request.data.get("rule_id")
        override_rate = request.data.get("overrideRate") or request.data.get("override_rate")
        reason = request.data.get("reason", "Revenue manager manual override")

        tenant = getattr(request, 'tenant', None) or getattr(request.user, 'organization', None)
        if not tenant:
            tenant = Organization.objects.first()

        rule = None
        if rule_id:
            rule = DynamicPricingRule.objects.filter(id=rule_id).first()
        elif room_type_id:
            rule = DynamicPricingRule.objects.filter(room_type_id=room_type_id).first()
            if not rule:
                rt = RoomType.objects.filter(id=room_type_id).first()
                if rt:
                    rule = DynamicPricingRule.objects.create(
                        organization=tenant,
                        room_type=rt,
                        demand_band=DemandBand.SURGE,
                        surge_multiplier=1.20,
                    )

        if not rule:
            # Fallback to first available rule or create for first room type
            rule = DynamicPricingRule.objects.filter(organization=tenant).first()
            if not rule:
                rt = RoomType.objects.first()
                if rt:
                    rule = DynamicPricingRule.objects.create(
                        organization=tenant,
                        room_type=rt,
                        demand_band=DemandBand.SURGE,
                    )

        if not rule:
            return Response({"detail": "Pricing rule or room category not found."}, status=status.HTTP_404_NOT_FOUND)

        rule.is_manual_override = True
        rule.manual_override_rate = override_rate
        rule.override_reason = reason
        rule.save()
        return Response(DynamicPricingRuleSerializer(rule).data)

    @action(detail=True, methods=["delete"], url_path="overrides")
    def delete_override(self, request, pk=None):
        rule = self.get_object()
        rule.is_manual_override = False
        rule.manual_override_rate = None
        rule.override_reason = ""
        rule.save()
        return Response({"success": True, "message": "Manual override revoked."}, status=status.HTTP_200_OK)
