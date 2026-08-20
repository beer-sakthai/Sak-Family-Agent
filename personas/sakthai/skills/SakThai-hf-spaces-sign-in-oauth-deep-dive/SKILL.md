---
name: SakThai-hf-spaces-sign-in-oauth-deep-dive
description: '>-   Complete deep-dive on the Hugging Face Spaces Sign-In with HF button (OAuth/OpenID
  Connect).   Covers enabling OAuth in Space metadata, environment variables, scopes
  system, authorization   and token endpoints, Gradio built-in integration, huggi'
---

# Hugging Face Spaces Sign-In with HF OAuth — Deep Dive

## Overview

**Sign-In with HF** is a built-in OAuth 2.0 / OpenID Connect flow that lets Space
developers add authentication with minimal configuration. By setting `hf_oauth: true`
in your Space's YAML metadata, the Hub automatically creates an OAuth app and
injects the credentials as environment variables.

**Key facts:**
- Free feature — no PRO/Team plan required
- Works with all Space SDKs (Gradio, Streamlit, Static HTML, Docker)
- Uses the Authorization Code grant flow
- OpenID Connect compliance: `openid` + `profile` scopes always included
- Supports org-restricted access via `hf_oauth_authorized_org`
- Token durations configurable (8h default, up to 30 days)

## Enabling OAuth in a Space

Add these fields to your Space's `README.md` YAML frontmatter:

```yaml
hf_oauth: true
# optional: token lifetime in minutes (default 480, max 43200)
hf_oauth_expiration_minutes: 480
# optional: restrict which org members can authenticate
hf_oauth_authorized_org: ORG_NAME
# or multiple:
hf_oauth_authorized_org:
  - ORG_NAME1
  - ORG_NAME2
# optional: custom scopes beyond openid+profile
hf_oauth_scopes:
  - read-repos
  - gated-repos
  - write-repos
  - manage-repos
  - inference-api
```

### Environment Variables Injected

| Variable              | Description                                      |
|-----------------------|--------------------------------------------------|
| `OAUTH_CLIENT_ID`     | Public client ID of the auto-created OAuth app   |
| `OAUTH_CLIENT_SECRET` | Secret for the OAuth app                         |
| `OAUTH_SCOPES`        | Scopes accessible by the OAuth app               |
| `OPENID_PROVIDER_URL` | OpenID provider base URL                         |

OpenID metadata at `{OPENID_PROVIDER_URL}/.well-known/openid-configuration`.

## OAuth Scopes

### Always Included

| Scope     | Purpose                                        |
|-----------|------------------------------------------------|
| `openid`  | Get ID token alongside access token            |
| `profile` | Get user profile (username, avatar, etc.)      |

### Optional (set via `hf_oauth_scopes`)

| Scope               | Permission |
|---------------------|------------|
| `email`             | Read user's email address |
| `read-billing`      | Check if user has payment method |
| `read-repos`        | Read access to user's personal repos |
| `gated-repos`       | Read content of public gated repos user has access to |
| `contribute-repos`  | Create repos + access those created by this app only |
| `write-repos`       | Write/read access to user's personal repos |
| `manage-repos`      | Full access including creation/deletion |
| `read-collections`  | Read user's personal collections |
| `write-collections` | Write/read + create/delete collections |
| `inference-api`     | Make inference requests on behalf of the user |
| `jobs`              | Run Jobs on behalf of the user |
| `webhooks`          | Manage webhooks |
| `write-discussions` | Open discussions and PRs, interact with comments/reactions |

## Authorization Flow

### Step 1: Redirect to authorize endpoint

```
GET https://huggingface.co/oauth/authorize
  ?redirect_uri={REDIRECT_URI}
  &scope=openid%20profile
  &client_id={CLIENT_ID}
  &state={STATE}
```

- `STATE`: A random string for CSRF protection. Verify on callback.
- `redirect_uri`: Any URL targeting your Space (use `SPACE_HOST` env var).
  Example: `https://{SPACE_HOST}/login/callback`
- **Important**: Use `target=_blank` to open auth in a new tab (unless running outside iframe) to avoid cookie issues.

### Step 2: Handle callback

User authorizes and is redirected back with: `code`, `state`, and optional `orgIds`.

### Step 3: Exchange code for tokens

```
POST https://huggingface.co/oauth/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}

client_id={CLIENT_ID}
code={CODE}
grant_type=authorization_code
redirect_uri={REDIRECT_URI}
```

Returns: `access_token`, `id_token` (JWT), `token_type`, `expires_in`.

### Step 4: Use the tokens

- **Access token**: Call HF Hub API on behalf of the user
- **ID token**: Read user claims (sub, name, avatar URL)

## Gradio Integration

Gradio has **built-in** support — no manual OAuth handling needed.

### Using `gr.LoginButton`

```python
import gradio as gr

with gr.Blocks() as demo:
    gr.LoginButton()
    user = gr.Textbox(label="Logged in as")

    def greet(request: gr.Request):
        if request.username:
            return f"Hello {request.username}"
        return "Not logged in"

    demo.load(greet, None, user)
demo.launch()
```

### Accessing user info from `gr.Request`

- `request.username`
- `request.oauth_userinfo` — full user info dict from the OAuth provider

### Environment-aware behavior

- Locally: Gradio auto-detects no OAuth env vars and skips auth
- In production (on HF Spaces with `hf_oauth: true`): login flow activates

