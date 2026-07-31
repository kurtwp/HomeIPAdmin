# REST API

> Enable external integrations with Home Assistant, Grafana, Ansible, and custom scripts.

---

## Overview

The Home Lab Manager exposes a REST API alongside the NiceGUI web interface. Both are served on the same port — no extra processes needed.

| Detail | Value |
|--------|-------|
| **Base URL** | `http://<host>:<port>/api` |
| **Auth** | `X-API-KEY` header |
| **Interactive docs** | `/api/docs` (Swagger UI) |
| **ReDoc** | `/api/redoc` |
| **OpenAPI spec** | `/api/openapi.json` |
| **Health check** | `/api/health` (no auth) |

---

## Configuration

Add to your `.env` file:

```bash
API_KEY=your_secret_key_here
```

Generate a strong key:

```bash
python3 -c "import secrets; print(secrets.token_hex(24))"
```

If `API_KEY` is empty or missing, all API requests return **503 Service Unavailable**.

---

## Authentication

Every request (except `/api/health`) must include the API key header:

```
X-API-KEY: your_secret_key_here
```

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 401 | Missing or invalid API key |
| 503 | `API_KEY` not configured in `.env` |

---

## Endpoints

### Health Check

```
GET /api/health
```

No authentication required.

```json
{
  "status": "ok",
  "service": "home-lab-manager"
}
```

---

### Dashboard

```
GET /api/dashboard
```

Returns aggregate statistics for the entire system.

```json
{
  "total_networks": 4,
  "total_ips": 87,
  "total_devices": 23,
  "active_ips": 62,
  "inactive_ips": 12,
  "unknown_ips": 13,
  "monitors_up": 18,
  "monitors_down": 2,
  "monitors_total": 20,
  "recent_changes": [
    {
      "id": 142,
      "entity_type": "device",
      "entity_name": "UniFi AP-AC-Pro",
      "action": "updated",
      "timestamp": "2026-07-26T14:30:00"
    }
  ]
}
```

---

### Networks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/networks` | List all networks |
| GET | `/api/networks/{id}` | Get single network |
| POST | `/api/networks` | Create network |
| PUT | `/api/networks/{id}` | Update network |
| DELETE | `/api/networks/{id}` | Delete network |

**Create / Update body:**

```json
{
  "name": "Office VLAN",
  "cidr": "192.168.10.0/24",
  "vlan_id": 10,
  "gateway": "192.168.10.1",
  "dns_servers": "192.168.1.53",
  "description": "Office devices",
  "dhcp_start": "192.168.10.100",
  "dhcp_end": "192.168.10.200"
}
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique ID |
| `name` | string | Network name |
| `cidr` | string | CIDR notation (e.g. `192.168.1.0/24`) |
| `vlan_id` | int \| null | VLAN tag |
| `gateway` | string \| null | Gateway IP |
| `dns_servers` | string \| null | DNS server(s) |
| `description` | string \| null | Description |
| `notes` | string \| null | Notes |
| `is_favorite` | bool | Bookmarked on dashboard |
| `dhcp_start` | string \| null | DHCP range start |
| `dhcp_end` | string \| null | DHCP range end |
| `ip_count` | int | Number of IPs in this network |
| `created_at` | string \| null | ISO-8601 timestamp |
| `updated_at` | string \| null | ISO-8601 timestamp |

---

### IP Addresses

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ips` | List IPs (see filters below) |
| GET | `/api/ips/{id}` | Get single IP |
| POST | `/api/ips` | Create IP |
| PUT | `/api/ips/{id}` | Update IP |
| DELETE | `/api/ips/{id}` | Delete IP |

**Query parameters for GET /api/ips:**

| Param | Type | Description |
|-------|------|-------------|
| `network_id` | int | Filter by network |
| `status` | string | `active`, `inactive`, or `unknown` |
| `search` | string | Match address or hostname |
| `limit` | int | Max results (default 100, max 500) |
| `offset` | int | Pagination offset |

**Create / Update body:**

