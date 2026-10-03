"use client";
import { CheckCircle2, Info, Sparkles, X } from "lucide-react";
import { createContext, useContext, useState } from "react";
type Toast = { id: number; message: string };
const ToastContext = createContext<(message: string) => void>(() => undefined);
export function ToastProvider({ children }: { children: React.ReactNode }) { const [toasts,setToasts] = useState<Toast[]>([]); const toast = (message:string) => { const id=Date.now(); setToasts(t=>[...t,{id,message}]); setTimeout(()=>setToasts(t=>t.filter(x=>x.id!==id)),2600); }; return <ToastContext.Provider value={toast}>{children}<div className="toast-stack">{toasts.map(t=><div className="toast" key={t.id}><CheckCircle2 size={17}/>{t.message}</div>)}</div></ToastContext.Provider>; }
export const useToast = () => useContext(ToastContext);
export function PageIntro({ eyebrow, title, copy, action }: { eyebrow?: string; title: string; copy: string; action?: React.ReactNode }) { return <div className="page-intro"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h1>{title}</h1><p>{copy}</p></div>{action}</div>; }
export function AiBadge({ children = "AI powered" }: { children?: React.ReactNode }) { return <span className="ai-badge"><Sparkles size={12}/>{children}</span>; }
export function ExplainPopover({ reasons }: { reasons: string[] }) { const [open,setOpen]=useState(false); return <div className="explain-wrap"><button className="ghost-button" onClick={()=>setOpen(!open)}><Info size={15}/> Explain this clip</button>{open&&<div className="explain-pop"><button onClick={()=>setOpen(false)} aria-label="Close"><X size={14}/></button><strong>Why the AI chose this</strong><p>The clip balances retention signals with a complete, useful thought.</p><ul>{reasons.map(r=><li key={r}>{r}</li>)}</ul></div>}</div>; }
