@echo off
echo Creating and switching to voice branch...
git checkout -b voice

echo Adding all files...
git add .

echo Committing voice recognition features...
git commit -m "feat: Intelligent Arabic voice recognition system

- Enhanced semantic classification for Arabic transactions
- Smart context understanding (repair services, food, transportation)
- Fixed English categories to prevent duplication
- Improved text segmentation for complex Arabic sentences
- Context-aware handling of ambiguous words (ست as number vs cleaning lady)
- Real-time voice transcription with AssemblyAI
- Comprehensive transaction extraction and categorization"

echo Pushing to voice branch...
git push -u origin voice

echo Done! Voice branch created and pushed.
pause