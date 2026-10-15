import { AlertTriangle, FlaskConical, Loader2, WifiOff, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/api";

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("rounded-xl border bg-card shadow-card", className)}>{children}</div>;
}

export function Panel({
  title,
  subtitle,
  action,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("p-6 sm:p-7", className)}>
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">{title}</h2>
          {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </Card>
  );
}

export function PageHeading({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-[34px]">{title}</h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}

type Tone = "success" | "warning" | "neutral" | "primary" | "destructive";
const toneClass: Record<Tone, string> = {
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning",
  neutral: "bg-secondary text-secondary-foreground",
  primary: "bg-primary-soft text-primary",
  destructive: "bg-destructive-soft text-destructive",
};

export function StatusBadge({ tone, children, dot = true }: { tone: Tone; children: ReactNode; dot?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium", toneClass[tone])}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}

export function IconTile({ icon: Icon, tone = "primary", size = "md" }: { icon: LucideIcon; tone?: Tone; size?: "md" | "lg" }) {
  return (
    <span className={cn("flex shrink-0 items-center justify-center rounded-lg", toneClass[tone], size === "lg" ? "h-13 w-13" : "h-10 w-10")}>
      <Icon className="h-5 w-5" strokeWidth={1.75} />
    </span>
  );
}

export function StatCard({ label, value, hint, icon, tone }: { label: string; value: ReactNode; hint: string; icon: LucideIcon; tone: Tone }) {
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between">
        <p className="mt-2 text-muted-foreground">{label}</p>
        <IconTile icon={icon} tone={tone} />
      </div>
      <p className="mt-5 text-4xl font-semibold">{value}</p>
      <p className="mt-5 text-sm text-muted-foreground">{hint}</p>
    </Card>
  );
}

export function DemoBanner({ text }: { text: string }) {
  return (
    <div className="mb-8 flex flex-wrap items-center justify-between gap-2 rounded-lg bg-primary-soft px-4 py-3 text-sm text-primary">
      <span className="inline-flex items-center gap-2">
        <FlaskConical className="h-4 w-4" /> <span className="font-medium">DEMO WORKSPACE</span> · {text}
      </span>
      <span className="font-medium">Local processing only</span>
    </div>
  );
}

export function OfflineNotice() {
  return (
    <div className="mb-6 flex items-start gap-3 rounded-lg border border-warning/30 bg-warning-soft p-4 text-sm text-warning">
      <WifiOff className="mt-0.5 h-4 w-4 shrink-0" />
      <p>
        The Python backend is not connected ({API_BASE_URL}). You can review this form, but nothing will be submitted
        until the local Flask API is running.
      </p>
    </div>
  );
}

export function ErrorMessage({ children }: { children: ReactNode }) {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive-soft p-4 text-sm text-destructive">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-muted-foreground">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </span>
  );
}

export function EmptyState({ icon: Icon, title, text }: { icon: LucideIcon; title: string; text: string }) {
  return (
    <div className="flex flex-col items-center rounded-lg border border-dashed p-8 text-center">
      <IconTile icon={Icon} tone="neutral" />
      <p className="mt-3 font-medium">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">{text}</p>
    </div>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="text-sm font-medium">{label}</span>
      <div className="mt-1.5">{children}</div>
      {hint && <span className="mt-1.5 block text-xs text-muted-foreground">{hint}</span>}
    </label>
  );
}

export const inputClass =
  "w-full rounded-lg border border-input bg-card px-3.5 py-2.5 text-sm outline-none transition focus:border-ring focus:ring-2 focus:ring-ring/20 disabled:opacity-60";

export function Button({
  variant = "primary",
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "outline" | "ghost" }) {
  return (
    <button
      {...props}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-[15px] font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-primary text-primary-foreground hover:bg-primary/90",
        variant === "outline" && "border bg-card text-foreground hover:bg-accent",
        variant === "ghost" && "text-primary hover:bg-primary-soft",
        className,
      )}
    />
  );
}
