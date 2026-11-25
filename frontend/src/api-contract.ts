/** Reject malformed or unexpected API responses before rendering telemetry.
 * Parsing is intentionally conservative: static hosts may return HTML on 404.
 */
type JsonRecord = Record<string, unknown>;
const record = (value: unknown): value is JsonRecord =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const text = (value: unknown) => typeof value === "string";
const count = (value: unknown) => typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
const counterMap = (value: unknown): value is Record<string, number> =>
  record(value) && Object.values(value).every(count);
const isoDate = (value: unknown) => text(value) && !Number.isNaN(Date.parse(value));
const optionalDate = (value: unknown) => value === null || isoDate(value);

export function assertDashboardPayload(
  health: unknown, events: unknown, alerts: unknown, metrics: unknown,
): void {
  if (!record(health) || health.status !== "ok" || !text(health.service) || !isoDate(health.time)) {
    throw new Error("API health response schema mismatch");
  }
  if (!Array.isArray(events) || !events.every(event =>
    record(event) && count(event.id) && isoDate(event.timestamp) &&
    (event.event_type === "login_success" || event.event_type === "login_failure") &&
    text(event.username) && text(event.source_ip) && text(event.host))) {
    throw new Error("API event response schema mismatch");
  }
  if (!Array.isArray(alerts) || !alerts.every(alert =>
    record(alert) && count(alert.id) && text(alert.rule_id) &&
    text(alert.title) && text(alert.description) &&
    ["low", "medium", "high", "critical"].includes(String(alert.severity)) &&
    ["new", "acknowledged", "investigating", "resolved", "false_positive"].includes(String(alert.status)) &&
    text(alert.source_ip) && (alert.username === null || text(alert.username)) &&
    isoDate(alert.first_seen) && isoDate(alert.last_seen) &&
    Array.isArray(alert.evidence) && alert.evidence.every(count))) {
    throw new Error("API alert response schema mismatch");
  }
  if (!record(metrics) || !record(metrics.events) || !record(metrics.alerts) ||
      !count(metrics.events.total) || !counterMap(metrics.events.by_type) ||
      !optionalDate(metrics.events.latest_at) || !count(metrics.alerts.total) ||
      !counterMap(metrics.alerts.by_severity) || !counterMap(metrics.alerts.by_status) ||
      !optionalDate(metrics.alerts.latest_at)) {
    throw new Error("API metrics response schema mismatch");
  }
}
