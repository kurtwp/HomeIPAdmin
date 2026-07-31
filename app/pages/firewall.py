"""Firewall rule viewer — display firewall policies from the UDM SE."""

from nicegui import ui

from app.services.unifi_service import (
    fetch_firewall_policies,
    is_configured,
)
from app.pages.layout import page_layout


def render_firewall():
    """Render the firewall rule viewer page."""
    page_layout()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Firewall Rules").classes("text-3xl font-bold")
            spinner = ui.spinner(size="md").classes("hidden")
            refresh_btn = ui.button(
                "Refresh", icon="refresh", on_click=lambda: load_rules()
            ).props("color=primary")

        ui.label(
            "View firewall policies from your UniFi Dream Machine."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        if not is_configured():
            with ui.card().classes("w-full mt-4"):
                ui.label(
                    "⚠️ UniFi integration not configured. "
                    "Set UNIFI_API_KEY, UNIFI_BASE_URL, and UNIFI_SITE_ID in .env."
                ).classes("text-orange")
            return

        status = ui.label("").classes("text-sm text-gray-500 mt-2")
        container = ui.column().classes("w-full mt-4 gap-4")

        def load_rules():
            status.text = "Fetching firewall rules..."
            spinner.visible = True
            refresh_btn.disable()
            try:
                data = fetch_firewall_policies()
                policies = data.get("policies", [])
                zones = data.get("zones", [])
                render_rules(policies, zones)
                status.text = (
                    f"{len(policies)} rule(s) from {len(zones)} zone(s) "
                    f"— fetched {__import__('datetime').datetime.now():%H:%M:%S}"
                )
            except Exception as e:
                status.text = ""
                ui.notify(f"Failed to fetch firewall rules: {e}", type="negative")
                with container:
                    ui.label(f"Error: {e}").classes("text-red")
            finally:
                spinner.visible = False
                refresh_btn.enable()

        def render_rules(policies: list[dict], zones: list[dict]):
            container.clear()
            if not policies:
                with container:
                    ui.label("No firewall rules found.").classes("text-gray-500 italic")
                return

            # Summary stats
            enabled = sum(1 for p in policies if p["enabled"])
            user_defined = sum(1 for p in policies if p["origin"] == "USER_DEFINED")
            with ui.row().classes("gap-4 mb-2"):
                with ui.card().classes("p-3"):
                    ui.label(str(len(policies))).classes("text-2xl font-bold text-primary")
                    ui.label("Total Rules").classes("text-xs text-gray-500")
                with ui.card().classes("p-3"):
                    ui.label(str(enabled)).classes("text-2xl font-bold text-green")
                    ui.label("Enabled").classes("text-xs text-gray-500")
                with ui.card().classes("p-3"):
                    ui.label(str(user_defined)).classes("text-2xl font-bold text-orange")
                    ui.label("User Defined").classes("text-xs text-gray-500")

            # Zones overview
            if zones:
                with ui.expansion("Zones", icon="share").classes("w-full"):
                    zcols = [
                        {"name": "zone", "label": "Zone", "field": "zone", "align": "left"},
                        {"name": "networks", "label": "Networks", "field": "networks", "align": "left"},
                    ]
                    zrows = [
                        {"id": z["id"], "zone": z["name"], "networks": ", ".join(z["networks"]) or "—"}
                        for z in zones
                    ]
                    ui.table(columns=zcols, rows=zrows, row_key="id").classes(
                        "w-full"
                    ).props("flat bordered dense")

            # Rules table
            cols = [
                {"name": "idx", "label": "Order", "field": "idx", "align": "left", "sortable": True},
                {"name": "name", "label": "Rule", "field": "name", "align": "left", "sortable": True},
                {"name": "action", "label": "Action", "field": "action", "align": "left", "sortable": True},
                {"name": "source", "label": "Source", "field": "source", "align": "left"},
                {"name": "destination", "label": "Destination", "field": "destination", "align": "left"},
                {"name": "ipver", "label": "IP Version", "field": "ipver", "align": "left"},
                {"name": "logging", "label": "Log", "field": "logging", "align": "center"},
                {"name": "origin", "label": "Origin", "field": "origin", "align": "left"},
                {"name": "enabled", "label": "Enabled", "field": "enabled", "align": "center", "sortable": True},
            ]
            rows = []
            for p in policies:
                rows.append(
                    {
                        "id": p["id"],
                        "idx": p["index"] if p["index"] is not None else "last",
                        "name": p["name"],
                        "action": p["action"],
                        "source": p["source_zone"],
                        "destination": p["destination_zone"],
                        "ipver": p["ip_version"].replace("_", " ").title() if p["ip_version"] else "—",
                        "logging": "yes" if p["logging"] else "",
                        "origin": "User" if p["origin"] == "USER_DEFINED" else "System",
                        "enabled": "yes" if p["enabled"] else "no",
                    }
                )
            with ui.card().classes("w-full"):
                table = ui.table(columns=cols, rows=rows, row_key="id").classes(
                    "w-full"
                ).props("flat bordered dense")
                table.on(
                    "rowClick",
                    lambda e: show_policy_detail(e.args[1]["id"], policies),
                )
                ui.label(
                    "Click a row for rule details. Order reflects rule precedence (lower runs first)."
                ).classes("text-xs text-gray-500 mt-1")

        def show_policy_detail(policy_id: str, policies: list[dict]):
            policy = next((p for p in policies if p["id"] == policy_id), None)
            if not policy:
                return
            with ui.dialog() as dialog, ui.card().classes("w-[500px] max-w-[90vw] p-4"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(policy["name"]).classes("text-xl font-bold")
                    ui.badge(
                        "ENABLED" if policy["enabled"] else "DISABLED"
                    ).props(f"color={'green' if policy['enabled'] else 'grey'}")
                ui.label(
                    f"{policy['action']} · {policy['source_zone']} → {policy['destination_zone']}"
                ).classes("text-sm text-gray-500 mt-1")

                details = [
                    ("Order", str(policy["index"]) if policy["index"] is not None else "last"),
                    ("Action", policy["action"]),
                    ("Source Zone", policy["source_zone"]),
                    ("Destination Zone", policy["destination_zone"]),
                    ("IP Version", policy["ip_version"].replace("_", " & ").title() if policy["ip_version"] else "—"),
                    ("Connection State", ", ".join(policy["connection_state"]) or "—"),
                    ("Logging", "Enabled" if policy["logging"] else "Disabled"),
                    ("Origin", "User Defined" if policy["origin"] == "USER_DEFINED" else "System Defined"),
                    ("Configurable", "Yes" if policy["configurable"] else "No"),
                    ("Traffic Filter", "Yes" if policy["has_traffic_filter"] else "No"),
                    ("Rule ID", policy["id"]),
                ]
                with ui.column().classes("w-full gap-1 mt-2"):
                    for label, value in details:
                        with ui.row().classes("w-full gap-2 items-start"):
                            ui.label(label).classes("w-40 text-gray-500 text-sm")
                            ui.label(str(value)).classes("text-sm break-all")

                with ui.row().classes("w-full justify-end mt-3"):
                    ui.button("Close", on_click=dialog.close).props("flat color=grey")

            dialog.open()

        load_rules()
