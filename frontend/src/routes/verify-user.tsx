import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useHealth, useUsers } from "@/lib/hooks";
import { Field, OfflineNotice, PageHeading, StatusBadge, inputClass } from "@/components/app/ui-kit";
import { VerifyForm } from "@/components/app/VerifyForm";

export const Route = createFileRoute("/verify-user")({
  head: () => ({
    meta: [
      { title: "Verify User Signature — SignaVerify" },
      { name: "description", content: "Check a signature image against a registered user's trained model." },
      { property: "og:title", content: "Verify User Signature — SignaVerify" },
      { property: "og:description", content: "Check a signature image against a registered user's trained model." },
    ],
  }),
  component: VerifyUserPage,
});

function VerifyUserPage() {
  const { connected } = useHealth();
  const users = useUsers(connected);
  const [username, setUsername] = useState("");
  useEffect(() => {
    if (!username && users.data?.length) setUsername(users.data[0]!.username);
  }, [users.data, username]);
  const user = users.data?.find((u) => u.username === username);

  let blocked: string | null = null;
  if (connected && users.isSuccess && users.data.length === 0) blocked = "No registered users yet. Register an identity first.";
  else if (user && !user.model_available) blocked = `${user.full_name} has no trained model. Train it on the Train User Model page.`;

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeading title="Verify User Signature" description="Classify a signature with a registered user's personal SVM." />
      {!connected && <OfflineNotice />}
      <VerifyForm
        resetKey={username}
        canVerify={connected && !!user?.model_available}
        blockedReason={blocked}
        onVerify={(f) => api.verifyUser(username, f)}
        selector={
          <div className="grid items-end gap-4 sm:grid-cols-[1fr_auto]">
            <Field label="Registered user">
              <select className={inputClass} value={username} disabled={!connected} onChange={(e) => setUsername(e.target.value)}>
                {!connected && <option>Backend not connected</option>}
                {users.data?.map((u) => (
                  <option key={u.username} value={u.username}>{u.full_name} ({u.username})</option>
                ))}
              </select>
            </Field>
            <div className="pb-2">
              {user ? (
                <StatusBadge tone={user.model_available ? "success" : "warning"}>{user.model_available ? "Model ready" : "Not trained"}</StatusBadge>
              ) : (
                <StatusBadge tone="neutral">—</StatusBadge>
              )}
            </div>
          </div>
        }
      />
    </div>
  );
}
