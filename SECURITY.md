# Security Considerations

This GitHub Action performs automated pull-request reviews using LLMs.
Because it interacts with untrusted PR content and uses repository secrets,
special care is taken to minimize risk.

## Trust Model

- The action runs on `pull_request_target` to allow commenting on PRs.
- Secrets are **never exposed to forked PRs** by default.
- Repository secrets are only available in the base repository context.

## Forked Pull Requests

⚠️ **Important**  
When using `pull_request_target`, checking out code from forked repositories
can be dangerous.

**Recommended safeguard:**
```yaml
if: github.event.pull_request.head.repo.full_name == github.repository
