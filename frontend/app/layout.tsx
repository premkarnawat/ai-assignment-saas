// frontend/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "AI Assignment Generator — Handwritten Notebooks",
  description:
    "Generate 95% realistic handwritten assignments & notebooks using AI. Trusted by 50,000+ students.",
  keywords: ["handwritten assignment", "AI notes", "notebook generator", "student tools"],
  openGraph: {
    title: "AI Handwritten Assignment Generator",
    description: "Generate realistic handwritten notebooks with AI",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;600;700&family=Patrick+Hand&family=Indie+Flower&family=Architects+Daughter&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: { borderRadius: "10px", background: "#1e293b", color: "#f1f5f9" },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
