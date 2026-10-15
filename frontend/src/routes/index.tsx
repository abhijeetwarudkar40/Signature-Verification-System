import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  CheckCircle2,
  Cpu,
  Database,
  FileText,
  History,
  ShieldAlert,
  ShieldCheck,
  User as UserIcon,
  UserPlus,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { useHealth } from "@/lib/hooks";
import { demoActivity, demoModels, demoStats, demoVerifications } from "@/lib/demo";
import { Button, Card, DemoBanner, EmptyState, IconTile, Panel, PageHeading, StatCard, StatusBadge } from "@/components/app/ui-kit";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — SignaVerify" },
      { name: "description", content: "Overview of registered identities, trained models and recent signature verifications." },
      { property: "og:title", content: "Dashboard — SignaVerify" },
      { property: "og:description", content: "Overview of registered identities, trained models and recent signature verifications." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const { connected } = useHealth();
  const stats = useQuery({ queryKey: ["stats"], queryFn: api.stats, enabled: connected });
  const users = useQuery({ queryKey: ["users"], queryFn: api.users, enabled: connected });
  const models = useQuery({ queryKey: ["models"], queryFn: api.models, enabled: connected });
  const verifs = useQuery({ queryKey: ["verifications"], queryFn: () => api.verifications(8), enabled: connected });

  const s = connected ? stats.data : demoStats;
  const pct = (n?: number) => (s && s.verifications ? `${Math.round(((n ?? 0) / s.verifications) * 100)}%` : "—");
  const sample = connected ? "" : "sample ";

  const modelRows = connected
    ? [
        ...(models.data?.cedar.filter((m) => m.available).slice(0, 2).map((m) => ({
          kind: "cedar" as const,
          title: `CEDAR writer ${m.writer_id}`,
          meta: `writer_${m.writer_id}.pkl`,
          ready: true,
        })) ?? []),
        ...(users.data?.slice(0, 3).map((u) => ({
          kind: "user" as const,
          title: `${u.full_name} · ${u.username}`,
          meta: `${u.sample_count} genuine references${u.model_available ? ` · ${u.username}.pkl` : ""}`,
          ready: u.model_available,
        })) ?? []),
      ]
    : demoModels;

  const rows = connected
    ? (verifs.data ?? []).map((v) => ({ ...v, created_at: new Date(v.created_at).toLocaleString() }))
    : demoVerifications;

  const activity = connected
    ? [
        ...(verifs.data ?? []).slice(0, 4).map((v) => ({
          title: `${v.kind === "user" ? "User" : "CEDAR"} signature verified`,
          detail: `${v.target} · ${v.prediction}`,
          time: new Date(v.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        })),
      ]
    : demoActivity;

  return (
    <div className="mx-auto max-w-[1440px]">
      <PageHeading
        title="Dashboard"
        description="
Welcome back, Admin. Your local signature verification workspace is ready.
"
        action={
          <Link to="/verify-user">
            <Button>
              <ShieldCheck className="h-5 w-5" /> Verify a signature
            </Button>
          </Link>
        }
      />
      {!connected && <DemoBanner text="Records, metrics and prediction scores are illustrative sample data." />}

      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Registered users" value={s?.registered_users ?? "—"} hint={connected ? "Identities in local database" : "3 new identities this week"} icon={Users} tone="primary" />
        <StatCard label="Signatures verified" value={s?.verifications ?? "—"} hint="Across benchmark and user models" icon={FileText} tone="primary" />
        <StatCard label="Genuine results" value={s?.genuine ?? "—"} hint={`${pct(s?.genuine)} of ${sample}verifications`} icon={CheckCircle2} tone="success" />
        <StatCard label="Flagged as forged" value={s?.forged ?? "—"} hint={`${pct(s?.forged)} of ${sample}verifications`} icon={ShieldAlert} tone="warning" />
      </div>

      <div className="mt-8 grid gap-8 xl:grid-cols-[1.65fr_1fr]">
        <Panel title="Model readiness" subtitle="Available local classifiers" action={<StatusBadge tone="neutral" dot={false}>HOG + SVM</StatusBadge>}>
          {modelRows.length === 0 ? (
            <EmptyState icon={Database} title="No models yet" text="Train a CEDAR writer or registered user model to see it here." />
          ) : (
            <ul className="divide-y">
              {modelRows.map((m) => (
                <li key={m.title} className="flex items-center gap-4 py-4">
                  <IconTile icon={m.kind === "cedar" ? Database : UserIcon} size="lg" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold">{m.title}</p>
                    <p className="truncate text-sm text-muted-foreground">{m.meta}</p>
                  </div>
                  <StatusBadge tone={m.ready ? "success" : "warning"}>{m.ready ? "Ready" : "Not trained"}</StatusBadge>
                </li>
              ))}
            </ul>
          )}
          <div className="mt-2 flex items-center justify-between border-t pt-4 text-sm">
            <span className="text-muted-foreground">{connected ? "Live from local backend" : "Last trained today, 14:05 (demo)"}</span>
            <Link to="/train-user" className="inline-flex items-center gap-1 font-medium text-primary">
              Manage models <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </Panel>

        <Panel title="Verification summary" subtitle={connected ? "All recorded outcomes" : "Illustrative outcomes · last 7 days"}>
          <div className="flex items-end justify-between">
            <p className="text-4xl font-semibold">{s?.verifications ?? "—"}</p>
            <p className="text-sm text-muted-foreground">{sample}checks</p>
          </div>
          <div className="mt-6 flex h-3 gap-1 overflow-hidden rounded-full bg-secondary">
            {s && s.verifications > 0 && (
              <>
                <div className="bg-success" style={{ width: pct(s.genuine) }} />
                <div className="flex-1 bg-warning" />
              </>
            )}
          </div>
          <div className="mt-4 flex justify-between text-sm">
            <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-success" /> Genuine <b>{s?.genuine ?? 0}</b></span>
            <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-warning" /> Forged <b>{s?.forged ?? 0}</b></span>
          </div>
          <p className="mt-6 border-t pt-4 text-sm text-muted-foreground">Outcome counts describe {connected ? "recorded verifications" : "this demo"}, not model accuracy.</p>
        </Panel>
      </div>

      <div className="mt-8 grid gap-8 xl:grid-cols-[1.65fr_1fr]">
        <Panel
          title="Recent verifications"
          subtitle={connected ? "Latest recorded checks" : "Today, 12 October 2026 (demo)"}
          action={<Link to="/verify-cedar" className="inline-flex items-center gap-1 text-sm font-medium text-primary">New check <ArrowRight className="h-4 w-4" /></Link>}
        >
          {rows.length === 0 ? (
            <EmptyState icon={History} title="No verifications yet" text="Results appear here after you verify a signature." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="rounded-l-lg px-4 py-3 font-medium">Signature / identity</th>
                    <th className="px-4 py-3 font-medium">Model</th>
                    <th className="px-4 py-3 font-medium">Result</th>
                    <th className="rounded-r-lg px-4 py-3 font-medium">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {rows.map((r) => (
                    <tr key={r.id}>
                      <td className="px-4 py-3.5 font-medium">{r.target}</td>
                      <td className="px-4 py-3.5 text-muted-foreground">{r.kind === "cedar" ? "CEDAR SVM" : "User SVM"}</td>
                      <td className="px-4 py-3.5">
                        <StatusBadge tone={r.prediction === "Genuine" ? "success" : "warning"}>
                          {r.prediction} · {(r.confidence * 100).toFixed(0)}%
                        </StatusBadge>
                      </td>
                      <td className="px-4 py-3.5 text-muted-foreground">{r.created_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        <Panel title="Recent activity" subtitle="Your workspace audit trail">
          {activity.length === 0 ? (
            <EmptyState icon={History} title="No activity yet" text="Verifications will be listed here." />
          ) : (
            <ul className="space-y-5">
              {activity.map((a, i) => (
                <li key={i} className="flex gap-3">
                  <IconTile icon={History} tone="neutral" />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{a.title}</p>
                    <p className="truncate text-sm text-muted-foreground">{a.detail}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">{a.time}</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <div className="mt-8 grid gap-5 md:grid-cols-3">
        {[
          { to: "/register" as const, icon: UserPlus, title: "Register an identity", text: "Upload genuine reference signatures." },
          { to: "/train-user" as const, icon: Cpu, title: "Train a local model", text: "Fit a writer-dependent HOG + SVM classifier." },
          { to: "/verify-user" as const, icon: ShieldCheck, title: "Verify a signature", text: "Get a Genuine or Forged decision." },
        ].map((q) => (
          <Link key={q.to} to={q.to}>
            <Card className="flex items-center gap-4 p-5 transition-colors hover:border-primary/40">
              <IconTile icon={q.icon} />
              <div className="flex-1">
                <p className="font-semibold">{q.title}</p>
                <p className="text-sm text-muted-foreground">{q.text}</p>
              </div>
              <ArrowRight className="h-4 w-4 text-primary" />
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
