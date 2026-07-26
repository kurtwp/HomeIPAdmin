# Authentication

Home Lab Manager includes optional user authentication to protect your data and settings from unauthorized access.

## How It Works

- **Auth is optional** — if no user account exists, the app runs without login (open access)
- **To enable auth** → navigate to `/login` and create your first admin account
- **After setup** → all pages require login, redirecting to `/login` if not authenticated
- **Session-based** — login persists via NiceGUI's user storage (browser cookie)

## Enabling Authentication

Authentication is disabled by default. To enable it:

1. Navigate to `http://your-server:8080/login`
2. Since no users exist, you'll see the **Create Admin Account** screen
3. Choose a username and password
4. Click "Create Account"

From this point forward, all pages require login. The app remains open (no login) until you explicitly create the first user.

## Logging In

After setup, visiting any page while not authenticated redirects to `/login`:

1. Enter your username and password
2. Press Enter or click "Sign In"
3. You're redirected to the Dashboard

## Logging Out

Click the **logout icon** (→) in the top-right corner of the navigation bar. You'll be redirected to the login page.

## Changing Your Password

1. Go to Tools → Settings (`/settings`)
2. Scroll to the **Change Password** section at the bottom
3. Enter your current password, new password, and confirm
4. Click "Change Password"

## Roles

Two roles are supported:

| Role | Access |
|------|--------|
| admin | Full access — all pages, settings, data modification, user management |
| viewer | Read-only access — can view data but cannot modify, delete, or access admin pages |

Admins can manage users via **Tools → Users** (`/users`). Viewer users are blocked from write operations and admin-only pages.

## Security Details

- Passwords are hashed with bcrypt (never stored in plain text)
- Sessions are stored in NiceGUI's encrypted user storage
- The login page does not reveal whether a username exists (generic error message)
- Failed login attempts are tracked with IP address and timestamp
- Account lockout after 5 failed attempts within 15 minutes (configurable in `auth_service.py`)
- Last-admin protection: cannot delete or deactivate the only admin user

## User Management

Navigate to **Tools → Users** (`/users`) to manage user accounts (admin only).

### Features

- **Add User** — create new accounts with admin or viewer role
- **Change Role** — switch between admin and viewer via dropdown
- **Activate/Deactivate** — disable a user without deleting them
- **Delete User** — permanently remove an account (requires confirmation)
- **Login History** — view recent login attempts with status and IP address

### Safeguards

- Cannot delete or deactivate the last admin user
- Cannot demote the last admin to viewer
- Users cannot modify their own role from the dropdown

## Disabling Authentication

To disable auth and go back to open access:

```bash
# Connect to your database and delete all users
sqlite3 /opt/HomeLabManager/home_lab_manager.db "DELETE FROM users;"
```
Or from the app: if you have access, you could run this via a Python script. With no users in the database, auth is automatically disabled.

## Check your database for users

```bash
python3 -c "
from app.database.db import get_session
from app.models.user import User
with get_session() as s:
    for u in s.query(User).all():
        print(f'User: {u.username}, Role: {u.role}, Active: {u.is_active}')
"
```

## Reset User Password

```bash
python3 -c "
from app.database.db import get_session
from app.models.user import User
from app.services.auth_service import _hash_password
with get_session() as s:
    u = s.query(User).first()
    if u:
        u.password_hash = _hash_password('changeme')
        s.commit()
        print(f'Reset password for {u.username} to: changeme')
"
```
ADMIN password changed to `changeme`

## Tips

- Set up auth if your app is accessible beyond your immediate workstation
- The logout button shows your username in its tooltip
- If you forget your password, delete the users table in SQLite and create a new account
- Auth protects the UI only — there's no REST API to secure separately
