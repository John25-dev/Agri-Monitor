# Agri-Business Multi-Branch ERP

## Security Implementation
1. **IP Masking:** Integrated via Cloudflare Tunnel. The server origin IP is never exposed.
2. **Server Obfuscation:** Apache `ServerTokens` configured to prevent version detection.
3. **Cashless Logic:** Transactions are validated via server-side hooks before stock is released.

## Deployment
1. Install requirements: `pip install -r requirements.txt`
2. Run Gunicorn: `gunicorn -w 4 app:app`
3. Connect Cloudflare Tunnel: `cloudflared tunnel run <tunnel-name>`
