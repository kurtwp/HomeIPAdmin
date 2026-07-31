# Firewall Rule Viewer

**Purpose:** View firewall policies from your UniFi Dream Machine (UDM SE) directly in the Home Lab Manager.

**Access:** Discovery → Firewall Rules, or `/firewall`

---

## Overview

The firewall rule viewer pulls policies, zones, and networks from the UniFi **Integration API** and presents them in a readable, sortable table. It's a read-only view — rules are managed in the UniFi console.

**Data source:** `GET /v1/sites/{siteId}/firewall/policies` and `GET /v1/sites/{siteId}/firewall/zones`

---

## Page Layout

### Summary Cards

| Card | Shows |
|------|-------|
| Total Rules | Number of firewall policies |
| Enabled | Rules currently active |
| User Defined | Rules created by you (vs. system defaults) |

### Zones Expansion

Expandable table of all firewall zones with their mapped networks:

| Column | Description |
|--------|-------------|
| Zone | Zone name (Internal, External, Vpn, Dmz, Gateway, Hotspot) |
| Networks | VLAN/network names mapped to the zone |

Zone IDs are resolved to network names using the networks endpoint, so you can see at a glance which networks belong to which zone.

### Rules Table

Sortable table with one row per policy:

| Column | Description |
|--------|-------------|
| Order | Rule precedence — lower runs first (null = last) |
| Rule | Policy name |
| Action | `ALLOW` or `BLOCK` |
| Source | Source zone (resolved name) |
| Destination | Destination zone (resolved name) |
| IP Version | IPv4, IPv6, or IPv4 & IPv6 |
| Log | Whether logging is enabled |
| Origin | User Defined or System |
| Enabled | Rule status |

### Rule Detail Dialog

Click any row to open a detail dialog with:

- Action, source zone, destination zone
- IP version (IPv4 & IPv6 shown as "IPv4 & IPv6")
- Connection state filters (e.g. `INVALID`)
- Logging and configurable flags
- Origin (user vs. system defined)
- Traffic filter presence
- Rule ID

---

## Refreshing

Click **Refresh** to re-fetch rules from the controller. The fetch timestamp is shown below the button.

---

## Requirements

- UniFi Integration configured (`UNIFI_API_KEY`, `UNIFI_BASE_URL`, `UNIFI_SITE_ID` in `.env`)
- Console firmware with firewall policy support (UDM SE / UniFi Network 8+)
- Read-only — no rule modifications are made

---

## Troubleshooting

| Problem | Cause |
|---------|-------|
| Empty rule list | No firewall policies exist, or API key lacks permission |
| Zone shows raw UUID | Zone/network name resolution failed — check firmware version |
| Connection error | Controller unreachable or `UNIFI_BASE_URL` incorrect |
