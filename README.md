# AgentDeck

> **Open-source AI coding-agent control plane** · Developed by [muhammedkoca.com.tr](https://muhammedkoca.com.tr)

AgentDeck; Codex, Claude Code, OpenCode ve benzeri yetkili CLI coding agent'larını tek bir arayüzden yönetmek için geliştirilen, self-hosted bir developer platformudur. Project'ler izole sandbox environment'larda çalışır; task output, file change, test sonucu ve approval akışı merkezi olarak takip edilir.

Bu proje açık kaynaklıdır; mimarisi ve development süreci [muhammedkoca.com.tr](https://muhammedkoca.com.tr) tarafından hazırlanmıştır.

## Neden AgentDeck?

AI agent'lar güçlüdür ancak ürettikleri command'ler güvenilir kabul edilemez. AgentDeck, agent'ın host machine üzerinde doğrudan `exec()` çalıştırması yerine, her task için sınırlı bir container sandbox oluşturur.

```text
Web UI
  ↓
API / Task Queue
  ↓
Execution Broker
  ↓
Isolated Sandbox
  ↓
Agent Adapter
```

Control plane ile execution plane birbirinden ayrılmıştır. API ve worker Docker socket'e erişemez; container lifecycle yalnızca daraltılmış policy uygulayan execution broker tarafından yönetilir.

## Özellikler

- Self-hosted project ve task management
- Tenant-aware organization, user ve role foundation
- Argon2id password hashing ve JWT authentication foundation
- Explicit task state machine: `PENDING`, `PREPARING`, `RUNNING`, `WAITING_APPROVAL`, `TESTING`, `SUCCEEDED`, `FAILED`, `CANCELLED`, `TIMED_OUT`
- Structured event logging: agent, command, stdout/stderr, file ve test event'leri
- Docker-based isolated sandbox architecture
- CPU, memory, PID, timeout ve workspace quota limits
- Default olarak network kapalı sandbox policy
- Non-root workload user, read-only root filesystem, dropped Linux capabilities ve `no-new-privileges`
- Deterministic `FakeAgentAdapter` ile paid API gerektirmeyen CI testleri
- Authenticated encryption için secret storage primitive'leri
- Next.js tabanlı dense developer UI
- FastAPI OpenAPI documentation, health/readiness endpoint'leri ve GitHub Actions CI

## Security model

Agent prompt'ları, repository code'u ve agent output'u untrusted input olarak değerlendirilir.

Workload container'larına kesinlikle mount edilmez:

- `/var/run/docker.sock`
- Host home directory
- SSH key'ler
- Host secret'ları veya server credential'ları
- AgentDeck infrastructure credential'ları

Her task sandbox'ı ayrı filesystem workspace, resource limits, timeout ve network policy ile provision edilir. `FULL` network mode varsayılan olarak kapalıdır ve explicit administrator opt-in gerektirir.

> Docker isolation, VM isolation ile aynı seviyede değildir. Production multi-tenant deployment için dedicated Docker host/VM, host firewall, image digest pinning ve mümkün olduğunda Kata/Firecracker gibi stronger isolation katmanları önerilir.

Detaylı değerlendirme için [SECURITY.md](SECURITY.md), [THREAT_MODEL.md](THREAT_MODEL.md) ve [execution broker dokümantasyonunu](services/broker/README.md) inceleyin.

## Tech stack

| Katman | Technology |
| --- | --- |
| Web | Next.js, React, TypeScript, TanStack Query |
| API | FastAPI, SQLAlchemy, PostgreSQL |
| Queue | Redis |
| Execution | Docker Engine, constrained execution broker |
| Realtime foundation | Structured persisted events / WebSocket-ready API |
| Testing | Pytest, Vitest |
| CI | GitHub Actions |

## Quick start

### Gereksinimler

- Docker Engine ve Docker Compose v2
- Dedicated veya güvenilir bir Docker host
- Git

### Kurulum

```bash
git clone https://github.com/MHuseyin7/AgentDeck.git
cd AgentDeck
cp .env.example .env
```

`.env` içindeki tüm placeholder değerleri production için benzersiz, güçlü secret'lar ile değiştirin. Özellikle `POSTGRES_PASSWORD`, `SESSION_SECRET`, `FERNET_MASTER_KEY` ve `BROKER_SHARED_TOKEN` zorunludur.

Deterministic test sandbox image'ını bir kez build edin:

```bash
docker compose --profile build-images build fake-adapter-image
```

Ardından services'i başlatın:

```bash
docker compose up --build -d
```

- Web UI: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/ready`

## Local development

### API

```powershell
cd services/api
uv sync --group dev
uv run pytest
uv run ruff check app tests
uv run mypy app
```

### Execution broker

```powershell
cd services/broker
uv sync --group dev
uv run pytest
uv run ruff check app tests
```

### Web

```powershell
cd apps/web
npm ci
npm run typecheck
npm run build
npm run test
```

## Project status

Bu repository şu an secure control-plane foundation'ını içerir. Provider adapter'ları için authentication bypass edilmez ve provider credential'ları repository içinde tutulmaz.

Roadmap'teki sonraki capabilities şunlardır:

- Authorized Codex, Claude Code ve OpenCode adapter implementations
- Git clone/worktree lifecycle, diff review, approval ve commit flow
- Authenticated live WebSocket event streaming
- Secret CRUD, scoped injection ve audit UI
- GitHub App integration, PR creation ve CI status
- End-to-end Playwright coverage

## Contributing

Contribution'lar memnuniyetle karşılanır. Değişiklik göndermeden önce test, lint ve typecheck komutlarını çalıştırın. Host-shell execution path, plaintext credential, sandbox'a Docker socket mount veya silent privilege escalation ekleyen contribution'lar kabul edilmez.

Detaylar için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın.

## License

MIT License altında sunulmaktadır. Ayrıntılar için [LICENSE](LICENSE) dosyasına bakın.

---

Developed with a security-first approach by [muhammedkoca.com.tr](https://muhammedkoca.com.tr).
