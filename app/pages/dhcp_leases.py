"""DHCP lease viewer — display active DHCP leases from the UDM SE."""

from datetime import datetime, timezone

from nicegui import ui

from app.services.unifi_service import fetch_dhcp_leases, is_configured
from app.services.ip_service import adopt_lease
from app.models.ip_address import IPAddress
from app.database.db import get_session_direct as get_session
from app.pages.layout import page_layout


def _fmt_ts(ts: float | None) -> str:
    """Format a unix timestamp as a local time string."""
    if ts is None:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _fmt_uptime(sec: int) -> str:
    """Format seconds as a human-readable duration."""
    if not sec:
        return "—"
    d, rem = divmod(sec, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    return " ".join(parts) or "0m"


def _fmt_lease_left(sec: int | None) -> str:
    """Format seconds remaining on a DHCP lease."""
    if sec is None:
        return "Static"
    if sec <= 0:
        return "Expired"
    return _fmt_uptime(sec)


def render_dhcp_leases():
    """Render the DHCP lease viewer page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("DHCP Leases").classes("text-3xl font-bold")
            spinner = ui.spinner(size="md").classes("hidden")
            refresh_btn = ui.button(
                "Refresh", icon="refresh", on_click=lambda: load_leases()
            ).props("color=primary")

        ui.label(
            "Active DHCP leases and statically assigned clients on your UniFi network."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        if not is_configured():
            with ui.card().classes("w-full mt-4"):
                ui.label(
                    "⚠️ UniFi integration not configured. "
                    "Set UNIFI_API_KEY, UNIFI_BASE_URL, and UNIFI_SITE_ID in .env."
                ).classes("text-orange")
            session.close()
            return

        status = ui.label("").classes("text-sm text-gray-500 mt-2")
        container = ui.column().classes("w-full mt-4 gap-4")

        def load_leases():
            status.text = "Fetching DHCP leases..."
            spinner.visible = True
            refresh_btn.disable()
            try:
                leases = fetch_dhcp_leases()
                tracked = {ip.address for ip in session.query(IPAddress).all()}
                render_leases(leases, tracked)
                status.text = (
                    f"{len(leases)} client(s) — "
                    f"fetched {datetime.now():%H:%M:%S}"
                )
            except Exception as e:
                status.text = ""
                ui.notify(f"Failed to fetch leases: {e}", type="negative")
                with container:
                    ui.label(f"Error: {e}").classes("text-red")
            finally:
                spinner.visible = False
                refresh_btn.enable()

        def render_leases(leases: list[dict], tracked: set):
            container.clear()
            if not leases:
                with container:
                    ui.label("No active clients found.").classes("text-gray-500 italic")
                return

            dhcp = [l for l in leases if not l["is_static"]]
            static = [l for l in leases if l["is_static"]]
            expired = [l for l in leases if l["lease_seconds_left"] == 0]
            untracked = [l for l in leases if l["ip"] not in tracked]

            with ui.row().classes("gap-4 mb-2"):
                with ui.card().classes("p-3"):
                    ui.label(str(len(leases))).classes("text-2xl font-bold text-primary")
                    ui.label("Total Clients").classes("text-xs text-gray-500")
                with ui.card().classes("p-3"):
                    ui.label(str(len(dhcp))).classes("text-2xl font-bold text-blue")
                    ui.label("DHCP Leases").classes("text-xs text-gray-500")
                with ui.card().classes("p-3"):
                    ui.label(str(len(static))).classes("text-2xl font-bold text-green")
                    ui.label("Static").classes("text-xs text-gray-500")
                if expired:
                    with ui.card().classes("p-3"):
                        ui.label(str(len(expired))).classes("text-2xl font-bold text-orange")
                        ui.label("Expiring/Expired").classes("text-xs text-gray-500")
                with ui.card().classes("p-3"):
                    ui.label(str(len(untracked))).classes("text-2xl font-bold text-red")
                    ui.label("Untracked in IP DB").classes("text-xs text-gray-500")

            cols = [
                {"name": "ip", "label": "IP Address", "field": "ip", "align": "left", "sortable": True},
                {"name": "hostname", "label": "Hostname", "field": "hostname", "align": "left", "sortable": True},
                {"name": "mac", "label": "MAC Address", "field": "mac", "align": "left"},
                {"name": "vendor", "label": "Vendor", "field": "vendor", "align": "left"},
                {"name": "network", "label": "Network", "field": "network", "align": "left"},
                {"name": "vlan", "label": "VLAN", "field": "vlan", "align": "center"},
                {"name": "lease", "label": "Lease Expires", "field": "lease", "align": "left"},
                {"name": "left", "label": "Time Left", "field": "left", "align": "left"},
                {"name": "uptime", "label": "Connected", "field": "uptime", "align": "left"},
                {"name": "type", "label": "Type", "field": "type", "align": "center", "sortable": True},
                {"name": "tracked", "label": "In IP DB", "field": "tracked", "align": "center", "sortable": True},
                {"name": "actions", "label": "", "field": "actions", "align": "center"},
            ]

            rows = []
            for l in leases:
                expire_label = _fmt_ts(l["lease_expires"]) if not l["is_static"] else "Static"
                left = _fmt_lease_left(l["lease_seconds_left"])
                if not l["is_static"] and l["lease_seconds_left"] is not None and l["lease_seconds_left"] <= 3600:
                    left = f"⚠️ {left}"
                rows.append(
                    {
                        "id": f"{l['ip']}-{l['mac']}",
                        "ip": l["ip"],
                        "hostname": l["hostname"] or "—",
                        "mac": l["mac"],
                        "vendor": l["vendor"] or "—",
                        "network": l["network"] or "—",
                        "vlan": l["vlan"] if l["vlan"] is not None else "—",
                        "lease": expire_label,
                        "left": left,
                        "uptime": _fmt_uptime(l["uptime_sec"]),
                        "type": "Static" if l["is_static"] else "DHCP",
                        "tracked": l["ip"] in tracked,
                        "is_static": l["is_static"],
                    }
                )

            search = ui.input(placeholder="Filter by IP, hostname, or MAC...").props(
                "clearable dense outlined"
            ).classes("w-96")

            table = ui.table(columns=cols, rows=rows, row_key="id").classes(
                "w-full"
            ).props("flat bordered dense")

            table.add_slot(
                "body-cell-tracked",
                '''
                <q-td :props="props">
                    <q-badge :color="props.row.tracked ? 'green' : 'red'" outline>
                        {{ props.row.tracked ? 'Tracked' : 'Untracked' }}
                    </q-badge>
                </q-td>
                ''',
            )

            table.add_slot(
                "body-cell-actions",
                '''
                <q-td :props="props">
                    <q-btn flat dense icon="add" color="primary" size="sm"
                        label="Adopt" @click="$parent.$emit('adopt', props.row)" />
                </q-td>
                ''',
            )

            def handle_adopt(e):
                row = e.args
                try:
                    created, msg = adopt_lease(session, row)
                    ui.notify(msg, type="positive" if created else "info")
                    load_leases()
                except Exception as exc:
                    ui.notify(f"Adopt failed: {exc}", type="negative")

            table.on("adopt", handle_adopt)

            def apply_filter():
                q = (search.value or "").strip().lower()
                if not q:
                    table.rows = rows
                    return
                table.rows = [
                    r for r in rows
                    if q in r["ip"].lower()
                    or q in r["hostname"].lower()
                    or q in r["mac"].lower()
                ]

            search.on("value", apply_filter)

        load_leases()

    session.close()