```json
{
  "address": "192.168.1.50",
  "hostname": "printer01",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "assignment_type": "static",
  "status": "active",
  "network_id": 1,
  "device_id": 5,
  "source": "manual"
}
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique ID |
| `address` | string | IP address |
| `hostname` | string \| null | DNS hostname |
| `mac_address` | string \| null | MAC address |
| `assignment_type` | string | `static`, `dhcp`, or `reserved` |
| `status` | string | `active`, `inactive`, or `unknown` |
| `network_id` | int | Parent network ID |
| `device_id` | int \| null | Linked device ID |
| `source` | string \| null | How it was discovered |
| `last_seen` | string \| null | Last seen timestamp |
| `tags` | array | Attached tags |
| `created_at` | string \| null | ISO-8601 timestamp |

---

### Devices

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/devices` | List devices (see filters below) |
| GET | `/api/devices/{id}` | Get single device (includes IPs, tags) |
| POST | `/api/devices` | Create device |
| PUT | `/api/devices/{id}` | Update device |
| DELETE | `/api/devices/{id}` | Delete device |

**Query parameters for GET /api/devices:**

| Param | Type | Description |
|-------|------|-------------|
| `category` | string | Filter by device type name |
| `search` | string | Match name, model, or serial |
| `limit` | int | Max results (default 100) |
| `offset` | int | Pagination offset |

**Create / Update body:**

```json
{
  "name": "Core Switch",
  "manufacturer": "Ubiquiti",
  "model": "USW-Pro-48-PoE",
  "serial_number": "ABC123",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "location": "Server Room",
  "rack_position": "U12",
  "device_type_id": 3
}
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique ID |
| `name` | string | Device name |
| `manufacturer` | string \| null | Manufacturer |
| `model` | string \| null | Model number |
| `serial_number` | string \| null | Serial number |
| `mac_address` | string \| null | Primary MAC |
| `location` | string \| null | Physical location |
| `rack_position` | string \| null | Rack position |
| `device_type` | object \| null | `{id, name, icon}` |
| `ip_addresses` | array | Linked IPs `[{id, address, hostname}]` |
| `tags` | array | Attached tags |
| `purchase_date` | string \| null | ISO-8601 date |
| `warranty_expiry` | string \| null | ISO-8601 date |
| `eol_date` | string \| null | ISO-8601 date |
| `created_at` | string \| null | ISO-8601 timestamp |

---

### Tags

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tags` | List all tags |
| GET | `/api/tags/{id}` | Get single tag |
| POST | `/api/tags` | Create tag |
| DELETE | `/api/tags/{id}` | Delete tag |

**Create body:**

```json
{
  "name": "production",
  "color": "#4caf50"
}
```

---

### Uptime Monitors

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/monitors` | List all monitors |
| GET | `/api/monitors/{id}` | Get single monitor |
| POST | `/api/monitors` | Create monitor |
| PUT | `/api/monitors/{id}` | Update monitor |
| DELETE | `/api/monitors/{id}` | Delete monitor |

**Create / Update body:**

```json
{
  "ip_address": "192.168.1.1",
  "name": "Gateway",
  "monitor_type": "ping",
  "check_interval": 60,
  "max_retries": 3,
  "is_enabled": true
}
```

**Response fields include:**

| Field | Type | Description |
|-------|------|-------------|
| `current_status` | string | `up`, `down`, or `unknown` |
| `uptime_percent` | float | Computed uptime % |
| `consecutive_failures` | int | Current failure streak |
| `total_checks` | int | All-time check count |
| `total_up` | int | All-time successful checks |

---

### Documentation

> **Note:** The documentation resource lives at `/articles`. The `/docs` path is reserved for the Swagger UI docs page.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/articles` | List all articles |
| GET | `/api/articles/{id}` | Get single article |
| POST | `/api/articles` | Create article |
| PUT | `/api/articles/{id}` | Update article |
| DELETE | `/api/articles/{id}` | Delete article |

**Create / Update body:**

```json
{
  "title": "How to reboot the UDM SE",
  "body": "SSH into the console and run `systemctl reboot`...",
  "category": "how-to",
  "linked_device_id": 1
}
```

