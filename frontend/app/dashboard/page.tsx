"use client";
// frontend/app/dashboard/page.tsx
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { assignments, users } from "@/lib/api";
import {
  Plus, FileText, Download, Trash2, Clock,
  CheckCircle, AlertCircle, Zap, BookOpen
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    done:       { color: "text-green-600 bg-green-50  border-green-200", icon: <CheckCircle className="w-3.5 h-3.5" />, label: "Done" },
    processing: { color: "text-blue-600  bg-blue-50   border-blue-200",  icon: <Clock className="w-3.5 h-3.5 animate-spin" />, label: "Processing" },
    pending:    { color: "text-amber-600 bg-amber-50  border-amber-200", icon: <Clock className="w-3.5 h-3.5" />, label: "Pending" },
    failed:     { color: "text-red-600   bg-red-50    border-red-200",   icon: <AlertCircle className="w-3.5 h-3.5" />, label: "Failed" },
  };
  const s = map[status] || map.pending;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs
                      font-semibold border ${s.color}`}>
      {s.icon} {s.label}
    </span>
  );
}

export default function DashboardPage() {
  const { data: statsData } = useQuery({
    queryKey: ["stats"],
    queryFn: () => users.stats().then((r) => r.data),
    refetchInterval: 30000,
  });

  const { data: listData, isLoading, refetch } = useQuery({
    queryKey: ["assignments"],
    queryFn: () => assignments.list(1, 20).then((r) => r.data),
    refetchInterval: 5000,
  });

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this assignment?")) return;
    await assignments.delete(id);
    refetch();
  };

  const stats = statsData || { total_assignments: 0, today_usage: 0, daily_limit: 3, remaining: 3, tier: "free" };
  const list = listData || [];

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black text-slate-900">My Assignments</h1>
            <p className="text-slate-500 text-sm mt-0.5">Manage your generated notebooks</p>
          </div>
          <Link href="/generate" className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Assignment
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Generated", value: stats.total_assignments, icon: <FileText className="w-5 h-5" />, color: "blue" },
            { label: "Today's Usage",   value: `${stats.today_usage}/${stats.daily_limit}`, icon: <Zap className="w-5 h-5" />, color: "amber" },
            { label: "Remaining Today", value: stats.remaining, icon: <BookOpen className="w-5 h-5" />, color: "green" },
            { label: "Plan",            value: stats.tier.charAt(0).toUpperCase() + stats.tier.slice(1), icon: <CheckCircle className="w-5 h-5" />, color: "violet" },
          ].map((s, i) => (
            <div key={i} className="card p-4">
              <div className={`text-${s.color}-500 mb-2`}>{s.icon}</div>
              <div className="text-2xl font-black text-slate-900">{s.value}</div>
              <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Usage bar (free tier) */}
        {stats.tier === "free" && (
          <div className="card p-4 mb-6 flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="font-semibold text-slate-700">Daily limit</span>
                <span className="text-slate-500">{stats.today_usage}/{stats.daily_limit}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${(stats.today_usage / stats.daily_limit) * 100}%` }}
                />
              </div>
            </div>
            <Link href="/pricing" className="btn-primary text-sm whitespace-nowrap">
              Upgrade →
            </Link>
          </div>
        )}

        {/* Assignment list */}
        {isLoading ? (
          <div className="text-center py-16 text-slate-400">Loading...</div>
        ) : list.length === 0 ? (
          <div className="card p-16 text-center">
            <FileText className="w-12 h-12 text-slate-200 mx-auto mb-4" />
            <h3 className="font-bold text-slate-700 mb-2">No assignments yet</h3>
            <p className="text-slate-400 text-sm mb-6">Generate your first handwritten assignment</p>
            <Link href="/generate" className="btn-primary inline-flex items-center gap-2">
              <Plus className="w-4 h-4" /> Generate Now
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {list.map((a: Record<string, unknown>) => (
              <div key={a.id as string} className="card p-4 flex items-center gap-4 hover:shadow-md transition-shadow">
                {/* Icon */}
                <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-blue-500" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-800 truncate text-sm">
                    {(a.question as string).slice(0, 80)}...
                  </p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-slate-400">
                      {formatDistanceToNow(new Date(a.created_at as string), { addSuffix: true })}
                    </span>
                    {(a.page_count as number) > 0 && (
                      <span className="text-xs text-slate-400">{a.page_count as number} pages</span>
                    )}
                  </div>
                </div>

                {/* Status */}
                <StatusBadge status={a.status as string} />

                {/* Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  {a.status === "done" && a.pdf_url && (
                    <>
                      <Link
                        href={`/preview/${a.id}`}
                        className="btn-secondary text-xs py-1.5 px-3"
                      >
                        View
                      </Link>
                      <a
                        href={a.pdf_url as string}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
                      >
                        <Download className="w-3.5 h-3.5" /> PDF
                      </a>
                    </>
                  )}
                  <button
                    onClick={() => handleDelete(a.id as string)}
                    className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg
                               hover:bg-red-50 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
