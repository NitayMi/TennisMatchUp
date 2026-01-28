# 🔒 TennisMatchUp Deployment Security Guide

## Critical Security Setup Required

### 1. Environment Variables Setup

**NEVER use the example .env file in production!**

1. Copy `.env.template` to `.env`
2. Replace all placeholder values with real credentials
3. Ensure `.env` is in `.gitignore` (already configured)

### 2. Required Secrets

#### Database Configuration
```bash
DATABASE_URL=postgresql://username:password@host:port/database
```
- Use a strong database password (minimum 16 characters)
- Restrict database access to application servers only
- Enable SSL connections

#### Flask Secret Key
```bash
SECRET_KEY=your-very-long-random-secret-key-here
```
- Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- Never reuse across environments

#### SendGrid Email Service
```bash
SENDGRID_API_KEY=SG.your-sendgrid-api-key-here
EMAIL_ADDRESS=your-verified-sender@domain.com
```
- Create API key with minimal required permissions
- Verify sender domain/email in SendGrid

#### OpenCage Geocoding API
```bash
OPENCAGE_API_KEY=your-opencage-api-key-here
```
- Get free API key from: https://opencagedata.com/
- Monitor usage to prevent quota exceeded

### 3. Production Environment Variables

For cloud deployment, set these environment variables:

```bash
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=your-production-database-url
SENDGRID_API_KEY=your-sendgrid-api-key
EMAIL_ADDRESS=your-production-email
OPENCAGE_API_KEY=your-opencage-api-key
```

### 4. Security Checklist

- [ ] No secrets in code repository
- [ ] `.env` file in `.gitignore`
- [ ] Database password is strong and unique
- [ ] Flask SECRET_KEY is cryptographically random
- [ ] SendGrid API key has minimal permissions
- [ ] Database connections use SSL
- [ ] Application runs with HTTPS only
- [ ] All API keys are production-specific

### 5. Development vs Production

**Development (.env)**:
- Use SQLite database
- Use development API keys with limited quotas
- FLASK_ENV=development

**Production (Environment Variables)**:
- Use PostgreSQL or similar production database
- Use production API keys
- FLASK_ENV=production
- Enable all security headers

### 6. Emergency Procedures

If secrets are exposed:
1. Immediately rotate all API keys
2. Change database passwords
3. Generate new Flask SECRET_KEY
4. Review git history for exposed credentials
5. Update deployment with new secrets
