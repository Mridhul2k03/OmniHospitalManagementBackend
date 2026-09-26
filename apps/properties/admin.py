from django.contrib import admin
from .models import Property, Building, Floor


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'property_type', 'city', 'state', 'country', 'organization', 'is_active')
    list_filter = ('property_type', 'country', 'is_active')
    search_fields = ('name', 'code', 'city')


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'property')
    list_filter = ('property',)
    search_fields = ('name', 'code')


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('name', 'floor_number', 'building')
    list_filter = ('building__property', 'building')
    search_fields = ('name',)
