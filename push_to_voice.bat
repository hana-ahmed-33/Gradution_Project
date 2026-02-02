@echo off
echo Pushing to hana_voice branch...
echo.
echo Current branch:
git branch
echo.
echo Remote URL:
git remote -v
echo.
echo Adding all files...
git add .
echo.
echo Committing changes...
git commit -m "feat: Enhanced Arabic voice recognition system - intelligent semantic classification"
echo.
echo Pushing to hana_voice branch...
git push -u origin hana_voice
echo.
echo Done!
pause