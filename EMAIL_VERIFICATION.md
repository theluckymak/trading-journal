# Email Verification Setup

## Overview
Email verification has been added to enhance security. Users must verify their email address before they can log in.

## Features
- ✅ **Email verification on registration** - Users receive a verification email with a secure token
- ✅ **24-hour token expiration** - Verification tokens expire after 24 hours
- ✅ **Resend verification** - Users can request a new verification email
- ✅ **Login protection** - Unverified users cannot log in (OAuth users bypass this)
- ✅ **Password reset** - Email service ready for password reset functionality

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Email Configuration (Required for email verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourdomain.com  # Optional, defaults to SMTP_USER
```

### Gmail Setup (Recommended for Development)

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "Trading Journal"
   - Copy the 16-character password
3. **Add to .env**:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   ```

### Other SMTP Providers

#### SendGrid
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

#### AWS SES
```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

#### Mailgun
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-smtp-password
```

## Database Migration

Run the migration to add verification fields:

```bash
cd backend
alembic upgrade head
```

## API Endpoints

### Register (Modified)
`POST /api/auth/register`
- Now sends verification email automatically
- User receives email with verification link

### Verify Email
`GET /api/auth/verify-email?token=<verification_token>`
- Verifies user's email address
- Returns success message

### Resend Verification
`POST /api/auth/resend-verification`
```json
{
  "email": "user@example.com"
}
```
- Sends new verification email
- Generates new 24-hour token

### Login (Modified)
`POST /api/auth/login`
- Now checks if email is verified
- Returns 403 error if email not verified
- OAuth users bypass verification check

## Frontend Implementation

### 1. Registration Success Page
Show message: "Please check your email to verify your account"

### 2. Verification Page
Create `/auth/verify-email` page that:
- Reads `token` from URL query parameter
- Calls verification API
- Shows success/error message
- Redirects to login

### 3. Login Error Handling
Handle 403 error with message:
"Please verify your email before logging in. Check your inbox or request a new verification email."

### 4. Resend Verification
Add "Resend Verification Email" button on login page for unverified users.

## Testing

### Development Mode (No SMTP)
If SMTP is not configured:
- Registration still works
- Email sending is skipped with a warning log
- You can manually verify users in the database:
  ```sql
  UPDATE users SET is_verified = TRUE WHERE email = 'user@example.com';
  ```

### With SMTP Configured
1. Register a new user
2. Check email inbox
3. Click verification link
4. Try to login before and after verification

## Security Benefits

1. **Prevents fake accounts** - Validates email ownership
2. **Reduces spam** - Limits automated registrations
3. **Account recovery** - Infrastructure ready for password reset
4. **Email verification tracking** - Audit trail of verified accounts
5. **Token expiration** - Time-limited verification links

## Production Considerations

1. **Use dedicated email service** (SendGrid, AWS SES, Mailgun)
2. **Enable HTTPS** for secure cookie transmission
3. **Set proper CORS origins** in production
4. **Monitor email delivery rates**
5. **Implement rate limiting** on resend verification endpoint
6. **Add email templates** with branding
7. **Track email bounces** and invalid addresses

## Troubleshooting

### Emails not sending
- Check SMTP credentials in `.env`
- Verify SMTP_HOST and SMTP_PORT
- Check firewall/network restrictions
- Review backend logs for errors

### Gmail "Less secure app" error
- Use App Password instead of account password
- Enable 2-Factor Authentication first

### Token expired
- Users can request new verification email
- Tokens expire after 24 hours by default

### User already verified
- API returns error if attempting to verify twice
- Check database `is_verified` column

## Future Enhancements

- [ ] Password reset via email
- [ ] Email change verification
- [ ] Welcome email after verification
- [ ] Email notifications for important events
- [ ] Email templates with HTML/CSS
- [ ] Unsubscribe functionality
- [ ] Email preferences in user settings
