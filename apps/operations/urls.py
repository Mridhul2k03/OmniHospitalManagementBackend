from django.urls import path
from .views import (
    DiningTablesView,
    MenuItemsView,
    DiningOrdersView,
    DiningOrderKOTView,
    DiningOrderFolioView,
    PostOrderToRoomView,
    KOTOrdersView,
    KOTOrderItemStatusView,
    CancelKOTOrderView,
    HousekeepingTasksView,
    HousekeepingChecklistView,
    LostAndFoundView,
    LostAndFoundClaimView,
    MaintenanceTicketsView,
    AssignTechnicianView,
    TransportTripsView,
    DispatchTripView,
    TransportVehiclesView,
    TransportDriversView,
    SpaServicesView,
    SpaAppointmentsView,
    SecurityGateLogsView,
    SecurityGateExitView,
    InventoryStockView,
    InventoryPurchaseOrderView,
    EventsVenuesView,
    EventsView,
    EventsFolioView,
    CloakroomTicketsView,
    CloakroomReleaseView,
    ChannelsListView,
    ChannelsSyncView,
    ChannelMappingsView,
    HRStaffView,
)

dining_urlpatterns = [
    path('tables/', DiningTablesView.as_view(), name='dining-tables'),
    path('tables/<str:pk>/', DiningTablesView.as_view(), name='dining-table-detail'),
    path('menu/', MenuItemsView.as_view(), name='dining-menu'),
    path('menu/<str:pk>/', MenuItemsView.as_view(), name='dining-menu-detail'),
    path('menu-items/', MenuItemsView.as_view(), name='dining-menu-items'),
    path('menu-items/<str:pk>/', MenuItemsView.as_view(), name='dining-menu-item-detail'),
    path('orders/', DiningOrdersView.as_view(), name='dining-orders'),
    path('orders/kot/', DiningOrderKOTView.as_view(), name='dining-orders-kot'),
    path('orders/folio/', DiningOrderFolioView.as_view(), name='dining-orders-folio'),
    path('orders/<str:order_id>/post-to-room/', PostOrderToRoomView.as_view(), name='dining-post-to-room'),
    path('kot/', KOTOrdersView.as_view(), name='dining-kot'),
    path('kot/<str:pk>/', KOTOrdersView.as_view(), name='dining-kot-detail'),
    path('kot/<str:pk>/status/', KOTOrdersView.as_view(), name='dining-kot-status'),
    path('kot/<str:pk>/items/<str:item_id>/status/', KOTOrderItemStatusView.as_view(), name='dining-kot-item-status'),
    path('kot/<str:pk>/cancel/', CancelKOTOrderView.as_view(), name='dining-kot-cancel'),
]

kot_urlpatterns = [
    path('orders/', KOTOrdersView.as_view(), name='kot-orders-list'),
    path('orders/<str:pk>/', KOTOrdersView.as_view(), name='kot-orders-detail'),
    path('orders/<str:pk>/status/', KOTOrdersView.as_view(), name='kot-orders-status'),
    path('orders/<str:pk>/items/<str:item_id>/status/', KOTOrderItemStatusView.as_view(), name='kot-orders-item-status'),
    path('orders/<str:pk>/cancel/', CancelKOTOrderView.as_view(), name='kot-orders-cancel'),
]

housekeeping_urlpatterns = [
    path('tasks/', HousekeepingTasksView.as_view(), name='housekeeping-tasks'),
    path('tasks/<str:pk>/', HousekeepingTasksView.as_view(), name='housekeeping-task-detail'),
    path('tasks/<str:pk>/checklist/', HousekeepingChecklistView.as_view(), name='housekeeping-task-checklist'),
    path('lost-found/', LostAndFoundView.as_view(), name='housekeeping-lost-found'),
    path('lost-found/<str:pk>/claim/', LostAndFoundClaimView.as_view(), name='housekeeping-lost-found-claim'),
]

maintenance_urlpatterns = [
    path('tickets/', MaintenanceTicketsView.as_view(), name='maintenance-tickets'),
    path('tickets/<str:pk>/', MaintenanceTicketsView.as_view(), name='maintenance-ticket-detail'),
    path('tickets/<str:pk>/assign/', AssignTechnicianView.as_view(), name='maintenance-ticket-assign'),
    path('work-orders/', MaintenanceTicketsView.as_view(), name='maintenance-work-orders'),
    path('work-orders/<str:pk>/', MaintenanceTicketsView.as_view(), name='maintenance-work-orders-detail'),
]

transport_urlpatterns = [
    path('trips/', TransportTripsView.as_view(), name='transport-trips'),
    path('trips/<str:pk>/', TransportTripsView.as_view(), name='transport-trip-detail'),
    path('trips/<str:pk>/dispatch/', DispatchTripView.as_view(), name='transport-trip-dispatch'),
    path('vehicles/', TransportVehiclesView.as_view(), name='transport-vehicles'),
    path('fleet/', TransportVehiclesView.as_view(), name='transport-fleet'),
    path('drivers/', TransportDriversView.as_view(), name='transport-drivers'),
]

spa_urlpatterns = [
    path('services/', SpaServicesView.as_view(), name='spa-services'),
    path('appointments/', SpaAppointmentsView.as_view(), name='spa-appointments'),
    path('appointments/<str:pk>/', SpaAppointmentsView.as_view(), name='spa-appointment-detail'),
]

security_urlpatterns = [
    path('gate-logs/', SecurityGateLogsView.as_view(), name='security-gate-logs'),
    path('gate-logs/<str:pk>/exit/', SecurityGateExitView.as_view(), name='security-gate-exit'),
    path('cloakroom/', CloakroomTicketsView.as_view(), name='security-cloakroom'),
    path('cloakroom/<str:pk>/release/', CloakroomReleaseView.as_view(), name='security-cloakroom-release'),
]

inventory_urlpatterns = [
    path('stock/', InventoryStockView.as_view(), name='inventory-stock'),
    path('stock/<str:pk>/', InventoryStockView.as_view(), name='inventory-stock-detail'),
    path('po/', InventoryPurchaseOrderView.as_view(), name='inventory-po'),
]

events_urlpatterns = [
    path('', EventsView.as_view(), name='events-list'),
    path('venues/', EventsVenuesView.as_view(), name='events-venues'),
    path('<str:pk>/folio/', EventsFolioView.as_view(), name='events-folio'),
]

cloakroom_urlpatterns = [
    path('tickets/', CloakroomTicketsView.as_view(), name='cloakroom-tickets'),
    path('tickets/<str:pk>/release/', CloakroomReleaseView.as_view(), name='cloakroom-release'),
]

channels_urlpatterns = [
    path('', ChannelsListView.as_view(), name='channels-list'),
    path('sync/', ChannelsSyncView.as_view(), name='channels-sync'),
    path('<str:pk>/', ChannelsListView.as_view(), name='channels-detail'),
    path('<str:pk>/mappings/', ChannelMappingsView.as_view(), name='channels-mappings'),
]

hr_urlpatterns = [
    path('staff/', HRStaffView.as_view(), name='hr-staff'),
    path('staff/<str:pk>/', HRStaffView.as_view(), name='hr-staff-detail'),
]
