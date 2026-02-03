# ExoStack AI - Landing Page & User Management

This is the landing page and user management system for ExoStack AI, providing authentication, user profiles, and seamless integration with the main ExoStack dashboard.

## 🚀 Features

### Authentication System
- **User Registration & Login**: Secure signup and signin with JWT tokens
- **Session Management**: HTTP-only cookies with automatic token refresh
- **Password Security**: Bcrypt hashing with secure password change functionality
- **Protected Routes**: Middleware-based authentication for dashboard and API routes

### User Management
- **Profile Management**: Complete user profiles with avatar upload
- **Settings & Preferences**: Customizable notification and account settings
- **User Stats**: Track login history and account usage
- **Social Profiles**: GitHub, Twitter, LinkedIn integration

### Dashboard Integration
- **Seamless Flow**: Landing page → Authentication → ExoStack Dashboard
- **User Context**: Dashboard displays user-specific nodes and tasks
- **Real-time Data**: Live integration with ExoStack API
- **Responsive Design**: Mobile-first design with sidebar navigation

## 📁 Project Structure

```
exostack/
├── app/
│   ├── api/
│   │   └── auth/
│   │       ├── login/route.ts
│   │       ├── register/route.ts
│   │       ├── logout/route.ts
│   │       └── me/route.ts
│   ├── api/user/
│   │   ├── profile/route.ts
│   │   └── password/route.ts
│   ├── dashboard/
│   │   └── page.tsx
│   └── page.tsx
├── components/
│   ├── auth/
│   │   └── AuthForm.tsx
│   ├── settings/
│   │   └── SettingsPage.tsx
│   └── DashboardLayout.tsx
├── lib/
│   ├── auth/
│   │   ├── auth.service.ts
│   │   └── middleware.ts
│   └── db.ts
├── prisma/
│   ├── schema.prisma
│   └── seed.ts
└── middleware.ts
```

## 🛠 Setup Instructions

### 1. Install Dependencies

```bash
# Install landing page dependencies
npm install

# Or use the separate package file
cp package-landing.json package.json
npm install
```

### 2. Environment Setup

Copy the environment template:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your configuration:

```env
# Database
DATABASE_URL="file:./dev.db"

# Authentication
JWT_SECRET="your-super-secret-jwt-key-change-this-in-production"
JWT_EXPIRES_IN="7d"

# ExoStack API
EXOSTACK_API_URL="http://localhost:8000"
```

### 3. Database Setup

```bash
# Generate Prisma client
npx prisma generate

# Push database schema
npx prisma db push

# (Optional) Seed with demo data
npx prisma db seed
```

### 4. Start Development

```bash
# Start the landing page
npm run dev

# Start ExoStack Hub (in another terminal)
cd exostack
python start_exostack.py hub

# Start an ExoStack Agent (in another terminal)
cd exostack
python start_exostack.py agent --node-id demo-laptop
```

Visit `http://localhost:3000` to see the landing page.

## 📊 Database Schema

### Core Models

- **User**: Basic user information and authentication
- **UserProfile**: Extended profile data and preferences
- **Session**: User login sessions and tokens
- **Node**: User's ExoStack compute nodes
- **Task**: AI tasks executed on user's nodes
- **NodeMetric**: Performance metrics for nodes
- **TaskMetric**: Performance metrics for tasks
- **ApiKey**: API keys for programmatic access
- **AuditLog**: Security and activity logging

## 🔐 Authentication Flow

1. **Registration**: User signs up → Password hashed → User created → JWT token generated
2. **Login**: User credentials validated → JWT token generated → Session created
3. **Dashboard Access**: Token verified → User data loaded → ExoStack integration
4. **Logout**: Session invalidated → Token cleared → Redirect to landing

## 🎨 UI Components

### Landing Page
- **Hero Section**: ExoStack AI value proposition
- **Auth Forms**: Tabbed login/register with validation
- **Feature Highlights**: Key platform benefits
- **Social Links**: GitHub and Twitter integration

### Dashboard
- **Navigation**: Responsive sidebar with user menu
- **Overview**: Stats and recent activity
- **Nodes Management**: AI compute node monitoring
- **Task History**: Complete task execution history
- **Settings**: Profile, security, and preferences

### Settings Page
- **Profile Management**: Personal info and social links
- **Security**: Password change and account security
- **Notifications**: Email and in-app preferences
- **Account Info**: Usage limits and subscription status

## 🔌 API Integration

### ExoStack API Endpoints Used

- `GET /nodes/status` - Get user's compute nodes
- `GET /tasks/status` - Get user's task history
- Real-time data updates every 5 seconds

### Authentication API

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `POST /api/user/password` - Change password

## 🎯 User Journey

1. **Discovery**: User lands on the marketing page
2. **Interest**: Learns about ExoStack AI benefits
3. **Registration**: Creates account with email/username
4. **Onboarding**: Redirected to dashboard with welcome
5. **Setup**: Adds their first compute node
6. **Usage**: Monitors AI tasks and earnings
7. **Management**: Updates profile and settings

## 🔧 Customization

### Branding
- Update colors in `tailwind.config.js`
- Modify logo and branding in components
- Customize copy in landing page

### Features
- Add new settings in `SettingsPage.tsx`
- Extend user schema in `prisma/schema.prisma`
- Create new API routes in `app/api/`

### Integration
- Modify ExoStack API calls in dashboard
- Update authentication logic for different backends
- Add third-party auth providers

## 🚀 Deployment

### Environment Variables

```env
NODE_ENV=production
DATABASE_URL="your-production-database-url"
JWT_SECRET="your-production-jwt-secret"
EXOSTACK_API_URL="https://your-exostack-api.com"
NEXTAUTH_URL="https://your-domain.com"
```

### Build Commands

```bash
# Build for production
npm run build

# Start production server
npm start

# Database operations
npx prisma db push
npx prisma generate
```

## 🧪 Testing

```bash
# Run linting
npm run lint

# Database operations
npx prisma studio  # View database
npx prisma db seed  # Reset demo data
```

## 📈 Analytics & Monitoring

### User Tracking
- Registration funnels
- Login patterns
- Feature usage
- Node activity

### Performance Metrics
- API response times
- Database query performance
- Authentication success rates
- Dashboard load times

## 🔒 Security Considerations

- JWT tokens with expiration
- HTTP-only cookies
- Password hashing with bcrypt
- Rate limiting on auth endpoints
- Input validation with Zod
- SQL injection prevention with Prisma
- XSS protection with Next.js defaults

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection**: Check `DATABASE_URL` in `.env.local`
2. **Authentication Failures**: Verify `JWT_SECRET` is set
3. **ExoStack Integration**: Ensure ExoStack Hub is running on port 8000
4. **Node Not Showing**: Check agent registration and heartbeat

### Debug Commands

```bash
# Check database
npx prisma studio

# View logs
npm run dev

# Reset database
npx prisma db push --force-reset
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📞 Support

- GitHub Issues: Report bugs and request features
- Documentation: Check inline code comments
- Community: Join Discord for discussions

---

**ExoStack AI Landing Page** - Your gateway to distributed AI computing! 🚀