# SecureAuth Enterprise

Enterprise Identity & Access Management Platform — Django 6-style implementation (built on Django 5.2 LTS-compatible APIs, fully forward-compatible).

## Screenshots
<img width="1920" height="1080" alt="10" src="https://github.com/user-attachments/assets/5f7cf123-82d6-4fb8-b1ce-fb01a12aef4e" />
<img width="1920" height="1080" alt="9" src="https://github.com/user-attachments/assets/ca3e811a-920b-4541-bbfc-a1d1ffde30a5" />
<img width="1920" height="1080" alt="8" src="https://github.com/user-attachments/assets/c5a3832c-b351-45b2-bfea-6bda0b8dddc3" />
<img width="1920" height="1080" alt="7" src="https://github.com/user-attachments/assets/8a1fb7f7-66ae-4077-9ec0-c837fdef7f67" />
<img width="1920" height="1080" alt="6" src="https://github.com/user-attachments/assets/87a53a78-2f76-4930-b3ba-47946c066911" />
<img width="1920" height="1080" alt="5" src="https://github.com/user-attachments/assets/f928af1b-b8c2-45d7-b7ac-76f0ded9128f" />
<img width="1920" height="1080" alt="4" src="https://github.com/user-attachments/assets/45c5bd1a-ca03-439c-917e-bf4aefa4a45d" />
<img width="1920" height="1080" alt="3" src="https://github.com/user-attachments/assets/f271674a-5d05-4203-9a3b-2e5db254cae0" />
<img width="1920" height="1080" alt="2" src="https://github.com/user-attachments/assets/20c079a2-c238-4851-aaa4-e59930f6220b" />
<img width="1920" height="1080" alt="1" src="https://github.com/user-attachments/assets/ae01d2db-95f7-4666-97d0-7d6ae11909d9" />

## What's implemented

- **Custom email-based User model** (`accounts`) with mandatory email verification before login.
- **Registration → Email Verification → Login → Logout** flows with audit logging at every step.
- **Password reset & password change**, with enumeration-safe responses and full session invalidation on reset.
- **Account lockout** after 3 failed login attempts (`accounts.views._is_locked_out`), configurable cooldown.
- **Rate limiting** on `/accounts/login/`, `/accounts/register/`, `/accounts/password-reset/` via cache-backed middleware.
- **Session inactivity timeout** (10 minutes default) via custom middleware.
- **RBAC** (`rbac` app): Guest / User / Moderator / Administrator roles, server-side enforced permission matrix, last-Administrator protection, role-change auditing.
- **Reauthentication** required before sensitive actions (role assignment, Security Dashboard, Audit Log Dashboard).
- **Audit logging** (`audit` app): immutable, signal-free explicit `AuditService.log(...)` calls covering registration, verification, login success/failure, lockout, logout, password reset/change, and role changes.
- **Dashboards** (`dashboard` app): home dashboard, User Management, Security Dashboard, Audit Log Dashboard — styled with the cybersecurity dark-glass theme (Tailwind CDN, Inter font, neon-blue glow cards).
- **Password complexity validator**: 12+ chars, upper/lower/digit/symbol.

## Not yet wired (left as roadmap, per the documentation set)

- Google OAuth (`django-allauth`) — the `OAuthAccount` data model and flow are documented in `08_AUTHENTICATION_DESIGN.md` from the docs package; wiring it in requires your own Google Cloud OAuth client ID/secret.
- Celery/Redis async email delivery — emails currently send synchronously via Django's console/SMTP backend; swap in Celery for production scale.
- Django Axes / django-csp — the build uses lightweight custom equivalents (see `accounts/middleware.py`) to keep the dependency footprint minimal; swapping in the dedicated packages is a drop-in upgrade.
- 
## Running locally (SQLite, fastest path)
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/accounts/register/` to create an account. Verification emails print to your console (default `EmailBackend`).

To make your first user an Administrator so you can see the Security/Audit dashboards, use the Django shell:

```bash
python manage.py shell -c "
from accounts.models import User
from rbac.models import Role, RoleAssignment
u = User.objects.get(email='you@example.com')
role, _ = Role.objects.get_or_create(name=Role.ADMINISTRATOR)
RoleAssignment.objects.create(user=u, role=role)
"
```

## Running with Docker (PostgreSQL)

```bash
cp .env.example .env
docker compose up --build
```

The `web` service runs migrations automatically and serves via Gunicorn on port 8000.

## Project layout

```
config/        Django settings, urls, wsgi/asgi
accounts/      Custom User model, auth views, forms, middleware, validators
rbac/          Role/Permission models, RBACService, decorators
audit/         AuditLog model, AuditService
dashboard/     Home, User Management, Security Dashboard, Audit Log Dashboard
templates/     Cyber-themed templates (glow cards, dark grid background)
```

## Tests

A smoke-tested flow (registration → verify → login → RBAC enforcement → lockout) was verified using Django's test client during the build. To extend into the full 90%-coverage suite described in the documentation package, add `pytest`, `pytest-django`, and `factory_boy`, then build out unit/integration/security tests per `13_TESTING_STRATEGY.md`.
