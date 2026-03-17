# KAF Office — Claude Code Instructions

## On Boot

This project is tracked in **ProductBrain** (`project_id=kaf-office`). At the start of each conversation:

1. Read ProductBrain docs: `/Users/anthonylee/Projects/productbrain/CLAUDE.md` and `/Users/anthonylee/Projects/productbrain/docs/LLM_GUIDE.md`
2. Fetch the current brain state:
```bash
SBK=$(grep SUPABASE_SERVICE_ROLE_KEY /Users/anthonylee/Projects/productbrain/.env.local | head -1 | cut -d= -f2)
curl -s "https://locdqsxdpnpfeoqqtbpa.supabase.co/rest/v1/nodes?project_id=eq.kaf-office&select=id,type,parent_id,data&order=id" \
  -H "apikey: $SBK" -H "Authorization: Bearer $SBK"
```
3. After completing significant work, update the brain (create/update job nodes, update approach notes).

## Conventions

- **AU English** throughout — enrolment (not enrollment), organised (not organized), etc.
- **Env var namespacing** — KAF-specific Stripe vars use `KAF_STRIPE_*` prefix to avoid collision with Sonzai's Stripe credentials on the shared server.

## Deployment

- GitHub Actions deploys `src/*` to DigitalOcean droplet via Tailscale
- **DO NOT** use `appleboy/ssh-action` or `appleboy/scp-action` — Docker containers can't access host Tailscale network. Use `tailscale/github-action@v3` then raw `ssh`/`scp` commands.
- Server SSH only reachable via Tailscale IP `100.98.110.31` — public IP blocked
- Deploy does NOT delete old files — must SSH in manually to remove renamed/deleted files
- KAF static files: `deploy@100.98.110.31:/home/deploy/webremote/kaf/`
- Server (ezeo_otg): separate repo, separate deploy workflow, pulls `kaf_server` as git dependency — run `dart pub upgrade kaf_server` after pushing KAF-Office changes

## Airtable API

- View creation NOT supported via API (even Meta API). Must use UI.
- Token `patADMbcJI2cmB0Sg` has `data.records:read`, `data.records:write`, `schema.bases:read`, `schema.bases:write`
- Rate limit: 5 req/sec, use 0.25s delay between batch calls
- Batch limit: 10 records per POST/PATCH
- Base ID: `appNuMdxaiSYdgxJS`
