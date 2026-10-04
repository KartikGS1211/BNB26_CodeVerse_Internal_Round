"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Sparkles } from "lucide-react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = isRegister
        ? await api.register(email, password, name)
        : await api.login(email, password);
      localStorage.setItem("token", res.token);
      localStorage.setItem("user", JSON.stringify(res.user));
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "grid", placeItems: "center", minHeight: "100vh", background: "#0c0e19" }}>
      <form onSubmit={submit} style={{ background: "#111425", border: "1px solid #22263a", borderRadius: 16, padding: 32, width: 360, display: "grid", gap: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <Sparkles size={20} color="#8b5cf6" />
          <h1 style={{ fontSize: 20, fontWeight: 700, color: "#fff" }}>CreatorAi</h1>
        </div>
        <p style={{ color: "#788096", fontSize: 13, marginTop: -8 }}>{isRegister ? "Create your account" : "Sign in to your studio"}</p>
        {isRegister && <input value={name} onChange={e => setName(e.target.value)} placeholder="Your name" style={inputStyle} />}
        <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" type="email" required style={inputStyle} />
        <input value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" type="password" required style={inputStyle} />
        {error && <p style={{ color: "#f87171", fontSize: 12 }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ background: "#7657dd", color: "#fff", border: 0, borderRadius: 8, padding: "10px 16px", fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
          {loading && <Loader2 size={16} className="animate-spin" />}
          {isRegister ? "Create account" : "Sign in"}
        </button>
        <button type="button" onClick={() => setIsRegister(!isRegister)} style={{ background: "none", border: 0, color: "#7657dd", cursor: "pointer", fontSize: 13 }}>
          {isRegister ? "Already have an account? Sign in" : "Need an account? Register"}
        </button>
      </form>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  background: "#0c0e19",
  border: "1px solid #22263a",
  borderRadius: 8,
  padding: "10px 12px",
  color: "#fff",
  fontSize: 14,
  outline: "none",
};
