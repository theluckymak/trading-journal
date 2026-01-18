# OAuth Configuration Instructions

## Setting Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "Google+ API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure consent screen:
   - Application name: Trading Journal
   - Authorized domains: localhost (for development)
6. Create OAuth Client ID:
   - Application type: Web application
   - Authorized JavaScript origins: `http://localhost:3000`
   - Authorized redirect URIs: `http://localhost:3000/auth/callback`
7. Copy Client ID and Client Secret

## Setting Up GitHub OAuth

1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - Application name: Trading Journal
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:3000/auth/callback`
4. Register application
5. Copy Client ID and generate Client Secret

## Environment Variables

Add these to your `docker-compose.yml` under backend environment:

```yaml
- GOOGLE_CLIENT_ID=your_google_client_id_here
- GOOGLE_CLIENT_SECRET=your_google_client_secret_here
- GITHUB_CLIENT_ID=your_github_client_id_here
- GITHUB_CLIENT_SECRET=your_github_client_secret_here
```

Add these to your frontend `.env.local`:

```
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here
NEXT_PUBLIC_GITHUB_CLIENT_ID=your_github_client_id_here
```

## Database Migration

Run this SQL to update your database:

```sql
ALTER TABLE users 
  ALTER COLUMN hashed_password DROP NOT NULL,
  ADD COLUMN oauth_provider VARCHAR(50),
  ADD COLUMN oauth_id VARCHAR(255);

CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_id);
```

## Testing

1. Rebuild containers: `docker-compose up --build`
2. Go to http://localhost:3000/login
3. Click "Google" or "GitHub" button
4. Complete OAuth flow
5. You should be redirected to dashboard

## Production Notes

For production deployment:
- Change `secure=False` to `secure=True` in auth.py for cookies
- Update redirect URIs to your production domain
- Use environment variables for all secrets
- Never commit secrets to git
