import { CheckCircle2, ShieldAlert, XCircle } from "lucide-react";
import type { Job, Metrics, VerifyResult } from "@/lib/api";
import { Card, ErrorMessage, Spinner, StatusBadge } from "./ui-kit";
import { cn } from "@/lib/utils";

const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

export function VerificationResultCard({ result }: { result: VerifyResult }) {
  const genuine = result.prediction === "Genuine";
  return (
    <Card className={cn("p-6", genuine ? "border-success/40" : "border-warning/40")}>
      <div className="flex items-center gap-4">
        {genuine ? <CheckCircle2 className="h-10 w-10 text-success" /> : <ShieldAlert className="h-10 w-10 text-warning" />}
        <div>
          <p className="text-sm text-muted-foreground">Model decision</p>
          <p className="text-2xl font-semibold">{result.prediction}</p>
        </div>
        <div className="ml-auto">
          <StatusBadge tone={genuine ? "success" : "warning"}>{pct(result.confidence)} confidence</StatusBadge>
        </div>
      </div>
      <div className="mt-6 space-y-3">
        {(["genuine", "forged"] as const).map((k) => (
          <div key={k}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="capitalize">{k} probability</span>
              <span className="font-medium">{pct(result.probabilities[k])}</span>
            </div>
            <div className="h-2 rounded-full bg-secondary">
              <div
                className={cn("h-2 rounded-full", k === "genuine" ? "bg-success" : "bg-warning")}
                style={{ width: pct(result.probabilities[k]) }}
              />
            </div>
          </div>
        ))}
      </div>
      <p className="mt-5 text-xs text-muted-foreground">
        Probabilities come from the SVM's predict_proba output and are not a guarantee of authenticity.
      </p>
    </Card>
  );
}

export function MetricsGrid({ metrics }: { metrics: Metrics }) {
  const items: [string, number][] = [
    ["Accuracy", metrics.accuracy],
    ["Precision", metrics.precision],
    ["Recall", metrics.recall],
    ["F1 score", metrics.f1_score],
  ];
  const cm = metrics.confusion_matrix;
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {items.map(([l, v]) => (
          <div key={l} className="rounded-lg border p-4">
            <p className="text-xs text-muted-foreground">{l}</p>
            <p className="mt-1 text-2xl font-semibold">{pct(v)}</p>
          </div>
        ))}
      </div>
      {cm?.length === 2 && (
        <div>
          <p className="mb-2 text-sm font-medium">Confusion matrix (test split)</p>
          <table className="text-sm">
            <thead>
              <tr className="text-muted-foreground">
                <th />
                <th className="px-4 py-1 font-normal">Pred. forged</th>
                <th className="px-4 py-1 font-normal">Pred. genuine</th>
              </tr>
            </thead>
            <tbody>
              {["Actual forged", "Actual genuine"].map((r, i) => (
                <tr key={r}>
                  <td className="pr-4 text-muted-foreground">{r}</td>
                  {cm[i]?.map((v, j) => (
                    <td key={j} className={cn("px-4 py-2 text-center font-semibold", i === j ? "bg-success-soft" : "bg-warning-soft")}>
                      {v}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function JobStatusView({ job, error }: { job?: Job | undefined; error?: Error | null }) {
  if (error) return <ErrorMessage>{error.message}</ErrorMessage>;
  if (!job) return null;
  if (job.status === "queued" || job.status === "running")
    return (
      <Card className="p-5">
        <Spinner label={job.status === "queued" ? "Training job queued…" : "Training in progress — extracting HOG features and tuning SVM…"} />
        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-secondary">
          <div className="h-full w-1/3 animate-pulse rounded-full bg-primary" />
        </div>
      </Card>
    );
  if (job.status === "failed")
    return (
      <ErrorMessage>
        <span className="inline-flex items-center gap-1 font-medium">
          <XCircle className="h-4 w-4" /> Training failed
        </span>
        <p className="mt-1">{job.error}</p>
      </ErrorMessage>
    );
  return (
    <Card className="p-6">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-2">
        <p className="text-lg font-semibold">Training complete</p>
        <StatusBadge tone="success">Saved {job.result?.model_file}</StatusBadge>
      </div>
      {job.result && <MetricsGrid metrics={job.result.metrics} />}
    </Card>
  );
}
