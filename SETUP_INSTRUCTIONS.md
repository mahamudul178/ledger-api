# Mini Ledger API - Quick Start Guide 🚀

##  System Requirements

- Python 3.9 or higher
- pip (Python package manager)
- Git (optional, but recommended)
- Postman (for API testing)

##  Installation Steps

### 1️⃣ Clone or Download the Project

**Using Git:**
```bash
git clone <repository-url>
cd ledger_api
```

**Or Download Manually:**
```bash
# Open the folder
cd ledger_api
```

### 2️⃣ Create Python Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

✅ When activated, you will see `(venv)` in the command line.

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages:
- Django
- Django REST Framework
- django-cors-headers
- PyJWT
- And others

### 4️⃣ Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates all tables in the SQLite database.

### 5️⃣ Create Admin User (Optional but useful)

```bash
python manage.py createsuperuser
```

It will ask you:
```
Username: admin
Email address: admin@example.com
Password: ****
Password (again): ****
```

With this you can login to the `/admin/` panel.

### 6️⃣ Start the Server

```bash
python manage.py runserver
```

Output will be:
```
Starting development server at http://127.0.0.1:8000/
```

## 🧪 Test the API

### Method 1: Using Postman (Recommended)

1. **Download Postman** (Free): https://www.postman.com/downloads/

2. **Import postman_collection.json:**
   - Open Postman
   - File → Import
   - Select `postman_collection.json`
   - All endpoints are ready!

3. **Start Testing:**
   - First POST to `/api/auth/register/`
   - Then POST to `/api/auth/login/`
   - Copy the `access_token` (paste it in Postman variable)
   - Test remaining endpoints

### Method 2: Using cURL

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### Method 3: Using Python Requests Library

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Register
response = requests.post(f"{BASE_URL}/auth/register/", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123"
})
print(response.json())

# Login
response = requests.post(f"{BASE_URL}/auth/login/", json={
    "username": "testuser",
    "password": "testpass123"
})
data = response.json()
token = data['access']

# Get Customers
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/customers/", headers=headers)
print(response.json())
```

## Access the Admin Panel

1. Keep the server running: `python manage.py runserver`
2. Open in browser: `http://localhost:8000/admin/`
3. Enter username and password (created with createsuperuser)
4. You can manage Customers and Ledger Entries

## 🔧 Common Issues and Solutions

### Error: "ModuleNotFoundError: No module named 'django'"
```
Problem: Django is not installed
Solution: Run pip install -r requirements.txt
```

###  Error: "no such table: ledger_api_customer"
```
Problem: Migrations have not been run
Solution: 
  python manage.py makemigrations
  python manage.py migrate
```

###  Port 8000 already in use
```
Problem: Another process is using port 8000
Solution: 
  python manage.py runserver 8001
  (or use another port)
```

###  Error: "CSRF token missing"
```
Problem: POST request is missing the token
Solution: Enable Cookies in Postman
         or provide appropriate headers in curl
```

###  Virtual Environment is not activating
```
Solution:
Windows: set PYTHONPATH=%PYTHONPATH%;%cd%
Linux: export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 📁 Understand the File Structure

```
ledger_api/
├── manage.py                    # Django command runner
├── db.sqlite3                   # Database (auto-created)
├── requirements.txt             # Dependencies list
├── README.md                    # English documentation
├── BANGLA_GUIDE.md             # Bengali tutorial
├── SETUP_INSTRUCTIONS.md       # Setup instructions
├── postman_collection.json     # Postman endpoints

├── ledger_project/             # Main project folder
│   ├── __init__.py
│   ├── settings.py             # Configuration
│   ├── urls.py                 # Main routing
│   └── wsgi.py                 # Production server

└── ledger_api/                 # Main application
    ├── __init__.py
    ├── models.py               # Database models
    ├── views.py                # API views/endpoints
    ├── serializers.py          # Data validation
    ├── urls.py                 # App routing
    ├── admin.py                # Admin configuration
    ├── apps.py                 # App configuration
    └── migrations/             # Database migrations
        └── __init__.py
```

## 🚀 To Deploy to Production

### Change Settings (settings.py):

```python
DEBUG = False  # Keep False in production

ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ledger_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

SECRET_KEY = 'generate-a-new-secret-key'  # Generate a new secret key
```

### Use PostgreSQL (instead of SQLite):

```bash
# Install PostgreSQL on Windows/Linux
pip install psycopg2-binary

# Run migrations
python manage.py migrate
```

### Run server with Gunicorn:

```bash
pip install gunicorn
gunicorn ledger_project.wsgi:application --bind 0.0.0.0:8000
```

## 🐳 If You Want to Run with Docker

### Create a Dockerfile:

```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py migrate

CMD ["gunicorn", "ledger_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Run with Docker:

```bash
docker build -t ledger-api .
docker run -p 8000:8000 ledger-api
```

## ✨ Next Steps

1. ✅ Test the API with Postman
2. ✅ Read the Bengali Guide (BANGLA_GUIDE.md)
3. ✅ Add custom features
4. ✅ Write unit tests
5. ✅ Deploy to production

## 📞 Enable Debug Mode

```bash
# Open Django shell
python manage.py shell

# Run Python code
from ledger_api.models import Customer, LedgerEntry, User
from django.contrib.auth.models import User

# View all users
users = User.objects.all()
for user in users:
    print(user.username)

# View all customers
customers = Customer.objects.all()
for c in customers:
    print(f"{c.name} - {c.user.username}")
```

## 🎯 API Checklist

- [ ] Tested Register endpoint
- [ ] Logged in and received token
- [ ] Created a Customer
- [ ] Viewed Customer list
- [ ] Checked Customer summary (balance)
- [ ] Added CREDIT entry
- [ ] Added DEBIT entry
- [ ] Tested Filter by date
- [ ] Tested Filter by type
- [ ] Checked Statistics endpoint

When all checklist items are ✅, you understand the API perfectly!

---

**Happy Coding! 🎉 If you have any issues, read the README and BANGLA_GUIDE.**