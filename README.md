# Home Lab Manager

A self-hosted IP address management (IPAM) and equipment tracking application for home labs. Built with Python, NiceGUI, and SQLite.

## Features

- **Network/VLAN tracking** with visual subnet maps showing IP allocation
- **Device inventory** with type categorization and manufacturer/model info
- **IP address management** — static, DHCP, reserved assignments with status tracking
- **Network scanning** — discover hosts via nmap or ICMP, auto-add/remove IPs, resolve hostnames
- **UniFi integration** — local API sync for networks, devices, clients; firmware tracking; Site Manager cloud API
- **Monitoring** — uptime ping monitor, port monitor, SSL certificate tracking, domain expiry tracking
- **Notifications** — email, webhook (Discord/Slack), Pushover, Telegram; per-event channel preferences
- **Security** — bcrypt password hashing, role-based access (admin/viewer), failed login tracking with lockout, MAC watchlist
- **Markdown notes** on IPs, devices, and networks with live preview
- **Knowledge base** — how-to guides, troubleshooting docs, and runbooks
- **Tags & labels** with color coding for visual organization
- **Global search** across all entities
- **Changelog** — full audit history of all changes
- **CSV import/export** for bulk operations and backup
- **Dashboard** with utilization stats, recent activity, and quick-add forms
- **Scheduled scans** — automatic network discovery, firmware checks, SSL/domain monitoring
- **Database migrations** — Alembic-managed schema versioning

## Screenshots

*(Coming soon)*

## Quick Start

```bash
# Clone the repo
git clone https://github.com/kurtwp/HomeLabManager.git
cd HomeLabManager

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the app
python main.py
```

Open http://localhost:8080 in your browser.

## Requirements

- Python 3.11+
- nmap (optional, for network scanning — falls back to ICMP ping)

## Configuration

Copy `.env.example` to `.env` and set your values:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:///./home_lab_manager.db` |
| `APP_TITLE` | Browser tab title | `Home Lab Manager` |
| `APP_PORT` | Web server port | `8080` |
| `STORAGE_SECRET` | NiceGUI session encryption key | auto-generated |
| `UNIFI_API_KEY` | UniFi Network API key | — |
| `UNIFI_BASE_URL` | UniFi console URL | `https://192.168.2.254` |
| `UNIFI_SITE_ID` | UniFi site UUID | — |
| `NOTIFICATIONS_ENABLED` | Enable notification system | `false` |
| `NOTIFY_EMAIL_ENABLED` | Enable email alerts | `false` |
| `NOTIFY_WEBHOOK_ENABLED` | Enable webhook alerts | `false` |
| `NOTIFY_PUSHOVER_ENABLED` | Enable Pushover alerts | `false` |
| `NOTIFY_TELEGRAM_ENABLED` | Enable Telegram alerts | `false` |

## Project Structure

```
HomeLabManager/
├── main.py                    # App entry point and page routing
├── config.py                  # Environment-based configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Config template
├── alembic/                   # Database migrations (Alembic)
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── static/custom.css          # Custom styles
└── app/
    ├── database/db.py         # SQLAlchemy setup, get_session() context manager
    ├── models/                # ORM models (Network, IP, Device, Tag, User, etc.)
    ├── pages/                 # NiceGUI page components
    ├── services/              # Business logic (CRUD, scanner, notifications, auth)
    └── utils/                 # Validators, formatters, constants
```

## Tech Stack

- **Backend**: Python 3.12
- **UI Framework**: [NiceGUI](https://nicegui.io/)
- **Database**: SQLite via SQLAlchemy
- **Migrations**: Alembic
- **Scanning**: python-nmap / ping3
- **Markdown**: markdown-it-py
- **Auth**: bcrypt password hashing
- **Scheduling**: APScheduler (background scans, firmware checks, SSL/domain monitoring)

## Roadmap

- [x] Phase 1A: Core CRUD, scanner, notes, search, changelog
- [x] Phase 1B: Subnet grid, tags, CSV import/export, quick-add
- [x] Phase 2: UniFi API integration, scheduled scans, custom fields
- [x] Phase 2.5: Notifications, auth, firmware tracking, monitoring
- [ ] Phase 3: REST API, reporting, mobile-responsive design

See [home-lab-features.md](home-lab-features.md) for the full feature roadmap.

## License

## 💼 Commercial Use & Licensing

Home Lab Manager is free for personal, home lab, and educational use under the PolyForm Noncommercial License. 

**Using this software in a commercial environment or embedding it into a commercial product is strictly prohibited under the standard license.**

If you represent a business and want to use, modify, or integrate Home Lab Manager commercially, please reach out to negotiate a standard commercial license.

📬 **Contact:** [Your Email Address] or open a private inquiry.

