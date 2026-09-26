from django.contrib import admin
from .models import RoomAmenity, RoomType, Room, RatePlan, RoomRate


@admin.register(RoomAmenity)
class RoomAmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'description')
    search_fields = ('name',)


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'property', 'base_price', 'max_occupancy', 'is_active')
    list_filter = ('property', 'is_active')
    search_fields = ('name', 'code')
    filter_horizontal = ('amenities',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'property', 'room_type', 'floor', 'status', 'is_active')
    list_filter = ('status', 'property', 'room_type', 'is_active')
    search_fields = ('room_number',)


@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'property', 'room_type', 'meal_plan', 'is_active')
    list_filter = ('property', 'meal_plan', 'is_active')
    search_fields = ('name', 'code')


@admin.register(RoomRate)
class RoomRateAdmin(admin.ModelAdmin):
    list_display = ('rate_plan', 'date', 'rate')
    list_filter = ('date',)
