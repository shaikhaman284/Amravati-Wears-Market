# Quick Deployment Script for FCM Changes

# This script will help you deploy the FCM notification changes to Railway

Write-Host "🚀 FCM Notification Deployment Script" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan

# Step 1: Check if we're in the backend directory
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ Error: Not in backend directory!" -ForegroundColor Red
    Write-Host "Please run this script from the backend folder" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ In backend directory`n" -ForegroundColor Green

# Step 2: Check if firebase-admin is in requirements.txt
Write-Host "📦 Checking requirements.txt..." -ForegroundColor Yellow
$hasFirebase = Select-String -Path "requirements.txt" -Pattern "firebase-admin" -Quiet
if ($hasFirebase) {
    Write-Host "✅ firebase-admin found in requirements.txt`n" -ForegroundColor Green
} else {
    Write-Host "❌ firebase-admin NOT in requirements.txt" -ForegroundColor Red
    Write-Host "Adding it now..." -ForegroundColor Yellow
    Add-Content -Path "requirements.txt" -Value "firebase-admin==7.1.0"
    Write-Host "✅ Added firebase-admin to requirements.txt`n" -ForegroundColor Green
}

# Step 3: Check if migration file exists
Write-Host "🔍 Checking migration file..." -ForegroundColor Yellow
if (Test-Path "accounts\migrations\0002_user_fcm_token.py") {
    Write-Host "✅ Migration file exists`n" -ForegroundColor Green
} else {
    Write-Host "❌ Migration file NOT found!" -ForegroundColor Red
    Write-Host "Please run: python manage.py makemigrations accounts" -ForegroundColor Yellow
    exit 1
}

# Step 4: Check Git status
Write-Host "📝 Checking Git status..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "📋 Uncommitted changes found:`n" -ForegroundColor Yellow
    git status --short
    Write-Host ""
} else {
    Write-Host "✅ No uncommitted changes`n" -ForegroundColor Green
}

# Step 5: Show files to be committed
Write-Host "📂 Files that will be deployed:" -ForegroundColor Cyan
Write-Host "  - accounts/models.py (fcm_token field)" -ForegroundColor White
Write-Host "  - accounts/migrations/0002_user_fcm_token.py (migration)" -ForegroundColor White
Write-Host "  - accounts/views.py (register_fcm_token endpoint)" -ForegroundColor White
Write-Host "  - accounts/urls.py (FCM route)" -ForegroundColor White
Write-Host "  - orders/notification_service.py (notification service)" -ForegroundColor White
Write-Host "  - orders/views.py (notification triggers)" -ForegroundColor White
Write-Host "  - requirements.txt (firebase-admin)`n" -ForegroundColor White

# Step 6: Prompt for deployment
Write-Host "🚀 Ready to deploy?" -ForegroundColor Cyan
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. Add all changes to Git" -ForegroundColor White
Write-Host "  2. Commit with message: 'Add FCM push notifications for seller app'" -ForegroundColor White
Write-Host "  3. Push to origin main (triggers Railway deployment)" -ForegroundColor White
Write-Host ""

$response = Read-Host "Continue? (y/n)"
if ($response -ne "y") {
    Write-Host "❌ Deployment cancelled" -ForegroundColor Red
    exit 0
}

# Step 7: Git add, commit, push
Write-Host "`n📦 Adding files to Git..." -ForegroundColor Yellow
git add .

Write-Host "💾 Committing changes..." -ForegroundColor Yellow
git commit -m "Add FCM push notifications for seller app"

Write-Host "🚀 Pushing to repository..." -ForegroundColor Yellow
git push origin main

Write-Host "`n✅ Deployment initiated!" -ForegroundColor Green
Write-Host ""
Write-Host "⏳ Next steps:" -ForegroundColor Cyan
Write-Host "  1. Go to Railway Dashboard: https://railway.app" -ForegroundColor White
Write-Host "  2. Check deployment logs" -ForegroundColor White
Write-Host "  3. Look for: 'Applying accounts.0002_user_fcm_token... OK'" -ForegroundColor White
Write-Host "  4. Wait for deployment to complete" -ForegroundColor White
Write-Host "  5. Upload firebase-credentials.json to Railway (if not done)" -ForegroundColor White
Write-Host "  6. Log out and log in again in seller app" -ForegroundColor White
Write-Host "  7. Test notifications!" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Done! Check Railway for deployment status." -ForegroundColor Green
