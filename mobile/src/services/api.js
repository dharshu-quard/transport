const API_BASE = 'http://127.0.0.1:8000/api';

class MobileApiService {
  constructor() {
    this.token = localStorage.getItem('transit360_mobile_token') || '';
  }

  setToken(t) {
    this.token = t;
    localStorage.setItem('transit360_mobile_token', t);
  }

  clearToken() {
    this.token = '';
    localStorage.removeItem('transit360_mobile_token');
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      ...(options.headers || {})
    };

    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let errDetail = 'Request failed';
      try {
        const errJson = await res.json();
        errDetail = errJson.detail || errJson.message || errDetail;
      } catch (e) {}
      throw new Error(errDetail);
    }
    return res.json();
  }

  // Auth
  loginOtp(phone, otp = '123456') {
    return this.request('/auth/login-otp', {
      method: 'POST',
      body: JSON.stringify({ phone, otp })
    });
  }

  // Passenger Core
  getStops() {
    return this.request('/passenger/stops');
  }

  searchRoutes(fromStopId, toStopId) {
    return this.request(`/passenger/routes/search?from_stop_id=${fromStopId}&to_stop_id=${toStopId}`);
  }

  getSeatMap(tripId) {
    return this.request(`/passenger/trips/${tripId}/seat-map`);
  }

  bookTicket(tripId, fromStopId, toStopId, passengerName, seatNumber, paymentMethod = 'upi') {
    return this.request('/passenger/bookings', {
      method: 'POST',
      body: JSON.stringify({
        trip_id: tripId,
        from_stop_id: fromStopId,
        to_stop_id: toStopId,
        passenger_name: passengerName,
        seat_number: seatNumber,
        payment_method: paymentMethod
      })
    });
  }

  getBookingHistory() {
    return this.request('/passenger/bookings/history');
  }

  cancelBooking(bookingId, reason = 'Schedule changed') {
    return this.request(`/passenger/bookings/${bookingId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  }

  // Safety & Tracking
  getLiveFleet() {
    return this.request('/tracking/live-fleet');
  }

  validateBoardedBus(ticketId, busReg) {
    return this.request('/tracking/validate-boarded-bus', {
      method: 'POST',
      body: JSON.stringify({
        ticket_id: ticketId,
        boarded_bus_registration: busReg
      })
    });
  }

  getMissedBusAlternatives(currentStopId) {
    return this.request(`/tracking/missed-bus-alternatives?current_stop_id=${currentStopId}`);
  }

  // Journey Autopilot
  getAutopilotPlan() {
    return this.request('/autopilot/plan');
  }

  createAutopilotPlan(plan) {
    return this.request('/autopilot/plan', {
      method: 'POST',
      body: JSON.stringify(plan)
    });
  }

  toggleAutopilot() {
    return this.request('/autopilot/plan/toggle', { method: 'POST' });
  }

  triggerAutopilotCron() {
    return this.request('/autopilot/trigger-cron', { method: 'POST' });
  }

  // Driver
  getDriverDuty() {
    return this.request('/driver/duty/current');
  }

  driverCheckIn() {
    return this.request('/driver/duty/check-in', { method: 'POST' });
  }

  driverCheckOut() {
    return this.request('/driver/duty/check-out', { method: 'POST' });
  }

  submitInspection(data) {
    return this.request('/driver/inspections', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  reportBreakdown(data) {
    return this.request('/driver/breakdowns', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  triggerSos(data) {
    return this.request('/driver/sos', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  getLicenceStatus() {
    return this.request('/driver/licence-status');
  }

  // Conductor
  validateQr(qrString) {
    return this.request('/conductor/validate-qr', {
      method: 'POST',
      body: JSON.stringify({ qr_string: qrString })
    });
  }

  issueSpotTicket(data) {
    return this.request('/conductor/issue-ticket', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  getPassengerCount(tripId) {
    return this.request(`/conductor/passenger-count/${tripId}`);
  }

  getReconciliation() {
    return this.request('/conductor/reconcile', { method: 'POST' });
  }

  // Employee & Passes
  getPassProfile() {
    return this.request('/passes/my-profile');
  }

  addFamilyMember(data) {
    return this.request('/passes/family-members', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  applyPass(data) {
    return this.request('/passes/apply', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  verifyPass(qrString) {
    return this.request('/passes/verify', {
      method: 'POST',
      body: JSON.stringify({ qr_string: qrString })
    });
  }
}

export const mobileApi = new MobileApiService();
