# Omni Hospitality Management Operating System (HMOS)
## Frontend-to-Backend Integration & Connection Guide

**Target Architecture:** React 19 / TypeScript / Vite / Tailwind CSS / Axios / TanStack Query  
**Backend Architecture:** Python 3.12+ / Django 5.x / Django REST Framework / Django Channels (WebSockets)  
**Standard Base API URL:** `http://127.0.0.1:8000/api/v1/` (configured via Vite proxy `/api/v1`)  
**WebSocket Gateway:** `ws://127.0.0.1:8000/ws/`  
**Tenant Scoping:** Handled via `X-Tenant-ID` request header or `omni_tenant_id` cookie.  

---

## 1. Environment & Network Configuration

### 1.1 Vite Environment Variables (`.env`)
Create or update `.env` in the root of `OmniHospitalManagementFrontend`:

```ini
# Base API URL (proxied locally through Vite to avoid CORS issues)
VITE_API_BASE_URL=/api/v1

# Direct Backend URL (for production or absolute references)
VITE_BACKEND_URL=http://127.0.0.1:8000

# WebSocket Gateway
VITE_WS_GATEWAY_URL=ws://127.0.0.1:8000/ws/

# Default Tenant Context (if not yet selected)
VITE_DEFAULT_TENANT_ID=oxford-crest
```

---

### 1.2 Vite Proxy Configuration (`vite.config.ts`)
Configure Vite's reverse proxy so all `/api/v1` requests and `/ws/` WebSockets are smoothly forwarded to Django on port `8000`:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        ws: false,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
```

---

## 2. Core API Client Setup (`src/api/client/axios.ts`)

The Django backend enforces:
1. **Dual-Mode Authentication:** HttpOnly cookies (`access_token`, `refresh_token`) + optional `Authorization: Bearer <token>`.
2. **Multi-Tenancy:** `X-Tenant-ID` header required on all operational endpoints.
3. **Standard Response Wrapper:** All responses arrive wrapped in `{ success: true, data: ..., meta: { ... } }`.

```typescript
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  withCredentials: true, // CRITICAL: Ensures browser sends HttpOnly JWT cookies
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request Interceptor: Attach Tenant Header & Bearer Token fallback
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 1. Multi-Tenant context resolution
    const activeTenantId = localStorage.getItem('omni_active_tenant_id') || 
                           import.meta.env.VITE_DEFAULT_TENANT_ID || 
                           'oxford-crest';
    config.headers.set('X-Tenant-ID', activeTenantId);

    // 2. Bearer token fallback if cookies are not used or in cross-domain mode
    const token = localStorage.getItem('omni_access_token');
    if (token && !config.headers.has('Authorization')) {
      config.headers.set('Authorization', `Bearer ${token}`);
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Unpack Standard Envelope & Handle 401 Refresh
apiClient.interceptors.response.use(
  (response) => {
    // Binary file downloads (PDF, CSV) bypass envelope unpacking
    if (response.config.responseType === 'blob') {
      return response.data;
    }
    // Automatically unwrap the standard DRF envelope if present
    if (response.data && response.data.success !== undefined && response.data.data !== undefined) {
      return response.data.data;
    }
    return response.data;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Auto-refresh access token if 401 received
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url?.includes('/auth/login/')) {
      originalRequest._retry = true;
      try {
        const refresh = localStorage.getItem('omni_refresh_token');
        await axios.post('/api/v1/auth/refresh/', { refresh }, { withCredentials: true });
        return apiClient(originalRequest);
      } catch (refreshErr) {
        localStorage.removeItem('omni_access_token');
        localStorage.removeItem('omni_refresh_token');
        if (window.location.pathname !== '/auth/login') {
          window.location.href = '/auth/login';
        }
      }
    }

    return Promise.reject(error.response?.data || error.message);
  }
);
```

---

## 3. Real-Time WebSockets Client (`src/hooks/useWebSocket.ts`)

Subscribes to operational broadcasts from Django Channels:

```typescript
import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketEvent<T = any> {
  type: 'KOT_ORDER_FIRED' | 'KOT_STATUS_CHANGED' | 'ROOM_STATUS_CHANGED' | 'GUEST_CHECKED_IN';
  data: T;
}

