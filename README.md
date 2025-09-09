# 🎾 TennisMatchUp - Professional Tennis Booking System

A comprehensive Flask-based web application for tennis court booking, player matching, and facility management. Built with professional MVC architecture and production-ready features.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ installed
- Git for version control
- Code editor (VS Code recommended)

### Installation

1. **Clone & Navigate**
   ```bash
   git clone <your-repo-url>
   cd TennisMatchUp
   ```

2. **Virtual Environment Setup**
   ```bash
   python -m venv tennis_env
   # Windows
   tennis_env\Scripts\activate
   # Linux/Mac
   source tennis_env/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys (see Configuration section)
   ```

5. **Initialize Database**
   ```bash
   python app.py
   # Database will be created automatically on first run
   ```

6. **Access Application**
   - Open browser to: http://localhost:5000
   - Use demo accounts (see Demo Accounts section)

## ⚙️ Configuration

### Required API Keys

Edit your `.env` file with these services:

#### 1. Secret Key (Required)
```bash
SECRET_KEY=your-unique-secret-key-here
```
Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

#### 2. SendGrid Email Service (Required for notifications)
```bash
SENDGRID_API_KEY=SG.your-sendgrid-api-key-here
EMAIL_ADDRESS=noreply@yourdomain.com
```
- Sign up at: https://sendgrid.com
- Get API key from Settings > API Keys
- Verify sender email address

#### 3. OpenCage Geocoding (Required for location features)
```bash
OPENCAGE_API_KEY=your-opencage-api-key-here
```
- Sign up at: https://opencagedata.com
- Free tier: 2,500 requests/day
- Used for player location matching

#### 4. Database Configuration
```bash
# Development (SQLite - Default)
DATABASE_URL=sqlite:///tennis_matchup.db

# Production (PostgreSQL example)
DATABASE_URL=postgresql://user:password@host:port/database
```

### Optional Configuration
```bash
# AI Features (Future use)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Environment
FLASK_ENV=development  # or 'production'
```

## 🎯 Demo Accounts

### Admin Account
- **Email:** admin@tennismatchup.com
- **Password:** admin123
- **Access:** Full system management, analytics, user management

### Player Account
- **Email:** player@demo.com
- **Password:** password123
- **Access:** Court booking, player matching, calendar

### Court Owner Account
- **Email:** owner@demo.com  
- **Password:** password123
- **Access:** Court management, booking approval, revenue tracking

## 🏗️ Project Architecture

### MVC Structure
```
TennisMatchUp/
├── app.py                 # Flask application factory
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (DO NOT COMMIT)
├── .env.template        # Template for environment setup
│
├── models/              # Data Layer
│   ├── database.py      # Database initialization
│   ├── user.py         # User/Player/Owner/Admin models
│   ├── court.py        # Court and facility models
│   └── booking.py      # Booking and reservation models
│
├── routes/              # Controller Layer
│   ├── main.py         # Home and general routes
│   ├── auth.py         # Authentication (login/register)
│   ├── player.py       # Player functionality
│   ├── owner.py        # Court owner features
│   ├── admin.py        # Admin management
│   ├── shared_booking.py # Two-player bookings
│   └── api.py          # RESTful API endpoints
│
├── services/            # Business Logic Layer
│   ├── rule_engine.py   # Business rules and validation
│   ├── matching_engine.py # Player matching algorithms
│   ├── booking_service.py # Booking workflow
│   ├── revenue_service.py # Financial calculations
│   ├── geo_service.py   # Location services
│   └── ai_service.py    # AI integrations
│
├── templates/           # View Layer (HTML)
│   ├── base.html       # Base template
│   ├── auth/           # Authentication templates
│   ├── player/         # Player interface
│   ├── owner/          # Owner dashboard
│   └── admin/          # Admin panels
│
├── static/              # Static Assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── images/         # Images and icons
│
└── utils/               # Utilities
    ├── template_filters.py # Jinja2 custom filters
    └── helpers.py       # Helper functions
```

## 🔧 Development

### Running the Application
```bash
# Development server
python app.py

# Production server (with Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Database Management
```bash
# Reset database (development)
rm instance/tennis_matchup.db
python app.py

# View database (SQLite)
sqlite3 instance/tennis_matchup.db
.tables
.schema users
```

### Code Quality
```bash
# Python code formatting
pip install black flake8
black .
flake8 .

