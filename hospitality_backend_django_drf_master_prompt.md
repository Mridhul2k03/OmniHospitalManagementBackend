# Hospitality Management Operating System — Django REST Framework Backend Master Prompt

## 0. Role and Mission

Act as a **principal backend architect, senior Django/DRF engineer, security engineer, database designer, integration engineer, and QA lead**.

You are taking ownership of a large hospitality operating system described in the two supplied product-blueprint PDFs:

1. **Hospitality Management Ecosystem — Complete Product Blueprint**
2. **Hospitality Management — Corporate Enhanced Blueprint**

Treat those documents as the product requirements baseline. The system is intended to operate as a **Hospitality Operating System**, not merely a booking website: PMS, booking engine, front office, guest CRM, housekeeping, maintenance, F&B/POS, KOT, banquets/events, billing/finance, inventory/procurement, staff/HR, loyalty/marketing, OTA distribution, gate security, cloakroom, transport/fleet/chauffeur, corporate governance, shareholder reporting, analytics, AI and external integrations.

The baseline architecture is:

**React/TypeScript clients → REST/WebSocket → Django + DRF → PostgreSQL + Redis + Celery → payments / OTA / transport / messaging / AI / storage integrations.**

The implementation must be modular, testable, secure, tenant-scoped, auditable, event-driven where appropriate, and designed so additional properties, departments, OTA providers and transport vendors can be added without redesigning the core PMS.

---

# 1. NON-NEGOTIABLE OPERATING RULE

## Phase 0 must be an AUDIT ONLY

Before changing, refactoring, generating replacement code, deleting files, changing models, changing migrations, or installing architectural dependencies, inspect the existing repository.

**Do not modify the codebase during the initial audit.**

Act as a senior developer preparing the project for handoff.

Return a structured audit containing:

### A. Version control
- Determine whether Git is configured.
- Inspect the repository status.
- Determine whether there is a real commit history rather than a single artificial/import commit.
- Identify the current branch and remotes if available.
- Identify uncommitted and untracked work.
- If Git is missing or broken, document the correct setup procedure, but do not perform it during the audit.

### B. Duplicate / dead code
Find:
- duplicate functions,
- repeated business logic,
- repeated API calls,
- duplicated serializers,
- duplicate permission classes,
- copy-pasted service code,
- repeated validation,
- repeated query logic,
- redundant React-facing endpoint implementations,
- obsolete/dead modules,
- unreachable code,
- unused imports,
- stale compatibility code.

For every finding report:
- file,
- symbol,
- approximate location,
- what is duplicated,
- whether it is definitely dead, likely dead, or uncertain,
- recommended consolidation target.

### C. Hardcoded secrets
Scan the repository for:
- API keys,
- access tokens,
- JWT secrets,
- Django SECRET_KEY,
- database passwords,
- Redis credentials,
- SMTP credentials,
- payment credentials,
- OTA credentials,
- transport provider credentials,
- cloud credentials,
- webhook secrets,
- private keys,
- service-account material.

Do not print secret values.

Report the file and variable/line context with values masked.

Recommend environment variables and a `.env.example`.

### D. Documentation
Determine whether the repository contains:
- README,
- architecture documentation,
- setup instructions,
- environment-variable documentation,
- API documentation,
- data-flow documentation,
- deployment documentation,
- operational/runbook documentation.

If documentation is inadequate, prepare a proposed documentation structure based on the actual code.

### E. Error tracking / observability
Determine whether a production user error would be discoverable.

Inspect:
- Django logging,
- structured logs,
- exception handlers,
- error monitoring,
- request IDs/correlation IDs,
- Celery failure handling,
- WebSocket error handling,
- integration failure tracking,
- audit logging,
- health checks.

Recommend the simplest production-ready error-reporting architecture.

### F. Access control
Find every place where one user's data could potentially be read or changed by another user.

Audit:
- authentication,
- authorization,
- DRF permissions,
- queryset filtering,
- object-level permission checks,
- organization scope,
- region scope,
- property scope,
- department scope,
- assigned-job scope,
- shareholder read-only boundaries,
- transport vendor job isolation,
- gate-security isolation,
- financial records,
- guest documents,
- reservations,
- folios,
- payments,
- refunds,
- reports,
- exports,
- file downloads,
- WebSockets,
- background tasks,
- webhook endpoints.

For every issue report:
- endpoint/view/service/task,
- resource/model,
- actor,
- intended scope,
- actual scope,
- exploit/data-leak scenario,
- severity,
- remediation.

### G. Audit output
Return:
1. Executive summary.
2. Repository map.
3. Git/version-control status.
4. Duplicate/dead-code findings.
5. Secret exposure findings.
6. Documentation gaps.
7. Error tracking status.
8. Access-control matrix.
9. Database/migration assessment.
10. API architecture assessment.
11. Async/Celery assessment.
12. Integration assessment.
13. Test coverage assessment.
14. Security risks.
15. Technical debt.
16. Recommended implementation sequence.
17. Blockers that must be resolved before production.

**Do not change anything during this phase.**

After the audit is explicitly accepted, proceed to implementation.

---

