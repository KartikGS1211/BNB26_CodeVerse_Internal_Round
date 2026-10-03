import { StudioWorkspace } from "@/components/studio/studio-workspace";
export default async function StudioPage({params}:{params:Promise<{projectId:string}>}){const {projectId}=await params;return <StudioWorkspace projectId={projectId}/>}
