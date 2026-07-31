import Editor from "@monaco-editor/react"

type VariantEditorProps = {
  value: string
  onChange: (value: string) => void
  readOnly?: boolean
  language?: string
  height?: string
}

export function VariantEditor({
  value,
  onChange,
  readOnly = false,
  language = "plaintext",
  height = "220px",
}: VariantEditorProps) {
  return (
    <div className="overflow-hidden rounded-md border border-border">
      <Editor
        height={height}
        language={language}
        value={value}
        theme="vs"
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          wordWrap: "on",
          automaticLayout: true,
        }}
        onChange={(v) => onChange(v ?? "")}
      />
    </div>
  )
}
