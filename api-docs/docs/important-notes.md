# 📌 Important Notes

--- 

Before you start using or modifying the project, it’s worth taking a look at this section.

Here you’ll find important information about how the project works behind the scenes. 
These are details that might not be obvious at first glance, but they play a key role in 
how everything functions — especially if you plan to extend features or prepare the project for a production environment.

Even if you're just exploring the project, these notes can help you avoid common mistakes and give you 
a better understanding of the overall structure.

## 📧 Email Sending Configuration in Development

In the current development configuration (`api/config/settings/development.py`), the project does **not** send real emails. Instead, it uses Django’s console backend to print email contents to the console of the `worker_send_email` container, which runs a Celery worker.

```python
# Email settings for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

This is useful during development to simulate the sending of emails without the need for an external SMTP server.

---

### 🛠️ How to Enable Real Email Sending

If you're deploying the application or want to test with a real email provider (like Gmail, SendGrid, etc.), you must:

1. **Uncomment the SMTP email configuration block** in `api/config/settings/development.py`:
   ```python
   EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
   EMAIL_HOST = os.environ.get("EMAIL_HOST")
   EMAIL_PORT = os.environ.get("EMAIL_PORT")
   EMAIL_USE_TLS = True if os.environ.get("TLS") == "True" else False
   EMAIL_HOST_USER = os.environ.get("USER_CREDENTIAL_SMTP")
   EMAIL_HOST_PASSWORD = os.environ.get("PASSWORD_CREDENTIAL_SMTP")
   DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_EMAIL")
   ```

2. **Set the following environment variables** in the `.env` file located at `api/environments/.env`:
   ```env
   # --------- Email Settings ---------
   # Credentials for authentication on the SMTP server
   # If you're using a Gmail account, do NOT use your Google password.
   # Instead, use an App Password (you must enable two-step verification in your Google account).

   USER_CREDENTIAL_SMTP=your_user_credential_for_authentication_smtp
   PASSWORD_CREDENTIAL_SMTP=your_password_credential_for_authentication_smtp

   # The default email address to appear as the sender in sent messages.
   DEFAULT_EMAIL=sender_email

   # Host SMTP server address.
   EMAIL_HOST=smtp.gmail.com

   # Port to connect to the SMTP server (e.g., 587 for TLS).
   EMAIL_PORT=587

   # Use TLS? Must be the string "True" or "False".
   TLS=True
   ```

3. (Optional) Restart the `worker_send_email` container to apply the changes.

---

> ⚠️ If you leave the console backend enabled and forget to switch to SMTP in production, no real emails will be sent, and users will not receive activation codes or password reset links.


---


## 🔗 Email Redirect Links

The application uses a set of environment variables to define the frontend URLs that will be embedded in the **body of emails sent to users**. These links point to pages on the frontend (e.g., reset password, login, registration) and are included in various email templates to guide the user through actions like account activation or password reset.

These variables must be configured in the `.env` file (`api/environments/.env`):

```env
# ---------- Redirect links to the email body -------------------
# These links are inserted into the email body, allowing the user to be redirected to the correct frontend page.
REDIRECT_TO_RESET_PASSWORD_PAGE=https://your-frontend-domain/reset/password/
REDIRECT_TO_ACTIVATE_ACCOUNT_PAGE=https://your-frontend-domain/activate/account/
REDIRECT_TO_LOGIN_PAGE=https://your-frontend-domain/login/
REDIRECT_TO_REGISTER_PAGE=https://your-frontend-domain/register/
REDIRECT_TO_REQUEST_NEW_ACTIVATE_ACCOUNT_CODE_PAGE=https://your-frontend-domain/request-new-code-activate-account/
```

> Notes:  
💡 These links are essential for user experience. Without them, users won’t be able to complete flows like resetting their password or confirming their account via the provided email links.

> ⚠️ Note: If you're only working on the backend and not integrating with a real frontend during development, you can set dummy values for these URLs. They will still appear in the emails, but won’t affect backend logic.

>Be sure to replace `https://your-frontend-domain/` with the actual domain of your frontend application.

---

## ✅ `my_environment`: Backend readiness control

To ensure the `api` service is **fully initialized** before allowing dependent services (like `nginx`, `worker_removal`, and `worker_send_email`) to run, a flag file named `my_environment` is created during startup.

This is handled by the startup script (`api/scripts/commands.sh`), which performs the following steps:

- Waits for the PostgreSQL database to be available
- Applies all database migrations
- Registers scheduled tasks using `manage.py schedule_*` commands

Once all of that is done, the script creates the file `/home/djuser/my_environment` and writes:

```env
MIGRATED=True
```

This file is used as a **health check condition** for the `api` container in `docker-compose.yml`. Only when this file is present and contains the expected value will the `api` container be considered **healthy**, allowing other containers to start by using:

```yaml
depends_on:
  api:
    condition: service_healthy
```

> 💡 This ensures that dependent services (like Celery workers and Nginx) won’t start until the backend is fully ready to handle requests.

---

## ⏰ Periodic Tasks Setup (via `commands.sh`)

During the `api` container startup, the script `api/scripts/commands.sh` executes a series of Django management commands:

```bash
python manage.py schedule_expired_codes_removal
python manage.py schedule_expired_tokens_removal
python manage.py schedule_notify_first_reminder
python manage.py schedule_notify_second_reminder
python manage.py schedule_delete_expired_accounts_and_notify
```

