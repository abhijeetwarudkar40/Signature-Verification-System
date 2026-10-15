import { Link, useRouterState } from "@tanstack/react-router";
import { Bell, ChevronDown, ChevronRight, Fingerprint, Lock, Menu, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { NAV } from "./nav";
import { useHealth } from "@/lib/hooks";
import { cn } from "@/lib/utils";

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col bg-sidebar px-5 py-8 text-sidebar-foreground">

      <div className="flex items-center gap-3 px-1">
        <Fingerprint className="h-9 w-9 text-primary" strokeWidth={1.5} />
        <div>
          <p className="text-2xl font-semibold leading-tight text-white">
            SignaVerify
          </p>
          <p className="text-xs text-sidebar-muted">
            Signature Intelligence
          </p>
        </div>
      </div>

      <p className="mt-12 px-1 text-xs font-medium uppercase tracking-wide text-sidebar-muted">Workspace</p>
      <nav className="mt-3 flex flex-col gap-1.5">
        {NAV.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            activeOptions={{ exact: true }}
            className="flex items-center gap-3 rounded-lg px-4 py-4 text-[15px] transition-colors hover:bg-sidebar-accent"
            activeProps={{ className: "bg-sidebar-primary font-semibold text-sidebar-primary-foreground hover:bg-sidebar-primary" }}
          >
            <item.icon className="h-5 w-5" strokeWidth={1.75} />
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="mt-auto flex items-start gap-2 rounded-lg border border-sidebar-border p-3 text-xs text-sidebar-muted">
        <Lock className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        Signatures are processed by your local Python backend only.
      </div>
    </div>
  );
}

function ConnectionPill() {
  const { connected, isLoading } = useHealth();
  const label = isLoading ? "Checking…" : connected ? "Backend connected" : "Offline mode";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium",
        connected ? "bg-success-soft text-success" : "bg-warning-soft text-warning",
      )}
    >
      <span className="h-2 w-2 rounded-full bg-current" />
      {label}
    </span>
  );
}

export function AppLayout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const current = NAV.find((n) => n.to === pathname) ?? NAV[0]!;

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-[300px] shrink-0 lg:block">
        <Sidebar />
      </aside>
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-foreground/40" onClick={() => setOpen(false)} />
          <div className="relative h-full w-[280px]">
            <Sidebar onNavigate={() => setOpen(false)} />
            <button
              aria-label="Close menu"
              onClick={() => setOpen(false)}
              className="absolute right-3 top-3 rounded-md p-1 text-sidebar-foreground"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-4 border-b bg-card px-5 py-5 sm:px-10">
          <button aria-label="Open menu" className="rounded-md p-1 lg:hidden" onClick={() => setOpen(true)}>
            <Menu className="h-5 w-5" />
          </button>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Workspace</span>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{current.label}</span>
            </div>
            <p className="mt-1 hidden truncate text-sm text-muted-foreground sm:block">{current.subtitle}</p>
          </div>
          <ConnectionPill />
          <button aria-label="Notifications" className="hidden rounded-md p-2 text-muted-foreground sm:block">
            <Bell className="h-5 w-5" />
          </button>
          <div className="hidden items-center gap-3 border-l pl-5 md:flex">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-primary-soft font-semibold text-primary">
              AM
            </span>
            <div className="leading-tight">
              <p className="text-sm font-semibold">Admin</p>
              <p className="text-xs text-muted-foreground">Project administrator</p>
            </div>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </div>
        </header>
        <main className="flex-1 px-5 py-8 sm:px-10 sm:py-12">{children}</main>
        <footer className="flex flex-wrap items-center justify-between gap-2 border-t px-5 py-5 text-xs text-muted-foreground sm:px-10">
          <span className="inline-flex items-center gap-1.5">
            <Lock className="h-3.5 w-3.5" /> All signature processing happens locally. No images are sent to third-party services.
          </span>
          <span>SignaVerify · HOG + SVM</span>
        </footer>
      </div>
    </div>
  );
}
