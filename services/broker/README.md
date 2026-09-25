# Execution broker

The broker is intentionally a small, separate security boundary. It accepts only an authenticated, schema-validated `RunRequest`, builds a fixed adapter command itself, and does not accept arbitrary Docker options, images, mounts, environment variables, or shell commands from clients.

Its Docker socket mount is privileged host access. Deploy it alone on a dedicated runner host, restrict its network, use mTLS in addition to the shared token, pin and verify workload images, and monitor Docker daemon events. Do not publish port 8081.

The initial implementation allows `fake` adapter execution only. Provider adapters must be registered with a reviewed image digest and a purpose-specific configuration validator before activation.
