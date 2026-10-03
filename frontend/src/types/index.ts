export type AssetType = "video" | "image" | "audio";
export interface Asset { id: string; name: string; type: AssetType; src: string; thumbnail?: string; duration?: number; tags: string[]; createdAt: string }
export interface Project { id: string; title: string; status: string; updatedAt: string; thumbnail?: string; progress: number }
export interface ScriptLine { id: string; text: string; order: number }
export interface Script { id: string; projectId: string; title: string; lines: ScriptLine[]; topic: string; niche: string; tone: string; platform: string }
export interface TranscriptWord { word: string; start: number; end: number }
export interface Mapping { scriptLineId: string; start: number; end: number; confidence: number }
export interface Clip { id: string; title: string; start: number; end: number; score: number; reasons: string[]; hook: string; platformCaptions: Record<string, string> }
export type Aspect = "9:16" | "1:1" | "16:9";
export interface TrackItem { id: string; start: number; end: number; text?: string; src?: string; style?: Record<string, string | number | boolean> }
export interface Track { type: "video" | "caption" | "music"; items: TrackItem[] }
export interface Timeline { id: string; clipId: string; aspect: Aspect; tracks: Track[] }
export interface WorkflowCard { id: string; title: string; column: "Idea" | "Script" | "Recorded" | "Editing" | "Scheduled" | "Published"; platform: string; dueDate: string; owner?: string }
export interface InsightMetric { id: string; label: string; value: number; change: number; unit?: string }
export interface HookVariant { id: string; text: string; score: number }
export interface TranscriptMoment { text: string; start: number; end: number; assetId: string }
export interface ScheduledPost { id: string; clipId: string; clipTitle: string; platform: string; scheduledAt: string; status: "scheduled" | "published" }
