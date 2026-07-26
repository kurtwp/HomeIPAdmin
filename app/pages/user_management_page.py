"""User management admin page — add, edit, delete users, view login history."""

from nicegui import ui, app

from app.database.db import get_session
from app.services.auth_service import (
    is_auth_enabled,
    get_all_users,
    create_user,
    delete_user,
    toggle_user_active,
    update_user_role,
    change_password,
    get_login_history,
)


def render_user_management():
    """Render the user management page."""
    from app.pages.layout import page_layout
    page_layout()

    # Only admins can access this page
    if app.storage.user.get("role") != "admin":
        with ui.column().classes("page-container w-full"):
            ui.label("Access Denied").classes("text-3xl font-bold text-red")
            ui.label("Only administrators can manage users.").classes("text-gray-500")
            ui.button("Go Back", on_click=lambda: ui.navigate.to("/")).props("color=primary")
        return

    with ui.column().classes("page-container w-full"):
        ui.label("User Management").classes("text-3xl font-bold")
        ui.label("Add, edit, and manage user accounts.").classes("text-gray-500 mb-4")
        ui.separator()

        # Add user form
        with ui.card().classes("w-full mt-4"):
            ui.label("Add User").classes("text-lg font-semibold mb-2")
            with ui.row().classes("items-end gap-4 w-full"):
                new_username = ui.input("Username", placeholder="username").classes("flex-grow").props("outlined dense")
                new_password = ui.input("Password", password=True, password_toggle_button=True).classes("w-48").props("outlined dense")
                new_role = ui.select(["admin", "viewer"], label="Role", value="viewer").classes("w-32")
                ui.button("Add User", icon="person_add", on_click=lambda: _add_user(
                    new_username.value, new_password.value, new_role.value
                )).props("color=primary")

        # Users table
        with ui.card().classes("w-full mt-4"):
            ui.label("Users").classes("text-lg font-semibold mb-2")
            users_table = ui.table(
                columns=[
                    {"name": "username", "label": "Username", "field": "username", "align": "left"},
                    {"name": "role", "label": "Role", "field": "role", "align": "center"},
                    {"name": "status", "label": "Status", "field": "status", "align": "center"},
                    {"name": "last_login", "label": "Last Login", "field": "last_login", "align": "left"},
                    {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
                ],
                rows=[],
                row_key="id",
            ).classes("w-full").props("flat bordered dense")

        def refresh_users():
            with get_session() as session:
                users = get_all_users(session)
            rows = []
            for u in users:
                is_self = u.username == app.storage.user.get("username")
                rows.append({
                    "id": u.id,
                    "username": u.username,
                    "role": u.role,
                    "status": "Active" if u.is_active else "Inactive",
                    "last_login": u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "Never",
                    "actions": "",
                })
            users_table.rows = rows
            users_table.update()

            # Rebuild action buttons
            users_table.clear()
            for row in rows:
                uid = row["id"]
                uname = row["username"]
                is_self = uname == app.storage.user.get("username")
                with users_table.add_slot(f"body-row-{uid}"):
                    with ui.tr().classes("items-center"):
                        with ui.td().classes("w-48"):
                            ui.label(uname)
                        with ui.td().classes("w-24 text-center"):
                            role_select = ui.select(
                                ["admin", "viewer"],
                                value=row["role"],
                                on_change=lambda e, id=uid: _update_role(id, e.value),
                            ).props("dense borderless").classes("w-24")
                            if is_self:
                                role_select.disable()
                        with ui.td().classes("w-24 text-center"):
                            status_color = "green" if row["status"] == "Active" else "gray"
                            ui.badge(row["status"]).props(f"color={status_color}")
                        with ui.td().classes("w-32"):
                            ui.label(row["last_login"]).classes("text-sm")
                        with ui.td().classes("text-center"):
                            if not is_self:
                                btn_label = "Deactivate" if row["status"] == "Active" else "Activate"
                                ui.button(
                                    btn_label,
                                    on_click=lambda id=uid: (_toggle(id), refresh_users()),
                                ).props("flat color=orange size=sm")
                                ui.button(
                                    "Delete",
                                    on_click=lambda id=uid, name=uname: _delete(id, name),
                                ).props("flat color=negative size=sm")

        def _add_user(username: str, password: str, role: str):
            if not username or not password:
                ui.notify("Username and password required", type="warning")
                return
            if len(password) < 4:
                ui.notify("Password must be at least 4 characters", type="warning")
                return
            with get_session() as session:
                try:
                    create_user(session, username, password, role)
                    ui.notify(f"User '{username}' created", type="positive")
                    new_username.value = ""
                    new_password.value = ""
                    refresh_users()
                except Exception as e:
                    ui.notify(f"Failed: {e}", type="negative")

        def _update_role(user_id: int, new_role: str):
            with get_session() as session:
                if update_user_role(session, user_id, new_role):
                    ui.notify("Role updated", type="positive")
                else:
                    ui.notify("Cannot demote the last admin", type="negative")
            refresh_users()

        def _toggle(user_id: int):
            with get_session() as session:
                if toggle_user_active(session, user_id):
                    ui.notify("User status updated", type="positive")
                else:
                    ui.notify("Cannot deactivate the last admin", type="negative")

        def _delete(user_id: int, username: str):
            def do_confirm():
                with get_session() as session:
                    if delete_user(session, user_id):
                        ui.notify(f"User '{username}' deleted", type="positive")
                        refresh_users()
                    else:
                        ui.notify("Cannot delete the last admin", type="negative")
                confirm_dialog.close()

            confirm_dialog = ui.dialog()
            with confirm_dialog:
                with ui.card():
                    ui.label(f"Delete user '{username}'?").classes("text-lg font-bold")
                    ui.label("This action cannot be undone.").classes("text-sm text-gray-500")
                    with ui.row().classes("gap-2 mt-4"):
                        ui.button("Cancel", on_click=confirm_dialog.close).props("flat")
                        ui.button("Delete", on_click=do_confirm).props("color=negative")
            confirm_dialog.open()

        refresh_users()

        # Login history
        ui.separator().classes("my-6")
        with ui.card().classes("w-full"):
            ui.label("Recent Login Attempts").classes("text-lg font-semibold mb-2")
            with get_session() as session:
                attempts = get_login_history(session, limit=30)
            if attempts:
                login_table = ui.table(
                    columns=[
                        {"name": "time", "label": "Time", "field": "time", "align": "left"},
                        {"name": "username", "label": "Username", "field": "username", "align": "left"},
                        {"name": "status", "label": "Status", "field": "status", "align": "center"},
                        {"name": "ip", "label": "IP Address", "field": "ip", "align": "left"},
                    ],
                    rows=[
                        {
                            "id": a.id,
                            "time": a.timestamp.strftime("%Y-%m-%d %H:%M:%S") if a.timestamp else "—",
                            "username": a.username,
                            "status": "✅ Success" if a.success else "❌ Failed",
                            "ip": a.ip_address or "—",
                        }
                        for a in attempts
                    ],
                    row_key="id",
                ).classes("w-full").props("flat bordered dense")
            else:
                ui.label("No login attempts recorded.").classes("text-gray-500 italic")
