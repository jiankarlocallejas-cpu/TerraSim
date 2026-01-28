# TerraSim Setup & Administration Guide

## For End Users

**You don't need to read this.** Just:

```bash
pip install -r requirements.txt
python terrasim.py
```

See `USER_README.md` for user guide.

---

## For Administrators (Setup)

### Choose Your Deployment Type

#### **Option 1: Local Database (Default - No Setup Needed)**

```bash
pip install -r requirements.txt
python terrasim.py
```

- ✅ Works offline
- ✅ No setup needed
- ❌ Data only on this computer
- ❌ No multi-device login

---

#### **Option 2: Cloud Database (Recommended - 15 Minutes Setup)**

**Benefits:**
- ✅ Multi-device login (Windows/Mac/Linux with same account)
- ✅ Data syncs automatically
- ✅ Teams can collaborate
- ✅ Automatic backups
- ✅ Always accessible

**Setup Time:** 15 minutes

**See:** `CLOUD_SETUP_QUICK_START.md` ← Start here!

---

## Quick Links

### For Different Tasks:

| Task | File | Time |
|------|------|------|
| Setup Cloud Database | `CLOUD_SETUP_QUICK_START.md` | 15 min |
| Cloud Database Details | `CLOUD_DATABASE_MIGRATION.md` | Read |
| Supabase Guide | `SUPABASE_SETUP_GUIDE.md` | 30 min |
| User Guide | `USER_README.md` | 5 min |
| Deployment Info | `DEPLOYMENT_COMPLETE.md` | Read |

---

## Admin Console Commands

All admin tasks in one place:

```bash
python admin_console.py
```

**Menu Options:**

```
1. Configure Email Service
   - Gmail, SendGrid, Mailgun, Outlook, Custom SMTP
   - For sending verification codes

2. Initialize Database
   - Create database tables
   - Must run after cloud setup

3. Reset Database
   - Delete all data (WARNING!)
   - Use for testing

4. Create Admin User
   - Add administrator account
   - Manual user creation

5. View Configuration
   - See current database/email config
   - Check user count

6. Set Up Cloud Database
   - Supabase, Railway, Render
   - Interactive wizard

7. Create Database Backup
   - Backup to timestamped file
   - For local databases

0. Exit
```

---

## Setup Path (Cloud Database)

### **Step 1: Prerequisites**
```bash
# Install Python dependencies
pip install -r requirements.txt
```

### **Step 2: Create Cloud Account (5 min)**
```
Go to: https://supabase.com
Create free account
Create database project
Get connection string
```

### **Step 3: Configure TerraSim (4 min)**
```bash
python admin_console.py
→ 6: Set Up Cloud Database
→ Choose Supabase
→ Paste connection string
```

### **Step 4: Initialize Database (2 min)**
```bash
python admin_console.py
→ 2: Initialize Database
```

### **Step 5: Create Admin User (2 min)**
```bash
python admin_console.py
→ 4: Create Admin User
→ Email: admin@example.com
→ Password: strong_password
```

### **Step 6: Test Application (2 min)**
```bash
python terrasim.py
```

**Login:**
```
Email: admin@example.com
Password: strong_password
```

---

## File Reference

### **User-Facing**
```
terrasim.py              ← Users run this
USER_README.md           ← User quick start
requirements.txt         ← Dependencies
```

### **Admin-Only**
```
admin_console.py         ← Admin setup menu
email_setup.py           ← Email configuration
database_setup.py        ← Cloud database setup
```

### **Documentation**
```
CLOUD_SETUP_QUICK_START.md      ← START HERE for cloud setup
CLOUD_DATABASE_MIGRATION.md     ← Architecture details
SUPABASE_SETUP_GUIDE.md         ← Detailed Supabase setup
DEPLOYMENT_COMPLETE.md          ← Deployment overview
USER_README.md                  ← User guide
README.md                       ← Project info
```

### **Auto-Created**
```
.env                           ← Cloud database config
backend/.email_config          ← Email service config
backend/.cloud_config          ← Cloud provider info
terrasim.db                    ← Local database (if using SQLite)
terrasim.log                   ← Application logs
```

---

## Email Configuration

### **Step 1: Run Email Setup**
```bash
python admin_console.py
→ 1: Configure Email Service
```

