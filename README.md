# 🧪 Django Authentication – A Case Study

> [!NOTE]
> **Project Status: Legacy / Planned Overhaul**  
> This monolithic API has been **deprecated** and split into two independent microservices to improve scalability and separation of concerns:
> 
> * 🔐 **Authentication Logic:** Moved to the [Auth Service](https://github.com).
> * ✉️ **Transactional Emails:** Extracted and rewritten in Go inside the [Email Service](https://github.com).
> 
> **Future Plans:** In the future, I intend to refactor this specific repository to significantly improve its architectural design, making it much cleaner, highly decoupled, and easier to maintain as a demonstration of best practices.


A comprehensive case study to deeply understand how authentication works in Django Rest Framework (DRF).  
This is **not** a plug-and-play authentication package, but a learning project designed for experimentation and in-depth exploration.

📚 Full documentation available at: [https://willkimen.github.io/simple-authuser-api](https://willkimen.github.io/simple-authuser-api)

---

## 🚀 Project Overview

This project was created to explore and master core concepts of user authentication in Django APIs. 
It includes custom flows for account activation, password reset, email verification, 
and more — all structured with scalability and security in mind.

While it's not intended to be directly reused in other applications, it provides a solid foundation that 
can be extended. You can easily add your own Django apps and continue using the authentication system provided here.

---

## 🔧 Key Features

- 🔐 Token-based user authentication with custom flows
- 📬 Email confirmation, reminders, and reset flows
- ⚙️ Background tasks with **Celery** and **Redis**
- 🧵 Scheduled periodic tasks via **django-celery-beat**
- 📦 Dockerized environment with **Docker Compose**
- 🔥 Health check & startup automation for multi-container setups
- 🧪 Good test coverage for reliability

---

## 📚 Who Is This For?
This project is ideal for:

- Developers learning how to build secure, real-world authentication systems in Django.
- Beginners seeking to understand how to structure APIs with modern tools like Docker, Celery, and Redis.
- Anyone who wants to explore best practices in asynchronous tasks, email workflows, and API reliability.
- Developers who want to **add their own Django apps** and take advantage of the **existing authentication system** as a foundation.

## 📄 License
This project is licensed under the MIT License.
See the [LICENSE](https://github.com/willkimen/simple-authuser-api/blob/master/LICENSE) file for details.