```python
import gradio as gr

def check_auth(request: gr.Request):
    if request.username:
        return f"Authenticated as: {request.username}"
    return "Not authenticated"

with gr.Blocks() as demo:
    status = gr.Textbox(label="Auth Status")
    demo.load(check_auth, None, status)
    gr.LoginButton()
```

## huggingface.js Integration

For Node.js / frontend Spaces (Static, Svelte, Vanilla JS):

```javascript
import { oauthLoginUrl, oauthHandleRedirectIfPresent } from "@huggingface/hub";

const oauthResult = await oauthHandleRedirectIfPresent();

if (!oauthResult) {
  window.location.href = await oauthLoginUrl();
}

// Authenticated!
console.log(oauthResult.accessToken, oauthResult.userInfo);
```

Works perfectly in Static HTML Spaces — full client-side flow.

## Organization Access

### Restricting auth to org members

```yaml
hf_oauth: true
hf_oauth_authorized_org: my-org
```

Non-members see an error instead of the consent screen.

### Requesting org resources

```text
GET https://huggingface.co/oauth/authorize?...
  &orgIds=ORG_ID
```

Get `ORG_ID` from `organizations.sub` in userinfo response.

## Token Configuration

| Setting                      | Default     | Max          | Description                          |
|------------------------------|-------------|--------------|--------------------------------------|
| `hf_oauth_expiration_minutes` | 480 (8h)   | 43200 (30d)  | Access token expiration              |

## Redirect URL Rules

- Any URL targeting your Space is valid
- Use `SPACE_HOST` env variable for dynamic construction
- Example: `https://{SPACE_HOST}/auth/callback`
- Must match exactly in the authorize request

## Security Considerations

1. **CSRF Protection**: Always generate and verify the `state` parameter
2. **Client Secret**: `OAUTH_CLIENT_SECRET` is injected as env var — never expose client-side
3. **Token Storage**: Server-rendered Spaces (Gradio, Streamlit) should store tokens server-side only
4. **HTTPS Only**: All OAuth endpoints enforce HTTPS
5. **Scope Minimization**: Request only the scopes you need
6. **Token Expiry**: Re-authorize after expiry; no refresh tokens provided

## Complete Example: Gradio Space

```yaml
# README.md
---
title: OAuth Demo
emoji: 🔐
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.x
python_version: 3.11
app_file: app.py
hf_oauth: true
hf_oauth_scopes:
  - inference-api
---
```

```python
# app.py
import gradio as gr
from huggingface_hub import InferenceClient

def greet(request: gr.Request):
    if not request.username:
        return "Please sign in with HF"
    token = request.oauth_userinfo.get("token")
    if token:
        client = InferenceClient(token=token)
        result = client.text_generation(
            "Hello!",
            model="HuggingFaceTB/SmolLM2-1.7B-Instruct"
        )
        return f"Hello {request.username}! AI: {result}"
    return f"Hello {request.username}!"

with gr.Blocks(title="OAuth Demo") as demo:
    gr.Markdown("## Sign-In with HF Demo")
    gr.LoginButton()
    output = gr.Textbox(label="Result")
    demo.load(greet, None, output)

demo.launch()
```

## Complete Example: Static HTML Space

```html
<!DOCTYPE html>
<html>
<head><title>OAuth Static Space</title></head>
<body>
  <div id="app">
    <h1>Sign-In with HF</h1>
    <button id="login-btn" onclick="login()">Sign in with HF</button>
    <pre id="userinfo"></pre>
  </div>
  <script type="module">
    import { oauthLoginUrl, oauthHandleRedirectIfPresent }
      from "https://cdn.jsdelivr.net/npm/@huggingface/hub/+esm";
    async function login() {
      window.location.href = await oauthLoginUrl();
    }
    window.addEventListener("load", async () => {
      const result = await oauthHandleRedirectIfPresent();
      if (result) {
        document.getElementById("userinfo").textContent =
          JSON.stringify(result.userInfo, null, 2);
        document.getElementById("login-btn").style.display = "none";
      }
    });
  </script>
</body>
</html>
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "App not authorized" | Missing `hf_oauth: true` | Add flag and push |
| Callback not received | Redirect URI mismatch | Ensure redirect_uri points to your Space |
| "Invalid state" | CSRF state mismatch | Verify state parameter on callback |
| 403 on token exchange | Wrong client secret | Check OAUTH_CLIENT_SECRET env var |
| Cookie issues in iframe | Third-party cookies blocked | Use `target=_blank` for auth in new tab |
| Users can't see org repos | Org access not requested | Add `orgIds` to auth URL |

## References

- [Official Docs: Sign-In with HF](https://huggingface.co/docs/hub/en/spaces-oauth)
- [Gradio OAuth Integration](https://huggingface.co/docs/hub/en/spaces-oauth-gradio)
- [huggingface.js OAuth](https://huggingface.co/docs/hub/en/spaces-oauth-huggingfacejs)
- [General HF OAuth](https://huggingface.co/docs/hub/en/oauth)
- [Spaces Configuration Reference](https://huggingface.co/docs/hub/en/spaces-configuration-reference)
- [@huggingface/hub on npm](https://www.npmjs.com/package/@huggingface/hub)
- [Example: Gradio OAuth Test App](https://huggingface.co/spaces/julien-c/gradio-oauth-test)
- [Example: HuggingChat (NodeJS/SvelteKit)](https://huggingface.co/spaces/huggingchat/chat-ui)
