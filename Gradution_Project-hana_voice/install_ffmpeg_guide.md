# Install FFmpeg on Windows

## Method 1: Using Chocolatey (Easiest)
1. Open PowerShell as Administrator
2. Install Chocolatey if you don't have it:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```
3. Install FFmpeg:
   ```powershell
   choco install ffmpeg
   ```

## Method 2: Manual Installation
1. Go to https://www.gyan.dev/ffmpeg/builds/
2. Download "release builds" → "ffmpeg-release-essentials.zip"
3. Extract to `C:\ffmpeg`
4. Add `C:\ffmpeg\bin` to your PATH:
   - Press Win+R, type `sysdm.cpl`
   - Click "Environment Variables"
   - Under "System Variables", find "Path"
   - Click "Edit" → "New" → Add `C:\ffmpeg\bin`
   - Click OK on all dialogs
5. Restart your command prompt/PowerShell

## Method 3: Using Winget (Windows 10/11)
```powershell
winget install Gyan.FFmpeg
```

## Verify Installation
Open new command prompt and run:
```cmd
ffmpeg -version
```

You should see FFmpeg version information.

## After Installation
1. Restart your Finance Analyzer server
2. Try recording again - it should now use your real voice!