# Max Memory - Authentication API

A robust FastAPI-based authentication system with email/password and Google OAuth support.

## Features

✅ **Email/Password Authentication**
- User registration with email verification
- Secure login with JWT tokens
- Password hashing with bcrypt

✅ **Google OAuth Integration**
- Sign up with Google
- Sign in with Google
- Automatic email verification for Google users

✅ **Password Management**
- Forgot password functionality
- Password reset via email
- Secure token-based reset flow

✅ **Security**
- JWT access and refresh tokens
- Password hashing
- Email verification
- Token expiration

## Project Structure

```
Max_Memory/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   └── auth.py          # Authentication endpoints
│   │   └── router.py            # API router
│   ├── core/
│   │   ├── dependencies.py      # FastAPI dependencies
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── security.py          # Security utilities
│   ├── models/
│   │   └── user.py              # User database model
│   ├── schemas/
│   │   └── user.py              # Pydantic schemas
│   ├── services/
│   │   └── auth_service.py      # Business logic
│   ├── utils/
│   │   └── email.py             # Email utilities
│   ├── config.py                # Configuration
│   ├── database.py              # Database setup
│   └── main.py                  # FastAPI app
├── .env.example                 # Environment variables template
├── requirements.txt             # Python dependencies
└── README.md
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

**Required configurations:**
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (generate a secure random string)
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `SMTP_*`: Email server configuration

### 3. Set Up Database

Make sure PostgreSQL is running, then the tables will be created automatically when you start the server.

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register with email/password |
| POST | `/api/v1/auth/login` | Login with email/password |
| POST | `/api/v1/auth/google` | Authenticate with Google |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password with token |
| POST | `/api/v1/auth/verify-email` | Verify email with token |
| GET | `/api/v1/auth/me` | Get current user info |
| POST | `/api/v1/auth/logout` | Logout current user |

### User Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/profile/me` | Get user profile |
| GET | `/api/v1/profile/account-details` | Get account details (member since, status) |
| PUT | `/api/v1/profile/me` | Update user profile |
| POST | `/api/v1/profile/change-password` | Change password |
| POST | `/api/v1/profile/avatar` | Upload avatar image |
| DELETE | `/api/v1/profile/avatar` | Delete avatar image |
| DELETE | `/api/v1/profile/me` | Delete account (soft delete) |

### Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Usage Examples

### Register User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

### Get Current User

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs
6. Copy Client ID and Client Secret to `.env`

## Email Configuration

For Gmail SMTP:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the app password in `SMTP_PASSWORD`

## Security Notes

- Always use HTTPS in production
- Keep `SECRET_KEY` secure and never commit it
- Use strong passwords (min 8 characters)
- Regularly rotate JWT secrets
- Set appropriate token expiration times

## Next Steps

- [ ] Add refresh token endpoint
- [ ] Implement rate limiting
- [ ] Add user profile management
- [ ] Add role-based access control
- [ ] Add social login (Facebook, GitHub, etc.)

## License

MIT
