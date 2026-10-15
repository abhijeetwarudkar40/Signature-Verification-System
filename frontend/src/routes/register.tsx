import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Info, UserPlus } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { useHealth } from "@/lib/hooks";
import { Button, Card, ErrorMessage, Field, OfflineNotice, PageHeading, Spinner, inputClass } from "@/components/app/ui-kit";
import { ImageDropzone } from "@/components/app/upload";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "Register User — SignaVerify" },
      { name: "description", content: "Enrol a new identity with genuine reference signatures for writer-dependent verification." },
      { property: "og:title", content: "Register User — SignaVerify" },
      { property: "og:description", content: "Enrol a new identity with genuine reference signatures." },
    ],
  }),
  component: RegisterPage,
});

function RegisterPage() {
  const { connected, data: health } = useHealth();
  const minSamples = health?.min_signatures ?? 10;
  const qc = useQueryClient();
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [localError, setLocalError] = useState<string | null>(null);

  const m = useMutation({
    mutationFn: () => api.registerUser(fullName.trim(), username.trim().toLowerCase(), files),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    if (!fullName.trim()) return setLocalError("Full name is required.");
    if (!/^[a-z0-9_]{3,32}$/i.test(username.trim()))
      return setLocalError("Username must be 3–32 characters: letters, numbers or underscores.");
    if (files.length < minSamples) return setLocalError(`Upload at least ${minSamples} genuine signatures (currently ${files.length}).`);
    m.mutate();
  };

  if (m.isSuccess)
    return (
      <div className="mx-auto max-w-2xl">
        <Card className="p-8 text-center">
          <CheckCircle2 className="mx-auto h-12 w-12 text-success" />
          <h1 className="mt-4 text-2xl font-semibold">{m.data.full_name} registered</h1>
          <p className="mt-2 text-muted-foreground">
            {m.data.sample_count} reference signatures stored locally. Train a model before verifying.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link to="/train-user" search={{ username: m.data.username }}>
              <Button>Train user model</Button>
            </Link>
            <Button variant="outline" onClick={() => { m.reset(); setFiles([]); setFullName(""); setUsername(""); }}>
              Register another
            </Button>
          </div>
        </Card>
      </div>
    );

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeading title="Register User" description="Create a new identity and upload genuine reference signatures." />
      {!connected && <OfflineNotice />}
      <form onSubmit={submit} className="grid gap-8 lg:grid-cols-[1fr_320px]">
        <Card className="space-y-6 p-6 sm:p-7">
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Full name">
              <input className={inputClass} value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Maya Patel" />
            </Field>
            <Field label="Unique username" hint="Stored in lowercase">
              <input className={inputClass} value={username} onChange={(e) => setUsername(e.target.value)} placeholder="maya" />
            </Field>
          </div>
          <Field label={`Genuine signatures (${files.length} / ${minSamples} minimum)`}>
            <ImageDropzone files={files} onChange={setFiles} multiple disabled={m.isPending} />
          </Field>
          {(localError || m.error) && <ErrorMessage>{localError ?? m.error?.message}</ErrorMessage>}
          <div className="flex items-center gap-4">
            <Button type="submit" disabled={!connected || m.isPending}>
              <UserPlus className="h-5 w-5" /> Register identity
            </Button>
            {m.isPending && <Spinner label="Uploading signatures…" />}
          </div>
        </Card>
        <Card className="h-fit p-6 text-sm">
          <p className="inline-flex items-center gap-2 font-semibold"><Info className="h-4 w-4 text-primary" /> How references are used</p>
          <p className="mt-3 text-muted-foreground">
            SignaVerify is writer-dependent: each person gets their own SVM classifier. These genuine samples become the
            positive class; CEDAR signatures from other writers serve as impostor examples.
          </p>
          <ul className="mt-4 list-disc space-y-1.5 pl-5 text-muted-foreground">
            <li>At least {minSamples} clean signatures</li>
            <li>Dark ink on a plain light background</li>
            <li>PNG or JPEG, up to 5 MB each</li>
            <li>Images are stored in the backend's local user_data folder</li>
          </ul>
        </Card>
      </form>
    </div>
  );
}
