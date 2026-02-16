"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Megaphone,
  FileText,
  Lightbulb,
} from "lucide-react";

const navItems = [
  {
    label: "ダッシュボード",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "キャンペーン",
    href: "/campaigns",
    icon: Megaphone,
  },
  {
    label: "週次レポート",
    href: "/reports",
    icon: FileText,
  },
  {
    label: "改善提案",
    href: "/proposals",
    icon: Lightbulb,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-60 border-r border-border bg-background">
      <div className="flex h-16 items-center border-b border-border px-6">
        <h1 className="text-lg font-bold text-white">
          <span className="text-signal-blue">GA</span> AI Agent
        </h1>
      </div>
      <nav className="mt-4 space-y-1 px-3">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-signal-blue/10 text-signal-blue"
                  : "text-muted-foreground hover:bg-card-hover hover:text-white"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
