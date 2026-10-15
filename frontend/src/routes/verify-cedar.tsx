import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { api } from "@/lib/api";
import { useHealth, useModels } from "@/lib/hooks";
import { Field, OfflineNotice, PageHeading, StatusBadge, inputClass } from "@/components/app/ui-kit";
import { VerifyForm } from "@/components/app/VerifyForm";

export const Route = createFileRoute("/verify-cedar")({
  head: () => ({
    meta: [
      { title: "Verify CEDAR Signature — SignaVerify" },
      { name: "description", content: "Check a signature image against a trained CEDAR writer model." },
      { property: "og:title", content: "Verify CEDAR Signature — SignaVerify" },
      { property: "og:description", content: "Check a signature image against a trained CEDAR writer model." },
    ],
  }),
  component: VerifyCedarPage,
});

function VerifyCedarPage() {
  const { connected, data: health } = useHealth();
  const models = useModels(connected);
  const [writer, setWriter] = useState(1);
  const total = health?.total_writers ?? 55;
  const available = models.data?.cedar.find((m) => m.writer_id === writer)?.available ?? false;

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeading title="Verify CEDAR Signature" description="Classify a signature image with a CEDAR writer's trained SVM." />
      {!connected && <OfflineNotice />}
      <VerifyForm
        resetKey={String(writer)}
        canVerify={connected && available}
        blockedReason={connected && models.isSuccess && !available ? `No trained model for writer ${writer}. Train it first.` : null}
        onVerify={(f) => api.verifyCedar(writer, f)}
        selector={
          <div className="grid items-end gap-4 sm:grid-cols-[1fr_auto]">
            <Field label="CEDAR writer">
              <select className={inputClass} value={writer} onChange={(e) => setWriter(Number(e.target.value))}>
                {Array.from({ length: total }, (_, i) => i + 1).map((w) => (
                  <option key={w} value={w}>Writer {w}</option>
                ))}
              </select>
            </Field>
            <div className="pb-2">
              {connected ? (
                <StatusBadge tone={available ? "success" : "warning"}>{available ? "Model ready" : "Not trained"}</StatusBadge>
              ) : (
                <StatusBadge tone="neutral">Status unknown</StatusBadge>
              )}
            </div>
          </div>
        }
      />
    </div>
  );
}
