// frontend/app/page.tsx
import Link from "next/link";
import { ArrowRight, Pen, BookOpen, Zap, Star, CheckCircle } from "lucide-react";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-white overflow-hidden">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <Pen className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-lg">WriteAI</span>
        </div>
        <div className="hidden md:flex items-center gap-6 text-sm text-slate-400">
          <Link href="#features" className="hover:text-white transition-colors">Features</Link>
          <Link href="#pricing" className="hover:text-white transition-colors">Pricing</Link>
          <Link href="/login" className="hover:text-white transition-colors">Login</Link>
        </div>
        <Link
          href="/register"
          className="bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold
                     px-4 py-2 rounded-lg transition-colors"
        >
          Get Started Free
        </Link>
      </nav>

      {/* Hero */}
      <section className="text-center px-6 py-20 max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20
                        rounded-full px-4 py-1.5 text-blue-400 text-sm mb-8">
          <Star className="w-3.5 h-3.5" />
          Trusted by 50,000+ students
        </div>

        <h1 className="text-5xl md:text-7xl font-black mb-6 leading-tight">
          Your AI
          <span className="block bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
            Handwriting Engine
          </span>
        </h1>

        <p className="text-slate-400 text-xl mb-10 max-w-2xl mx-auto leading-relaxed">
          Enter any question. Get a complete, realistic handwritten notebook assignment in seconds.
          95% human-like handwriting. Zero effort.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/register"
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white
                       font-bold px-8 py-4 rounded-xl text-lg transition-all
                       hover:scale-105 shadow-lg shadow-blue-500/25"
          >
            Generate Free Assignment <ArrowRight className="w-5 h-5" />
          </Link>
          <Link
            href="/demo"
            className="flex items-center gap-2 border border-slate-700 hover:border-slate-500
                       text-slate-300 font-semibold px-8 py-4 rounded-xl text-lg transition-all"
          >
            Watch Demo
          </Link>
        </div>

        {/* Notebook preview mockup */}
        <div className="mt-16 relative">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-2 shadow-2xl max-w-2xl mx-auto">
            <div className="notebook-bg rounded-xl p-6 text-left min-h-64">
              <div className="text-slate-400 text-xs mb-3 flex justify-between">
                <span>Subject: Operating Systems</span>
                <span>Date: 11/03/2026</span>
              </div>
              {/* Animated typing effect lines */}
              <div className="space-y-2 font-['Caveat',cursive] text-slate-700 text-xl">
                <p className="border-b border-slate-300 pb-1">CPU Scheduling</p>
                <p className="border-b border-slate-300/60 pb-1 text-slate-500">
                  CPU scheduling is the process by which the OS decides
                </p>
                <p className="border-b border-slate-300/60 pb-1 text-slate-500">
                  which process runs on the processor at a given time.
                </p>
                <p className="border-b border-slate-300/60 pb-1">
                  1. First Come First Serve (FCFS)
                </p>
                <p className="border-b border-slate-300/60 pb-1">
                  2. Shortest Job First (SJF)
                </p>
                <p className="border-b border-slate-300/60 pb-1">
                  3. Round Robin (RR){" "}
                  <span className="writing-cursor text-blue-600">|</span>
                </p>
              </div>
            </div>
          </div>

          {/* Floating badge */}
          <div className="absolute -top-4 -right-4 bg-green-500 text-white text-xs font-bold
                          px-3 py-1.5 rounded-full shadow-lg hidden md:block">
            95% Realistic ✓
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 py-20 max-w-6xl mx-auto">
        <h2 className="text-3xl font-black text-center mb-12">
          Everything you need
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: <Pen className="w-6 h-6" />,
              title: "95% Realistic Handwriting",
              desc: "Per-character variation, ink simulation, baseline drift, and human imperfections. Not just a font.",
              color: "blue",
            },
            {
              icon: <BookOpen className="w-6 h-6" />,
              title: "Full Notebook Generator",
              desc: "Enter subject + topic + pages. Get a complete handwritten notebook. This is the viral feature.",
              color: "violet",
            },
            {
              icon: <Zap className="w-6 h-6" />,
              title: "30-Second Generation",
              desc: "Groq LLaMA3 70B generates structured content. Async Celery workers render PDFs in background.",
              color: "amber",
            },
          ].map((f, i) => (
            <div key={i} className="card p-6 bg-slate-900 border-slate-800">
              <div className={`w-12 h-12 rounded-xl bg-${f.color}-500/10 flex items-center
                              justify-center text-${f.color}-400 mb-4`}>
                {f.icon}
              </div>
              <h3 className="font-bold text-lg mb-2">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="px-6 py-20 max-w-4xl mx-auto">
        <h2 className="text-3xl font-black text-center mb-12">Simple Pricing</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {/* Free */}
          <div className="card bg-slate-900 border-slate-800 p-8">
            <div className="text-slate-400 font-semibold mb-2">FREE</div>
            <div className="text-4xl font-black mb-6">₹0 <span className="text-slate-500 text-lg font-normal">/mo</span></div>
            <ul className="space-y-3 mb-8">
              {["3 assignments/day", "Basic handwriting styles", "Standard notebook", "Watermarked PDF"].map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-slate-300 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" /> {f}
                </li>
              ))}
            </ul>
            <Link href="/register" className="btn-secondary w-full text-center block">
              Start Free
            </Link>
          </div>

          {/* Pro */}
          <div className="card bg-blue-600 border-blue-500 p-8 relative">
            <div className="absolute -top-3 right-6 bg-amber-400 text-amber-900 text-xs font-bold
                            px-3 py-1 rounded-full">
              MOST POPULAR
            </div>
            <div className="text-blue-100 font-semibold mb-2">STUDENT PRO</div>
            <div className="text-4xl font-black text-white mb-6">
              ₹99 <span className="text-blue-200 text-lg font-normal">/mo</span>
            </div>
            <ul className="space-y-3 mb-8">
              {[
                "Unlimited assignments",
                "All handwriting fonts",
                "6 paper styles",
                "Full Notebook Generator",
                "No watermark",
                "Priority processing",
              ].map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-white text-sm">
                  <CheckCircle className="w-4 h-4 text-blue-200" /> {f}
                </li>
              ))}
            </ul>
            <Link href="/register" className="bg-white text-blue-600 font-bold px-5 py-2.5
                                              rounded-lg w-full text-center block hover:bg-blue-50
                                              transition-colors">
              Get Pro
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 px-6 py-8 text-center text-slate-500 text-sm">
        <p>© 2026 WriteAI. Built with ❤️ for students everywhere.</p>
      </footer>
    </main>
  );
}
