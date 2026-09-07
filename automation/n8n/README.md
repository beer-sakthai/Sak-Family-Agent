# n8n Issue Triage Workflow

`issue-triage.json` is a portable n8n workflow export for triaging newly opened GitHub issues.

## Flow

The workflow follows the webhook and HTTP API integration pattern:

`GitHub webhook → validate event → classify with AI → normalize result → apply labels → post comment → acknowledge`

Non-`opened` events and malformed payloads are acknowledged with HTTP `202` and do not create side effects.

## Import and configure

1. Import `issue-triage.json` into n8n.
2. Set the following environment variables in the n8n runtime:
   - `OPENAI_API_KEY`: API key allowed to call the OpenAI-compatible chat completions endpoint.
   - `GITHUB_TOKEN`: fine-grained GitHub token with **Issues: Read and write** permission for the target repository.
   - `OPENAI_TRIAGE_MODEL` (optional): model name; defaults to `gpt-4o-mini`.
3. Configure a GitHub repository webhook:
   - Payload URL: the n8n production webhook URL for `/webhook/github-issue-triage`.
   - Content type: `application/json`.
   - Event: **Issues**; the workflow itself filters to `opened` events.
   - Secret/signature verification: configure GitHub and add signature verification before production use. The portable export validates payload shape but does not verify `X-Hub-Signature-256`.
4. Ensure the repository already has the labels used by the workflow, or allow GitHub to create them as needed: `bug`, `feature`, `documentation`, `question`, `security`, `priority:high`, `priority:critical`, and `needs-triage`.
5. Review the AI prompt and comment text, then activate the workflow only after testing with a test repository or a safe issue.

## Security and operational notes

The issue title and body are treated as untrusted text. The classifier prompt explicitly instructs the model not to follow instructions embedded in issue content, and the normalization step allowlists categories, priorities, and labels before making GitHub writes.

The workflow is intentionally inactive in the export. Test the webhook response and inspect executions before activation. The label and comment nodes have real external side effects, so use a test repository or disable those nodes during dry runs.

For production, add a separate error workflow using n8n's **Error Trigger** to alert maintainers, and consider replacing environment-variable authentication with n8n credentials managed by the instance.
