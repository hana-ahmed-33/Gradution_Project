@echo off
echo Connecting to existing repository and voice branch...

echo Step 1: Initialize git if not already done...
git init

echo Step 2: Add remote origin...
git remote add origin https://github.com/hana-ahmed-33/Gradution_Project.git

echo Step 3: Fetch all branches from remote...
git fetch origin

echo Step 4: Switch to voice branch...
git checkout voice

echo Step 5: Set upstream for voice branch...
git branch --set-upstream-to=origin/voice voice

echo Step 6: Add all current changes...
git add .

echo Step 7: Commit voice recognition improvements...
git commit -m "feat: Enhanced intelligent Arabic voice recognition

- Improved semantic classification system
- Better context understanding for Arabic phrases
- Fixed categorization issues (cleaning services, transportation, food)
- Enhanced text segmentation for complex sentences
- Smart handling of ambiguous Arabic words
- Real-time voice analysis with proper categorization"

echo Step 8: Push to voice branch...
git push origin voice

echo Done! Connected to repo and pushed to voice branch.
pause