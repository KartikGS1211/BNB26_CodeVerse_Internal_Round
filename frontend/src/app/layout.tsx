import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/app-shell";
import { Providers } from "@/components/layout/providers";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"),
  title: "CreatorAi — Your creator operating system",
  description: "Turn one strong idea into scripts, clips, edits, and scheduled content without losing creative control.",
  openGraph: { title: "CreatorAi — Your creator operating system", description: "One idea. Every format. Keep every AI edit in your hands.", images: [{ url: "/og.png", width: 1200, height: 630, alt: "CreatorAi — One idea. Every format." }] },
  twitter: { card: "summary_large_image", title: "CreatorAi — Your creator operating system", description: "One idea. Every format. Keep every AI edit in your hands.", images: ["/og.png"] },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full"><Providers><AppShell>{children}</AppShell></Providers></body>
    </html>
  );
}
