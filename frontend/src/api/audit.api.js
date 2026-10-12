/**
 * KaushalTwin — Audit Events API
 *
 * The backend stores audit events inside each assessment's report.
 * The report endpoint returns: { audit_timeline: [...], ... }
 * This module aggregates audit events from assessment reports.
 */

import apiClient from '../lib/api-client';

export const auditApi = {
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
