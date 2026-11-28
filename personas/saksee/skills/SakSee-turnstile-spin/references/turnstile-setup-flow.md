# Cloudflare Turnstile Spin — End-to-End Setup Flow & Integration Reference

This reference contains the full multi-step setup wizard, existing widget retrieval flows, backend integration code, and edge-case handling for Turnstile setup.

---

## 1. Multi-Step Setup Wizard

1. **Brief acknowledge**: Confirm user intent: "I'll run Turnstile setup end to end: check auth, scan codebase, create widget, embed frontend, wire server-side siteverify, validate."
2. **CLI check**: Uses `curl` against `api.cloudflare.com` and approved `WRANGLER_BIN` outside project root.
3. **Auth + scope probe**: Run `scripts/auth-probe.sh`. Handle `ok`, `missing_token`, `missing_scope`, `network_failure`, `upstream_failure`, `multiple_accounts`, or `account_mismatch`.
4. **Account selection**: Select single or chosen account ID.
5. **Domain selection**: Localhost (`localhost`, `127.0.0.1`) plus production domain from `package.json`, `wrangler.toml`, or `README.md`.
6. **Codebase scan**: Detect frontend framework, backend handler location, and any existing CAPTCHA (reCAPTCHA / hCaptcha).
7. **Insertion plan**: Assign stable actions (`signup`, `login`, `contact`) and map to handlers.
8. **Widget creation**:
   ```bash
   WRANGLER_WRITE_LOGS=false WRANGLER_LOG=log WRANGLER_LOG_SANITIZE=true \
     "$WRANGLER_BIN" turnstile widget create "<name>" \
     --domain <d1> --domain <d2> ... --mode managed --json
   ```
9. **Wire the integration**: Embed frontend widget and insert canonical siteverify in backend handler.
10. **Validation**: Run validation script with secret piped through stdin (`validate.sh`).
11. **Persist skill**: Optionally save to `.claude/skills/turnstile-spin/SKILL.md`.
12. **Final report**: Print structured deployment summary.

---

## 2. Canonical Backend Siteverify Implementation

```javascript
const expectedAction = 'signup';
const expectedHostnames = new Set(
  (process.env.TURNSTILE_HOSTNAMES ?? '')
    .split(',')
    .map((hostname) => hostname.trim())
    .filter(Boolean),
);

if (typeof token !== 'string' || token.length === 0 || token.length > 2048 || expectedHostnames.size === 0) {
  return res.status(403).send('forbidden');
}

let result;
try {
  const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    signal: AbortSignal.timeout(10_000),
    body: new URLSearchParams({
      secret: process.env.TURNSTILE_SECRET,
      response: token,         // cf-turnstile-response from the request
      remoteip: clientIp,      // X-Forwarded-For / req.ip
    }),
  });
  if (!r.ok) throw new Error(`siteverify ${r.status}`);
  result = await r.json();
} catch (err) {
  return res.status(403).send('forbidden');
}
if (
  !result.success ||
  result.action !== expectedAction ||
  !expectedHostnames.has(result.hostname)
) {
  return res.status(403).send('forbidden');
}
// Existing handler logic continues here
```

---

## 3. Existing Widget Retrieval & Guarded Flow

When a user supplies an existing sitekey:
1. Skip widget creation; retain provided sitekey.
2. Require Wrangler $\ge 4.109.0$ approved outside project root.
3. Validate widget metadata via JSON query without exposing secrets.
4. Retrieve, validate dummy token response (`invalid-input-response` confirms valid secret), and write secret to destination store (`.env` or `wrangler secret put`).
5. Exercise live verification with replay rejection.

---

## 4. Frontend Embedding Pattern

```html
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>

<form action="/signup" method="POST">
  <div class="cf-turnstile" data-sitekey="<SITEKEY>" data-action="signup"></div>
  <button type="submit">Sign up</button>
</form>
```

---

## 5. CAPTCHA Migration Cheat Sheet

- Replace script with `https://challenges.cloudflare.com/turnstile/v0/api.js`.
- Replace `class="g-recaptcha"` / `class="h-captcha"` with `class="cf-turnstile"`.
- Replace token field name: `g-recaptcha-response` $\to$ `cf-turnstile-response`.
- Backend siteverify URL: `https://challenges.cloudflare.com/turnstile/v0/siteverify`.
- Turnstile returns boolean `success` (no score threshold).
