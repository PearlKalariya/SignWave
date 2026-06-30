import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SignWave",
  description: "Accessible meetings with live sign-language and speech transcription",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
