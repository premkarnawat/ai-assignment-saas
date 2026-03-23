"use client";
// frontend/app/register/page.tsx
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";
import { Pen, Loader2 } from "lucide-react";
import { auth } from "@/lib/api";
import { useAuthStore } from "@/lib/store";

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    try {
      const { data } = await auth.register(form);
      setAuth(data.user, data.access_token, data.refresh_token);
      toast.success("Account created! Welcome 🎉");
      router.push("/generate");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail || "Registration failed";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Pen className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-black text-white">Create your account</h1>
          <p className="text-slate-400 text-sm mt-1">Free forever. No credit card needed.</p>
        </div>

        <div className="card bg-slate-900 border-slate-800 p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label text-slate-300">Full Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="John Doe"
                required
                className="input bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
              />
            </div>
            <div>
              <label className="label text-slate-300">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@example.com"
                required
                className="input bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
              />
            </div>
            <div>
              <label className="label text-slate-300">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="Min 6 characters"
                required
                minLength={6}
                className="input bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 py-3"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Create Free Account
            </button>
          </form>

          <p className="text-center text-slate-400 text-sm mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-blue-400 hover:text-blue-300 font-semibold">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
