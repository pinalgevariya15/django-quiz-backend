# Django REST Framework Quiz Backend API

[![Django Version](https://img.shields.io/badge/django-5.0.14-green.svg)](https://www.djangoproject.com/)
[![DRF Version](https://img.shields.io/badge/django--rest--framework-3.15-orange.svg)](https://www.django-rest-framework.org/)
[![Swagger Documentation](https://img.shields.io/badge/swagger-interactive-blue.svg)](http://127.0.0.1:8000/api/docs/)

A backend application for an interactive Quiz Game built using **Django**, **Django REST Framework (DRF)**, **Simple JWT (JSON Web Tokens)**, and **Swagger UI** for testing.

---

## 🌟 Suggested Repository Names
- `django-quiz-backend` (Recommended - Simple & clear)
- `quiz-api-drf` (Highlights Django REST Framework)
- `interactive-quiz-engine` (Highlights functionality)

---

## 📝 GitHub "About" Section Description (Short & Sweet)
> "A backend API for an interactive Quiz Game built with Django, Django REST Framework, JWT authentication, and Swagger-based interactive testing. Supports 6-digit verification code password recovery and quiz session submission scoring."

---

## 🚀 Key Features

* **User Authentication**:
  - Secure registration and login via JWT (JSON Web Tokens).
  - Case-insensitive login verification.
  - Custom password strength validators.
* **Password Recovery**:
  - Forgot Password API generating a **6-digit verification code** sent via email.
  - Password Reset API validating the code, checking expiration (15-min limits), and setting the new password.
* **Quiz Management**:
  - Dynamic session startup generating **10 random unique questions** per quiz.
  - Interactive answer submission matching user choices to correct answers, computing scores, and outputting performance breakdowns.
* **Standardized Responses**:
  - Unified envelope format for all API success responses:
    `{"status": true, "message": "...", "data": {...}}`
  - Clean client exception formatting (e.g. fields don't prefix messages like "Code: Invalid code").
* **Interactive Testing (Swagger)**:
  - Documented schemas for all GET and POST requests allowing live testing in Swagger UI.

---

## 🛠️ Technology Stack
- **Backend Framework**: Django 5.0.14
- **API Engine**: Django REST Framework (DRF)
- **Token Security**: Simple JWT (JWT Authentication)
- **API Visualizer / Sandbox**: DRF-YASG (Swagger UI & ReDoc)
- **Database**: SQLite3 (Local development database)

---

## 💻 Quick Start Guide

### 1. Install Dependencies
Ensure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Run Database Migrations
Create the database tables (including custom user and password reset code structures):
```bash
python manage.py migrate
```

### 3. Create a Superuser (Admin)
If you want to access the Django admin panel (`/admin/`):
```bash
python manage.py createsuperuser
```

### 4. Run the Server
Launch the development server:
```bash
python manage.py runserver
```
Visit the Swagger UI Sandbox at: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)

### 5. Run Unit Tests
Execute the test suites for both authentication and quiz logic:
```bash
python manage.py test
```

---

## 📡 API Endpoints Reference

### 🔐 Authentication (`auth`)
* `POST /api/auth/register/` - Register a new account.
* `POST /api/auth/login/` - Validate credentials and receive JWT access + refresh tokens.
* `POST /api/auth/refresh/` - Request a new access token using a refresh token.
* `POST /api/auth/forgot-password/` - Send a 6-digit code to the user's email address.
* `POST /api/auth/reset-password/` - Verify the 6-digit code and set a new password.

### 🎮 Quiz Game Operations (`quiz`)
* `GET /api/quiz/{id}/start/` - Start a quiz session and receive 10 random questions.
* `POST /api/quiz/{id}/submit/` - Submit a JSON list of answers to receive scoring metrics.

### ⚙️ Admin Actions
* `GET/POST/PUT/PATCH/DELETE /api/admin/users/` - Admin endpoints for user account CRUD management.
