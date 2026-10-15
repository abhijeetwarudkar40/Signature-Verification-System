import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Database, Play } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useHealth, useJob, useModels } from "@/lib/hooks";
import { Button, Card, ErrorMessage, Field, OfflineNotice, PageHeading, StatusBadge, inputClass } from "@/components/app/ui-kit";
import { JobStatusView } from "@/components/app/results";

export const Route = createFileRoute("/train-cedar")({
  head: () => ({
    meta: [
      { title: "Train CEDAR Model — SignaVerify" },
      { name: "description", content: "Train a writer-dependent HOG + SVM classifier for a CEDAR benchmark writer." },
      { property: "og:title", content: "Train CEDAR Model — SignaVerify" },
      { property: "og:description", content: "Train a writer-dependent HOG + SVM classifier for a CEDAR writer." },
    ],
  }),
  component: TrainCedarPage,
});

function TrainCedarPage() {
  const { connected, data: health } = useHealth();
  const models = useModels(connected);
  const qc = useQueryClient();
  const total = health?.total_writers ?? 55;
  const [writer, setWriter] = useState(1);
  const [jobId, setJobId] = useState<string | null>(null);
  const job = useJob(jobId);
  const available = models.data?.cedar.find((m) => m.writer_id === writer)?.available;
  const running = job.data?.status === "queued" || job.data?.status === "running";

  const start = useMutation({ mutationFn: () => api.trainCedar(writer), onSuccess: (j) => setJobId(j.job_id) });
  useEffect(() => {
    if (job.data?.status === "completed") qc.invalidateQueries({ queryKey: ["models"] });
  }, [job.data?.status, qc]);

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeading title="Train CEDAR Model" description="Train or retrain the benchmark classifier for a single CEDAR writer." />
      {!connected && <OfflineNotice />}
      {connected && health && !health.dataset_available && (
        <div className="mb-6">
          <ErrorMessage>CEDAR dataset not found on the backend (expected at dataset/cedar/signatures). Training is unavailable.</ErrorMessage>
        </div>
      )}
      <Card className="space-y-6 p-6 sm:p-7">
        <div className="grid items-end gap-5 sm:grid-cols-[1fr_auto]">
          <Field label="CEDAR writer">
            <select className={inputClass} value={writer} disabled={running} onChange={(e) => { setWriter(Number(e.target.value)); setJobId(null); }}>
              {Array.from({ length: total }, (_, i) => i + 1).map((w) => (
                <option key={w} value={w}>Writer {w}</option>
              ))}
            </select>
          </Field>
          <div className="pb-2">
            {!connected ? (
              <StatusBadge tone="neutral">Status unknown</StatusBadge>
            ) : available ? (
              <StatusBadge tone="success">Model available</StatusBadge>
            ) : (
              <StatusBadge tone="warning">Not trained</StatusBadge>
            )}
          </div>
        </div>
        <p className="flex items-start gap-2 text-sm text-muted-foreground">
          <Database className="mt-0.5 h-4 w-4 shrink-0" />
          Uses 24 genuine and 24 forged signatures for this writer plus impostor samples from other writers. The dataset stays on the backend.
        </p>
        {start.error && <ErrorMessage>{start.error.message}</ErrorMessage>}
        <Button onClick={() => start.mutate()} disabled={!connected || running || start.isPending || health?.dataset_available === false}>
          <Play className="h-4 w-4" /> {available ? "Retrain model" : "Train model"}
        </Button>
      </Card>
      <div className="mt-6">
        <JobStatusView job={job.data} error={job.error} />
      </div>
    </div>
  );
}
