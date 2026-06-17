# Git setup script for voice branch
Write-Host "Setting up Git repository..." -ForegroundColor Green

# Initialize git
Write-Host "Initializing Git repository..." -ForegroundColor Yellow
git init

# Add remote origin
Write-Host "Adding remote origin..." -ForegroundColor Yellow
git remote add origin https://github.com/hana-ahmed-33/Gradution_Project.git

# Fetch branches
Write-Host "Fetching branches from remote..." -ForegroundColor Yellow
git fetch origin

# Check if voice branch exists remotely
Write-Host "Checking available branches..." -ForegroundColor Yellow
git branch -a

# Switch to voice branch or create it
Write-Host "Switching to voice branch..." -ForegroundColor Yellow
try {
    git checkout voice
    Write-Host "Switched to existing voice branch" -ForegroundColor Green
} catch {
    git checkout -b voice
    Write-Host "Created new voice branch" -ForegroundColor Green
}

# Add all files
Write-Host "Adding all files..." -ForegroundColor Yellow
git add .

# Commit changes
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "feat: Enhanced Arabic voice recognition system

- Intelligent semantic classification for Arabic transactions
- Context-aware understanding of repair services, food, transportation
- Smart handling of ambiguous Arabic words (ست as number vs cleaning lady)
- Improved text segmentation for complex Arabic sentences
- Fixed English categories to prevent duplication
- Real-time voice transcription with AssemblyAI integration"

# Push to voice branch
Write-Host "Pushing to voice branch..." -ForegroundColor Yellow
git push -u origin voice

Write-Host "Git setup completed successfully!" -ForegroundColor Green
Write-Host "Repository connected and voice branch is ready." -ForegroundColor Cyan