# 2. PRODUCT ARCHITECTURE

Use a layered modular-monolith architecture first, with clean domain boundaries so selected domains can later be extracted into services if scale requires it.

Recommended layers:

```text
Client Applications
        |
        v
API / Authentication / Rate Limiting
        |
        v
DRF Views / ViewSets / Serializers
        |
        v
Application Services / Use Cases
        |
        v
Domain Rules / State Machines
        |
        v
Repositories / Django ORM
        |
        v
PostgreSQL

Cross-cutting:
Redis
Celery
Django Channels
Object Storage
Observability
Audit
Integrations
```

Do not put complex business rules directly into serializers or giant views.

Use:
- thin API views,
- explicit service/use-case functions,
- domain validation,
- transactions,
- scoped querysets,
- reusable policies,
- explicit state transitions.

---

# 3. MULTI-TENANCY

The tenancy model is:

```text
Platform
  └── Organization / Tenant
       ├── Regions / Property Groups
       └── Properties
            └── Departments
                 └── Users / Staff
```

Every organization-owned business record must be traceable to the correct organization and, where applicable, property and department.

Implement mandatory scope rules for:
- Organization,
- Region,
- Property,
- Department,
- assigned resource/job.

Do not rely only on frontend filtering.

The backend must enforce isolation using:
- scoped querysets,
- permission policies,
- object-level checks,
- service-layer authorization,
- safe foreign-key validation,
- constrained write paths.

A user must never be able to switch tenant/property IDs in a request and gain access to another tenant's data.

---

# 4. AUTHENTICATION AND IDENTITY

Implement:

- Django user/account system.
- JWT access tokens.
- Refresh tokens.
- Token rotation/revocation strategy.
- Strong password hashing.
- Account activation/deactivation.
- Session/device metadata where useful.
- Login/logout auditing.
- Password reset.
- Email verification where required.
- Optional/mandatory 2FA depending on role.
- Privileged-role 2FA for:
  - President,
  - Vice President,
  - CEO,
  - Operations Director,
  - shareholder,
  - organization owner/admin,
  - accountant/finance,
  - system administrator.

Keep shareholder authentication boundary distinct from operational capabilities.

Never encode authorization only in JWT claims. JWT claims may inform context; backend permissions and data scope remain authoritative.

---

# 5. ROLE AND PERMISSION SYSTEM

Implement RBAC plus scope-aware authorization.

Core operational roles from the baseline:

- Super Admin
- Organization Admin / Owner
- Property Manager
- Front Desk
- Housekeeping
- Restaurant / POS
- Chef / Kitchen
- Maintenance
- Accountant
- HR
- Guest

Corporate-enhanced roles:

- President
- Vice President
- CEO
- Operations Director
- Shareholder

Additional scoped users:

- Security / Gate Staff
- Transport Dispatcher
- Driver
- Transport Vendor
- OTA/Integration Operator
- Sales / Events
- Spa / Activities Staff

Permission structure should support:

```text
module.resource.action
```

Examples:

```text
reservations.view
reservations.create
reservations.update
reservations.cancel
reservations.check_in
reservations.check_out

folios.view
folios.adjust
folios.transfer
folios.void
folios.refund

pricing.view
pricing.manage
pricing.override

shareholder.reports.view
shareholder.dividends.view

security.gate_entries.manage
transport.jobs.assigned_only
```

Implement permissions as reusable policy components rather than scattered `if user.role == ...` conditions.

---

# 6. CORPORATE GOVERNANCE

Implement:

### Corporate entities
- Organization
- CorporateRole
- ExecutiveAssignment
- Region
- PropertyGroup
- ExecutivePropertyScope

### Executive hierarchy

```text
Shareholders [READ ONLY]
President
Vice President
CEO
Operations Directors
Properties
  └── Property Manager
      └── Departments / Staff
```

### Dashboard scopes

President:
- group revenue,
- profitability,
- occupancy,
- property comparison,
- strategic KPIs,
- alerts.

Vice President:
- region/cluster occupancy,
- revenue,
- ADR,
- RevPAR,
- trends,
- property exceptions.

CEO:
- consolidated P&L,
- revenue mix,
- cash position,
- occupancy,
- forecasts,
- major risks.

Operations Director:
- live room status,
- arrivals/departures,
- housekeeping,
- maintenance,
- guest requests,
- SLAs.

The backend must calculate these from authoritative transactional data, not from untrusted client values.

---

# 7. SHAREHOLDER PORTAL BACKEND

Shareholders have a dedicated secure read-only boundary.

Support:
- ownership summary,
- authorized portfolio scope,
- approved P&L,
- reporting periods,
- dividend declarations,
- dividend payments,
- pending distributions,
- selected KPIs,
- downloadable approved reports,
- shareholder login audit,
- report-access audit.

Explicitly deny:
- operational booking edits,
- room changes,
- staff changes,
- price changes,
- refunds,
- POS changes,
- maintenance actions,
- housekeeping actions,
- security actions,
- transport actions.

Do not expose operational mutation endpoints through shareholder authorization.

---

# 8. CORE PMS MODULES

Implement independent Django apps/modules for:

