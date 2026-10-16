/**
 * KaushalTwin — Audit Events API
 *
 * Real append-only AuditEvent ledger in MongoDB with SHA-256 hash chaining.
 */

import apiClient from '../lib/api-client';

export const auditApi = {
  /**
   * Fetch all audit events from the immutable audit ledger with optional filtering.
   */
  getAuditEvents: async (params = {}) => {
    const { data } = await apiClient.get('/api/v1/audit/events', { params });
    return data;
  },

  /**
   * Independently recompute and verify the cryptographic SHA-256 hash chain.
   * Returns verification status, counts, and tamper detection details.
   */
  verifyLedger: async () => {
    const { data } = await apiClient.get('/api/v1/audit/verify');
    return data;
  },

  /**
   * Fetch audit events for a specific assessment by pulling its report.
   * Returns the audit_timeline array from the report, or [] if unavailable.
   */
  getAssessmentAuditEvents: async (assessmentId) => {
    try {
      const { data } = await apiClient.get(`/api/v1/assessments/${assessmentId}/report`);
      return data?.audit_timeline || [];
    } catch {
      return [];
    }
  },

  /**
   * Fetch the full report for an assessment (includes audit timeline, evidence summary, tasks, etc.)
   */
  getAssessmentReport: async (assessmentId) => {
    const { data } = await apiClient.get(`/api/v1/assessments/${assessmentId}/report`);
    return data;
  },
};

export default auditApi;
