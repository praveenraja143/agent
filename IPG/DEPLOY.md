# IPG - Full Deployment Guide

## Complete Flow
```
1. Export IPG Web App → Host on Render (Free)
2. Use Render URL in Android Studio WebView App
3. Build APK → Install on Phone
```

---

## PART 1: Host Web App on Render (Free)

### Step 1: Export Web Build
```bash
cd IPG
npm install
npm run export:web
```
This creates `dist/` folder with all web files.

### Step 2: Deploy to Render

**Method 1: GitHub Connect (Recommended)**
1. Go to https://render.com
2. Sign up with GitHub account
3. Click **New +** → **Static Site**
4. Connect repository: `praveenraja143/Link`
5. Configure:
   - **Name**: `ipg-app`
   - **Branch**: `main`
   - **Root Directory**: `IPG`
   - **Build Command**: `npm install && npm run export:web`
   - **Publish Directory**: `dist`
6. Click **Create Static Site**
7. Wait 2-3 minutes for build
8. Your URL: `https://ipg-app-xxxx.onrender.com`

**Method 2: Manual Upload**
1. Run `npm run export:web` in IPG folder
2. Go to https://render.com
3. New Static Site
4. Upload `dist/` folder directly
5. Get your URL

### Step 3: Test Web App
Open `https://your-app.onrender.com` in browser
- Works on mobile browser too!
- Setup flow: Upload resume → LinkedIn credentials → API key

---

## PART 2: Build APK with Android Studio

### Step 1: Open Android Studio
1. Open Android Studio
2. **Open Existing Project**
3. Navigate to: `D:\gowri\New folder\IPG-Android-App`
4. Wait for Gradle sync to complete

### Step 2: Update URL in MainActivity.java
Open `app/src/main/java/com/ipg/app/MainActivity.java`

Find this line:
```java
private static final String APP_URL = "https://ipg-app.onrender.com";
```

Replace `https://ipg-app.onrender.com` with your actual Render URL.

### Step 3: Build APK

**Debug APK (For Testing)**
1. Menu: **Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**
2. Wait for build to complete
3. Click **locate** in popup
4. APK location: `app/build/outputs/apk/debug/app-debug.apk`
5. Transfer to phone and install

**Release APK (For Distribution)**
1. Menu: **Build** → **Generate Signed Bundle / APK**
2. Select **APK**
3. Create new keystore or use existing
4. Select **release** build variant
5. Click **Finish**
6. APK location: `app/release/app-release.apk`

### Step 4: Install APK on Phone
1. Transfer APK to phone (USB, WhatsApp, email, etc.)
2. Enable **Install from Unknown Sources** in phone settings
3. Tap APK file to install
4. App name: **IPG**
5. Open and use!

---

## PART 3: Alternative - EAS Build (No Android Studio Needed)

If you don't want to use Android Studio:

```bash
cd IPG
npm install -g eas-cli
eas login
eas build:configure
eas build --platform android --profile preview
```

Download APK from https://expo.dev dashboard

---

## PART 4: Update App After Changes

### Web App Update
1. Make changes in IPG folder
2. `git add -A && git commit -m "update"`
3. `git push origin main`
4. Render auto-deploys in 1-2 minutes
5. APK automatically shows new content (loads from URL)

### APK Update
If you change the Render URL or app structure:
1. Update MainActivity.java with new URL
2. Rebuild APK in Android Studio
3. Install new APK on phone

---

## File Structure
```
IPG/                          ← Web app (hosted on Render)
├── app/                      ← All screens
├── src/                      ← API and utils
├── package.json
├── render.yaml               ← Render config
└── dist/                     ← Generated web build

IPG-Android-App/              ← Android Studio project
├── app/
│   ├── src/main/
│   │   ├── java/com/ipg/app/
│   │   │   └── MainActivity.java    ← WebView loader
│   │   ├── res/layout/
│   │   │   └── activity_main.xml    ← WebView layout
│   │   └── AndroidManifest.xml      ← Permissions
│   └── build.gradle
└── settings.gradle
```

---

## Quick Commands

### Web Development
```bash
cd IPG
npm install          # First time only
npm run web          # Test in browser
npm run export:web   # Build for production
```

### Git
```bash
git add -A
git commit -m "your message"
git push origin main
```

### Android Studio
1. Open IPG-Android-App folder
2. Build → Build APK
3. Install on phone

---

## Troubleshooting

**Render Build Fails:**
- Check build logs on render.com
- Make sure `dist/` folder exists after export

**APK Shows Blank Screen:**
- Check internet connection on phone
- Verify URL in MainActivity.java is correct
- Check Render URL is working in browser first

**APK Install Failed:**
- Enable "Unknown Sources" in phone settings
- Uninstall old version first
- Check minimum SDK (API 24+)

**Web App Not Loading:**
- Clear browser cache
- Check Render dashboard for errors
- Try incognito mode

---

## App Name: IPG
## GitHub: https://github.com/praveenraja143/Link