```text
config/
accounts/
organizations/
corporate/
properties/
rooms/
reservations/
availability/
guests/
frontoffice/
housekeeping/
maintenance/
restaurants/
kitchen/
events/
services/
spa/
activities/
transportation/
payments/
billing/
finance/
inventory/
procurement/
vendors/
employees/
attendance/
crm/
loyalty/
reviews/
marketing/
communications/
notifications/
channels/
pricing/
security/
cloakroom/
reports/
analytics/
integrations/
audit_logs/
```

Keep dependencies directional and intentional.

---

# 9. PROPERTY AND ROOM MANAGEMENT

Models should cover:

- Property
- Building
- Floor
- RoomType
- Room
- RoomAmenity
- PropertyAmenity
- RatePlan
- RoomRate
- RoomAvailability
- RoomBlock

Property profile:
- name,
- type,
- address,
- GPS,
- contact information,
- media,
- amenities,
- policies,
- taxes,
- currency,
- supported languages,
- check-in time,
- check-out time.

Room statuses:

```text
Available
Reserved
Occupied
Dirty
Cleaning
Inspection
Out of Order
Maintenance
Blocked
```

Use validated state transitions instead of unrestricted status writes.

---

# 10. RESERVATION AND AVAILABILITY ENGINE

Support:
- direct booking,
- guest app,
- walk-in,
- phone,
- email,
- travel agent,
- OTA,
- corporate booking,
- API partner.

Reservation states:

```text
Pending
Confirmed
Checked-in
In-house
Checked-out
Cancelled
No-show
Completed
```

Booking workflow:

```text
Search
→ Availability
→ Room Selection
→ Guest Details
→ Add Services
→ Price Calculation
→ Payment
→ Confirmation
→ Pre-arrival
→ Check-in
→ Stay
→ Checkout
```

Support:
- multiple rooms,
- room selection,
- guest assignment,
- children/adults,
- add-ons,
- coupons,
- discounts,
- taxes,
- partial payment,
- room transfer,
- stay extension,
- early check-in,
- late checkout,
- refunds,
- cancellation rules.

## Critical requirement: concurrency safety

Availability cannot be implemented as a simple:

```python
if room.available:
    create_reservation()
```

Use:
- database transactions,
- row locks where appropriate,
- inventory locking,
- unique constraints,
- deterministic overlap validation,
- idempotency keys,
- retry-safe commands.

Prevent double booking under concurrent requests.

---

# 11. GUEST CRM AND FRONT OFFICE

Guest profile:
- contact details,
- booking history,
- stay history,
- preferences,
- documents,
- payments,
- complaints,
- reviews,
- loyalty.

Preferences:
- room/floor,
- bed type,
- food preference,
- smoking preference,
- pillow preference,
- special requests.

Front desk operations:
- arrivals,
- departures,
- in-house guests,
- available rooms,
- cleaning rooms,
- maintenance rooms,
- revenue,
- walk-ins,
- reservation lookup,
- allocation,
- ID verification,
- check-in,
- check-out,
- room transfer,
- stay extension,
- folio.

Digital check-in:
- guest details,
- identity document,
- signature,
- emergency contact,
- confirmation.

Guest documents must use controlled access and signed/object-storage URLs where applicable.

---

# 12. HOUSEKEEPING

Workflow:

```text
Checkout
→ Dirty
→ Cleaning Assigned
→ Cleaning Started
→ Cleaning Completed
→ Inspection
→ Available
```

Support:
- assignment by floor/room,
- workload,
- priority,
- shift,
- checklist,
- linen count,
- minibar inspection,
- toiletries,
- damage report,
- lost & found,
- supervisor inspection,
- room-release control.

Do not allow front-end status manipulation that bypasses inspection rules.

---

# 13. MAINTENANCE

Workflow:

```text
Reported
→ Assigned
→ In Progress
→ Waiting
→ Resolved
→ Verified
→ Closed
```

Ticket fields:
- category,
- priority,
- room/asset,
- technician,
- parts,
- cost,
- SLA,
- resolution notes,
- timestamps,
- verification.

Tickets may be raised by:
- guest,
- front desk,
- housekeeping,
- manager.

---

# 14. RESTAURANT / POS / KOT

Support:
- restaurant,
- cafe,
- bar,
- menus,
- menu categories,
- menu items,
- modifiers,
- pricing,
- taxes,
- availability,
- tables,
- floor plans,
- orders.

## KOT terminology is mandatory

Use **KOT = Kitchen Order Ticket** consistently across:
- API,
- database naming where practical,
- UI-facing labels,
- reports,
- documentation,
- events.

A single POS order may generate multiple KOTs by kitchen station.

Stations may include:
- hot kitchen,
- cold kitchen,
- bakery,
- beverage,
- specialty counter.

KOT statuses:

```text
New
Accepted
Preparing
Ready
Served
Cancelled
Voided
```

Track:
- station,
- queue position,
- priority,
- preparation timestamps,
- responsible staff,
- item state.

Room-service KOT must retain:
- property,
- room,
- reservation,
- guest,
- folio references.

KOT changes/cancellations must be audited.

