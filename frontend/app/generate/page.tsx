"use client";
// frontend/app/generate/page.tsx
import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import toast from "react-hot-toast";
import {
  Pen, Upload, Loader2, Sparkles, BookOpen,
  ChevronDown, FileText, Image as ImageIcon
} from "lucide-react";
import { assignments, notebook, ocr, pollStatus } from "@/lib/api";

const HANDWRITING_STYLES = [
  { value: "casual",    label: "Casual",     font: "Caveat" },
  { value: "neat",      label: "Neat",       font: "PatrickHand" },
  { value: "indie",     label: "Indie",      font: "IndieFlower" },
  { value: "architect", label: "Architect",  font: "ArchitectsDaughter" },
];

const PAPER_TYPES = [
  { value: "notebook", label: "Blue Ruled Notebook" },
  { value: "exam",     label: "Exam Answer Sheet" },
  { value: "graph",    label: "Graph Paper" },
  { value: "white",    label: "White Sheet" },
];

export default function GeneratePage() {
  const router = useRouter();
  const [mode, setMode] = useState<"single" | "notebook">("single");
  const [question, setQuestion] = useState("");
  const [subject, setSubject] = useState("General");
  const [hwStyle, setHwStyle] = useState("casual");
  const [paperType, setPaperType] = useState("notebook");
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState("");

  // Notebook mode
  const [nbTopic, setNbTopic] = useState("");
  const [nbPages, setNbPages] = useState(5);

  // OCR
  const [extractedText, setExtractedText] = useState("");
  const [isOcr, setIsOcr] = useState(false);

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setIsOcr(true);
    toast.loading("Extracting text from image...", { id: "ocr" });
    try {
      const { data } = await ocr.extract(file);
      setQuestion(data.extracted_text);
      toast.success(`Extracted ${data.char_count} characters`, { id: "ocr" });
    } catch {
      toast.error("OCR failed. Try a clearer image.", { id: "ocr" });
    } finally {
      setIsOcr(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp"] },
    maxFiles: 1,
  });

  const handleGenerate = async () => {
    if (mode === "single" && !question.trim()) {
      toast.error("Please enter a question");
      return;
    }
    if (mode === "notebook" && !nbTopic.trim()) {
      toast.error("Please enter a topic");
      return;
    }

    setIsGenerating(true);
    setProgress(5);
    setProgressLabel("Sending to AI...");

    try {
      let assignmentId: string;

      if (mode === "single") {
        const { data } = await assignments.generate({
          question: question.trim(),
          subject,
          handwriting_style: hwStyle,
          paper_type: paperType,
        });
        assignmentId = data.assignment_id;
      } else {
        const { data } = await notebook.generate({
          subject,
          topic: nbTopic,
          pages: nbPages,
          handwriting_style: hwStyle,
          paper_type: paperType,
          include_diagrams: true,
          include_examples: true,
        });
        assignmentId = data.assignment_id;
      }

      setProgress(20);
      setProgressLabel("AI generating content...");

      await pollStatus(
        assignmentId,
        (status) => {
          if (status === "processing") {
            setProgress((p) => Math.min(p + 10, 85));
            setProgressLabel("Rendering handwriting...");
          }
        }
      );

      setProgress(100);
      setProgressLabel("Done!");
      toast.success("Assignment ready! 🎉");
      router.push(`/preview/${assignmentId}`);

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Generation failed";
      toast.error(msg);
    } finally {
      setIsGenerating(false);
      setProgress(0);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-black text-slate-900 mb-2">
            Generate Assignment
          </h1>
          <p className="text-slate-500">AI-powered → Handwritten PDF in ~30 seconds</p>
        </div>

        {/* Mode Toggle */}
        <div className="card p-1 mb-6 flex">
          {[
            { key: "single",   label: "Single Assignment", icon: <FileText className="w-4 h-4" /> },
            { key: "notebook", label: "Full Notebook",     icon: <BookOpen  className="w-4 h-4" /> },
          ].map((m) => (
            <button
              key={m.key}
              onClick={() => setMode(m.key as "single" | "notebook")}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg
                          text-sm font-semibold transition-all ${
                mode === m.key
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {m.icon} {m.label}
              {m.key === "notebook" && (
                <span className="bg-amber-400 text-amber-900 text-[10px] font-bold px-1.5 py-0.5 rounded-full ml-1">PRO</span>
              )}
            </button>
          ))}
        </div>

        {/* Form */}
        <div className="card p-6 space-y-5">

          {/* Subject */}
          <div>
            <label className="label">Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g. Operating Systems, Physics, History..."
              className="input"
            />
          </div>

          {mode === "single" ? (
            <>
              {/* Question */}
              <div>
                <label className="label">Assignment Question</label>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Enter your assignment question here..."
                  className="input min-h-[120px] resize-y"
                  rows={5}
                />
              </div>

              {/* OCR Upload */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer
                            transition-all ${
                  isDragActive
                    ? "border-blue-400 bg-blue-50"
                    : "border-slate-200 hover:border-blue-300 hover:bg-slate-50"
                }`}
              >
                <input {...getInputProps()} />
                {isOcr ? (
                  <div className="flex items-center justify-center gap-2 text-blue-600">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span className="text-sm">Extracting text...</span>
                  </div>
                ) : (
                  <>
                    <ImageIcon className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-sm text-slate-500">
                      Drop question image here to auto-extract text (OCR)
                    </p>
                  </>
                )}
              </div>
            </>
          ) : (
            <>
              {/* Notebook Topic */}
              <div>
                <label className="label">Topic</label>
                <input
                  type="text"
                  value={nbTopic}
                  onChange={(e) => setNbTopic(e.target.value)}
                  placeholder="e.g. CPU Scheduling, Photosynthesis, World War II..."
                  className="input"
                />
              </div>

              {/* Pages */}
              <div>
                <label className="label">Number of Pages (max 20)</label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min={2} max={20} value={nbPages}
                    onChange={(e) => setNbPages(Number(e.target.value))}
                    className="flex-1"
                  />
                  <span className="bg-blue-100 text-blue-700 font-bold px-3 py-1 rounded-lg text-sm">
                    {nbPages} pages
                  </span>
                </div>
              </div>
            </>
          )}

          {/* Handwriting Style */}
          <div>
            <label className="label">Handwriting Style</label>
            <div className="grid grid-cols-2 gap-2">
              {HANDWRITING_STYLES.map((s) => (
                <button
                  key={s.value}
                  onClick={() => setHwStyle(s.value)}
                  style={{ fontFamily: `'${s.font}', cursive` }}
                  className={`py-3 px-4 rounded-lg border-2 text-left transition-all ${
                    hwStyle === s.value
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-slate-200 hover:border-slate-300 text-slate-700"
                  }`}
                >
                  <span className="text-lg">{s.label}</span>
                  <span className="block text-xs text-slate-400 font-sans">{s.font}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Paper Type */}
          <div>
            <label className="label">Paper Style</label>
            <div className="grid grid-cols-2 gap-2">
              {PAPER_TYPES.map((p) => (
                <button
                  key={p.value}
                  onClick={() => setPaperType(p.value)}
                  className={`py-2.5 px-4 rounded-lg border-2 text-sm text-left transition-all ${
                    paperType === p.value
                      ? "border-blue-500 bg-blue-50 text-blue-700 font-semibold"
                      : "border-slate-200 hover:border-slate-300 text-slate-600"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Progress bar */}
          {isGenerating && (
            <div>
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>{progressLabel}</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-base"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Handwritten {mode === "notebook" ? "Notebook" : "Assignment"}
              </>
            )}
          </button>
        </div>

        {/* Tips */}
        <div className="mt-4 text-center text-sm text-slate-400">
          💡 Tip: More specific questions get better, longer answers
        </div>
      </div>
    </div>
  );
}