### **Step 2: Choose Provider**

**Gmail (Easiest for Testing)**
1. Go to: https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Create App Password: https://myaccount.google.com/apppasswords
4. Copy 16-character password
5. Enter in wizard

**SendGrid (Free 100/day)**
1. Go to: https://sendgrid.com/free
2. Create account
3. Create API Key
4. Enter API key in wizard

**Mailgun (Free 100/day)**
1. Go to: https://mailgun.com
2. Create account
3. Get SMTP credentials
4. Enter in wizard

**Outlook (Easiest)**
1. Use your Outlook password
2. Supported by wizard

---

## Cloud Database Providers

### **Recommended: Supabase**
- **Storage:** 500 MB free (unlimited rows)
- **Setup:** 5 minutes
- **Cost:** Free tier (then $25+/month)
- **URL:** https://supabase.com

### **Alternative: Railway**
- **Credits:** $5/month (usually sufficient)
- **Setup:** 5 minutes
- **Cost:** Pay as you go
- **URL:** https://railway.app

### **Alternative: Render**
- **Storage:** Limited free tier
- **Setup:** 10 minutes
- **Cost:** Free tier + paid
- **URL:** https://render.com

---

## Troubleshooting

### **"Email not configured"**
```
python admin_console.py → 1 → Configure Email Service
```

### **"Database error"**
```
python admin_console.py → 2 → Initialize Database
```

### **"Can't connect to cloud database"**
```
1. Check internet connection
2. Verify connection string is correct
3. Check Supabase project is running
4. Try again
```

### **"Need to reset everything"**
```
python admin_console.py → 3 → Reset Database
WARNING: This deletes all data!
```

### **"Need to backup data"**
```
python admin_console.py → 7 → Create Database Backup
```

---

## Multi-Device Testing

### **Test Setup:**

**Device A (Windows):**
```bash
python terrasim.py
→ Sign up: testuser@gmail.com
→ Verify email
→ Create project "Test"
```

**Device B (Mac/Linux):**
```bash
python terrasim.py
→ Login: testuser@gmail.com
→ See "Test" project (synced!)
```

**Device C (Phone - if supported):**
```
Same login: testuser@gmail.com
See all data
```

All devices see the same data instantly! ✅

---

## Monitoring

### **Check Configuration**
```bash
python admin_console.py → 5
```

Shows:
- Email service status
- Database type and size
- User count
- Connection details

### **View Logs**
```bash
tail terrasim.log
```

### **Check Supabase Dashboard**
```
https://supabase.com → Your Project
View:
- Storage usage
- User count
- Database activity
- Backups
```

---

## Deployment Checklist

Before distributing to users:

**Setup:**
- [ ] Create cloud account (Supabase)
- [ ] Run `python admin_console.py`
- [ ] Option 6: Configure cloud database
- [ ] Option 2: Initialize database
- [ ] Option 1: Configure email service
- [ ] Option 4: Create admin user

**Testing:**
- [ ] Test on Windows
- [ ] Test on Mac
- [ ] Test on Linux
- [ ] Test multi-device sync
- [ ] Test email verification
- [ ] Test password reset (if implemented)

**Distribution:**
- [ ] Package with `terrasim.py`
- [ ] Include `requirements.txt`
- [ ] Include `USER_README.md`
- [ ] Include all backend/frontend code
- [ ] Do NOT include `admin_console.py` (admin-only)
- [ ] Do NOT include setup scripts

**Documentation:**
- [ ] Verify `USER_README.md` is clear
- [ ] Create admin guide for your team
- [ ] Document how to contact support
- [ ] Create emergency procedures

---

## Support

### **For Users:**
- See `USER_README.md`
- Check email verification steps
- Try restarting application

### **For Admins:**
- See `CLOUD_SETUP_QUICK_START.md`
- Check `SUPABASE_SETUP_GUIDE.md`
- See this file (SETUP.md)
- Check `backend/.cloud_config`

---

## Next Steps

1. **Read**: `CLOUD_SETUP_QUICK_START.md`
2. **Follow**: 7-step setup process
3. **Test**: Multi-device login
4. **Distribute**: To users
5. **Monitor**: Via admin console

---

**Ready to deploy?** Start with `CLOUD_SETUP_QUICK_START.md` ➜