---

# 15. UNIFIED FOLIO AND CHARGE-EVENT LAYER

Use a standardized financial charge-event architecture:

```text
POS
Room Service
Spa
Activities
Laundry
Minibar
Banquet
Other Services
        ↓
Charge Event Layer
        ↓
Folio Service
        ↓
Guest Folio
        ↓
Invoice / Payment
```

Each charge event should contain:
- event ID,
- idempotency key,
- source,
- outlet,
- organization,
- property,
- guest,
- reservation,
- room,
- folio,
- amount,
- tax,
- timestamp,
- actor.

Implement:
- duplicate-event prevention,
- posting status,
- reversals,
- adjustments,
- transfers,
- splits,
- voids,
- audit history.

Critical financial events must be durable and idempotent.

---

# 16. BANQUETS / EVENTS / ROOM BLOCKS

Support:
- weddings,
- conferences,
- seminars,
- birthdays,
- meetings,
- corporate events.

Event:
- customer,
- venue,
- date/time,
- guest count,
- menu,
- decoration,
- equipment,
- staff,
- package,
- contract,
- payments.

Meeting rooms:
- capacity,
- seating layout,
- projector,
- sound,
- Wi-Fi,
- catering,
- equipment.

Banquet-to-room integration:

```text
Corporate Event
├── Venue
├── Event Package
├── Room Block
│   ├── Rooming List
│   └── Guest Reservations
└── Master / Individual Folios
    ├── Rooms
    ├── Banquet
    ├── F&B
    └── Services
```

Support:
- room blocks,
- rooming lists,
- guest assignment,
- pickup,
- attrition,
- release dates,
- company-paid components,
- guest-paid components,
- master folio,
- individual folios.

---

# 17. SPA / ACTIVITIES / SERVICES

Support:
- service catalog,
- availability,
- appointment schedules,
- staff/therapists,
- packages,
- memberships,
- room charging.

Activities:
- trekking,
- kayaking,
- cycling,
- sightseeing,
- campfire,
- kids activities,
- adventure experiences.

Activity/service charges must post into folios via the same charge-event architecture.

---

# 18. BILLING, PAYMENTS AND FINANCE

Unified folio must support:

```text
Room Rate
+ Extra Guest / Bed
+ Food
+ Services
+ Taxes
- Discount / Coupon
= Final Amount
```

Support:
- invoices,
- receipts,
- deposits,
- partial payments,
- refunds,
- credit balances,
- tax lines,
- cash management,
- reconciliation,
- daily closing,
- revenue,
- expenses,
- accounts payable,
- accounts receivable.

Payment methods:
- UPI,
- card,
- net banking,
- wallet,
- cash,
- bank transfer.

Payment states:

```text
Pending
Authorized
Paid
Failed
Refunded
Partially Refunded
```

Never trust client-side payment success.

Verify payment-provider webhook signatures.

Use idempotency for payment creation, capture, refund and webhook processing.

---

# 19. INVENTORY / PROCUREMENT / VENDORS

Inventory:
- category,
- SKU,
- unit,
- warehouse/store,
- stock level,
- batch,
- expiry,
- movement,
- transfer,
- consumption,
- adjustment.

Procurement workflow:

```text
Low Stock
→ Purchase Request
→ Approval
→ Purchase Order
→ Vendor
→ Delivery
→ Quality Check
→ Inventory
→ Invoice
```

Vendor:
- contacts,
- products/services,
- contracts,
- pricing,
- payment terms,
- purchase history,
- ratings,
- documents.

Use transactions around stock movements to prevent inconsistent inventory.

---

# 20. STAFF / HR / ATTENDANCE

Departments:
- Management,
- Front Office,
- Housekeeping,
- F&B,
- Kitchen,
- Maintenance,
- Security,
- Accounts,
- HR,
- Sales,
- Marketing.

Employee:
- designation,
- department,
- shift,
- attendance,
- salary,
- leave,
- documents,
- performance.

Shift examples:
- Morning 06:00–14:00
- Evening 14:00–22:00
- Night 22:00–06:00

Attendance channels:
- web/app,
- QR,
- GPS where legally/operationally appropriate,
- biometric integration.

Support:
- overtime,
- late arrival,
- early departure,
- leave requests,
- manager approval.

Protect HR and salary data with stricter permission scopes.

---

# 21. COMMUNICATION / SUPPORT

Central communication services:
- email,
- SMS,
- WhatsApp,
- push notifications,
- in-app chat.

Automations:
- booking confirmation,
- payment confirmation,
- check-in reminder,
- welcome message,
- service update,
- checkout reminder,
- invoice,
- review request.

Helpdesk ticket types:
- complaint,
- service request,
- maintenance,
- billing,
- lost item.

Ticket states:

```text
Open
Assigned
In Progress
Waiting
Resolved
Closed
```

Run scheduled/outbound notifications asynchronously with Celery.

---

# 22. LOYALTY / REVIEWS / MARKETING

Loyalty:
- points,
- redemption,
- expiry,
- transaction history,
- tiers.

Example configurable tiers:
- Bronze,
- Silver,
- Gold,
- Platinum.

