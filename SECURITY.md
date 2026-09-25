# Security policy

## Reporting

Do not publish vulnerabilities in public issues. Email the project maintainer with reproduction details and impact. Rotate any exposed credentials immediately.

## Deployment requirements

- Run the execution broker on a dedicated Docker host or VM. Docker daemon access is effectively host-root.
- Do not expose broker ports publicly. It must be reachable only from the worker network with a high-entropy shared token and, in production, mTLS.
- Keep `ALLOW_FULL_NETWORK=false`; FULL network mode requires an explicit administrator configuration and egress controls outside Docker.
- Use a secrets manager or KMS-backed `FERNET_MASTER_KEY`; never use development values in production.
- Restrict image supply chain with pinned digests and signature verification before enabling non-fake adapters.

## Supported report scope

Tenant isolation, authorization, secret handling, task state transitions, broker authorization, sandbox escape paths, log redaction, and dependency vulnerabilities are in scope.
