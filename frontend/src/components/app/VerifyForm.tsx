import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { useState, type ReactNode } from "react";
import type { VerifyResult } from "@/lib/api";
import { Button, Card, ErrorMessage, Spinner } from "./ui-kit";
import { ImageDropzone } from "./upload";
import { VerificationResultCard } from "./results";

export function VerifyForm({
  selector,
  canVerify,
  blockedReason,
  onVerify,
  resetKey,
}: {
  selector: ReactNode;
  canVerify: boolean;
  blockedReason?: string | null;
  onVerify: (file: File) => Promise<VerifyResult>;
  resetKey: string;
}) {
  const qc = useQueryClient();
  const [files, setFiles] = useState<File[]>([]);
  const [key, setKey] = useState(resetKey);
  const m = useMutation({
    mutationFn: () => onVerify(files[0]!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["verifications"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });
  if (key !== resetKey) {
    setKey(resetKey);
    m.reset();
  }

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <Card className="space-y-6 p-6 sm:p-7">
        {selector}
        <ImageDropzone files={files} onChange={(f) => { setFiles(f); m.reset(); }} disabled={m.isPending} />
        {blockedReason && <ErrorMessage>{blockedReason}</ErrorMessage>}
        <div className="flex items-center gap-4">
          <Button onClick={() => m.mutate()} disabled={!canVerify || files.length === 0 || m.isPending}>
            <ShieldCheck className="h-5 w-5" /> Verify signature
          </Button>
          {m.isPending && <Spinner label="Preprocessing and classifying…" />}
        </div>
      </Card>
      <div>
        {m.error && <ErrorMessage>{m.error.message}</ErrorMessage>}
        {m.data && <VerificationResultCard result={m.data} />}
        {!m.data && !m.error && (
          <Card className="flex h-full min-h-60 items-center justify-center p-8 text-center text-sm text-muted-foreground">
            The Genuine / Forged decision from your local model will appear here.
          </Card>
        )}
      </div>
    </div>
  );
}