Rewards:
- room discounts,
- breakfast,
- late checkout,
- upgrades,
- complimentary services.

Reviews:
- property,
- room,
- food,
- staff,
- cleanliness,
- service,
- facilities,
- value.

Marketing:
- promo codes,
- coupons,
- packages,
- campaigns,
- referral programs.

Prevent unauthorized manipulation of loyalty points or review ownership.

---

# 23. DYNAMIC / DEMAND-BASED PRICING

Inputs:

```text
Current Occupancy
Forecast Occupancy
Historical Demand
Day / Weekend
Season / Holiday
Event Calendar
Booking Pace
```

Engine:

```text
Rules
Thresholds
Minimum Rate
Maximum Rate
Rate Plan Mapping
        ↓
Calculated Rate
```

Demand bands:
- Low,
- Normal,
- High,
- Surge.

Support:
- seasonal calendars,
- holidays,
- events,
- blackout dates,
- minimum-stay,
- closed-to-arrival,
- closed-to-departure,
- early-bird,
- last-minute,
- long-stay,
- corporate,
- loyalty pricing.

Every automated/manual adjustment must record:
- rule,
- old rate,
- new rate,
- timestamp,
- actor/system job,
- property,
- rate plan.

Do not allow price changes that bypass min/max controls.

---

# 24. OTA / CHANNEL MANAGEMENT

Build a pluggable channel-management layer.

Target integrations from the blueprint include:
- Booking.com,
- Agoda,
- Expedia.

Do not hardwire provider-specific business logic into reservations.

Use:

```text
Internal Channel Interface
        |
        +-- Booking.com Adapter
        +-- Agoda Adapter
        +-- Expedia Adapter
        +-- Future Adapter
```

Outbound synchronization:
- availability,
- inventory,
- prices,
- restrictions,
- mappings.

Inbound:
- reservations,
- modifications,
- cancellations,
- webhooks/events.

Implement:
- external reservation IDs,
- mapping tables,
- idempotency,
- retries,
- dead-letter handling,
- reconciliation,
- inventory locking,
- atomic reservation operations,
- connection health,
- last sync,
- error tracking.

Store raw webhook events for troubleshooting, securely and with retention controls.

---

# 25. GATE SECURITY

Dedicated property-scoped security subsystem.

Track:
- guest entries,
- visitor logs,
- vendor entry,
- contractor entry,
- staff movement,
- vehicle movement,
- material movement,
- checkpoints,
- approvals,
- incidents,
- notes,
- audit log.

Entry fields:
- identity,
- purpose,
- host,
- room,
- vehicle,
- entry time,
- exit time,
- security notes.

Vehicle:
- number plate,
- driver,
- purpose,
- destination.

Material movement:
- inbound delivery,
- stock/equipment movement,
- outgoing item.

Security staff must not gain financial permissions merely because they can access security workflows.

---

# 26. CLOAKROOM / LUGGAGE

Use unique ticket/tag IDs.

Optional:
- QR,
- barcode.

Track:
- guest/owner,
- reservation,
- room,
- item count,
- description,
- deposit time,
- staff,
- storage location.

Support:
- partial release,
- identity verification,
- authorized release,
- lost/damaged incidents,
- evidence references.

Prevent duplicate claims with server-side ticket validation.

---

# 27. TRANSPORT / FLEET / CHAUFFEUR

Services:
- airport pickup/drop,
- hotel shuttle,
- point-to-point,
- corporate transport,
- chauffeur.

Fleet:
- vehicle category,
- capacity,
- registration,
- permits,
- insurance,
- availability,
- maintenance status.

Driver:
- identity,
- license,
- availability,
- shift,
- vehicle assignment,
- service rating.

Trip lifecycle:

```text
Requested
→ Quoted
→ Assigned
→ Driver Confirmed
→ En Route
→ Arrived
→ Picked Up
→ Completed
→ Billed
```

Transport request flow:

```text
Transport Request
→ Capacity Check
→ Internal Fleet OR External Provider API
→ Assignment
→ Driver / Vehicle
→ Trip
→ Billing
→ Customer Charge + Vendor Cost + Margin
```

Track:
- internal/external fulfillment,
- vendor cost,
- customer charge,
- margin,
- reconciliation.

---

# 28. EXTERNAL TRANSPORT PROVIDER ADAPTERS

Internal contract:

```text
POST /transport/quote
POST /transport/book
GET  /transport/{id}
POST /transport/{id}/cancel
```

Normalize:
- quote,
- ETA,
- vehicle category,
- fare,
- driver details,
- booking,
- cancellation,
- status.

Implement:
- timeouts,
- retries,
- fallback,
- reconciliation,
- provider booking IDs,
- fulfillment state,
- provider-specific credential isolation.

The guest-facing contract must not change when a provider adapter is replaced.

---

# 29. REAL-TIME ARCHITECTURE

Use Django Channels + Redis.

WebSocket domains:
- kitchen orders,
- KOT updates,
- housekeeping,
- maintenance,
- guest chat,
- room status,
- front desk,
- notifications,
- transport status where needed.

