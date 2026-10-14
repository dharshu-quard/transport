# TamilNadu Transit 360 AI - Implementation Progress

**Project Status:** Active Development  
**Last Updated:** Phase 1 Initialization  
**System Architecture:** Full-Stack Monorepo (FastAPI + React Admin Web + React Native/Expo Mobile + ML Services)

---

## Milestone Status Summary

| Milestone | Description | Status | Tests | Notes |
|---|---|---|---|---|
| **M1** | Foundation (Monorepo, DB Models, RBAC, Auth, Seed Data, i18n) | IN PROGRESS | Pending | 34 tables, 4 depots, 60 buses, 20 routes |
| **M2** | Passenger Core (Search, Seat Alloc, Booking, Fare, QR, Cancel/Refund) | PENDING | Pending | Offline tamper-proof HMAC QR |
| **M3** | Live Tracking & Safety (WS GPS, ETA, Live Map, Dest/Wrong-bus alert) | PENDING | Pending | 5s ping simulator + audio/voice cues |
| **M4** | Driver & Conductor Portals (Inspection, Duty, SOS, QR Scan, Reconcile) | PENDING | Pending | Conductor digital tickets & counter |
| **M5** | Admin & Depot Web (Fleet, Duty Alloc, Leave, Maintenance, Revenue, Audits)| PENDING | Pending | Depot-scoped + Global admin view |
| **M6** | Employee & Family Pass (Rules, Document Upload, Review, QR Pass) | PENDING | Pending | Dynamic rules in config_rules table |
| **M7** | Journey Autopilot (Consent, Commute Plan, Scheduler, Auto-booking) | PENDING | Pending | APScheduler daemon with safety stops |
| **M8** | Complaints & Lost & Found (Photo submission, ML classification, Matching) | PENDING | Pending | Auto-categorization model |
| **M9** | AI Services (8 ML modules, Reports, Insights Dashboard, Drowsiness) | PENDING | Pending | Scikit-learn + OpenCV EAR alerts |
| **M10** | Hardening & Demo Verification (Acceptance checks 1-12, Walkthrough) | PENDING | Pending | All 12 acceptance checks pass |

---

## Detailed Milestone Checklist

### M1 Foundation
- [x] Monorepo structure (`/backend`, `/mobile`, `/admin-web`, `/ml`, `/docker`, `/docs`)
- [x] Environment configuration (`.env`, `.env.example`)
- [x] Architectural decisions recorded (`DECISIONS.md`)
- [ ] Database models (34 tables with UUID PKs, audit timestamps, soft delete, indexes, FKs)
- [ ] RBAC & JWT authentication with OTP login (Dev OTP: `123456`)
- [ ] Depot-scoped permissions + Admin audit logging
- [ ] i18n support (Tamil + English)
- [ ] Realistic synthetic seed dataset (Corporations, Depots, Buses, Routes, Staff, Passengers, Historical trips/GPS)

### M2 Passenger Core
- [ ] Route and stop search with stage-based fare computation
- [ ] Seat availability map & allocation
- [ ] Mock payment gateway (UPI, Card, NetBanking) with instant callback
- [ ] Cryptographically signed offline QR ticket (HMAC-SHA256)
- [ ] Journey history & cancellation with configurable refund rules

### M3 Live Tracking + Journey Safety
- [ ] Driver GPS simulator (5-second pings via WebSocket)
- [ ] Live Leaflet + OSM map for passengers and depot managers
- [ ] ETA baseline calculation + AI arrival comparison
- [ ] Destination alert (audio/voice alarm within radius + missed stop loud alert)
- [ ] Wrong-bus mismatch detection & missed-bus alternative route finder

### M4 Driver & Conductor
- [ ] Driver dashboard (Schedule, Check-in/out, Pre-trip inspection checklist)
- [ ] Driver incident reporting & SOS panic trigger
- [ ] Driver leave & duty-change request workflow
- [ ] Conductor QR scanner & validator (rejects forged/duplicate/expired tickets)
- [ ] Conductor spot ticketing & real-time passenger counter
- [ ] Cash vs Digital collection reconciliation

### M5 Admin and Depot Web
- [ ] Role-scoped dashboard (Depot Manager vs State Admin)
- [ ] CRUD for fleet, routes, stops, and crew
- [ ] Crew duty allocation & attendance/leave approval
- [ ] Fleet maintenance & fuel records
- [ ] Revenue and booking analytics with CSV exports
- [ ] Live fleet monitoring map & audit log viewer

### M6 Employee and Family Pass
- [ ] Mock employee registry verification
- [ ] Admin-configurable eligibility rules
- [ ] Family member registration & document upload (access-controlled)
- [ ] Multi-stage pass approval (Depot Review -> Admin Approval)
- [ ] Tamper-proof QR pass issuance & conductor validation mode

### M7 Journey Autopilot
- [ ] Passenger recurring commute plan setup with explicit consent
- [ ] Automated scheduled booking engine with safety spending caps
- [ ] Pre-booking reminders and post-booking notification alerts
- [ ] Failure recovery & pause/resume controls

### M8 Complaints, Lost and Found
- [ ] Complaint portal with photo upload and ML category routing
- [ ] Depot resolution workflow and status tracking
- [ ] Lost & Found reporting with automated matching engine

### M9 AI Services
- [ ] 1. Route/hour Demand prediction
- [ ] 2. Arrival time prediction (vs baseline)
- [ ] 3. Corridor route deviation detector & alert
- [ ] 4. Predictive fleet maintenance risk score (0-100)
- [ ] 5. Demand-driven bus allocation engine
- [ ] 6. Velocity pass fraud / duplicate scan detector
- [ ] 7. Complaint auto-categorization NLP model
- [ ] 8. Driver drowsiness detector (OpenCV Eye Aspect Ratio)
- [ ] Interactive "AI Insights" web interface

### M10 Hardening & Acceptance Checks
- [ ] Automated unit & integration tests passing
- [ ] 12/12 End-to-end acceptance scenarios verified
- [ ] Complete `DEMO.md` interactive walkthrough

---

## Known Issues / Mocked External Systems
- **Government / TNSTC Registry:** Mocked via internal verified employee table.
- **Payment Gateway:** Mock adapter simulating UPI / Razorpay / NetBanking transactions.
- **SMS / Push Notifications:** In-app mock notification center and event bus simulating FCM.
- **Maps:** Free OpenStreetMap tiles via Leaflet (zero API key dependency).
