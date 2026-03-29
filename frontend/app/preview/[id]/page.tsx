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
    queryFn:  () => assignments.status(id).then((r) => r.data),
    refetchInterval: (query) => {
      const status = (query.state.data as any)?.status;
      return status === "done" || status === "failed" ? false : 2000;
    },
  });

  const assignment = data as any;

  // ── Download via backend endpoint (correct PDF headers) ──────────────────
  const handleDownload = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token  = localStorage.getItem("access_token");

      const response = await fetch(
        `${apiUrl}/api/v1/assignments/${id}/download`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) throw new Error("Download failed");

      // Convert response to blob and trigger browser download
      const blob = await response.blob();
      const url  = window.URL.createObjectURL(
        new Blob([blob], { type: "application/pdf" })
      );
      const link      = document.createElement("a");
      link.href       = url;
      link.download   = `assignment-${id?.slice(0, 8)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      alert("Download failed. Please try again.");
    }
  };

  const handleShare = async () => {
    const shareUrl = window.location.href;
    if (navigator.share) {
      await navigator.share({ title: "My Handwritten Assignment", url: shareUrl });
    } else {
      navigator.clipboard?.writeText(shareUrl);
      alert("Link copied to clipboard!");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 text-slate-500 hover:text-slate-700 text-sm transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>

          {assignment?.status === "done" && (
            <div className="flex items-center gap-3">
              <button
                onClick={handleShare}
                className="btn-secondary flex items-center gap-2 text-sm"
              >
                <Share2 className="w-4 h-4" /> Share
              </button>
              <button
                onClick={handleDownload}
                className="btn-primary flex items-center gap-2 text-sm"
              >
                <Download className="w-4 h-4" /> Download PDF
              </button>
            </div>
          )}
        </div>

        {/* Processing */}
        {(assignment?.status === "processing" || assignment?.status === "pending") && (
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
        )}

        {/* Failed */}
        {assignment?.status === "failed" && (
          <div className="card p-16 text-center border-red-200">
            <h2 className="text-xl font-bold text-red-600 mb-2">Generation Failed</h2>
            <p className="text-slate-500 text-sm mb-6">
              {assignment.error || "Something went wrong. Please try again."}
            </p>
            <div className="flex items-center justify-center gap-3">
              <Link href="/generate" className="btn-primary">Try Again</Link>
              <button
                onClick={() => refetch()}
                className="btn-secondary flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" /> Refresh
              </button>
            </div>
          </div>
        )}

        {/* Done */}
        {assignment?.status === "done" && (
          <div className="space-y-4">

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Pages",   value: assignment.page_count || "—" },
                { label: "Format",  value: "PDF"             },
                { label: "Quality", value: "95% Realistic"   },
              ].map((s, i) => (
                <div key={i} className="card p-4 text-center">
                  <div className="text-2xl font-black text-slate-900">{s.value}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
                </div>
              ))}
            </div>

            {/* PDF Preview — uses Google Docs viewer for reliable rendering */}
            <div className="card overflow-hidden">
              <div className="border-b border-slate-100 px-4 py-3 flex items-center justify-between">
                <span className="font-semibold text-slate-700 text-sm">PDF Preview</span>
                <span className="text-xs text-slate-400">{assignment.page_count} pages</span>
              </div>

              {assignment.pdf_url && (
                <iframe
                  src={`https://docs.google.com/viewer?url=${encodeURIComponent(assignment.pdf_url)}&embedded=true`}
                  className="w-full"
                  style={{ height: "700px", border: "none" }}
                  title="Assignment PDF Preview"
                />
              )}
            </div>

            {/* Actions */}
            <div className="card p-6">
              <h3 className="font-bold text-slate-800 mb-4">What&apos;s next?</h3>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleDownload}
                  className="btn-primary flex items-center gap-2"
                >
                  <Download className="w-4 h-4" /> Download PDF
                </button>
                <Link href="/generate" className="btn-secondary">
                  Generate Another
                </Link>
                <button
                  onClick={handleShare}
                  className="btn-secondary flex items-center gap-2"
                >
                  <Share2 className="w-4 h-4" /> Share
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
