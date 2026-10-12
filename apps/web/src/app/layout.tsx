import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StudyGraph",
  description:
    "A source-grounded, misconception-aware AI study companion.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
