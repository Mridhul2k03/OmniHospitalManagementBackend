"""
Availability search API view.
"""
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.rooms.models import RoomType
from .services import AvailabilityService
from .serializers import AvailabilitySearchResponseSerializer


class AvailabilitySearchView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AvailabilitySearchResponseSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter('property_id', str, description='Target property UUID', required=True),
            OpenApiParameter('check_in', str, description='Check-in date YYYY-MM-DD', required=True),
            OpenApiParameter('check_out', str, description='Check-out date YYYY-MM-DD', required=True),
            OpenApiParameter('adults', int, description='Number of adult guests', default=1),
        ],
        responses={200: AvailabilitySearchResponseSerializer}
    )
    def get(self, request):
        property_id = request.query_params.get('property_id')
        check_in_str = request.query_params.get('check_in')
        check_out_str = request.query_params.get('check_out')
        adults = int(request.query_params.get('adults', 1))

        if not all([property_id, check_in_str, check_out_str]):
            return Response(
                {"success": False, "message": "property_id, check_in, and check_out are required query parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"success": False, "message": "Dates must be formatted as YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if check_out_date <= check_in_date:
            return Response(
                {"success": False, "message": "check_out must be strictly after check_in."},
                status=status.HTTP_400_BAD_REQUEST
            )

        room_types = RoomType.objects.filter(
            property_id=property_id,
            is_active=True,
            max_occupancy__gte=adults
        )

        num_nights = (check_out_date - check_in_date).days
        available_list = []

        for rt in room_types:
            AvailabilityService.ensure_availability_records(rt.property, rt, check_in_date, check_out_date)
            is_avail = AvailabilityService.check_availability(property_id, rt.id, check_in_date, check_out_date, requested_count=1)
            if is_avail:
                total_est = rt.base_price * num_nights
                available_list.append({
                    "room_type_id": str(rt.id),
                    "name": rt.name,
                    "code": rt.code,
                    "base_occupancy": rt.base_occupancy,
                    "max_occupancy": rt.max_occupancy,
                    "nightly_rate": float(rt.base_price),
                    "total_nights": num_nights,
                    "estimated_total": float(total_est),
                })

        return Response({
            "success": True,
            "property_id": property_id,
            "check_in": check_in_str,
            "check_out": check_out_str,
            "total_nights": num_nights,
            "available_room_types": available_list,
        })
