# 📧 Email Provider Setup Guide - QUICK START

## ✅ COMPLETE! All 4 Providers Supported:

- **SendGrid** (100/day free - Enterprise trusted)
- **Resend** (100/day free - Modern, simple)
- **Brevo** (300/day free - Best free tier!)
- **Mailgun** (5000 emails for 3 months)

---

## 🚀 QUICK SETUP (5 minutes):

### Step 1: Run SQL Migration (Supabase)

```sql
-- Copy and run: backend/migrations/010_email_provider_settings.sql
```

### Step 2: Choose Your Provider & Get API Key

#### Option A: SendGrid (Recommended for Render)
1. Sign up: https://signup.sendgrid.com/
2. Settings → API Keys → Create API Key
3. Name: `Farm Management`
4. Permissions: **Mail Send** or Full Access
5. Copy key (starts with `SG.`)

#### Option B: Brevo (Best Free Tier - 300/day!)
1. Sign up: https://app.brevo.com/
2. SMTP & API → API Keys → Generate new key
3. Copy key

#### Option C: Resend (Modern & Simple)
1. Sign up: https://resend.com/
2. API Keys → Create API Key
3. Copy key (starts with `re_`)

#### Option D: Mailgun
1. Sign up: https://www.mailgun.com/
2. Settings → API Keys → Copy Private API key
3. Also note your domain (e.g., `mg.yourdomain.com`)

---

### Step 3: Configure in Supabase (Choose ONE provider)

#### For SendGrid:
```sql
UPDATE system_settings SET setting_value = '"sendgrid"' WHERE setting_key = 'email.provider';
UPDATE system_settings SET setting_value = '"SG.your-api-key-here"' WHERE setting_key = 'email.sendgrid_api_key';
UPDATE system_settings SET setting_value = '"no_reply@sustenance.co.in"' WHERE setting_key = 'email.from_email';
UPDATE system_settings SET setting_value = '"Sustenance"' WHERE setting_key = 'email.from_name';
UPDATE system_settings SET setting_value = 'true' WHERE setting_key = 'email.smtp_enabled';
```

#### For Brevo:
```sql
UPDATE system_settings SET setting_value = '"brevo"' WHERE setting_key = 'email.provider';
UPDATE system_settings SET setting_value = '"your-brevo-api-key"' WHERE setting_key = 'email.brevo_api_key';
UPDATE system_settings SET setting_value = '"no_reply@sustenance.co.in"' WHERE setting_key = 'email.from_email';
UPDATE system_settings SET setting_value = '"Sustenance"' WHERE setting_key = 'email.from_name';
UPDATE system_settings SET setting_value = 'true' WHERE setting_key = 'email.smtp_enabled';
```

#### For Resend:
```sql
UPDATE system_settings SET setting_value = '"resend"' WHERE setting_key = 'email.provider';
UPDATE system_settings SET setting_value = '"re_your-api-key"' WHERE setting_key = 'email.resend_api_key';
UPDATE system_settings SET setting_value = '"no_reply@sustenance.co.in"' WHERE setting_key = 'email.from_email';
UPDATE system_settings SET setting_value = '"Sustenance"' WHERE setting_key = 'email.from_name';
UPDATE system_settings SET setting_value = 'true' WHERE setting_key = 'email.smtp_enabled';
```

#### For Mailgun:
```sql
UPDATE system_settings SET setting_value = '"mailgun"' WHERE setting_key = 'email.provider';
UPDATE system_settings SET setting_value = '"your-mailgun-api-key"' WHERE setting_key = 'email.mailgun_api_key';
UPDATE system_settings SET setting_value = '"mg.yourdomain.com"' WHERE setting_key = 'email.mailgun_domain';
UPDATE system_settings SET setting_value = '"no_reply@sustenance.co.in"' WHERE setting_key = 'email.from_email';
UPDATE system_settings SET setting_value = '"Sustenance"' WHERE setting_key = 'email.from_name';
UPDATE system_settings SET setting_value = 'true' WHERE setting_key = 'email.smtp_enabled';
```

---

### Step 4: Redeploy Backend
- Commit: `9a83fd9`
- Redeploy on Render

---

### Step 5: Test!
1. Go to: `/communication/smtp`
2. Click "Test Email"
3. Enter your email
4. Click Send
5. Check inbox! ✅

---

## 📊 Provider Comparison:

| Provider | Free Tier | Forever? | Best For |
|----------|-----------|----------|----------|
| **Brevo** | 300/day | ✅ Yes | Best free tier |
| **SendGrid** | 100/day | ✅ Yes | Enterprise trusted |
| **Resend** | 100/day | ✅ Yes | Modern, simple |
| **Mailgun** | 5000 (3mo) | ❌ No | Pay-as-you-go after |

---

## 🎯 Recommendation:

**For 100 emails/day**: Use **SendGrid** or **Brevo**

**Quick Setup**:
1. Run SQL migration
2. Get API key from provider
3. Update settings in Supabase
4. Redeploy
5. Test!

**Done!** 🎉

---

## 🔄 Switching Providers:

Just change these two settings:
```sql
UPDATE system_settings SET setting_value = '"brevo"' WHERE setting_key = 'email.provider';
UPDATE system_settings SET setting_value = '"your-new-api-key"' WHERE setting_key = 'email.brevo_api_key';
```

No code changes needed! ✅
