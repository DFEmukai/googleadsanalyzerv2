import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

export const metadata: Metadata = {
  title: "Google Ads AI Agent",
  description: "Google Ads analysis and improvement proposal dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja" className="dark" suppressHydrationWarning>
      <body className="bg-background text-white antialiased" suppressHydrationWarning>
        <Sidebar />
        <div className="ml-60">
          <Header />
          <main className="p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