Each of these commands **registers a periodic task** using `django-celery-beat`. These tasks are essential for background maintenance operations and user notifications. They are scheduled using `CrontabSchedule` and stored in the `PeriodicTask` database table.

These tasks include:

* **Removing expired verification codes** (daily at 3:00 AM)
* **Removing expired tokens** (daily at 3:00 AM)
* **Sending activation email reminders** (first and second reminders, daily at 9:00 AM)
* **Deleting unconfirmed accounts and notifying users** (daily at 12:00 AM)

> ⚠️ These scheduled tasks are **critical** for correct application behavior and user experience.
> Without them, expired codes and tokens will accumulate, and users may not receive important reminders or cleanup actions.

> ✅ These commands ensure that tasks are **only registered once** and will not be duplicated on repeated deployments.

Make sure these commands are not removed or skipped in other environments (e.g., production or staging).

---

## 🧩 Serving Django Admin Static Files with Nginx

To ensure that the Django Admin interface loads correctly with full styling and JavaScript functionality, it's essential to serve static files properly through Nginx.

### 🔹 `collectstatic` and Volume Mounting

The following lines in the `commands.sh` script:

```bash
echo "Collecting static files..."
python manage.py collectstatic --noinput
```

This collects all static files (e.g., CSS, JS, images) from installed apps (including `django.contrib.admin`) and places them into the `/api/static/` directory.

In `docker-compose.yml`, this directory is mounted to a named volume:

```yaml
volumes:
  - ./../api/:/api
  - static_volume:/api/static/
```

This volume is then **shared with the `nginx` container** as a **read-only mount**:

```yaml
nginx:
  volumes:
    - static_volume:/static/:ro
```

This setup allows Nginx to access and serve the static files collected by Django.

### 🔹 Nginx Configuration for Static Files

The following block in the `nginx.conf` tells Nginx how to serve static content:

```nginx
http {
    include mime.types;
    default_type application/octet-stream;

    location /static/ {
        alias /static/;
    }

    location /admin/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }
}
```

* The `include mime.types;` directive allows Nginx to correctly identify and serve file types like `.css`, `.js`, `.png`, etc.
* The `/static/` location block tells Nginx to serve files from `/static/` on disk, which maps to the shared `static_volume`.
* The `/admin/` location proxies requests to the Django backend and ensures that the Admin panel is accessible.

### ✅ Why This Matters

Without these configurations:

* The Django Admin panel might load without CSS or JavaScript, appearing broken or unstyled.
* Static files wouldn't be served correctly, especially in production, where Django does not serve them directly.
* You’d likely see 404 errors for CSS/JS files in the browser console.

> 📌 In summary:  
> These settings are **essential for the Django Admin UI to function properly** when running behind Nginx in Dockerized environments.

---


## 🚫 Blocking Certain User Agents (e.g., `curl`, `wget`, scanners)

In the Nginx configuration, the following directive blocks requests coming from specific user agents:

```nginx
if ($http_user_agent ~* (wget|curl|scanner)) {
    return 403;
}
```

### 🔍 What It Does

This rule inspects the `User-Agent` header of incoming HTTP requests. If the user agent string matches any of the listed patterns (`wget`, `curl`, or `scanner`), Nginx immediately returns a **403 Forbidden** response, effectively blocking the request.

### ✅ Why It's Useful

This is often used to:

* Prevent automated tools like `curl` and `wget` from scraping or testing your endpoints.
* Block certain types of scanners that may probe for vulnerabilities.
* Add a basic layer of protection against bots or simple malicious scripts.

### ⚠️ Note for Developers

If you're trying to test your application using `curl`, `wget`, Postman (with custom agents), or other similar tools and you're receiving unexpected 403 errors, **this might be the reason**.

To allow such tools again, **you can remove or comment out this block**:

```nginx
# if ($http_user_agent ~* (wget|curl|scanner)) {
#     return 403;
# }
```

> 📌 In summary:  
> This is a basic protection mechanism. It's helpful in production but might get in the way during development or debugging. Adjust accordingly based on your needs.

---


## 📌 Registering Celery Tasks in `celery.py`

Every time you create a new Celery task in your Django project, **you must explicitly register it in the `celery.py` module** if you're using custom queues via `task_routes`.

In this project, we define specific queues for task types (e.g., emails, removals), and use `app.conf.task_routes` to route each task accordingly:

```python
app.conf.task_routes = {
    "account_auth.tasks.task_remove_exp_code": {"queue": REMOVALS_QUEUE_NAME},
    "account_auth.tasks.task_send_account_activation_code": {"queue": EMAIL_QUEUE_NAME},
    ...
}
```

### 🚨 Why This Matters

If you forget to register a new task here:

* The task may not be assigned to the correct queue.
* Celery workers listening on specific queues (like `email_queue` or `removal_queue`) **will not receive the task**.
* This could lead to tasks silently not running or being stuck.

### ✅ What You Should Do

Whenever you define a new task (e.g., in `account_auth/tasks.py`), **make sure to add it to `task_routes`** in `celery.py` like so:

```python
app.conf.task_routes.update({
    "account_auth.tasks.my_new_task": {"queue": EMAIL_QUEUE_NAME},
})
```

> 📎 Tip: Use constants for task names to keep things organized and reduce the chance of typos.

### 🧠 Summary

* Task registration here ensures correct routing to queues.
* This is essential for projects using multiple queues with dedicated workers.
* Don't forget to keep `celery.py` in sync with your task definitions.

