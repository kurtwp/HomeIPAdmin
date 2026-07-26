"""Network detail page — shows a single network with IPs, tags, DHCP, and notes."""

from nicegui import ui

from app.database.db import get_session
from app.pages.layout import page_layout
from app.pages.subnet_grid import render_subnet_grid
from app.services.network_service import get_network_by_id, get_network_utilization, update_network
from app.services.ip_service import get_ips_for_network
from app.services.scanner import resolve_hostname


def render_network_detail(network_id: int):
    """Render the network detail page."""
    page_layout()
    with get_session() as session:
        network = get_network_by_id(session, network_id)

        if not network:
            with ui.column().classes("page-container"):
                ui.label("Network not found").classes("text-xl text-red")
            return

        util = get_network_utilization(session, network_id)
        ips = get_ips_for_network(session, network_id)
        from app.models.tag import Tag, network_tags
        all_tags = session.query(Tag).order_by(Tag.name).all()
        current_tags = list(network.tags)
        current_tag_ids = {t.id for t in current_tags}

        with ui.column().classes("page-container w-full"):
            with ui.row().classes("items-center gap-4"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/networks")).props(
                    "flat round"
                )
                ui.label(network.name).classes("text-3xl font-bold")
                ui.label(network.cidr).classes("text-xl font-mono text-gray-500")
                if network.vlan_id:
                    ui.badge(f"VLAN {network.vlan_id}").props("color=blue outline")

            ui.separator().classes("my-4")

            # Utilization bar
            with ui.card().classes("w-full"):
                ui.label("Utilization").classes("text-lg font-semibold")
                ui.linear_progress(
                    value=util.get("utilization_percent", 0) / 100,
                    show_value=False,
                ).classes("w-full mt-2")
                ui.label(
                    f'{util.get("used", 0)} used / {util.get("free", 0)} free / '
                    f'{util.get("total", 0)} total — {util.get("utilization_percent", 0)}%'
                ).classes("text-sm text-gray-500")

            # Visual subnet grid
            with ui.card().classes("w-full mt-4"):
                ui.label("Subnet Map").classes("text-lg font-semibold mb-2")
                render_subnet_grid(network.cidr, ips)

            # Tags + DHCP Range (side by side)
            with ui.row().classes("w-full gap-4 mt-4 flex-wrap"):
                # Tags (left half)
                with ui.card().classes("flex-1 min-w-[300px]"):
                    ui.label("Tags").classes("text-lg font-semibold mb-2")
                    # Inline tag assignment (from the reusable component logic)

                    tags_display = ui.row().classes("flex-wrap gap-1 mb-3")

                    def refresh_tag_display():
                        tags_display.clear()
                        with tags_display:
                            if not network.tags:
                                ui.label("No tags").classes("text-sm text-gray-400 italic")
                            else:
                                for tag in network.tags:
                                    with ui.row().classes("items-center gap-0"):
                                        ui.html(
                                            f'<span style="display:inline-flex; align-items:center; '
                                            f"padding:2px 10px; border-radius:12px; font-size:0.75rem; "
                                            f"font-weight:500; background:{tag.color}20; "
                                            f'color:{tag.color}; border:1px solid {tag.color}40;">'
                                            f"{tag.name}</span>"
                                        )
                                        def remove_net_tag(t=tag):
                                            network.tags.remove(t)
                                            with get_session() as s:
                                                s.execute(
                                                    network_tags.delete().where(
                                                        network_tags.c.network_id == network_id,
                                                        network_tags.c.tag_id == t.id,
                                                    )
                                                )
                                                s.commit()
                                            refresh_tag_display()

                                        ui.button(
                                            icon="close",
                                            on_click=remove_net_tag,
                                        ).props("flat round size=xs").classes("ml-0")

                    refresh_tag_display()

                    available_tags = {t.id: t.name for t in all_tags if t.id not in current_tag_ids}
                    if available_tags:
                        with ui.row().classes("items-center gap-2"):
                            tag_select = ui.select(available_tags, label="Add tag", with_input=True).classes("w-36")

                            def add_net_tag():
                                if tag_select.value:
                                    with get_session() as s:
                                        tag = s.query(Tag).filter(Tag.id == tag_select.value).first()
                                        if tag and tag not in network.tags:
                                            network.tags.append(tag)
                                            s.commit()
                                            refresh_tag_display()

                            ui.button("Add", on_click=add_net_tag).props("flat color=primary size=sm")

                # DHCP Range (right half)
                with ui.card().classes("flex-1 min-w-[300px]"):
                    ui.label("DHCP Range").classes("text-lg font-semibold mb-2")
                    ui.label(
                        "IPs within this range → DHCP. Outside → Static."
                    ).classes("text-xs text-gray-500 mb-2")

                    with ui.row().classes("gap-2 items-end"):
                        dhcp_start_edit = ui.input(
                            "Start", value=network.dhcp_start or "", placeholder="e.g. 192.168.2.100"
                        ).classes("w-40")
                        dhcp_end_edit = ui.input(
                            "End", value=network.dhcp_end or "", placeholder="e.g. 192.168.2.245"
                        ).classes("w-40")

                        def save_dhcp_range():
                            with get_session() as s:
                                update_network(
                                    s, network.id,
                                    dhcp_start=dhcp_start_edit.value or None,
                                    dhcp_end=dhcp_end_edit.value or None,
                                )
                            ui.notify("DHCP range saved!", type="positive")

                        ui.button("Save", on_click=save_dhcp_range).props("color=primary size=sm")

            # IP table with hostname refresh
            with ui.row().classes("items-center justify-between mt-4"):
                ui.label("IP Addresses").classes("text-xl font-semibold")
                def refresh_hostnames():
                    with get_session() as s:
                        fresh_ips = get_ips_for_network(s, network_id)
                        updated = 0
                        for ip in fresh_ips:
                            new_hostname = resolve_hostname(ip.address)
                            if new_hostname and new_hostname != ip.hostname:
                                ip.hostname = new_hostname
                                updated += 1
                        s.commit()
                    ui.notify(f"Refreshed hostnames: {updated} updated", type="positive")
                    ui.navigate.to(f"/networks/{network_id}")

                ui.button("Refresh Hostnames", icon="dns", on_click=refresh_hostnames).props(
                    "flat color=primary size=sm"
                )

            if ips:
                columns = [
                    {"name": "address", "label": "Address", "field": "address", "align": "left"},
                    {"name": "hostname", "label": "Hostname", "field": "hostname", "align": "left"},
                    {"name": "status", "label": "Status", "field": "status", "align": "center"},
                    {"name": "type", "label": "Type", "field": "type", "align": "center"},
                    {"name": "tags", "label": "Tags", "field": "tags", "align": "left"},
                ]
                rows = [
                    {
                        "id": ip.id,
                        "address": ip.address,
                        "hostname": ip.hostname or "—",
                        "status": ip.status.value,
                        "type": ip.assignment_type.value.upper(),
                        "tags": ", ".join(t.name for t in ip.tags) if ip.tags else "—",
                    }
                    for ip in ips
                ]
                ui.table(columns=columns, rows=rows, row_key="id").classes("w-full").props(
                    "flat bordered dense"
                )
            else:
                ui.label("No IPs tracked in this network yet.").classes("text-gray-500")

            # Notes editor
            with ui.card().classes("w-full mt-4"):
                ui.label("Network Notes").classes("text-lg font-semibold mb-2")

                with ui.tabs().classes("w-full") as tabs:
                    edit_tab = ui.tab("Edit")
                    preview_tab = ui.tab("Preview")

                with ui.tab_panels(tabs, value=preview_tab).classes("w-full"):
                    with ui.tab_panel(edit_tab):
                        notes_editor = ui.textarea(
                            value=network.notes or ""
                        ).classes("w-full").props('rows="8"')

                        def save_network_notes():
                            with get_session() as s:
                                update_network(s, network.id, notes=notes_editor.value)
                            ui.notify("Notes saved!", type="positive")

                        ui.button("Save Notes", on_click=save_network_notes).props(
                            "color=primary"
                        )

                    with ui.tab_panel(preview_tab):
                        ui.markdown(network.notes or "*No notes yet*").classes("w-full")
