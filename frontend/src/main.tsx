import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import "./index.css"
import AnnotateApp from "./pages/AnnotateApp"

const el = document.getElementById("annotate-root")
if (el) {
  createRoot(el).render(
    <StrictMode>
      <AnnotateApp />
    </StrictMode>
  )
}
