const API_BASE = 'http://127.0.0.1:8000/api';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('transit360_token') || '';
  }

  setToken(t) {
    this.token = t;
    localStorage.setItem('transit360_token', t);
  }

  clearToken() {
    this.token = '';
    localStorage.removeItem('transit360_token');
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

  getMyProfile() {
    return this.request('/auth/me');
  }

  // Live Fleet & Tracking
  getLiveFleet() {
    return this.request('/tracking/live-fleet');
  }

  getBusEta(busId, targetStopId) {
    return this.request(`/tracking/bus/${busId}/eta?target_stop_id=${targetStopId}`);
  }

  testDeviation(tripId, deviated = true) {
    return this.request('/tracking/test-deviation', {
      method: 'POST',
      body: JSON.stringify({ trip_id: tripId, deviated })
    });
  }

  // Admin Fleet CRUD
  getBuses(depotId = '') {
    return this.request(`/admin/buses${depotId ? `?depot_id=${depotId}` : ''}`);
  }

  createBus(data) {
    return this.request('/admin/buses', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  updateBus(busId, data) {
    return this.request(`/admin/buses/${busId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }

  allocateDuty(data) {
    return this.request('/admin/duties/allocate', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  getAttendance(date = '') {
    return this.request(`/admin/attendance${date ? `?date=${date}` : ''}`);
  }

  getLeaveRequests() {
    return this.request('/admin/leave-requests');
  }

  reviewLeaveRequest(requestId, status, reviewNotes) {
    return this.request(`/admin/leave-requests/${requestId}/review`, {
      method: 'POST',
      body: JSON.stringify({ status, review_notes: reviewNotes })
    });
  }

  getRevenueReports() {
    return this.request('/admin/reports/revenue');
  }

  getAuditLogs(action = '') {
    return this.request(`/admin/audit-logs${action ? `?action=${action}` : ''}`);
  }

  getConfigRules() {
    return this.request('/admin/config-rules');
  }

  updateConfigRule(key, value, description) {
    return this.request('/admin/config-rules', {
      method: 'PUT',
      body: JSON.stringify({ key, value, description })
    });
  }

  // Employee Passes
  getPassApplications() {
    return this.request('/passes/applications');
  }

  reviewPassDepot(appId, status, rejectionReason) {
    return this.request(`/passes/applications/${appId}/review-depot`, {
      method: 'POST',
      body: JSON.stringify({ status, rejection_reason: rejectionReason })
    });
  }

  approvePassAdmin(appId, status, rejectionReason) {
    return this.request(`/passes/applications/${appId}/approve-admin`, {
      method: 'POST',
      body: JSON.stringify({ status, rejection_reason: rejectionReason })
    });
  }

  // Complaints & Lost Found
  getComplaints() {
    return this.request('/support/complaints');
  }

  resolveComplaint(complaintId, resolution) {
    return this.request(`/support/complaints/${complaintId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution, status: 'resolved' })
    });
  }

  getLostFound() {
    return this.request('/support/lost-found');
  }

  // AI Insights
  getAiInsights() {
    return this.request('/ai/insights-overview');
  }

  processDrowsinessEar(earValue, driverId, busId) {
    return this.request(`/ai/process-drowsiness-frame?ear_value=${earValue}&driver_id=${driverId}&bus_id=${busId}`, {
      method: 'POST'
    });
  }

  triggerAutopilot() {
    return this.request('/autopilot/trigger-cron', {
      method: 'POST'
    });
  }

  getStops() {
    return this.request('/passenger/stops');
  }
}

export const api = new ApiService();