**Categories:** `how-to`, `troubleshooting`, `runbook`, `general`

---

### Global Search

```
GET /api/search?q=<query>&limit=20
```

Returns matches across networks, IPs, devices, and documentation:

```json
{
  "networks": [...],
  "ip_addresses": [...],
  "devices": [...],
  "docs": [...]
}
```

---

## Usage Examples

### curl

```bash
API_KEY="your_key_here"
BASE="http://localhost:8080/api"

# List all networks
curl -H "X-API-KEY: $API_KEY" "$BASE/networks"

# Get a specific device
curl -H "X-API-KEY: $API_KEY" "$BASE/devices/5"

# Create a new IP
curl -X POST -H "X-API-KEY: $API_KEY" -H "Content-Type: application/json" \
  -d '{"address":"192.168.1.99","hostname":"test-host","network_id":1,"status":"active"}' \
  "$BASE/ips"

# Search
curl -H "X-API-KEY: $API_KEY" "$BASE/search?q=ubiquiti"
```

### Home Assistant

```yaml
# configuration.yaml
rest:
  - resource: http://localhost:8080/api/dashboard
    headers:
      X-API-KEY: "your_key_here"
    sensor:
      - name: "Lab Total Devices"
        value_template: "{{ value_json.total_devices }}"
        unit_of_measurement: "devices"
      - name: "Lab Monitors Down"
        value_template: "{{ value_json.monitors_down }}"
        unit_of_measurement: "monitors"
```

### Python (httpx)

```python
import httpx

API_KEY = "your_key_here"
BASE = "http://localhost:8080/api"
headers = {"X-API-KEY": API_KEY}

# Get all active IPs
r = httpx.get(f"{BASE}/ips", headers=headers, params={"status": "active"})
ips = r.json()
print(f"Active IPs: {len(ips)}")
```

### Ansible Inventory (INI)

```bash
#!/bin/bash
API_KEY="your_key_here"
BASE="http://localhost:8080/api"

echo "[all:vars]"
echo "ansible_user=ansible"

curl -s -H "X-API-KEY: $API_KEY" "$BASE/devices" | \
  python3 -c "
import sys, json
devices = json.load(sys.stdin)
for d in devices:
    ips = d.get('ip_addresses', [])
    if ips:
        ip = ips[0]['address']
        dtype = d.get('device_type', {}).get('name', 'server').lower().replace(' ', '_')
        print(f'{d[\"name\"]} ansible_host={ip}')
"
```

### Grafana (JSON API Datasource)

1. Install the [JSON API](https://grafana.com/grafana/plugins/marcusolsson-json-datasource/) plugin
2. Add a data source pointing to `http://localhost:8080/api`
3. Set `X-API-KEY` in the custom headers section
4. Query: `GET /api/dashboard` for overview stats

---

## Testing the API

A curl-based test script is included at `test_api.sh` in the project root. It runs a full CRUD cycle (create → read → update → search → delete) against every resource and cleans up after itself.

```bash
export API_KEY="your_secret_key_here"
bash test_api.sh
```

Requirements:
- The app must be running (`python main.py`) on the configured port (default `8080`)
- `API_KEY` exported in the shell — or set inline: `API_KEY=your_key bash test_api.sh`
- Override the port with `APP_PORT` if not 8080: `APP_PORT=9000 bash test_api.sh`

The script exits with a clear error if the server isn't reachable, and fails fast with the raw response body if any create operation returns an error status.

Alternatively, the interactive **Swagger UI** at `/api/docs` lets you test every endpoint in the browser, including saving the `X-API-KEY` via the **Authorize** button.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **503 Service Unavailable** | Set `API_KEY` in your `.env` and restart |
| **401 Unauthorized** | Check the `X-API-KEY` header matches your `.env` value |
| **404 Not Found** | Verify the resource ID exists. Use `/api/docs` to browse all endpoints |
| **Empty arrays in response** | The resource may not have data yet — create some via the web UI first |
| **Connection refused** | Ensure the app is running on the expected port |
