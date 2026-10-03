"use client";
import { useState } from "react";
import { DndContext, DragEndEvent, DragOverlay, PointerSensor, useDraggable, useDroppable, useSensor, useSensors } from "@dnd-kit/core";
import { Calendar, GripVertical, Plus } from "lucide-react";
import { workflowCards as seed } from "@/mocks/demo";
import type { WorkflowCard } from "@/types";
import { api } from "@/lib/api";
import { useToast } from "@/components/shared/ui";
const cols:WorkflowCard["column"][]=["Idea","Script","Recorded","Editing","Scheduled","Published"];
function Card({card}:{card:WorkflowCard}){const {setNodeRef,listeners,attributes,transform,isDragging}=useDraggable({id:card.id,data:{card}});return <article ref={setNodeRef} {...listeners} {...attributes} style={{transform:transform?`translate3d(${transform.x}px,${transform.y}px,0)`:undefined,opacity:isDragging?.35:1}}><div><span>{card.platform}</span><GripVertical/></div><strong>{card.title}</strong><small><Calendar/> {card.dueDate}</small></article>}
function Column({name,cards}:{name:WorkflowCard["column"];cards:WorkflowCard[]}){const {setNodeRef,isOver}=useDroppable({id:name});return <section className={`kanban-column ${isOver?"over":""}`} ref={setNodeRef}><header><span><i className={`dot-${cols.indexOf(name)}`}/>{name}</span><em>{cards.length}</em></header><div>{cards.map(c=><Card card={c} key={c.id}/>)}</div><button><Plus/> Add card</button></section>}
export function KanbanBoard(){const [cards,setCards]=useState(seed);const [active,setActive]=useState<WorkflowCard|null>(null);const toast=useToast();const sensors=useSensors(useSensor(PointerSensor,{activationConstraint:{distance:6}}));const end=async(e:DragEndEvent)=>{setActive(null);if(!e.over)return;const column=e.over.id as WorkflowCard["column"];const card=cards.find(c=>c.id===e.active.id);if(!card||!cols.includes(column)||card.column===column)return;const changed={...card,column};setCards(v=>v.map(c=>c.id===card.id?changed:c));await api.updateWorkflow(changed);toast(`Moved to ${column}`)};return <DndContext sensors={sensors} onDragStart={e=>setActive(cards.find(c=>c.id===e.active.id)??null)} onDragEnd={e=>void end(e)}><div className="kanban-board">{cols.map(c=><Column key={c} name={c} cards={cards.filter(x=>x.column===c)}/>)}</div><DragOverlay>{active&&<div className="drag-card">{active.title}</div>}</DragOverlay></DndContext>}
