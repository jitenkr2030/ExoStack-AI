#!/bin/bash

echo "🚀 Setting up ExoStack AI Landing Page..."
echo "=================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed (for ExoStack)
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install landing page dependencies
echo "📦 Installing landing page dependencies..."
cp package-landing.json package.json
npm install

# Setup environment file
if [ ! -f .env.local ]; then
    echo "⚙️ Creating environment file..."
    cp .env.local .env.local.backup 2>/dev/null || true
    cat > .env.local << EOF
# Database
DATABASE_URL="file:./dev.db"

# Authentication
JWT_SECRET="exostack-$(openssl rand -hex 32)"
JWT_EXPIRES_IN="7d"

# Next.js
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="exostack-$(openssl rand -hex 32)"

# ExoStack API
EXOSTACK_API_URL="http://localhost:8000"

# Email (for future email verification)
EMAIL_FROM="noreply@exostack.ai"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER=""
SMTP_PASS=""

# File Upload (for avatars)
UPLOAD_DIR="./uploads"
MAX_FILE_SIZE=2097152  # 2MB

# Rate Limiting
RATE_LIMIT_WINDOW=900000  # 15 minutes in milliseconds
RATE_LIMIT_MAX=100  # requests per window
EOF
    echo "✅ Environment file created with secure random secrets"
else
    echo "✅ Environment file already exists"
fi

# Setup database
echo "🗄️ Setting up database..."
npx prisma generate
npx prisma db push
npx prisma db seed

# Create uploads directory
mkdir -p uploads

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start the landing page:     npm run dev"
echo "2. Start ExoStack Hub:        cd exostack && python start_exostack.py hub"
echo "3. Start ExoStack Agent:      cd exostack && python start_exostack.py agent --node-id my-laptop"
echo ""
echo "🌐 Visit: http://localhost:3000"
echo ""
echo "👤 Demo account:"
echo "   Email: demo@exostack.ai"
echo "   Password: password123"
echo ""
echo "📚 For more info, see LANDING_README.md"