export function useHotelWebSocket(propertyId: string = 'prop-001') {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const wsUrl = `${import.meta.env.VITE_WS_GATEWAY_URL || 'ws://127.0.0.1:8000/ws/'}?property_id=${propertyId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket connected to HMOS Gateway');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const payload: WebSocketEvent = JSON.parse(event.data);
        setLastMessage(payload);
      } catch (err) {
        console.error('Failed to parse WS frame:', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Auto-reconnect after 3 seconds
      setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
      ws.close();
    };
  }, [propertyId]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { isConnected, lastMessage };
}
```

---

## 4. Bridging Gaps: Module-by-Module API Client Code

Below are the exact TypeScript API files and functions required to connect all modules that were previously partially connected or disconnected.

### Module 5: Front Desk Walk-In & Digital Check-In (`src/api/endpoints/reservations.api.ts`)

```typescript
import { apiClient } from '../client/axios';

export interface WalkInBookingPayload {
  guest: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
  };
  roomId: string;
  checkInDate: string; // YYYY-MM-DD
  checkOutDate: string; // YYYY-MM-DD
  channel: 'walk_in' | 'direct';
  autoCheckIn?: boolean;
}

export interface DigitalCheckInPayload {
  confirmationCode: string;
  firstName?: string;
  lastName?: string;
  idType?: string;
  idNumber?: string;
  signatureBase64: string;
}

export const reservationsApi = {
  // Master Manifest
  getReservations: (params?: Record<string, any>) => 
    apiClient.get('/reservations/', { params }),

  // Walk-in booking creation (Bridges FrontDeskHub & ReservationsHub buttons)
  createWalkInBooking: (payload: WalkInBookingPayload) => 
    apiClient.post('/reservations/', payload),

  // Front Desk physical Check-In
  checkInGuest: (id: string, payload: { assignedRoomId?: string; keyCardsCount?: number; notes?: string }) => 
    apiClient.post(`/reservations/${id}/check-in/`, payload),

  // Front Desk departure Check-Out
  checkOutGuest: (id: string, payload?: { settlementMethod?: string; notes?: string }) => 
    apiClient.post(`/reservations/${id}/check-out/`, payload),

  // Digital Contactless Check-In (Bridges 4-step wizard)
  submitDigitalCheckIn: (payload: DigitalCheckInPayload) => 
    apiClient.post('/reservations/digital-check-in/', payload),

  // Quick queues
  getTodayArrivals: () => apiClient.get('/reservations/today-arrivals/'),
  getTodayDepartures: () => apiClient.get('/reservations/today-departures/'),
  getInHouseGuests: () => apiClient.get('/reservations/in-house/'),
};
```

---

### Module 6: Master Folios, Cashiering & GL Export (`src/api/endpoints/folios.api.ts`)

```typescript
import { apiClient } from '../client/axios';

export const foliosApi = {
  getFolios: (params?: { roomNumber?: string; status?: string; search?: string }) => 
    apiClient.get('/folios/', { params }),

  getFolioDetails: (id: string) => 
    apiClient.get(`/folios/${id}/`),

  postCharge: (id: string, charge: { department: string; description: string; amount: number; referenceNumber?: string }) => 
    apiClient.post(`/folios/${id}/charges/`, charge),

  voidCharge: (id: string, chargeId: string, reason: string) => 
    apiClient.post(`/folios/${id}/charges/${chargeId}/void/`, { reason }),

  settlePayment: (id: string, payment: { amount: number; paymentMethod: string; transactionReference?: string }) => 
    apiClient.post(`/folios/${id}/payments/`, payment),

  // Tax Invoice PDF streaming
  downloadInvoicePdf: async (id: string, filename = `Folio-${id}.pdf`) => {
    const blob = await apiClient.get(`/folios/${id}/invoice-pdf/`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([blob as any], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  // Daily Night Audit ledger closing
  runNightAudit: () => 
    apiClient.post('/folios/night-audit/'),

  // General Ledger CSV Export (Bridges FinanceHub "Export GL CSV" button)
  exportGeneralLedgerCsv: async () => {
    const blob = await apiClient.get('/finance/gl-export/', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([blob as any], { type: 'text/csv' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `GL-Export-${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};
```

---

### Module 7: Dining POS & Kitchen Display System (`src/api/endpoints/dining.api.ts` & `kot.api.ts`)

```typescript
import { apiClient } from '../client/axios';

// Dining POS
export const diningApi = {
  getTables: () => apiClient.get('/dining/tables/'),
  getMenu: () => apiClient.get('/dining/menu/'),

  // Firing orders to KDS
  fireKOTOrder: (payload: {
    tableNumber: string;
    roomNumber?: string;
    serverName?: string;
    items: Array<{ menuItemId?: string; name: string; quantity: number; specialInstructions?: string; station: string }>;
  }) => apiClient.post('/dining/orders/kot/', payload),

  // Room folio charge posting
  postDiningToRoomFolio: (payload: { roomNumber: string; amount: number; tip?: number; orderNumber: string }) => 
    apiClient.post('/dining/orders/folio/', payload),
};

// Kitchen Display System (KDS)
export const kotApi = {
  getActiveTickets: (params?: { status?: string; station?: string }) => 
    apiClient.get('/kot/orders/', { params }),

  advanceTicketStatus: (id: string, status: 'preparing' | 'ready' | 'served' | 'cancelled') => 
    apiClient.patch(`/kot/orders/${id}/status/`, { status }),

  bumpItemStatus: (ticketId: string, itemId: string, status: string) => 
    apiClient.patch(`/kot/orders/${ticketId}/items/${itemId}/status/`, { status }),
};
```

---

### Module 8: Housekeeping Lost & Found Bridge (`src/api/endpoints/housekeeping.api.ts`)

```typescript
import { apiClient } from '../client/axios';

export const housekeepingApi = {
  getTurnoverTasks: (params?: Record<string, any>) => 
    apiClient.get('/housekeeping/tasks/', { params }),

  updateTaskStatus: (id: string, payload: { status: string; checklist?: any[] }) => 
    apiClient.patch(`/housekeeping/tasks/${id}/`, payload),

  getLostAndFoundItems: () => 
    apiClient.get('/housekeeping/lost-found/'),

  // Bridges registering found items into custody vault
  registerFoundItem: (payload: { itemDescription: string; category?: string; foundLocation: string; foundBy: string }) => 
    apiClient.post('/housekeeping/lost-found/', payload),

  // Bridges releasing custody item to verified owner
  claimFoundItem: (id: string, payload: { claimantName: string; verifiedBy: string }) => 
    apiClient.post(`/housekeeping/lost-found/${id}/claim/`, payload),
};
```

---

### Module 14: Events & Banquet BEO Master Folio (`src/api/endpoints/operations.api.ts`)

```typescript
import { apiClient } from '../client/axios';

export const operationsApi = {
  // Venues & Events
  getVenues: () => apiClient.get('/events/venues/'),
  getEvents: () => apiClient.get('/events/'),

  // Bridges Master Folio modal displaying real BEO charges
  getEventBEOFolio: (eventId: string) => 
    apiClient.get(`/events/${eventId}/folio/`),

  // OTA Channel Mappings bridge
  getChannelMappings: (channelId: string) => 
    apiClient.get(`/channels/${channelId}/mappings/`),

  saveChannelMapping: (channelId: string, payload: { pmsRoomTypeId: string; otaRoomCode: string; rateMultiplier?: number }) => 
    apiClient.post(`/channels/${channelId}/mappings/`, payload),

  // Inventory PO history
  getPurchaseOrders: () => apiClient.get('/inventory/po/'),
};
```

---

### Module 16: Dynamic AI Pricing Engine (`src/api/endpoints/pricing.api.ts`)

Replaces the local React `useState` pricing calculations in `DynamicPricingHub.tsx` with backend persistence:

```typescript
import { apiClient } from '../client/axios';

export interface PricingRule {
  id: string;
  roomTypeName: string;
  baseRate: number;
  calculatedRate: number;
  demandBand: 'low' | 'normal' | 'high' | 'surge';
  occupancyPace: string;
  isManualOverride: boolean;
  manualOverrideRate: number | null;
}

export const dynamicPricingApi = {
  // Lists active automated rate rules
  getRules: () => 
    apiClient.get<any, PricingRule[]>('/pricing/rules/'),

  // Real-time demand bands & surge recommendations
  getDemandBands: () => 
    apiClient.get('/pricing/demand-bands/'),

  // Enforces authorized rate override
  setRateOverride: (payload: { roomTypeId?: string; ruleId?: string; overrideRate: number; reason?: string }) => 
    apiClient.post('/pricing/overrides/', payload),

  // Revokes override back to automated algorithm
  revokeOverride: (ruleId: string) => 
    apiClient.delete(`/pricing/rules/${ruleId}/overrides/`),
};
```

---

### Module 18: Corporate Executive Dashboard (`src/api/endpoints/executive.api.ts`)

Connects the live corporate metrics in `ExecutiveDashboard.tsx`:

```typescript
import { apiClient } from '../client/axios';

export const executiveApi = {
  getKPIs: (period: 'today' | 'week' | 'month' | 'quarter' | 'year' = 'month') => 
    apiClient.get('/executive/kpis/', { params: { period } }),

  getPropertyComparison: () => 
    apiClient.get('/executive/property-comparison/'),

  getOccupancyTrends: (months: number = 6) => 
    apiClient.get('/executive/occupancy-trend/', { params: { months } }),

  getRevenueMix: () => 
    apiClient.get('/executive/revenue-mix/'),

  // Generates and downloads the certified Executive Board Pack PDF
  exportBoardPackPdf: async () => {
    const blob = await apiClient.get('/executive/export-board-pack/', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([blob as any], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Executive-Board-Pack-${new Date().toISOString().split('T')[0]}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};
```

---

### Module 19: Shareholder Portal (`src/api/endpoints/shareholder.api.ts`)

```typescript
import { apiClient } from '../client/axios';

export const shareholderApi = {
  // Shareholder equity profile
  getProfile: () => 
    apiClient.get('/shareholder/profile/'),

  // Dividends history
  getDividends: () => 
    apiClient.get('/shareholder/dividends/'),

  // Dividend voucher PDF download
  downloadVoucherPdf: async (dividendId: string) => {
    const blob = await apiClient.get(`/shareholder/dividends/${dividendId}/voucher-pdf/`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([blob as any], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Dividend-Voucher-${dividendId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  // SEC / certified filings list
  getFinancialFilings: () => 
    apiClient.get('/shareholder/financials/'),

  // Certified filing download
  downloadFilingPdf: async (filingId: string, filename: string) => {
    const blob = await apiClient.get(`/shareholder/financials/${filingId}/download/`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([blob as any], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  // Appraised physical hotel assets
  getAppraisedAssets: () => 
    apiClient.get('/shareholder/assets/'),
};
```

---

### Module 21: Loyalty, Guest CRM & Reputation (`src/api/endpoints/loyalty.api.ts`)

Bridges all features of `LoyaltyHub.tsx`:

```typescript
import { apiClient } from '../client/axios';

export const loyaltyApi = {
  // Member tiers summary (Silver, Gold, Platinum counts, NPS)
  getTierSummary: () => 
    apiClient.get('/loyalty/tiers/'),

  // Loyalty members ledger
  getMembers: () => 
    apiClient.get('/loyalty/members/'),

  // Verified guest reviews & sentiment
  getGuestReviews: () => 
    apiClient.get('/loyalty/reviews/'),

  // Respond to guest review
  respondToReview: (reviewId: string, responseText: string) => 
    apiClient.post(`/loyalty/reviews/${reviewId}/respond/`, { responseText }),

  // Create promo campaign
  createPromoCampaign: (payload: { name: string; promoCode: string; discountPercentage: number }) => 
    apiClient.post('/loyalty/campaigns/', payload),
};
```

---

### Module 22: Property Policies & Settings (`src/api/endpoints/properties.api.ts`)

```typescript
import { apiClient } from '../client/axios';

export const propertiesApi = {
  getProperties: () => apiClient.get('/properties/'),

  // Fetch operational policies & tax configuration
  getPolicies: (propertyId: string) => 
    apiClient.get(`/properties/${propertyId}/policies/`),

  // Persists policies from SettingsHub.tsx
  updatePolicies: (propertyId: string, policies: {
    checkInTime?: string;
    checkOutTime?: string;
    stateTaxRate?: number;
    cityUnitFee?: number;
    name?: string;
    phone?: string;
    email?: string;
  }) => apiClient.patch(`/properties/${propertyId}/policies/`, policies),
};
```

---

## 5. UI Integration Checklist & Verification

Follow this checklist when linking the React components to backend APIs:

| Step | Action | Verification |
|---|---|---|
| **1** | Run `python manage.py seed_hotel_data` | Confirms tenant `oxford-crest` and rooms are present. |
| **2** | Start Django backend on port 8000 | Verify `http://127.0.0.1:8000/api/v1/health/` returns `healthy`. |
| **3** | Start Vite frontend with `npm run dev` | Access `http://localhost:5173/auth/login`. |
| **4** | Check Network tab in Chrome DevTools | All requests should show `200 OK` with request header `X-Tenant-ID: oxford-crest`. |
| **5** | Dynamic Pricing Hub (`/app/pricing`) | Verify surge multipliers load from `/api/v1/pricing/rules/` and manual rate overrides persist across page reload. |
| **6** | Loyalty Hub (`/app/loyalty`) | Confirm tiers (Silver/Gold/Platinum) and reviews load from `/api/v1/loyalty/tiers/` and `/api/v1/loyalty/reviews/`. |
| **7** | Executive Dashboard (`/app/corporate`) | Metrics ($3.38M revenue, 91.5% occupancy) reflect API response from `/api/v1/executive/kpis/`. |
| **8** | Front Desk & Reservations | Click "Create Walk-In" or test Digital Check-in to verify that bookings create real reservation records. |
| **9** | Real-Time KDS (`/app/kds`) | Place an order from POS (`/app/pos`); verify the ticket appears instantly on the KDS board without manual refresh. |
