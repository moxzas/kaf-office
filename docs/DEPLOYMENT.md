# KAF Enrollment Form - Deployment Guide

## Overview

The KAF enrollment form is a static HTML application that deploys to your existing Shelf server at `app.sonzai.com`.

**Deployment Target:**
- Server: 209.38.86.222 (Sydney DigitalOcean droplet)
- Path: `/home/deploy/webremote/kaf/`
- URL: `https://app.sonzai.com/kaf/enrollment.html`

---

## Automatic Deployment (Recommended)

### Setup (One-Time)

1. **Add GitHub Secrets** to this repository:
   - `SERVER_HOST`: `209.38.86.222`
   - `SSH_PRIVATE_KEY`: Your SSH private key (same as ezeo_otg project)

2. **Enable GitHub Actions**:
   - Go to repository Settings → Actions → General
   - Enable "Allow all actions and reusable workflows"

### How It Works

- **Trigger**: Push to `main` branch (when files in `src/` change)
- **Process**:
  1. Copies all files from `src/` to `/home/deploy/webremote/kaf/`
  2. Sets correct permissions (755)
  3. Files are immediately accessible via Shelf server

- **Manual Trigger**:
  - Go to Actions tab → "Deploy KAF Enrollment Form" → Run workflow

---

## Manual Deployment

If you need to deploy without GitHub Actions:

```bash
# From your local machine
cd /Users/anthonylee/Projects/KAF-Office

# Deploy files via SCP
scp src/*.html deploy@209.38.86.222:/home/deploy/webremote/kaf/

# Set permissions
ssh deploy@209.38.86.222 'chmod -R 755 /home/deploy/webremote/kaf/'
```

---

## Shelf Server Configuration

Your Shelf server (from ezeo_otg project) needs to serve static files from `/home/deploy/webremote/`.

**Expected routes:**
- `GET /kaf/enrollment.html` → `/home/deploy/webremote/kaf/enrollment.html`
- `GET /kaf/index.html` → `/home/deploy/webremote/kaf/index.html`

**Check if static file serving is enabled** in your Shelf server (`packages/server/bin/main.dart`):

```dart
import 'package:shelf_static/shelf_static.dart';

final staticHandler = createStaticHandler(
  '/home/deploy/webremote',
  defaultDocument: 'index.html',
);

final handler = Cascade()
  .add(staticHandler)
  .add(apiHandler)
  .handler;
```

If not configured, you'll need to add static file serving to your Shelf server.

---

## Verification

After deployment:

1. **Check files exist**:
   ```bash
   ssh deploy@209.38.86.222 'ls -la /home/deploy/webremote/kaf/'
   ```

2. **Test URL**:
   ```bash
   curl https://app.sonzai.com/kaf/enrollment.html
   ```

3. **Open in browser**:
   - https://app.sonzai.com/kaf/enrollment.html

---

## Custom Domain (Optional)

If you want `kaf.sonzai.com` instead of `app.sonzai.com/kaf/`:

1. **Add DNS A record**:
   - Host: `kaf.sonzai.com`
   - Points to: `209.38.86.222`

2. **Configure Shelf server** to handle `kaf.sonzai.com` virtual host

3. **Update Airtable API URLs** in enrollment.html if needed

---

## Troubleshooting

### Files not accessible after deployment

**Check Shelf server is serving static files:**
```bash
ssh deploy@209.38.86.222
curl localhost:8080/kaf/enrollment.html
```

If this returns HTML, the server is configured correctly. If not, check Shelf static handler configuration.

### Permission denied errors

```bash
ssh deploy@209.38.86.222
sudo chown -R deploy:deploy /home/deploy/webremote/kaf/
chmod -R 755 /home/deploy/webremote/kaf/
```

### 404 Not Found

1. Check files exist: `ls /home/deploy/webremote/kaf/`
2. Check Shelf server routes in ezeo_otg project
3. Check nginx/reverse proxy configuration (if applicable)

---

## Security Notes

- Airtable API key is currently **exposed in client-side code** (enrollment.html:77)
- For production, move API calls to server-side endpoints
- See `docs/ENROLLMENT_FORM_DESIGN.md` for planned Shelf API endpoints

---

## Next Steps

1. Set up GitHub secrets (SERVER_HOST, SSH_PRIVATE_KEY)
2. Push to `main` branch to trigger first deployment
3. Verify files are accessible at `app.sonzai.com/kaf/enrollment.html`
4. Test enrollment form end-to-end
5. (Later) Build Shelf server endpoints to proxy Airtable API calls
