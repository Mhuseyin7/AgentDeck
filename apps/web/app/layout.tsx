import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = { title: "AgentDeck", description: "Self-hosted control plane for coding agents" };

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
