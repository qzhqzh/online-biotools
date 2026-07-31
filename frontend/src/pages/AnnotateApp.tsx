import { useEffect, useMemo, useState } from "react"
import { Loader2 } from "lucide-react"

import { VariantEditor } from "@/components/editors/VariantEditor"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  annotateVariants,
  fetchEngines,
  type EngineInfo,
  type VariantResult,
} from "@/lib/api"

const SAMPLE = "17:43092951 G>A\n13:32906732 G>A"

export default function AnnotateApp() {
  const [engines, setEngines] = useState<EngineInfo[]>([])
  const [engine, setEngine] = useState("vep")
  const [assembly, setAssembly] = useState("GRCh37")
  const [text, setText] = useState(SAMPLE)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<VariantResult[]>([])
  const [rawJson, setRawJson] = useState("")

  useEffect(() => {
    fetchEngines()
      .then((list) => {
        setEngines(list)
        const preferred = list.find((e) => e.ready) || list[0]
        if (preferred) {
          setEngine(preferred.id)
          if (preferred.default_assembly) setAssembly(preferred.default_assembly)
        }
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  const assemblies = useMemo(() => {
    const current = engines.find((e) => e.id === engine)
    return current?.supported_assemblies ?? ["GRCh37", "GRCh38"]
  }, [engines, engine])

  const readyHint = useMemo(() => {
    const current = engines.find((e) => e.id === engine)
    if (!current) return "加载引擎信息中…"
    if (!current.ready) return "引擎未就绪：请挂载/下载对应 cache"
    const ready = current.ready_assemblies.join(", ") || "无"
    return `就绪 assembly：${ready}`
  }, [engines, engine])

  async function onSubmit() {
    const variants = text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
    if (!variants.length) {
      setError("请至少输入一条变异")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await annotateVariants({ engine, assembly, variants })
      setResults(data.results)
      setRawJson(JSON.stringify(data, null, 2))
    } catch (err) {
      setResults([])
      setRawJson("")
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-5 p-6">
      <Card>
        <CardHeader>
          <CardTitle>变异注释</CardTitle>
          <CardDescription>
            Django Template 壳 + React（shadcn/ui + Monaco）。调用{" "}
            <code className="rounded bg-background px-1">POST /api/v1/annotations/</code>
          </CardDescription>
        </CardHeader>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>引擎</Label>
            <Select value={engine} onValueChange={setEngine}>
              <SelectTrigger>
                <SelectValue placeholder="选择引擎" />
              </SelectTrigger>
              <SelectContent>
                {engines.map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.name}
                    {item.ready ? "" : "（未就绪）"}
                  </SelectItem>
                ))}
                <SelectItem value="both">VEP + ANNOVAR</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Assembly</Label>
            <Select value={assembly} onValueChange={setAssembly}>
              <SelectTrigger>
                <SelectValue placeholder="选择 assembly" />
              </SelectTrigger>
              <SelectContent>
                {assemblies.map((item) => (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <p className="mt-3 text-sm text-muted">{readyHint}</p>

        <div className="mt-4 space-y-2">
          <Label>变异输入（每行一条）</Label>
          <VariantEditor value={text} onChange={setText} />
        </div>

        <div className="mt-4 flex items-center gap-3">
          <Button onClick={onSubmit} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            运行注释
          </Button>
          <Button variant="outline" onClick={() => setText(SAMPLE)} disabled={loading}>
            填入样例
          </Button>
        </div>

        {error ? (
          <p className="mt-4 text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : null}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>结果</CardTitle>
          <CardDescription>主字段表格；完整 JSON 可在下方 Monaco 只读查看</CardDescription>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-border text-muted">
                <th className="py-2 pr-3 font-medium">input</th>
                <th className="py-2 pr-3 font-medium">gene</th>
                <th className="py-2 pr-3 font-medium">consequence</th>
                <th className="py-2 pr-3 font-medium">c.</th>
                <th className="py-2 pr-3 font-medium">p.</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr>
                  <td className="py-3 text-muted" colSpan={5}>
                    尚无结果
                  </td>
                </tr>
              ) : (
                results.map((row) => (
                  <tr key={`${row.input}-${row.feature}`} className="border-b border-border">
                    <td className="py-2 pr-3 align-top">{row.input}</td>
                    <td className="py-2 pr-3 align-top">{row.gene ?? "—"}</td>
                    <td className="py-2 pr-3 align-top">{row.consequence ?? "—"}</td>
                    <td className="py-2 pr-3 align-top">{row.cdot ?? "—"}</td>
                    <td className="py-2 pr-3 align-top">{row.protein ?? "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {rawJson ? (
          <div className="mt-4 space-y-2">
            <Label>原始 JSON</Label>
            <VariantEditor
              value={rawJson}
              onChange={() => undefined}
              readOnly
              language="json"
              height="280px"
            />
          </div>
        ) : null}
      </Card>
    </div>
  )
}
