"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

function Deck() {
  return <main>
    <aside>
      <div className="brand">AgentDeck <span>self-hosted</span></div>
      <nav><a className="active">Overview</a><a>Projects</a><a>Tasks</a><a>Agents</a><a>Sandbox profiles</a><a>Audit log</a></nav>
      <div className="identity"><i /> Control plane<br /><small>Sign in to access an organization</small></div>
    </aside>
    <section className="content">
      <header><div><p className="crumb">AgentDeck / Overview</p><h1>Your isolated coding-agent control plane</h1></div><div className="actions"><button className="quiet">Sign in</button><button>Create project</button></div></header>
      <div className="notice">No task data is simulated. Sign in, select an organization, then create a project and task to see its live, broker-recorded event stream.</div>
      <div className="workspace">
        <div className="sidepanel"><h2>Execution boundary</h2><p>Broker-managed sandboxes</p><small>Workloads have no host shell or Docker socket.</small><hr /><h3>Default policy</h3><ul><li><em>•</em> Network off</li><li><em>•</em> Non-root user</li><li><em>•</em> Bounded CPU / memory / PIDs</li><li><em>•</em> Read-only root filesystem</li></ul></div>
        <div className="work"><div className="tabs"><button className="selected">Tasks</button><button disabled>Terminal</button><button disabled>Files</button><button disabled>Diff</button><button disabled>Tests</button><button disabled>Events</button></div><div className="panel"><div className="empty"><strong>No task selected</strong><p>AgentDeck will only render events persisted by the execution broker. The FakeAgentAdapter is available for deterministic integration tests and is executed inside the same sandbox boundary.</p></div></div></div>
      </div>
    </section>
  </main>;
}

export default function Page() { return <QueryClientProvider client={queryClient}><Deck /></QueryClientProvider>; }
