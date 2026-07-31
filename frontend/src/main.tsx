import { StrictMode, type ReactNode } from "react"
import { createRoot } from "react-dom/client"

import "./index.css"
import AnnotateApp from "./pages/AnnotateApp"
import AminoAcidKnowledgeApp from "./pages/AminoAcidKnowledgeApp"
import DocsApp from "./pages/DocsApp"
import EnginesApp from "./pages/EnginesApp"
import GeneKnowledgeApp from "./pages/GeneKnowledgeApp"
import HomeApp from "./pages/HomeApp"
import JobsApp from "./pages/JobsApp"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"

function mount(id: string, node: ReactNode) {
  const el = document.getElementById(id)
  if (!el) return
  createRoot(el).render(
    <StrictMode>
      <TooltipProvider>
        {node}
        <Toaster />
      </TooltipProvider>
    </StrictMode>
  )
}

mount("home-root", <HomeApp />)
mount("annotate-root", <AnnotateApp />)
mount("jobs-root", <JobsApp />)
mount("engines-root", <EnginesApp />)
mount("docs-root", <DocsApp />)
mount("gene-knowledge-root", <GeneKnowledgeApp />)
mount("amino-acid-knowledge-root", <AminoAcidKnowledgeApp />)