# Run tests
python -m pytest tests/
```

## 🎮 Features Overview

### Player Features
- **Registration & Profile:** Complete player profiles with skill levels
- **Court Search:** Find available courts by date, time, location
- **Player Matching:** AI-powered player matching by skill, location, availability
- **Booking System:** Reserve courts solo or request shared bookings
- **Calendar View:** Personal booking calendar with availability
- **Match History:** Track past games and partners

### Court Owner Features
- **Facility Management:** Add/edit courts with pricing and availability
- **Booking Approval:** Approve or decline booking requests
- **Revenue Analytics:** Detailed financial reporting and insights
- **Schedule Management:** Set court availability and maintenance windows
- **Player Communication:** Message system for booking coordination

### Admin Features
- **User Management:** Manage all players, owners, and system users
- **System Analytics:** Platform-wide usage and performance metrics
- **Content Moderation:** Review and manage user-generated content
- **System Configuration:** Manage business rules and platform settings
- **Financial Oversight:** Monitor all transactions and revenue

### Technical Features
- **RESTful API:** Complete API for mobile/external integrations
- **Real-time Updates:** AJAX-powered dynamic content
- **Geographic Services:** Location-based matching and search
- **Email Notifications:** Automated booking confirmations and reminders
- **Security:** CSRF protection, session management, role-based access
- **Responsive Design:** Mobile-friendly interface

## 🔐 Security

### Environment Security
- **Never commit `.env` file** - Contains sensitive API keys
- **Use strong SECRET_KEY** - Generate cryptographically secure key
- **HTTPS in Production** - Always use SSL certificates
- **Database Security** - Use proper credentials and connection encryption

### Application Security
- **CSRF Protection:** Enabled on all forms
- **Session Security:** Secure session management
- **Input Validation:** Server-side validation on all inputs
- **SQL Injection Protection:** SQLAlchemy ORM prevents SQL injection
- **XSS Prevention:** Template escaping enabled by default

## 📦 Deployment

### Production Checklist
1. **Environment Variables**
   - Set `FLASK_ENV=production`
   - Use production database URL
   - Configure real SMTP settings
   - Set secure SECRET_KEY

2. **Database**
   - Use PostgreSQL for production
   - Enable database backups
   - Configure connection pooling

3. **Web Server**
   - Use Gunicorn or uWSGI
   - Configure reverse proxy (Nginx/Apache)
   - Enable HTTPS with SSL certificates

4. **Monitoring**
   - Configure logging
   - Set up error tracking
   - Monitor performance metrics

### Environment Examples
```bash
# Development
FLASK_ENV=development
DATABASE_URL=sqlite:///tennis_matchup.db

# Production
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/db
```

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Solution: Initialize database
python app.py
```

**Import Errors**
```bash
# Solution: Activate virtual environment
tennis_env\Scripts\activate  # Windows
source tennis_env/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

**API Key Errors**
```bash
# Solution: Check .env file
cat .env  # Linux/Mac
type .env  # Windows
# Ensure all required API keys are set
```

**Email Not Sending**
- Verify SendGrid API key is correct
- Check sender email is verified in SendGrid
- Confirm EMAIL_ADDRESS matches verified sender

**Location Features Not Working**
- Verify OpenCage API key is valid
- Check API usage limits not exceeded
- Test API key at: https://opencagedata.com/dashboard

### Getting Help
- Check logs in console output
- Review Flask debug messages
- Verify all services are configured correctly
- Ensure database permissions are correct

## 📊 API Documentation

### Authentication Endpoints
```
POST /auth/login          # User login
POST /auth/register       # User registration
POST /auth/logout         # User logout
```

### Player API
```
GET  /api/courts          # List available courts
POST /api/bookings        # Create booking
GET  /api/matches/find    # Find player matches
GET  /api/calendar/events # Get calendar events
```

### Owner API
```
GET  /api/revenue         # Revenue analytics
PUT  /api/courts/:id      # Update court details
GET  /api/bookings        # Manage bookings
```

### Admin API
```
GET  /api/users           # User management
GET  /api/analytics       # System analytics
PUT  /api/settings        # System configuration
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Follow MVC architecture guidelines
4. Write tests for new features
5. Submit pull request

### Code Standards
- Follow Python PEP 8 style guide
- Maintain strict MVC separation
- No embedded CSS/JS in templates
- Use service layer for business logic
- Add tests for new functionality

## 📝 License

This project is developed for academic purposes. All rights reserved.

---

**🎾 TennisMatchUp** - Connecting players, courts, and communities through technology.

For technical support or questions, please review the troubleshooting section or check the project documentation.