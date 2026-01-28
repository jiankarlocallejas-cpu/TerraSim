# TerraSim - Terrain Simulation Platform

## Quick Start (3 Steps)

### Step 1: Install
```bash
pip install -r requirements.txt
```

### Step 2: Run
```bash
python terrasim.py
```

### Step 3: Login or Sign Up
Done! The app will show a login/signup window.

---

## First Time Setup

**New User?**
1. Click "Sign Up"
2. Enter your email, password, and username
3. Check your email for a verification code
4. Enter the code
5. Start using TerraSim!

**Already have an account?**
1. Click "Login"
2. Enter your email and password
3. Access your projects

---

## Features

- 🗺️ **Terrain Simulation** - Create and simulate terrain models
- 📊 **Analysis Tools** - Advanced terrain analysis
- 💾 **Project Management** - Save and manage projects
- 📱 **Multi-Device** - Login from different devices
- 🔒 **Secure** - Your data is encrypted and protected

---

## System Requirements

- **Python 3.10** or newer
- **Windows, macOS, or Linux**
- **Internet connection** (for email verification, optional for local use)
- **~100 MB** disk space

### Install Python
- **Windows**: https://www.python.org/downloads/
- **macOS**: `brew install python3`
- **Linux**: `apt-get install python3`

---

## Troubleshooting

### "python command not found"
Make sure Python 3.10+ is installed and added to PATH
- Windows: Reinstall Python, check "Add to PATH"
- macOS/Linux: `python3 --version`

### "Module not found"
Install dependencies:
```bash
pip install -r requirements.txt
```

### "Can't connect to database"
TerraSim initializes automatically on first run. If issues:
```bash
# For admins only:
python admin_console.py
→ Option 2: Initialize Database
```

### "Email not received"
Email verification is configured during first deployment. Contact your administrator if signup emails aren't arriving.

---

## For Administrators

To set up TerraSim before distributing to users:

```bash
python admin_console.py
```

Menu options:
1. Configure Email Service (required for signups)
2. Initialize Database
3. Create admin user
4. View configuration
5. Backup database

See **TERRASIM_DEPLOYMENT_GUIDE.md** for full admin guide.

---

## Getting Help

1. Check this file (README.md)
2. Review **TERRASIM_DEPLOYMENT_GUIDE.md**
3. Check logs: `terrasim.log`
4. Contact your administrator

---

## What's Happening Behind the Scenes?

- ✓ Database initializes automatically
- ✓ Your login info is encrypted
- ✓ Device tracking is automatic
- ✓ All backups are saved securely
- ✓ You don't need to configure anything - it just works!

---

## Privacy & Security

- **Your password** is encrypted with industry-standard security
- **Your email** is only used for verification and notifications
- **Your data** stays on your device or our secure servers
- **Your device info** is only tracked for security purposes

No third parties can see your data.

---

## Next Steps

1. **Run TerraSim**: `python terrasim.py`
2. **Sign Up or Login**
3. **Start creating simulations!**

Enjoy using TerraSim! 🎉
