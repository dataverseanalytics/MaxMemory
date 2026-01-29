# Authentication & Email Troubleshooting Guide

## Problem 1: "Could not validate credentials" in Swagger

### Common Causes:
1. **Token not provided correctly** - Make sure you're using the token in the correct format
2. **Token expired** - Tokens expire after 30 minutes by default
3. **User not active** - User account might be deactivated

### How to Fix:

#### Step 1: Get a Valid Token
Run the diagnostic script:
```bash
python diagnose_auth_email.py
```

This will:
- Create a test user if needed
- Generate a fresh token
- Show you exactly how to use it in Swagger

#### Step 2: Use Token in Swagger
1. Go to `http://localhost:8000/docs`
2. Click the **"Authorize"** button (🔒 icon, top right)
3. In the **"Value"** field, paste your token (just the token, no "Bearer" prefix)
4. Click **"Authorize"** then **"Close"**
5. Try any protected endpoint

#### Step 3: Alternative - Login via API
Instead of manually pasting tokens, you can login through Swagger:

1. Find the `POST /api/v1/auth/login` endpoint
2. Click "Try it out"
3. Enter credentials:
   ```json
   {
     "email": "admin@example.com",
     "password": "admin123"
   }
   ```
4. Copy the `access_token` from the response
5. Use it in the Authorize dialog

## Problem 2: Email Not Working

### Current Status:
Email requires SMTP configuration. Check your `.env` file:

```env
SMTP_HOST=mail.shiviontech.com
SMTP_PORT=587
SMTP_USER=contact@shiviontech.com
SMTP_PASSWORD=H=wJfe_DM9%K
EMAIL_FROM=contact@shiviontech.com
```

### How to Test:
```bash
python diagnose_auth_email.py
```

This will:
- Check if SMTP is configured
- Attempt to send a test email
- Show any errors

### Common Email Issues:

1. **SMTP credentials invalid**
   - Verify username/password are correct
   - Check if the email account allows SMTP access

2. **Firewall blocking SMTP**
   - Port 587 might be blocked
   - Try port 465 (SSL) instead

3. **Email provider restrictions**
   - Some providers require "App Passwords" instead of regular passwords
   - Gmail requires "Less secure app access" or App Password

### To Disable Email (Development Only):
If you don't need email verification during development, the app will skip sending emails if SMTP is not configured. You can manually verify users:

```bash
python promote_admin.py user@example.com
```

This creates/promotes a user with `is_verified=True`.

## Quick Test Commands

### Test Authentication:
```bash
# Run diagnostics
python diagnose_auth_email.py

# Or create a test user manually
python promote_admin.py test@example.com
```

### Test API Endpoints:
```bash
# Using curl (replace TOKEN with your actual token)
curl -X GET "http://localhost:8000/api/v1/profile/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Still Having Issues?

1. **Check server logs** - Look for error messages when calling endpoints
2. **Verify .env file** - Make sure all required variables are set
3. **Restart server** - After changing .env, restart uvicorn
4. **Check database** - Run `python diagnose_auth_email.py` to verify user exists

## Endpoints Requiring Authentication

All endpoints except these require authentication:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/google`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `GET /api/v1/subscriptions/plans` (public)

All other endpoints need a valid Bearer token.
