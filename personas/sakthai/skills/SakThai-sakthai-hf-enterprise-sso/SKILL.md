---
name: SakThai-sakthai-hf-enterprise-sso
description: ">   Complete reference on Hugging Face Hub Enterprise Single Sign-On (SSO) —   SAML 2.0 and OIDC authentication for Team & Enterprise organizations.   Covers Basic SSO (org resource authentication), Managed SSO (full   IdP-controlled user lifecycle),"
---

# Hugging Face Hub Enterprise Single Sign-On (SSO)

## What It Is

Hugging Face offers **two SSO models** for Team & Enterprise plans that let
organizations control how members authenticate. Both support **SAML 2.0** and
**OpenID Connect (OIDC)** protocols with Identity Providers (IdPs): Okta,
Microsoft Entra ID (Azure AD), and Google Workspace.

## SSO Models at a Glance

| Feature | Basic SSO | Managed SSO |
|---------|-----------|-------------|
| Plan | Team & Enterprise | Enterprise Plus |
| Scope | Organization resources only | Entire Hugging Face platform |
| Replaces HF login? | No | Yes |
| User accounts | Users keep personal HF accounts | Org‑owned and managed |
| Personal content | Allowed in personal namespace | Only within org |
| Multi‑org membership | Yes | No (single org only) |
| User provisioning | Manual or SCIM (Enterprise) | Full SCIM lifecycle |
| Setup | Self‑service from org settings | Requires HF team |
| External collaborators | Yes | Yes |
| Protocols | SAML 2.0 + OIDC | SAML 2.0 + OIDC |
| Role mapping | Yes | Yes |
| Resource group mapping | Yes | Yes |

## Basic SSO

Adds an **access‑control layer** on top of the standard HF login. Members keep
their own HF account and use SSO only when accessing org resources.

**Use when:** your team needs org resource security but still wants individual
accounts and community participation.

**Setup:** Organization Settings > Authentication (self‑service).
Configure IdP metadata, share the SSO join link with members.

**SCIM (Enterprise):** automates inviting existing HF users — they must accept
the invitation.

## Managed SSO

**Replaces** the HF login entirely. The IdP is the sole authentication method
across the whole platform. Org controls the full user lifecycle.

**Use when:** enterprise requires centralized identity control, strict data
governance, and no content outside the org.

**Key traits:**
- Org‑owned accounts; no personal namespace content
- Full SCIM lifecycle (auto‑provision, update, deactivate)
- Setup requires coordination with HF team

## SCIM Provisioning

| Aspect | Basic SSO (Enterprise) | Managed SSO (Enterprise Plus) |
|--------|----------------------|------------------------------|
| What SCIM does | Automates invitations | Full account lifecycle |
| User acceptance | Required | Not required |
| Deactivation | Org admin removes | Auto‑syncs from IdP |

## Role Mapping

Map IdP group/role attributes (e.g. SAML `groups`, OIDC `roles` claims) to HF
org roles:

- **Admin** — full org management
- **Write** — create & modify repos
- **Contributor** — contribute to repos
- **Read** — view‑only
- **No access** — explicitly denied

Configure in Organization Settings > Authentication > Role Mapping.

## Resource Group Mapping

Combine SSO with **Resource Groups** for repo‑level access control:

1. Create Resource Groups in org settings to group repos
2. Map IdP groups to resource groups in SSO config
3. Members auto‑inherit correct permissions on SSO login

## IdP Quick‑Start

### Okta
1. Create SAML 2.0 or OIDC app integration
2. Set ACS URL / Redirect URI from HF org settings
3. Copy IdP metadata → paste into HF org settings
4. Assign users/groups; configure attribute mappings

### Microsoft Entra ID (Azure AD)
1. Create Enterprise Application (gallery or custom SAML/OIDC)
2. Configure SSO URL + identifier from HF org settings
3. Upload signing certificate to HF
4. Assign users/groups; set up SCIM provisioning endpoint

### Google Workspace
1. Set up SAML app for Hugging Face in Admin Console
2. Use ACS URL + Entity ID from HF org settings
3. Map email / name attributes; assign users/OU groups
4. For SCIM: configure Cloud Directory Sync or custom connector

## Verification Checklist

- [ ] Users authenticate via IdP (org access for Basic; full login for Managed)
- [ ] Role mapping assigns correct org permissions
- [ ] Resource group restrictions apply as expected
- [ ] SCIM provisions/invites new users automatically
- [ ] Deactivation in IdP propagates to HF (Managed)
- [ ] External collaborators can still access shared repos
- [ ] SSO session timeout matches your security policy

## Limitations

- **Basic SSO** — users maintain two sessions (personal + org SSO)
- **Managed SSO** — users cannot create personal repos outside the org
- **SCIM** — Enterprise plan (Basic SSO) or Enterprise Plus (Managed)
- **Managed SSO setup** — requires HF team coordination, not instant
- **IdP lockout** — misconfigured IdP can lock all users; test with a small
  group first
- **Zero‑Cost note:** SSO requires a paid Team/Enterprise plan — no free tier

## Related HF Enterprise Features

- [Resource Groups](https://huggingface.co/docs/hub/en/enterprise-resource-groups)
  — fine‑grained repo‑level access control
- [Audit Logs](https://huggingface.co/docs/hub/en/enterprise-audit-logs)
  — track auth events and resource access
- [Network Security](https://huggingface.co/docs/hub/en/enterprise-network-security)
  — IP allowlisting and VPC integration
- [Gating Group Collections](https://huggingface.co/docs/hub/en/enterprise-gating-groups)
  — manage gated model/dataset access groups
- [Service Accounts](https://huggingface.co/docs/hub/en/service-accounts)
  — machine‑to‑machine auth
- [Token Presets](https://huggingface.co/settings/tokens)
  — fine‑grained access tokens with permission bundles

## References

- [HF Hub SSO Docs](https://huggingface.co/docs/hub/en/enterprise-sso)
- [HF Team & Enterprise Plans](https://huggingface.co/docs/hub/en/enterprise)
- [OAuth / Sign in with HF](https://huggingface.co/docs/hub/en/oauth)
