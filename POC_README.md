# POC - SurveyJS + Airtable Integration

## What This Is

A proof of concept showing SurveyJS forms submitting data directly to your live Airtable base.

**Form:** Simple parent registration form with 2 pages
**Target Table:** Parents table in Airtable (appNuMdxaiSYdgxJS)

## What It Does

The form collects:
- Parent name, email, phone, mobile
- Pickup authorization checkbox
- Interest categories (multi-select)
- Interest notes (text area)

On submit, it:
1. Formats the data for Airtable API
2. POSTs to the Parents table
3. Shows success/error message
4. Creates a new Parent record in your live Airtable

## Quick Start

### Option 1: Local Server (Recommended)

```bash
npm start
```

This will:
- Start a local server on http://localhost:8080
- Automatically open your browser to the form
- Allow you to test the form

### Option 2: Direct File Open

Simply open `src/index.html` in your browser.

**Note:** Some browsers may block API calls when opening files directly. Use the local server if you have issues.

## Testing the Form

1. **Run the form** (npm start or open src/index.html)
2. **Fill out the form** with test data
3. **Submit** and watch the console (F12 → Console)
4. **Check Airtable** - Go to your Parents table and see the new record

### Test Data Suggestion

```
Name: Test Parent
Email: test@example.com
Phone: 07 3xxx xxxx
Mobile: 04xx xxx xxx
Authorized: Yes (checked)
Interest Categories: Pottery, Holiday Programs
Interest Notes: Testing the POC form - please ignore
```

## What to Check in Airtable

After submitting, verify in your Airtable base:
- New record appears in Parents table
- All fields are populated correctly
- Interest Categories is an array
- Authorized for Pickup is a checkbox (true/false)

## Troubleshooting

### Form doesn't submit
- Check browser console (F12) for errors
- Verify Airtable API key is valid
- Check network tab to see the API request/response

### "Failed to submit" error
- Field names in the form must EXACTLY match Airtable field names
- Check that field types are compatible (text → text, boolean → checkbox, etc.)
- Verify the base ID is correct: `appNuMdxaiSYdgxJS`

### CORS errors
- Use `npm start` instead of opening the file directly
- Airtable API should allow CORS from localhost

## Form Structure (SurveyJS)

The form is defined in `src/index.html` as a JSON object:

```javascript
const surveyJson = {
    pages: [
        { name: "contactInfo", elements: [...] },
        { name: "authorization", elements: [...] }
    ]
}
```

### Form Elements Match Airtable Fields

| SurveyJS Field Name | Airtable Field | Type |
|---------------------|----------------|------|
| Name | Name | Single line text |
| Email | Email | Email |
| Phone | Phone | Phone number |
| Mobile | Mobile | Phone number |
| Authorized for Pickup | Authorized for Pickup | Checkbox |
| Interest Categories | Interest Categories | Multiple select |
| Interest Notes | Interest Notes | Long text |

## Next Steps After POC

Once you verify the POC works:

1. **Plan the real forms:**
   - Parent → Student → Enrollment flow
   - Class browsing/selection
   - Emergency contacts
   - Photo permissions

2. **Decide on approach:**
   - Single long form vs. multi-step wizard
   - Which fields are required vs. optional
   - Validation rules

3. **Clean up test data:**
   - Delete POC test records from Airtable
   - Start fresh with real enrollment workflow

4. **Add features:**
   - File uploads (student photos)
   - Dynamic class listing from Airtable
   - Form pre-fill for returning parents
   - Email confirmation

## Security Note

⚠️ **The API key is currently hardcoded in the HTML file.**

This is ONLY for POC testing. Before deploying:
- Move API key to a backend server
- Use environment variables
- Never expose API keys in client-side code
- Consider using Airtable's Web API with authentication

For now, this is fine for local testing.

## Files in This POC

```
src/
└── index.html          # Complete SurveyJS form + Airtable integration
```

Single file POC - everything is in one HTML file using CDN links.

---

**Ready to test?** Run `npm start` and fill out the form!
