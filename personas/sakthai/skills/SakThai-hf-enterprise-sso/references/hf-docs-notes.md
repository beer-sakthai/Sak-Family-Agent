# HF Enterprise SSO — Research Source Notes

Extracted from https://huggingface.co/docs/hub/en/enterprise-sso (accessed 2026-07-26).

## Two Models

### Basic SSO
- Part of Team & Enterprise plans
- Adds access-control layer on top of standard HF login
- Does NOT replace HF login — members keep existing credentials
- Prompted to complete SSO only when accessing org resources
- Self-service from organization settings
- SCIM on Enterprise: automates invitation of existing HF users (users must accept)

### Managed SSO
- Enterprise Plus plan
- Replaces HF login entirely — IdP becomes sole auth method across entire platform
- Org controls full user lifecycle (creation to deactivation)
- Accounts owned and managed by org
- Users can only create content within org (no personal namespace)
- Users restricted to their managing org (no multi-org membership)
- Full lifecycle SCIM (auto-provision, update, deactivate)
- Setup requires coordination with HF team

## Protocols
- Both models: SAML 2.0 and OIDC
- Popular IdPs: Okta, Microsoft Entra ID (Azure AD), Google Workspace
- Role mapping: Yes (both)
- Resource group mapping: Yes (both)
- External collaborators: Yes (both)

## User Provisioning (SCIM)

| Aspect | Basic SSO (Enterprise) | Managed SSO (Enterprise Plus) |
|--------|----------------------|------------------------------|
| What SCIM does | Automates invitations | Full account lifecycle |
| User acceptance required | Yes | No |
| Deactivation | Org admin removes | Auto-syncs from IdP |

## Related HF Docs Pages discovered

- https://huggingface.co/docs/hub/en/enterprise-sso — SSO overview
- https://huggingface.co/docs/hub/en/enterprise-resource-groups — Resource Groups
- https://huggingface.co/docs/hub/en/enterprise — Team & Enterprise plans
- https://huggingface.co/docs/hub/en/oauth — OAuth / Sign in with HF

## Enterprise Feature Family (discovered from HF docs sidebar)

Under Team & Enterprise Plans:
- Single Sign-On (SSO)
- Audit Logs
- Storage Regions
- Data Studio for Private datasets
- Resource Groups (Access Control)
- Advanced Compute Options
- Advanced Security
- Tokens Management
- Service Accounts
- Publisher Analytics
- Gating Group Collections
- Network Security
- Rate Limits
- Blog Articles
