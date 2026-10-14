# TamilNadu Transit 360 AI - Architecture Decisions Record (ADR)

## ADR-001: Monorepo Layout and Multi-Platform Target
- **Decision:** Structure project as a unified monorepo with:
  - `/backend`: Python FastAPI with SQLAlchemy 2, Alembic, Pydantic v2, APScheduler, WebSockets.
  - `/admin-web`: React + Vite + Tailwind CSS + Leaflet for Depot Managers and State Admins.
  - `/mobile`: React Native (Expo) supporting Passenger, Driver, Conductor, and Employee views. Includes Expo Web bundling so that it can also run as an interactive web mobile preview without requiring physical mobile devices.
  - `/ml`: Dedicated Python scikit-learn and OpenCV modules with training scripts and metric evaluations saved to `/ml/reports`.
  - `/docker`: Dockerfiles and `docker-compose.yml` for unified local containerization.
- **Rationale:** Ensures clean code sharing, rapid local verification, and easy deployment.

## ADR-002: Dual Database Strategy (PostgreSQL + SQLite Dual-Engine)
- **Decision:** Support both PostgreSQL (with PostGIS in Docker) and SQLite (with spatial distance math fallback in Python) through SQLAlchemy 2 ORM.
- **Rationale:** When Docker or PostgreSQL is available, PostgreSQL is used. When running on environments without Docker or active PostgreSQL service, SQLite seamlessly works out of the box with zero setup hurdles, while maintaining identical schema and query semantics.

## ADR-003: Cryptographically Signed QR Tickets & Passes
- **Decision:** Generate tamper-proof QR payloads containing:
  `{ "ticket_id": uuid, "trip_id": uuid, "fare": float, "passenger_name": str, "timestamp": int, "sig": hmac_sha256(secret, payload) }`
- **Rationale:** Enables conductors to validate tickets even when offline or in poor connectivity areas. The signature cannot be forged without the server's private secret.

## ADR-004: Live GPS Tracking via WebSocket and Simulation Loop
- **Decision:** Provide a real-time WebSocket `/ws/tracking` endpoint and a background GPS Simulator that advances buses along their designated route stop coordinates in 5-second intervals.
- **Rationale:** Simulates live bus movement across Tamil Nadu corridors (Chennai-Madurai, Coimbatore-Trichy, etc.) without requiring physical GPS hardware.

## ADR-005: Mock External Adapters
- **Decision:**
  - Mock Payment Gateway: Returns instant authorization with transaction reference.
  - Mock FCM Notifications: Emits in-app alerts and stores notifications in the database.
  - Mock Government Registry: Pre-seeded employee directory with service numbers and verified family member links.
- **Rationale:** Strictly honors the rule: no connection to real government or banking infrastructure; all external interfaces are cleanly isolated behind mock adapters.

## ADR-006: Driver Drowsiness Detection Architecture
- **Decision:** Computer vision pipeline uses OpenCV + Eye Aspect Ratio (EAR) calculations with a real-time web demo page and video/webcam feed processing.
- **Rationale:** Complies with privacy requirements: no raw video frames are permanently stored; only state events (e.g. `DROWSINESS_ALERT`) are logged. Assistive only, never punitive.

## ADR-007: Journey Autopilot Scheduler
- **Decision:** Use APScheduler with SQLite/SQLAlchemy persistent job store and a 1-minute evaluation cycle.
- **Rationale:** Evaluates passenger commute rules, checks seat inventory, confirms monthly spending caps, and executes bookings safely with pre/post notifications.