Enforce authorization during WebSocket connection and per-message/channel subscription.

Never rely on a client-controlled room/property ID for WebSocket isolation.

---

# 30. CELERY / ASYNC PROCESSING

Use Celery for:
- email,
- SMS,
- WhatsApp jobs,
- push notifications,
- report generation,
- scheduled jobs,
- payment reconciliation,
- OTA synchronization,
- integration retries,
- AI processing,
- analytics aggregation where appropriate.

Requirements:
- idempotent tasks,
- retries with bounded backoff,
- failure visibility,
- task IDs,
- structured logging,
- dead-letter/failure tracking,
- timeout configuration,
- operational metrics.

Do not place critical user-facing transactional writes solely inside unreliable async work.

---

# 31. AUDIT LOGGING

Audit sensitive actions:

- login,
- logout,
- permission change,
- booking edits,
- reservation cancellation,
- room transfer,
- check-in/out,
- rate changes,
- manual rate overrides,
- folio adjustments,
- refunds,
- payment actions,
- financial adjustments,
- KOT modifications,
- security actions,
- cloakroom release,
- transport reassignment,
- shareholder report access,
- integration changes.

Audit record should include as appropriate:
- actor,
- action,
- resource type,
- resource ID,
- organization,
- property,
- timestamp,
- request ID,
- IP/device metadata where appropriate,
- before/after summary,
- reason/comment for sensitive changes.

Do not store secrets in audit logs.

---

# 32. API ARCHITECTURE

Version all APIs:

```text
/api/v1/
```

Baseline resources:

```text
auth/
organizations/
corporate/
shareholders/
properties/
rooms/
room-types/
availability/
reservations/
guests/
check-in/
check-out/
folios/
housekeeping/
maintenance/
restaurants/
menu/
orders/
kot/
events/
services/
spa/
activities/
payments/
invoices/
inventory/
procurement/
vendors/
staff/
employees/
attendance/
loyalty/
reviews/
marketing/
pricing/
channels/
security/
cloakroom/
transport/
reports/
analytics/
notifications/
integrations/
audit/
```

Corporate enhanced endpoints:

```text
/api/v1/corporate/executives/
/api/v1/corporate/portfolio/
/api/v1/corporate/dashboards/

/api/v1/shareholders/portfolio/
/api/v1/shareholders/financials/
/api/v1/shareholders/dividends/
/api/v1/shareholders/reports/

/api/v1/folios/{id}/charges/

/api/v1/kot/orders/
/api/v1/kot/stations/
/api/v1/kot/queues/
/api/v1/kot/{id}/status/

/api/v1/pricing/rules/
/api/v1/pricing/seasons/
/api/v1/pricing/demand/
/api/v1/pricing/audits/

/api/v1/channels/connections/
/api/v1/channels/mappings/
/api/v1/channels/sync/
/api/v1/channels/reconciliation/

/api/v1/security/gate-entries/
/api/v1/security/visitors/
/api/v1/security/vehicles/
/api/v1/security/materials/
/api/v1/security/cloakroom/

/api/v1/transport/vehicles/
/api/v1/transport/drivers/
/api/v1/transport/requests/
/api/v1/transport/trips/
/api/v1/transport/shuttles/
/api/v1/transport/providers/
```

Use:
- pagination,
- filtering,
- sorting,
- search,
- validation,
- consistent error structures,
- idempotency for critical commands.

Preferred command examples:

```text
GET  /availability?property=&check_in=&check_out=&adults=&children=
POST /reservations/
POST /reservations/{id}/confirm/
POST /reservations/{id}/cancel/
POST /stays/{id}/check-in/
POST /stays/{id}/check-out/
POST /orders/
GET  /kitchen/orders/
POST /payments/create/
POST /payments/webhook/
GET  /reports/occupancy/
GET  /reports/revenue/
GET  /reports/adr/
GET  /reports/revpar/
```

---

# 33. API CONTRACT STANDARDS

Every API must clearly document:

- purpose,
- HTTP method,
- URL,
- authentication,
- required permissions,
- organization/property scope,
- request headers,
- request body,
- validation rules,
- success response,
- error responses,
- pagination,
- filtering,
- examples,
- idempotency behavior,
- side effects,
- emitted domain events,
- audit behavior.

Generate OpenAPI/Swagger documentation.

Maintain API contract documentation as a first-class deliverable because web, mobile and partner integrations share the backend.

---

# 34. DATABASE DESIGN RULES

Use PostgreSQL in production.

General model requirements:
- UUID primary keys where suitable,
- explicit timestamps,
- created_by/updated_by where useful,
- organization_id/property_id where required,
- database constraints,
- meaningful indexes,
- unique constraints,
- foreign-key protection,
- soft-delete only where business/audit requirements justify it,
- immutable financial records where appropriate,
- immutable event IDs.

Model financial records as append-oriented/auditable data where practical instead of silently overwriting historical facts.

Use migrations properly.

Never edit an old applied migration in a shared/production environment without a deliberate migration strategy.

---

# 35. SECURITY

