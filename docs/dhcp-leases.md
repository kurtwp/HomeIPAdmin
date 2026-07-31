# DHCP Lease Viewer

**Purpose:** View active DHCP leases and statically assigned clients on your UniFi network.

**Access:** Discovery → DHCP Leases, or `/dhcp-leases`

---

## Overview

The DHCP lease viewer lists every active client on your UniFi network — both DHCP leases and static assignments — pulled live from the controller.

**Data source:** The UniFi Integration API has no dedicated lease endpoint, so this uses the **legacy controller API** (`GET /proxy/network/api/s/default/stat/sta`), which includes lease expiry information (`dhcpend_time`).

---

## Page Layout

### Summary Cards

| Card | Shows |
|------|-------|
| Total Clients | All active clients |
| DHCP Leases | Clients with an active DHCP lease |
| Static | Clients with static/fixed IPs (or lease `0`) |
| Expiring/Expired | Clients whose lease has ≤ 0 seconds remaining (shown only when non-zero) |

### Clients Table

| Column | Description |
|--------|-------------|
| IP Address | Current IP |
| Hostname | Client name/hostname |
| MAC Address | Hardware address |
| Vendor | Manufacturer from device fingerprint (if available) |
| Network | VLAN/network the client is connected to |
| VLAN | VLAN tag |
| Lease Expires | Local time the lease ends ("Static" for static assignments) |
| Time Left | Human-readable time until lease expiry — ⚠️ prefix when under 1 hour |
| Connected | Client uptime |
| Type | `DHCP` or `Static` |

### Search Filter

The filter box above the table narrows rows live by IP, hostname, or MAC as you type.

---

## Understanding the Data

### Lease Expiry

`Time Left` shows how long until the DHCP lease renews:

- **Static** — the client uses a fixed IP (no DHCP lease)
- **⚠️ < 1 hour** — lease about to renew; normal for short-lease clients
- **Expired** — lease `dhcpend_time` reached zero

Lease expiry is computed from `dhcpend_time` (seconds until the lease ends) reported by the controller.

### Static vs DHCP

A client is marked **static** when:

- It has a fixed IP assignment (`useFixedIp`), or
- The lease counter is zero/missing (no DHCP lease)

---

## Refreshing

Click **Refresh** to re-fetch clients from the controller. Data is live — no database writes occur.

---

## Requirements

- UniFi Integration configured (`UNIFI_API_KEY`, `UNIFI_BASE_URL`, `UNIFI_SITE_ID` in `.env`)
- Controller must allow the legacy `/stat/sta` endpoint (default on UDM SE)
- Read-only — no lease changes are made

---

## Related

- [Firewall Rule Viewer](firewall-viewer) — security rules on the same controller
- [UniFi Sync (Local)](discovery-features) — import clients into the database for long-term tracking
- [Monitoring](monitoring) — uptime/port monitoring of discovered hosts

---

## Troubleshooting

| Problem | Cause |
|---------|-------|
| Empty list | No active clients, or API key lacks access to the legacy endpoint |
| All "Expired" | Controller returning `dhcpend_time: 0` — clients may be on short leases |
| Static for everything | Some firmware reports static for lease-less clients — verify in UniFi console |
