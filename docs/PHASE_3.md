# NEXUS-X Phase 3 — Product Layer

Phase 3 turns the intelligence engine into a more complete product layer.

## Implemented

- Account creation with password hashing and validation
- Session-based login/logout
- CSRF protection for authenticated write requests in production
- Profile name update and password change APIs
- Project access isolation for owners, project members and admins
- Admin-only user role/plan management API
- Project membership records
- Team CRUD: add, edit, remove and invite existing NEXUS-X users
- Role-aware team management permissions
- Notification read/unread state and mark-all-read
- Dashboard decision summary and unread alert count
- Activity history retained for project actions
- Backward compatibility with Phase 1 and Phase 2 endpoints

## Security notes

- Passwords are stored as Werkzeug password hashes, never plaintext.
- Authenticated write requests require the session CSRF token through `X-CSRF-Token`.
- Project access is checked server-side; do not rely on frontend navigation for authorization.
- Production deployments should set `NEXUS_SECRET_KEY` to a long random secret and `NEXUS_SECURE_COOKIE=1` behind HTTPS.

## Demo accounts

- Demo admin: `demo@nexus-x.local` / `demo123`
- New users can create their own Free account from the Login dialog.

## Phase 3 verification

Run:

```powershell
pip install -r requirements.txt
python -m pytest -q
```

Then start:

```powershell
python -m backend.app
```

The Phase 3 target flow is:

Login/Create account → Create project → Add/invite team → Update tasks → Watch notifications → Review dashboard → Verify access control.
