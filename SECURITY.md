# Security Policy

## Supported Version

| Version | Supported |
| --- | --- |
| `0.1.x` | Yes |

## Reporting a Vulnerability

Do not report vulnerabilities through public issue trackers.

To report a vulnerability:

1. Notify the repository owner through the approved internal security channel.
2. Include a concise description, impact statement, and reproduction steps.
3. Attach relevant evidence artifacts instead of screenshots alone.
4. Wait for triage before sharing details outside the approved review group.

## Security Practices

- No credentials, tokens, or secrets in repository content or committed
  artifacts.
- Supply-chain checks are part of the CI baseline via Snyk.
- GitHub Actions repository secrets are used for Codacy, Codecov, and Snyk
  tokens and must never appear in committed files.
