import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Play, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { z } from "zod";
import { api } from "@/lib/api";
import { useHealth, useJob, useUsers } from "@/lib/hooks";
import { Button, Card, EmptyState, ErrorMessage, Field, OfflineNotice, PageHeading, Spinner, StatusBadge, inputClass } from "@/components/app/ui-kit";
import { JobStatusView } from "@/components/app/results";

export const Route = createFileRoute("/train-user")({
  validateSearch: z.object({ username: z.string().optional() }),
  head: () => ({
    meta: [
      { title: "Train User Model — SignaVerify" },
      { name: "description", content: "Train a writer-dependent HOG + SVM classifier for a registered user." },
      { property: "og:title", content: "Train User Model — SignaVerify" },
      { property: "og:description", content: "Train a writer-dependent classifier for a registered user." },
    ],
  }),
  component: TrainUserPage,
});

function TrainUserPage() {
  const { connected, data: health } = useHealth();
  const minSamples = health?.min_signatures ?? 10;
  const users = useUsers(connected);
  const qc = useQueryClient();
  const search = Route.useSearch();
  const [username, setUsername] = useState(search.username ?? "");
  const [jobId, setJobId] = useState<string | null>(null);
  const job = useJob(jobId);
  const running = job.data?.status === "queued" || job.data?.status === "running";

  useEffect(() => {
    if (!username && users.data?.length) setUsername(users.data[0]!.username);
  }, [users.data, username]);
  useEffect(() => {
    if (job.data?.status === "completed") qc.invalidateQueries({ queryKey: ["users"] });
  }, [job.data?.status, qc]);

  const user = users.data?.find((u) => u.username === username);
  const insufficient = !!user && user.sample_count < minSamples;
  const start = useMutation({ mutationFn: () => api.trainUser(username), onSuccess: (j) => setJobId(j.job_id) });

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeading title="Train User Model" description="Fit a personal classifier from a registered user's reference signatures." />
      {!connected && <OfflineNotice />}
      <Card className="space-y-6 p-6 sm:p-7">
        {connected && users.isLoading ? (
          <Spinner label="Loading users…" />
        ) : connected && users.data?.length === 0 ? (
          <EmptyState icon={Users} title="No registered users" text="Register an identity with genuine signatures first." />
        ) : (
          <>
            <Field label="Registered user">
              <select className={inputClass} value={username} disabled={!connected || running} onChange={(e) => { setUsername(e.target.value); setJobId(null); }}>
                {!connected && <option>Backend not connected</option>}
                {users.data?.map((u) => (
                  <option key={u.username} value={u.username}>{u.full_name} ({u.username})</option>
                ))}
              </select>
            </Field>
            {user && (
              <div className="flex flex-wrap gap-3">
                <StatusBadge tone={insufficient ? "warning" : "primary"}>{user.sample_count} reference samples</StatusBadge>
                <StatusBadge tone={user.model_available ? "success" : "neutral"}>{user.model_available ? "Model trained" : "No model yet"}</StatusBadge>
              </div>
            )}
            {insufficient && (
              <ErrorMessage>
                {user!.full_name} has {user!.sample_count} samples; at least {minSamples} are required.
              </ErrorMessage>
            )}
            {connected && health && !health.dataset_available && (
              <ErrorMessage>User training needs CEDAR impostor samples, but the dataset was not found on the backend.</ErrorMessage>
            )}
            {start.error && <ErrorMessage>{start.error.message}</ErrorMessage>}
            <Button onClick={() => start.mutate()} disabled={!connected || !user || insufficient || running || start.isPending || health?.dataset_available === false}>
              <Play className="h-4 w-4" /> {user?.model_available ? "Retrain model" : "Train model"}
            </Button>
          </>
        )}
      </Card>
      <div className="mt-6">
        <JobStatusView job={job.data} error={job.error} />
        {job.data?.status === "completed" && (
          <Link to="/verify-user" className="mt-4 inline-block text-sm font-medium text-primary">Verify a signature for this user →</Link>
        )}
      </div>
    </div>
  );
}
