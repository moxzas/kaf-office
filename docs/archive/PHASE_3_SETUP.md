# Phase 3 Setup: Audit Trail + Email Notifications

**Status:** ⏳ Ready to deploy
**Date:** 2025-11-06

---

## Manual Setup Required

### 1. Create Audit Log Table in Airtable

Follow instructions in `docs/AUDIT_LOG_TABLE.md`:

1. Go to KAF Airtable base
2. Add new table: **"Audit Log"**
3. Add these fields:
   - Timestamp (Created time) - automatic
   - Action (Single select: Created, Updated)
   - Parent Record (Link to Parents)
   - Parent Email (Email)
   - Parent Name (Single line text)
   - Before State (Long text)
   - After State (Long text)
   - Delta Summary (Long text)
   - Student Count (Number)
   - IP Address (Single line text)
   - User Agent (Long text)
   - Processing Status (Single select: Pending, Email Sent, Failed)
   - Email Sent At (Date & time)
   - Error Message (Long text)

4. Create view: **"Recent Changes"** filtered by last 7 days

### 2. Get Resend API Key

1. Go to: https://resend.com
2. Sign up / log in
3. Go to API Keys
4. Create new API key
5. Copy the key (starts with `re_`)

**Important:** You'll need to verify your sending domain (`sonzai.com`) in Resend:
- Go to Domains → Add Domain
- Add DNS records (SPF, DKIM, DMARC)
- Wait for verification

### 3. Add GitHub Secrets to ezeo_otg

Go to: https://github.com/YOUR_USERNAME/ezeo_otg/settings/secrets/actions

Add these secrets:

| Secret Name | Value | Where to Get It |
|-------------|-------|-----------------|
| **AIRTABLE_API_KEY** | `patYJhlgK2q6sAnyZ...` | Already have it (same as KAF-Office) |
| **AIRTABLE_BASE_ID** | `appNuMdxaiSYdgxJS` | Already have it (same as KAF-Office) |
| **RESEND_API_KEY** | `re_123abc...` | From Resend dashboard (step 2) |

### 4. Update Sophia's Email Address

Edit `/Users/anthonylee/Projects/ezeo_otg/packages/server/lib/handlers/kaf/audit_handler.dart`

Change line 123:
```dart
'to': ['sophia@kidsartfun.com.au'],  // TODO: Get Sophia's real email
```

To Sophia's actual email address.

---

## What Gets Deployed

### ezeo_otg Server Changes
- ✅ New handler: `audit_handler.dart`
- ✅ New route: `POST /api/kaf/audit`
- ✅ Environment variables added to deployment workflow

### KAF-Office Form Changes
- ✅ Calls audit endpoint on final submit
- ✅ Sends before/after state snapshots
- ✅ Shows "email sent" confirmation

---

## How It Works

### On New Enrollment

1. **Parent completes form** at `app.sonzai.com/kaf/enrollment.html`

2. **Form saves to Airtable** (progressive saving after each page)

3. **On final submit:**
   - Form calls `POST /api/kaf/audit` with:
     - Action: "Created"
     - Parent record ID
     - Complete enrollment data

4. **Server creates audit log:**
   - Writes record to Audit Log table
   - Stores complete "after state" as JSON

5. **Server sends 2 emails:**
   - **Email to Sophia:**
     - Subject: "New Enrollment: Sarah Johnson"
     - Shows complete enrollment details
     - Link to view/edit

   - **Email to Parent:**
     - Subject: "Welcome to Kids Art Fun!"
     - Enrollment summary
     - Edit link for future changes

6. **Server updates audit log:**
   - Processing Status → "Email Sent"
   - Email Sent At → timestamp

### On Enrollment Update

Same as above, but:
- Action: "Updated"
- Before State: Original data
- After State: New data
- Delta Summary: Shows what changed
- Email subjects say "updated" instead of "new"

---

## Email Templates

### Sophia's Notification Email

