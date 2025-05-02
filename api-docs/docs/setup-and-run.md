# Setup and Run

---

## ⚙️ Setup and Execution for Development

This section explains how to set up and run the project in a local development environment.

### 1. 🧬 Clone the Repository

Clone the repository to your local machine.

> ⚠️ This guide assumes you already have basic knowledge of Git.

### 2. 📦 Create a Virtual Environment and Install Dependencies

Create a virtual environment in the root of the repository. This ensures Python environment isolation and avoids conflicts with other system libraries.

On Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

With the virtual environment activated, install the backend dependencies:

```bash
pip install -r api/requirements.txt
```

### 3. 🗒️ Set Environment Variables

The project uses two `.env` files: one for the Django application (`api`) and another for Docker Compose (`docker`).

#### a. Application Variables (API)

Inside the `api/environments/` directory, there's a `.env.example` file listing all required variables for the app to run properly.

Create your own `.env` file based on this template:

```bash
cp api/environments/.env.example api/environments/.env
```

Edit the new `.env` file with values appropriate for your local environment.

#### b. Docker Variables

Inside the `docker/` directory, there's a `.env.example` file containing instructions and variables used in `docker-compose.yml`.

Create your `.env` file based on that template:

```bash
cp docker/.env.example docker/.env
```

This file is required to define variables used directly by Docker Compose, such as:

* `POSTGRES_DB`: database name
* `POSTGRES_USER`: database user
* `COMPOSE_PROJECT_NAME`: project name (used to prefix container names)

> 💡 This file **must** be named `.env` and reside in the same directory as `docker-compose.yml` to work correctly.

### 4. 🐳 Start the Containers

> 💡 **Prerequisite**: Make sure [Docker](https://docs.docker.com/get-docker/) is installed on your system.
>
> If not installed yet, follow the official instructions:
> 👉 [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

With dependencies installed and `.env` files set, start the application containers with the following command:

```bash
cd api
python manage.py dev_up
```

This command is a custom wrapper that runs `docker compose up` inside the `docker/` directory.

#### 🚩 Available Flags:

You can use additional options to control startup behavior:

* `--build`: forces image rebuild.
* `--recreate`: forces container recreation.
* `--build --recreate`: applies both options simultaneously.

Example:

```bash
python manage.py dev_up --build --recreate
```

This ensures all services are rebuilt and restarted from scratch — useful after changes to dependencies or environment variables.

## 🔑 Accessing Services and Tools

This project provides various interfaces for easier development, testing, and maintenance. Below are the main ways to interact with the application.

> Make sure the containers are running.

### 📡 API Routes - `/api/v1/`

All routes available in version 1 of the API (`/api/v1/`) are listed below. They are grouped by functionality, including user-related endpoints and JWT authentication.

#### 🌐 Access via HTTPS

> All API requests must be made using **HTTPS on port 433**.
> Example: `https://localhost:433/api/v1/...`

If accessed via **HTTP (port 80)**, Nginx will automatically redirect to **HTTPS on port 433**, ensuring secure communication.

#### 👤 User Endpoints

| Method | Route                                   | Description          |
| ------ | --------------------------------------- | -------------------- |
| POST   | `/api/v1/account/register/`             | Create a new user    |
| PUT    | `/api/v1/account/update/`               | Update user data     |
| GET    | `/api/v1/account/detail/`               | Retrieve user data   |
| DELETE | `/api/v1/account/delete/`               | Delete user account  |
| POST   | `/api/v1/account/change_password/`      | Change user password |

#### 📧 Account Activation

| Method | Route                                               | Description                     |
| ------ | --------------------------------------------------- | ------------------------------- |
| POST   | `/api/v1/account/email/send_code/activate_account/` | Request account activation code |
| POST   | `/api/v1/account/code/activate/`                    | Activate account using the code |

#### 📨 Email Change

| Method | Route                                           | Description                  |
| ------ | ----------------------------------------------- | ---------------------------- |
| POST   | `/api/v1/account/email/send_code/change_email/` | Request code to change email |
| POST   | `/api/v1/account/code/change_email/`            | Change email using the code  |

#### 🔒 Password Reset

| Method | Route                                             | Description                   |
| ------ | ------------------------------------------------- | ----------------------------- |
| POST   | `/api/v1/account/email/send_code/reset_password/` | Request password reset code   |
| POST   | `/api/v1/account/code/reset_password/`            | Reset password using the code |

#### 🔐 JWT Endpoints

| Method | Route                      | Description                              |
| ------ | -------------------------- | ---------------------------------------- |
| POST   | `/api/v1/token/pair/`      | Get token pair (access and refresh)      |
| POST   | `/api/v1/token/access/`    | Refresh access token using refresh token |
| POST   | `/api/v1/token/blacklist/` | Invalidate token (logout)                |
| POST   | `/api/v1/token/verify/`    | Verify token validity                    |

### 🐚 Accessing the Containers

To access the shell of the API container, run:

```bash
docker exec -it api sh
```

This allows you to run commands directly inside the container, such as running tests.

### 📚 Accessing API Documentation (drf-spectacular)

Auto-generated documentation by **drf-spectacular** is available at the following paths:

* Swagger UI: [http://localhost:8000/schema/swagger-ui/](http://localhost:8000/schema/swagger-ui/)
* ReDoc: [http://localhost:8000/schema/redoc/](http://localhost:8000/schema/redoc/)
* Raw schema (OpenAPI): [http://localhost:8000/schema/](http://localhost:8000/schema/)

These URLs are available after the containers are up.

### 🛠️ Accessing Django Admin

To access the Django admin panel:

1. Enter the API container:
   ```bash
   docker exec -it api sh
   ```

2. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
   Follow the instructions to set an email and password.

3. Open your browser and go to:
     * [https://localhost:443/admin/](https://localhost:443/admin/)
     * or [https://127.0.0.1:443/admin/](https://127.0.0.1:443/admin/)

### 📖 Accessing Technical Documentation (MkDocs)

Technical documentation written with **MkDocs** is located in the `api-docs` directory. To serve it locally:

1. Navigate to the directory:
   ```bash
   cd api-docs
   ```

2. Run the documentation server:
   ```bash
   mkdocs serve
   ```

3. Open your browser:
     * [http://localhost:8000](http://localhost:8000)
     * or [https://127.0.0.1:8000](https://127.0.0.1:8000)

### 🧪 Running Automated Tests

To run automated tests using `pytest`:

```bash
docker exec -it api sh
pytest
```

### 📊 Generating Test Coverage Report

1. Run tests with coverage:
   ```bash
   coverage run -m pytest
   ```

2. View summary in terminal:
   ```bash
   coverage report
   ```

3. Generate HTML report:
   ```bash
   coverage html
   ```

4. Browse the report inside `htmlcov/` by launching a server:
   ```bash
   python -m http.server
   ```
   Then access: [http://localhost:8000](http://localhost:8000)

### 🐘 Accessing PostgreSQL via External Client

You can connect to the PostgreSQL database using a client like DBeaver.

The required credentials are defined in the `.env` file inside the `docker/` directory:

* `POSTGRES_DB` → Database name
* `POSTGRES_USER` → Username
* `POSTGRES_PASSWORD` → Password
* `POSTGRES_PORT` → Port (5432)
* `POSTGRES_HOST` → Hostname (if using a PostgreSQL container, use the service name)

> Make sure the containers are up before trying to connect.
