/** Browser-only, deterministic synthetic security telemetry for public Pages previews.
 * All addresses are TEST-NET examples. No API requests and no real incidents.
 */
const users = ["demo-admin","demo-analyst","demo-operator","demo-auditor","demo-service","demo-reviewer"];
const hosts = ["lab-win01","lab-linux01","lab-workstation","lab-vm02"];
const ips = ["192.0.2.10","198.51.100.25","203.0.113.40","192.0.2.45"];
const severities = ["high","medium","critical","low"] as const;
const statuses = ["new","acknowledged","investigating","resolved"] as const;

export function makeSyntheticPreview(reference = new Date()) {
  const events = Array.from({ length: 36 }, (_, i) => ({
    id: 36 - i,
    timestamp: new Date(reference.getTime() - (i * 4 + 2) * 60_000).toISOString(),
    event_type: i % 4 === 0 ? "login_success" : "login_failure",
    username: users[(i * 3 + Math.floor(i / 6)) % users.length],
    source_ip: ips[(i + Math.floor(i / 7)) % ips.length],
    host: hosts[i % hosts.length],
  }));
  const alerts = Array.from({ length: 8 }, (_, i) => ({
    id: 8 - i,
    rule_id: i % 2 ? "SF-AUTH-002" : "SF-AUTH-001",
    title: i % 2 ? "Multiple accounts from one source (synthetic)" : "Repeated login failures (synthetic)",
    severity: severities[i % severities.length],
    description: "FICTIONAL EXAMPLE. This alert is generated for a dashboard preview and was not detected by a live system.",
    evidence: [events[i * 3].id, events[i * 3 + 1].id],
    source_ip: ips[i % ips.length],
    username: i % 2 ? null : users[i % users.length],
    first_seen: events[Math.min(i * 4 + 3, events.length - 1)].timestamp,
    last_seen: events[i * 3].timestamp,
    status: statuses[i % statuses.length],
    updated_at: null,
  }));
  const countBy = (items: Array<string>) => items.reduce<Record<string,number>>((counts,key) => {
    counts[key] = (counts[key] ?? 0) + 1; return counts;
  }, {});
  return {
    events,
    alerts,
    metrics: {
      events: { total: events.length, by_type: countBy(events.map(e => e.event_type)), latest_at: events[0].timestamp },
      alerts: { total: alerts.length, by_severity: countBy(alerts.map(a => a.severity)),
        by_status: countBy(alerts.map(a => a.status)), latest_at: alerts[0].last_seen },
    },
  };
}