```
Subject: New Enrollment: Sarah Johnson
From: Kids Art Fun <enrollments@sonzai.com>
To: sophia@kidsartfun.com.au

KAF Enrollment Received

Parent: Sarah Johnson (sarah@example.com)

Changes:
• New enrollment created
• Parent: Sarah Johnson
• Students: Emma Johnson (1 student)

View Full Enrollment: [Link]

---
Submitted: 2025-11-06 3:45 PM
Record ID: recABC123
```

### Parent's Confirmation Email

```
Subject: Welcome to Kids Art Fun!
From: Kids Art Fun <enrollments@sonzai.com>
To: sarah@example.com

Thanks for enrolling with Kids Art Fun!

Hi Sarah,

We've received your enrollment and are excited to have your family join us!

Your Enrollment Details:
• Contact: sarah@example.com, 0444 444 444
• Address: 123 Main St, Chapel Hill 4069
• Students: Emma Johnson - Ironside State School

Need to make changes?

Use this link anytime to view or update your enrollment:
[View/Edit Enrollment Button]

---
Save this email! You'll need this link to make changes later.

Questions? Reply to this email or call us at XXX XXX XXX.

See you soon!
The Kids Art Fun Team
```

---

## Testing

### Test Audit Logging

1. Complete a new enrollment
2. Check console for: `✓ Audit log created and emails sent`
3. Check Airtable Audit Log table for new record
4. Check Sophia's email inbox
5. Check parent's email inbox

### Test Delta Calculation

1. Create enrollment with 1 student
2. Edit enrollment:
   - Change mobile number
   - Add 2nd student
3. Submit changes
4. Check Audit Log → Delta Summary should show:
   ```
   Enrollment updated
   • Mobile changed: 0444 444 444 → 0411 555 666
   • Student added: Noah Johnson
   • Total students: 2
   ```

### Test Error Handling

1. **Invalid Resend API key:**
   - Audit log created with Processing Status: "Failed"
   - Error Message populated
   - Form submission still succeeds

2. **Airtable unavailable:**
   - Form submission still succeeds
   - Error logged to console
   - User sees success message

---

## Deployment Steps

1. ✅ Create Audit Log table in Airtable (manual)
2. ✅ Get Resend API key (manual)
3. ✅ Add GitHub secrets to ezeo_otg (manual)
4. ✅ Update Sophia's email in audit_handler.dart (manual)
5. ⏳ Commit and push ezeo_otg changes
6. ⏳ Commit and push KAF-Office changes
7. ⏳ Test end-to-end
8. 🎉 Phase 3 complete!

---

## Monitoring

### Check Audit Logs

https://airtable.com/appNuMdxaiSYdgxJS/Audit%20Log

**Look for:**
- Processing Status = "Failed" → Investigate errors
- Email Sent At = empty → Email sending stuck
- Recent Changes view → Monitor activity

### Check Email Delivery

**Resend Dashboard:**
- https://resend.com/emails
- See delivery status, opens, clicks
- Check bounce rate

### Server Logs

```bash
ssh deploy@209.38.86.222
sudo journalctl -u ezeo-otg -f | grep -i kaf
```

Look for:
- `✓ Audit log created`
- `✓ Emails sent`
- `ERROR:` messages

---

## Troubleshooting

### Emails not sending

1. Check Resend API key is correct
2. Verify domain is verified in Resend
3. Check Resend dashboard for errors
4. Look at Audit Log → Error Message field

### Audit log not created

1. Check Airtable API key/base ID
2. Verify "Audit Log" table exists with correct fields
3. Check server logs for errors

### Parent doesn't receive email

1. Check spam folder
2. Check Resend dashboard - was it sent?
3. Verify parent email is correct in Airtable
4. Check domain reputation in Resend

---

## Cost Estimate

**Resend Pricing:**
- Free tier: 100 emails/day, 3,000/month
- Pro: $20/month for 50,000 emails

**For KAF:**
- ~10 enrollments/week = 40/month
- 2 emails per enrollment = 80 emails/month
- **Free tier is plenty!**

---

## Next Steps After Phase 3

**Future Enhancements:**
1. PDF attachments (enrollment summary)
2. SMS notifications (Twilio)
3. Automated reminders (class starting soon)
4. Payment links (Stripe integration)
5. Class scheduling in enrollment form

---

**Ready to deploy Phase 3!** 🚀
