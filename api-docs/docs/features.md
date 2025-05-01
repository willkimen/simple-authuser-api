# Features

---

## 🛠️ Technologies Used
- Django + Django Rest Framework
- Postgres
- Celery + Celery Beat + Redis
- PyJWT + Cors
- Docker + Docker Compose + Shell Scripts
- Nginx
- Gunicorn
- Pytest + Pytest Django + Mock Unittest + Coverage + Time Machine
- Black + Flake8 + Isort
- Venv
- Ipython
- Dotenv
- Pyright + Stubs (To work with Nvim)
- drf-spectacular + MkDocs

## 👤 User Data Management
- Allows creating, viewing, updating, and deleting user data efficiently and securely using a robust authentication and permissions system.
- When a user is removed, an email is sent informing them that their account has been successfully deleted.

## 🔑 Authentication and Token Management
- Authentication is done using **JWT tokens**, ensuring secure access to protected functionalities.
- After login, a pair of tokens (**access** and **refresh**) is generated and sent to the client.
- These tokens can be added to the blacklist, rendering them invalid immediately.

## 📬 Account Activation
- After registration, the user receives a verification code in the registered email.
- The account must be activated using this code, which is valid for a specific period.
- Upon successful activation, a confirmation email is sent to the user.
- If the user doesn't complete activation within the time frame, the application allows resending the verification code.

## 🔑 Password Reset
- If the user forgets their password, they can request a reset by submitting the registered email.
- A verification code is sent to the user's email, valid for a period of time, to allow password reset.

## 📨 Email Change
- Authenticated users can change the email associated with their account.
- A verification code will be sent to the new email address, valid for a specified period, to confirm the change.
- New access and refresh tokens will be generated and returned to the user, without the need to log in again.

## 🔑 🔁 Password Change
- Authenticated users can change their account password.
- All tokens related to the user will automatically be added to the blacklist.
- New access and refresh tokens will be generated and returned to the user, without the need to log in again.

## 🗑️ Automated Expiration of Tokens and Verification Codes
- Expired tokens and verification codes are automatically removed through Celery tasks, scheduled with Celery Beat.

## ⏰ Celery and Celery Beat for Asynchronous Tasks and Schedules
- Various functionalities use Celery tasks for asynchronous execution, while some are scheduled and executed by Celery Beat.
- Failed tasks are logged in the database and written to log files.
- Additionally, these failures are displayed in the Django Admin page, allowing the administrator to resend the task with the same arguments used initially.

## 🔬 Comprehensive Testing
The project includes over **200 automated tests** covering the following areas:

  - Views
  - Serializers
  - Authentication classes and functions
  - Email sending classes and functions
  - Celery tasks and Celery Beat scheduling
  - Models
  - Logging

The tests utilize the following tools:

  - Pytest  
  - Mocks and patches with Unittest
  - Monkey patch
  - Time Machine for simulating time travel
  - Coverage

These tests ensure a robust and reliable application.

## 👤 Admin Panel Configured
- All models are configured in Django Admin.
- Failed tasks appear in the Django Admin page, allowing the administrator to resend the task with the same arguments used originally.

## 🔒 Advanced Protection
- **Protection against DoS (Denial of Service) attacks**:
      - Implemented by limiting the number of requests per client.
      - Configured both in the application and the reverse proxy **Nginx**.
- **Protection against CSRF (Cross-Site Request Forgery)**:
      - Managed using **CORS**, allowing access only from specified domains.

## 🐳 Docker and Docker Compose
- The application runs exclusively in Docker containers, simplifying dependency installation and ensuring consistency across environments.
- The following services run in containers, sharing the same internal network:
      - API
      - Postgres
      - Celery Workers
      - Celery Beat
      - Redis (broker)
      - Nginx

## 🖥️ Gunicorn as Server
- The API is run using **Gunicorn** as the WSGI (Web Server Gateway Interface) server, providing an efficient and scalable way to serve Python applications.

## 🔁 Reverse Proxy and HTTPS

The application uses **Nginx** as a reverse proxy to manage HTTP and HTTPS connections, providing an additional layer of security, scalability, and control.

1. **Redirect to HTTPS**
       - All requests made on port 80 (HTTP) are automatically redirected to HTTPS on port 443.
       - This ensures that all data exchanged between the client and the server is encrypted.

2. **SSL Certificates**
       - The server uses SSL certificates configured in the following files:
         - **`crt.pem`**: Public certificate.
         - **`key.pem`**: Private key.
       - Protocols and Ciphers:
         - Only secure TLSv1.2 and TLSv1.3 protocols are supported.
         - A strong set of ciphers is configured to ensure protection against modern attacks.

3. **Upstream to Django**
       - Nginx acts as an intermediary between clients and the Django service, defined in Docker Compose as `api` on port 8000.
       - Direct access to the API is not possible, only through Nginx.

4. **Request and Connection Limiting**
       - Protection against DoS (Denial of Service) attacks:
         - **Request limit**: Maximum of 10 requests per second per client, with a burst allowed up to 20 requests without delay.
         - **Connection limit**: Maximum of 20 simultaneous connections per client.

5. **Additional Security**
       - Protection against unauthorized access tools like `wget` and `curl`, blocking these user agents.
       - Security headers configuration:
         - **Strict-Transport-Security (HSTS):** Ensures that browsers always use HTTPS to connect to the server.

6. **Access and Error Logs**
       - Access and error logs are stored in specific files, useful for debugging and monitoring.

### ⚠️ SSL Certificate Note
This application uses a self-signed SSL certificate, suitable for local development or internal environments. This avoids costs and simplifies configuration, but:

Browsers and tools will show a security warning because the certificate is not validated by a Certification Authority (CA).
Requests may require ignoring SSL verification.
💡 For production: Use a valid certificate from a trusted CA, such as the free Let's Encrypt, to avoid warnings and ensure full security.

## 💻 For Neovim Devs
- If you use **Neovim**, the stubs are already installed, as well as the necessary configuration for **Pyright LSP**.