Implement:
- secure password hashing,
- JWT refresh-token security,
- 2FA for privileged roles,
- object-level permissions,
- tenant isolation,
- rate limiting,
- CORS controls,
- secure headers,
- CSRF protection where applicable,
- input validation,
- output filtering,
- TLS,
- encrypted sensitive data where appropriate,
- secure file/document access,
- signed URLs,
- webhook signature verification,
- secret isolation,
- dependency vulnerability management.

Never:
- trust tenant IDs supplied by the client,
- trust role names supplied by the client,
- trust payment success sent by the browser,
- expose integration credentials,
- return unrestricted model serializers for sensitive objects,
- use sequential IDs as the sole authorization mechanism.

---

# 36. ERROR HANDLING AND OBSERVABILITY

Provide:
- standardized API error envelope,
- structured logs,
- request/correlation IDs,
- exception monitoring,
- Celery task failure visibility,
- webhook failure visibility,
- integration status,
- health endpoints,
- readiness/liveness checks,
- database/Redis connectivity monitoring.

Production operations should be able to answer:

```text
Who experienced the error?
Which request?
Which organization/property?
Which resource?
Which server/task?
What exception?
What was the previous state?
What external provider was involved?
Was the transaction rolled back?
Was a retry performed?
```

Use error tracking such as Sentry or an equivalent production service if the repository/project does not already provide one.

---

# 37. REPORTING AND ANALYTICS

Support:

### Corporate
- consolidated revenue,
- P&L,
- occupancy,
- ADR,
- RevPAR,
- property comparison.

### Shareholder
- approved P&L,
- dividend ledger,
- ownership summary,
- selected portfolio KPIs.

### Pricing
- occupancy vs rate,
- booking pace,
- seasonal performance,
- demand,
- rate adjustments.

### OTA
- production,
- revenue,
- cancellations,
- sync health,
- mapping errors.

### Operations
- room turnaround,
- KOT preparation time,
- service SLA,
- maintenance,
- gate traffic.

### Transport
- trips,
- utilization,
- internal/external fulfillment,
- vendor cost,
- customer revenue,
- margin.

### Security
- visitors,
- vehicle/material movement,
- cloakroom,
- incidents.

Hospitality KPI definitions:

```text
Occupancy Rate = Occupied Rooms / Available Rooms × 100
ADR            = Room Revenue / Rooms Sold
RevPAR         = Room Revenue / Available Rooms
Average LOS    = Total Room Nights / Reservations or Stays
Cancellation   = Cancelled Bookings / Total Bookings
No-show        = No-show Bookings / Total Bookings
Direct Share   = Direct Bookings / Total Bookings
OTA Share      = OTA Bookings / Total Bookings
F&B Revenue    = Restaurant + Room Service + Banquet Food Revenue
```

Dashboards must support:
- daily,
- weekly,
- monthly,
- yearly,
- property,
- room,
- channel,
- department drill-downs.

---

# 38. AI / ADVANCED FEATURES

Design extension points for:
- AI concierge,
- room/restaurant/activity/package recommendations,
- occupancy forecasting,
- demand forecasting,
- revenue intelligence,
- review sentiment analysis,
- anomaly alerts,
- natural-language management reports.

Do not make AI a hard dependency for core hotel operations.

AI failures must not block:
- reservations,
- check-in,
- check-out,
- payments,
- folio posting,
- KOT workflow,
- room status.

---

# 39. STORAGE

Use S3-compatible object storage for:
- property media,
- guest documents,
- identity documents,
- invoices,
- approved shareholder reports,
- evidence attachments.

Implement:
- signed URLs,
- content type validation,
- file-size limits,
- malware-scanning hook if required,
- access policy by tenant/property/role,
- retention/deletion policy.

---

# 40. TESTING STRATEGY

Minimum test layers:

### Unit tests
- pricing,
- tax,
- availability,
- folio calculations,
- permissions,
- KOT transitions,
- transport selection,
- inventory calculations.

### API tests
- authentication,
- authorization,
- tenant isolation,
- CRUD,
- filtering,
- pagination,
- errors,
- idempotency.

### Transaction/concurrency tests
- double booking,
- duplicate payment webhook,
- duplicate charge event,
- simultaneous KOT updates,
- inventory race conditions.

### Integration tests
- payment webhook,
- OTA adapter,
- transport adapter,
- object storage,
- Celery,
- Redis,
- WebSocket.

### Security tests
Explicitly test attempts to:
- change organization ID,
- change property ID,
- access another guest,
- access another reservation,
- view another user's document,
- refund another property,
- mutate shareholder reports,
- view another vendor's transport job,
- subscribe to another property's WebSocket events.

### Regression
Every previously discovered production bug must receive a regression test.

---

# 41. CI/CD AND QUALITY GATES

Pipeline should include:

```text
Install
→ Lint
→ Type/static checks where applicable
→ Unit tests
→ API tests
→ Security checks
→ Migration checks
→ Build
→ Deployment
→ Smoke tests
```

Block deployment on:
- failing tests,
- missing required migrations,
- critical secret exposure,
- obvious tenant-isolation failures,
- broken API contract generation.

---

# 42. REQUIRED DOCUMENTATION OUTPUT

Create/maintain:

