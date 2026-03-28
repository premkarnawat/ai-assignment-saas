"use client";
// frontend/app/preview/[id]/page.tsx
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { assignments } from "@/lib/api";
import { Download, ArrowLeft, Share2, RefreshCw, Loader2 } from "lucide-react";

export default function PreviewPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["assignment-status", id],
    queryFn: () => assignments.status(id).then((r) => r.data),

    // ✅ FIXED (React Query v5)
    refetchInterval: (query) => {
      const status = (query.state.data as any)?.status;
      return status === "done" || status === "failed" ? false : 2000;
    },
  });

  const handleShare = async () => {
    if (navigator.share && (data as any)?.pdf_url) {
      await navigator.share({
        title: "My Handwritten Assignment",
        url: (data as any).pdf_url,
      });
    } else {
      navigator.clipboard?.writeText((data as any)?.pdf_url || window.location.href);
      alert("Link copied!");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const assignment = data as any;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Link href="/dashboard" className="flex items-center gap-2 text-slate-500
                                             hover:text-slate-700 text-sm transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>

          <div className="flex items-center gap-3">
            {assignment?.status === "done" && (
              <>
                <button
                  onClick={handleShare}
                  className="btn-secondary flex items-center gap-2 text-sm"
                >
                  <Share2 className="w-4 h-4" /> Share
                </button>
                <a
                  href={assignment.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary flex items-center gap-2 text-sm"
                >
                  <Download className="w-4 h-4" /> Download PDF
                </a>
              </>
            )}
          </div>
        </div>

        {/* Status states */}
        {assignment?.status === "processing" || assignment?.status === "pending" ? (
          <div className="card p-16 text-center">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            </div>
            <h2 className="text-xl font-bold text-slate-800 mb-2">
              Rendering Your Handwriting...
            </h2>
            <p className="text-slate-500 text-sm max-w-sm mx-auto">
              AI is generating content and rendering realistic handwriting.
              This takes 15–30 seconds.
            </p>
          </div>
        ) : assignment?.status === "failed" ? (
          <div className="card p-16 text-center border-red-200">
            <h2 className="text-xl font-bold text-red-600 mb-2">Generation Failed</h2>
            <p className="text-slate-500 text-sm mb-6">
              {assignment.error || "Something went wrong"}
            </p>
            <div className="flex items-center justify-center gap-3">
              <Link href="/generate" className="btn-primary">Try Again</Link>
              <button onClick={() => refetch()} className="btn-secondary flex items-center gap-2">
                <RefreshCw className="w-4 h-4" /> Refresh
              </button>
            </div>
          </div>
        ) : assignment?.status === "done" ? (
          <div className="space-y-4">

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Pages", value: assignment.page_count || "—" },
                { label: "Format", value: "PDF" },
                { label: "Quality", value: "95% Realistic" },
              ].map((s, i) => (
                <div key={i} className="card p-4 text-center">
                  <div className="text-2xl font-black text-slate-900">{s.value}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
                </div>
              ))}
            </div>

            {/* PDF Preview */}
            <div className="card overflow-hidden">
              <div className="border-b border-slate-100 px-4 py-3 flex items-center justify-between">
                <span className="font-semibold text-slate-700 text-sm">PDF Preview</span>
                <span className="text-xs text-slate-400">{assignment.page_count} pages</span>
              </div>
              {typeof assignment.pdf_url === "string" && (
                <iframe
                  src={assignment.pdf_url}
                  className="w-full"
                  style={{ height: "700px", border: "none" }}
                  title="Assignment PDF"
                />
              )}
            </div>

            {/* Actions */}
            <div className="card p-6">
              <h3 className="font-bold text-slate-800 mb-4">What&apos;s next?</h3>
              <div className="flex flex-wrap gap-3">
                <a
                  href={assignment.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary flex items-center gap-2"
                >
                  <Download className="w-4 h-4" /> Download PDF
                </a>
                <Link href="/generate" className="btn-secondary">
                  Generate Another
                </Link>
                <button onClick={handleShare} className="btn-secondary flex items-center gap-2">
                  <Share2 className="w-4 h-4" /> Share with Friends
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
