import { useQuery } from "@tanstack/react-query";
import { api } from "./api";

export function useHealth() {
  const q = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    retry: false,
    refetchInterval: 15000,
  });
  return { ...q, connected: q.isSuccess };
}

export function useUsers(enabled: boolean) {
  return useQuery({ queryKey: ["users"], queryFn: api.users, enabled, retry: false });
}

export function useModels(enabled: boolean) {
  return useQuery({ queryKey: ["models"], queryFn: api.models, enabled, retry: false });
}

export function useJob(jobId: string | null) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.job(jobId!),
    enabled: !!jobId,
    retry: false,
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s === "completed" || s === "failed" ? false : 1500;
    },
  });
}
