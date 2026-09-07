import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NahaLabs Video Factory — Content OS",
  description:
    "Open-source video content factory: topic → research → script → visuals → narration → captions → quality-gated vertical video. Part of the NahaLabs Content OS.",
  keywords: ["NahaLabs", "Content OS", "Video Factory", "AI video", "UGC ads", "short-form video"],
  authors: [{ name: "NahaLabs" }],
  openGraph: {
    title: "NahaLabs Video Factory",
    description: "Topic in. Video out. — open-source content pipeline",
    siteName: "NahaLabs",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
