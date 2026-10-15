import {
  LayoutGrid,
  UserPlus,
  Database,
  Cpu,
  FileSignature,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  to: "/" | "/register" | "/train-cedar" | "/train-user" | "/verify-cedar" | "/verify-user";
  label: string;
  subtitle: string;
  icon: LucideIcon;
}

export const NAV: NavItem[] = [
  { to: "/", label: "Dashboard", subtitle: "System overview and recent verification activity", icon: LayoutGrid },
  { to: "/register", label: "Register User", subtitle: "Enrol a new identity with genuine reference signatures", icon: UserPlus },
  { to: "/train-cedar", label: "Train CEDAR Model", subtitle: "Train a writer-dependent benchmark classifier", icon: Database },
  { to: "/train-user", label: "Train User Model", subtitle: "Train a classifier for a registered identity", icon: Cpu },
  { to: "/verify-cedar", label: "Verify CEDAR Signature", subtitle: "Check a signature against a CEDAR writer model", icon: FileSignature },
  { to: "/verify-user", label: "Verify User Signature", subtitle: "Check a signature against a registered user model", icon: ShieldCheck },
];
