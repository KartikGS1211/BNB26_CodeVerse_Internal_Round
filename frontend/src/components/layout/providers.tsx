"use client";
import { ToastProvider } from "@/components/shared/ui";
export function Providers({ children }: { children: React.ReactNode }) { return <ToastProvider>{children}</ToastProvider>; }
