import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import "./index.css"
import AnnotateApp from "./pages/AnnotateApp"
import HomeApp from "./pages/HomeApp"
import { Toaster } from "@/components/ui/sonner"

function mount(id: string, node: React.ReactNode) {
  const el = document.getElementById(id)
  if (!el) return
  createRoot(el).render(
    <StrictMode>
      {node}
      <Toaster />
    </StrictMode>
  )
}

mount("annotate-root", <AnnotateApp />)
mount("home-root", <HomeApp />)