```text
README.md
docs/
  architecture.md
  domain-model.md
  tenancy-and-access-control.md
  authentication.md
  api.md
  api-examples.md
  events.md
  celery.md
  websockets.md
  integrations.md
  payments.md
  ota.md
  transport-providers.md
  security.md
  deployment.md
  observability.md
  testing.md
  troubleshooting.md
  data-retention.md
```

README must explain in plain language:
- what the system does,
- who uses it,
- major modules,
- data flow,
- local setup,
- environment variables,
- migrations,
- running API,
- running Celery,
- running Redis,
- running WebSocket server,
- running tests,
- production deployment.

---

# 43. SUGGESTED REPOSITORY STRUCTURE

Prefer:

```text
hospitality_backend/
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py
├── apps/
│   ├── accounts/
│   ├── organizations/
│   ├── corporate/
│   ├── shareholders/
│   ├── properties/
│   ├── rooms/
│   ├── availability/
│   ├── reservations/
│   ├── guests/
│   ├── frontoffice/
│   ├── housekeeping/
│   ├── maintenance/
│   ├── restaurants/
│   ├── kitchen/
│   ├── events/
│   ├── services/
│   ├── spa/
│   ├── activities/
│   ├── transportation/
│   ├── payments/
│   ├── billing/
│   ├── finance/
│   ├── inventory/
│   ├── procurement/
│   ├── vendors/
│   ├── employees/
│   ├── attendance/
│   ├── crm/
│   ├── loyalty/
│   ├── reviews/
│   ├── marketing/
│   ├── notifications/
│   ├── communications/
│   ├── pricing/
│   ├── channels/
│   ├── security/
│   ├── cloakroom/
│   ├── reports/
│   ├── analytics/
│   ├── integrations/
│   └── audit_logs/
├── common/
│   ├── permissions/
│   ├── tenancy/
│   ├── exceptions/
│   ├── idempotency/
│   ├── audit/
│   ├── pagination/
│   ├── validators/
│   └── utils/
├── tests/
├── docs/
├── .env.example
├── .gitignore
├── pyproject.toml / requirements.txt
└── README.md
```

Do not create unnecessary abstractions merely for appearance. Prefer simple, explicit, testable code.

---

# 44. DEVELOPMENT ROADMAP

Use this implementation order unless the audit identifies a blocking dependency:

### Phase 1 — Enterprise Foundation
- authentication,
- organizations,
- tenancy,
- corporate hierarchy,
- RBAC,
- properties,
- rooms,
- guests,
- reservations,
- availability.

### Phase 2 — PMS and Front Office
- room assignment,
- check-in/out,
- folio,
- billing,
- payments.

### Phase 3 — Operations
- housekeeping,
- maintenance,
- service requests,
- notifications,
- staff basics.

### Phase 4 — F&B and KOT
- restaurant,
- POS,
- menus,
- tables,
- KOT,
- kitchen queues,
- room posting.

### Phase 5 — Banquets
- events,
- venues,
- room blocks,
- rooming lists,
- master/individual folios.

### Phase 6 — Pricing and Distribution
- pricing rules,
- seasonal pricing,
- dynamic pricing,
- OTA adapters,
- mapping,
- reconciliation.

### Phase 7 — Corporate Governance
- executive dashboards,
- consolidated analytics,
- shareholder portal,
- dividends.

### Phase 8 — Security
- gate,
- visitors,
- vehicles,
- materials,
- cloakroom.

### Phase 9 — Transport
- fleet,
- drivers,
- airport transfers,
- shuttles,
- chauffeur,
- external provider adapters.

### Phase 10 — Intelligence
- forecasting,
- AI concierge,
- recommendations,
- sentiment,
- revenue intelligence,
- AI reports.

The general MVP should prioritize stable, auditable PMS fundamentals before OTA synchronization and advanced finance.

---

# 45. DEFINITION OF DONE

A module is not complete merely because its model, endpoint, or page exists.

A feature is complete only when:

- data model exists,
- migrations are valid,
- scoped permissions exist,
- object-level isolation is tested,
- service/business rules are implemented,
- API endpoints exist,
- validation exists,
- error handling exists,
- audit behavior exists where required,
- idempotency exists where required,
- concurrency behavior is safe where required,
- unit/API/security tests exist,
- documentation exists,
- OpenAPI is updated,
- frontend contract is clear,
- logs/observability exist for operational failures.

---

# 46. FINAL HANDOFF OUTPUT

When implementation work begins, return:

1. Architecture summary.
2. Repository tree.
3. Model/entity map.
4. Permission matrix.
5. API endpoint matrix.
6. Domain events list.
7. Celery task list.
8. WebSocket channel list.
9. Integration adapter list.
10. Migration plan.
11. Test plan.
12. Security test matrix.
13. Deployment plan.
14. README/documentation plan.
15. Phase-by-phase implementation checklist.

For every implementation step, show:
- files to create/change,
- reason,
- dependencies,
- migration impact,
- API impact,
- authorization impact,
- tests required.

Never silently weaken tenant isolation, auditing, idempotency, or authorization to make a feature easier to implement.
