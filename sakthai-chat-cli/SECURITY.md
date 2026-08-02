# Security Policy

This document outlines the security practices and procedures for the sakthai-chat-cli project.

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please **do not** file a public issue. Instead:

1. **Email Security Team**: Send a detailed report to any maintainer via private GitHub message or email
2. **Include**: CVE ID (if available), affected version(s), impact assessment, and reproduction steps
3. **Timeline**: Expect acknowledgment within 48 hours and updates every 5 business days

## Vulnerability Response Process

### 1. Assessment (0-24 hours)
- Receive and validate the report
- Determine severity (Critical, High, Medium, Low)
- Identify affected versions
- Assign a maintainer to coordinate the fix

### 2. Development (1-7 days)
- Develop and test the fix
- Prepare security patches for all affected versions
- Draft security advisory

### 3. Disclosure (7-14 days)
- Publish fixes to main repository
- Release patched versions
- Publish security advisory (with 24-48 hour advanced notice to major users if applicable)
- Credit reporter (unless they prefer anonymity)

## Automated Security Scanning

The project uses multiple layers of automated security scanning:

### Continuous Scanning
- **Dependabot**: Daily dependency vulnerability scanning
- **GitHub Security**: Advanced scanning for code vulnerabilities
- **pip-audit**: Weekly Python dependency vulnerability audit
- **Bandit**: Static security analysis on every push

### Manual Reviews
- Code reviews by maintainers (required for all PRs)
- Periodic security audits of critical code paths
- Dependency version freeze analysis

## Dependency Management

### Update Strategy
- **Patch versions** (e.g., 1.0.0 → 1.0.1): Applied immediately if security-related
- **Minor versions** (e.g., 1.0.0 → 1.1.0): Applied weekly unless blocked by compatibility
- **Major versions** (e.g., 1.0.0 → 2.0.0): Evaluated for breaking changes before update

### Vulnerability Response Timelines
- **Critical (CVSS 9.0-10.0)**: Fix within 24 hours, release within 48 hours
- **High (CVSS 7.0-8.9)**: Fix within 7 days, release within 14 days
- **Medium (CVSS 4.0-6.9)**: Fix within 30 days, release in next scheduled update
- **Low (CVSS 0.1-3.9)**: Include in next regular update

## Security Best Practices

### For Contributors
1. **Never commit secrets** (API keys, tokens, credentials)
2. **Run local security checks**: `uv run bandit -r sakthai/` before committing
3. **Audit dependencies**: `uv run pip-audit --skip-editable` for new dependencies
4. **Use strong authentication**: Enable 2FA on GitHub accounts
5. **Report suspicious activity**: Contact maintainers immediately

### For Maintainers
1. **Review dependencies monthly** for known vulnerabilities
2. **Keep Python and tools updated**: Use latest stable versions
3. **Audit high-risk modules**: Memory store, agent loop, auth, sandbox
4. **Test security patches**: Verify no breaking changes
5. **Document CVEs**: Add to repository security advisories

## Security-Sensitive Modules

These modules have additional review requirements due to security implications:

- `sakthai/auth.py` — Authentication and token handling
- `sakthai/sandbox.py` — Command execution restrictions
- `sakthai/agent/guardrails.py` — Tool execution safety policies
- `sakthai/agent/tools.py` — Tool registry and validation
- `sakthai/memory/store.py` — Database and data persistence

## Compliance

- **Python Version**: Supports only actively maintained Python versions (3.11+)
- **Dependencies**: All dependencies are tracked in `uv.lock` (committed) for reproducibility
- **License**: Follows open-source practices; no license-violating dependencies
- **Data Privacy**: No telemetry or external data collection

## Security Headers and Policies

When running sakthai as a server or web service:

1. **Set secure headers** on all HTTP responses
2. **Use HTTPS only** in production
3. **Implement rate limiting** on public endpoints
4. **Validate all input** from untrusted sources
5. **Log security events** for audit trails

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [CWE/CVSS Severity Ratings](https://www.cve.org/About/Metrics)

## FAQ

**Q: How do I know if a dependency has a vulnerability?**
A: Dependabot will automatically create a PR if vulnerabilities are found. You can also run `uv run pip-audit --skip-editable` locally.

**Q: Can I use a vulnerable dependency if I need it?**
A: Only with explicit documentation of the risk and remediation plan. This must be approved by at least two maintainers.

**Q: What should I do if I accidentally commit secrets?**
A: Use `git-filter-repo` to remove them from history, rotate the secret immediately, and notify maintainers.

**Q: How often are security audits performed?**
A: Automated checks run on every push and daily via scheduled jobs. Manual reviews happen quarterly or on-demand.
