import { useEffect, useState } from "react"
import Editor, { loader, type OnMount } from "@monaco-editor/react"
import type { editor } from "monaco-editor"

import { cn } from "@/lib/utils"

loader.config({
  paths: {
    vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs",
  },
})

const VCF_LANGUAGE_ID = "vcf"

function registerVcfLanguage(monaco: typeof import("monaco-editor")) {
  if (monaco.languages.getLanguages().some((l) => l.id === VCF_LANGUAGE_ID)) {
    return
  }
  monaco.languages.register({ id: VCF_LANGUAGE_ID })
  monaco.languages.setMonarchTokensProvider(VCF_LANGUAGE_ID, {
    tokenizer: {
      root: [
        [/^##.*$/, "comment"],
        [/^#CHROM.*$/, "keyword"],
        [/chr[0-9XYM]+|[0-9]+/, "number"],
        [/\t/, "white"],
      ],
    },
  })
}

type VariantEditorProps = {
  value: string
  onChange: (value: string) => void
  readOnly?: boolean
  language?: "vcf" | "json" | "plaintext"
  height?: string
  className?: string
}

export function VariantEditor({
  value,
  onChange,
  readOnly = false,
  language = "vcf",
  height = "320px",
  className,
}: VariantEditorProps) {
  const [ready, setReady] = useState(false)

  useEffect(() => {
    void loader.init().then(() => setReady(true))
  }, [])

  const handleMount: OnMount = (_editor, monaco) => {
    registerVcfLanguage(monaco)
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-md border border-input bg-background shadow-xs",
        className
      )}
    >
      {!ready ? (
        <div
          className="flex items-center justify-center bg-muted/40 text-sm text-muted-foreground"
          style={{ height }}
        >
          正在加载 Monaco Editor…
        </div>
      ) : null}
      <Editor
        height={height}
        defaultLanguage={language === "vcf" ? VCF_LANGUAGE_ID : language}
        language={language === "vcf" ? VCF_LANGUAGE_ID : language}
        value={value}
        theme="vs"
        loading={
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            正在加载 Monaco Editor…
          </div>
        }
        options={
          {
            readOnly,
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            wordWrap: "on",
            automaticLayout: true,
            renderLineHighlight: "line",
            tabSize: 4,
            insertSpaces: false,
            padding: { top: 8, bottom: 8 },
          } satisfies editor.IStandaloneEditorConstructionOptions
        }
        onMount={handleMount}
        onChange={(v) => onChange(v ?? "")}
      />
    </div>
  )
}
