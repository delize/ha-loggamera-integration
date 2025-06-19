# Security Policy

## Workflow Security

This repository uses automated GitHub Actions workflows with built-in security controls:

### 🔒 Permission Levels

| Workflow | Required Permission | Description |
|----------|-------------------|-------------|
| **Auto-Fix Code** | Write or PR Author | Can format code on PRs you created or if you're a collaborator |
| **Release Creation** | Admin/Maintain | Only repository admins can create releases |
| **Version Bumping** | Automatic | Triggered only by merged PRs with proper labels |
| **Validation** | None | Runs on all PRs for safety |

### 🛡️ Security Controls

1. **Permission Checks**: All manual workflows verify user permissions before running
2. **Rate Limiting**: Auto-fix workflow limited to 5 runs per user per hour
3. **PR Validation**: Users can only auto-fix their own PRs or PRs from the main repo
4. **Audit Logging**: All manual workflow runs are logged with user and timestamp
5. **Fork Protection**: Special handling for PRs from forks

### 🚨 Abuse Prevention

- **No anonymous access**: All workflows require GitHub authentication
- **Collaborator-only**: Manual workflows restricted to repository collaborators
- **Admin-only releases**: Only admins/maintainers can create releases
- **Rate limiting**: Prevents workflow spam
- **Audit trail**: All actions are logged and traceable

### 📞 Reporting Security Issues

#### Loggamera API Security Issues

**For security issues related to the Loggamera Platform API itself** (authentication, data exposure, API vulnerabilities), please report directly to **Loggamera**:

- **Contact**: Loggamera support or security team
- **Scope**: API endpoints, authentication mechanisms, data handling on Loggamera's servers
- **Examples**:
  - API authentication bypass
  - Data exposure in API responses
  - Server-side vulnerabilities in Loggamera infrastructure

**Note**: This integration is a client that connects to Loggamera's API. Security issues with the API service itself are outside the scope of this integration and should be addressed by Loggamera directly.

#### Home Assistant Integration Security Issues

**For security issues specific to this Home Assistant integration** (workflows, code, configuration), please follow the procedure below:

1. **DO NOT** create a public issue
2. Email the repository maintainers directly
3. Include details about the vulnerability and potential impact
4. Allow time for the issue to be addressed before public disclosure

**Integration security scope**:
- Integration code vulnerabilities
- Local data exposure in Home Assistant
- Workflow security issues
- Configuration security problems

### 🔧 Workflow Security Best Practices

For contributors:
- Only run auto-fix workflows on your own PRs
- Don't share workflow URLs with unauthorized users
- Report suspicious workflow activity
- Use proper branch protection in your forks

For maintainers:
- Regularly review workflow run logs
- Monitor for unusual usage patterns
- Keep workflows updated with latest security practices
- Review and approve all workflow changes

---

*Last updated: 2025-06-13*
