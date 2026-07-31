import { useEffect, useMemo, useState } from "react"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"

import { VariantEditor } from "@/components/editors/VariantEditor"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { AppShell } from "@/layouts/AppShell"
import {
  annotateVariants,
  fetchEngines,
  getApiKey,
  setApiKey,
  type EngineInfo,
  type VariantResult,
} from "@/lib/api"

const SAMPLE_LINES = "17:43092951 G>A\n13:32906732 G>A"

const SAMPLE_VCF = `##fileformat=VCFv4.2
##reference=GRCh38
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
17\t43092951\t.\tG\tA\t.\t.\t.
13\t32906732\t.\tG\tA\t.\t.\t.`

export default function AnnotateApp() {
  const [engines, setEngines] = useState<EngineInfo[]>([])
  const [engine, setEngine] = useState("vep")
  const [assembly, setAssembly] = useState("GRCh37")
  const [text, setText] = useState(SAMPLE_LINES)
  const [apiKey, setApiKeyState] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<VariantResult[]>([])
  const [rawJson, setRawJson] = useState("")

  useEffect(() => {
    setApiKeyState(getApiKey())
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

  const currentEngine = engines.find((e) => e.id === engine)

  async function onSubmit() {
    const variants = text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("##") && !line.startsWith("#CHROM"))
      .map((line) => {
        const parts = line.split(/\t+|\s+/)
        if (
          parts.length >= 5 &&
          /^(?:chr)?(?:\d+|X|Y|MT)$/i.test(parts[0]) &&
          /^\d+$/.test(parts[1])
        ) {
          const chrom = parts[0].replace(/^chr/i, "")
          return `${chrom}:${parts[1]} ${parts[3]}>${parts[4]}`
        }
        return line
      })

    if (!variants.length) {
      setError("请至少输入一条变异或 VCF 记录")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await annotateVariants({ engine, assembly, variants })
      setResults(data.results)
      setRawJson(JSON.stringify(data, null, 2))
      toast.success(`完成：${data.results.length} 条结果`)
    } catch (err) {
      setResults([])
      setRawJson("")
      const message = err instanceof Error ? err.message : String(err)
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      title="变异注释"
      description="左侧选择引擎与基因组版本，右侧用 Monaco 编辑 VCF / 变异后提交。"
      crumbs={[
        { label: "工具", href: "/tools/annotate/" },
        { label: "变异注释" },
      ]}
      actions={
        <>
          <Badge variant={currentEngine?.ready ? "default" : "secondary"}>
            {currentEngine ? currentEngine.name : "加载中"}
          </Badge>
          <Badge variant="outline">{assembly}</Badge>
        </>
      }
    >
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">API Key（生产环境）</CardTitle>
          <CardDescription>
            当服务配置了 <code>BIOTOOLS_API_KEYS</code> 时，注释请求需携带{" "}
            <code>X-API-Key</code>。密钥仅保存在本机浏览器 localStorage。
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="w-full space-y-2 sm:max-w-md">
            <Label htmlFor="api-key">X-API-Key</Label>
            <Input
              id="api-key"
              type="password"
              autoComplete="off"
              placeholder="可选：未配置服务端密钥时可留空"
              value={apiKey}
              onChange={(e) => setApiKeyState(e.target.value)}
            />
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setApiKey(apiKey.trim())
              toast.success(apiKey.trim() ? "API Key 已保存到本机" : "已清除本机 API Key")
            }}
          >
            保存
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle>输入与运行</CardTitle>
            <CardDescription>
              Monaco Editor 用于 VCF 片段或逐行变异；提交时自动抽取数据行。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="engine">引擎</Label>
                <Select value={engine} onValueChange={setEngine}>
                  <SelectTrigger id="engine" className="w-full">
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
                <Label htmlFor="assembly">Assembly</Label>
                <Select value={assembly} onValueChange={setAssembly}>
                  <SelectTrigger id="assembly" className="w-full">
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

            <p className="text-sm text-muted-foreground">
              {currentEngine
                ? currentEngine.ready
                  ? `就绪 assembly：${currentEngine.ready_assemblies.join(", ") || "无"}`
                  : "引擎未就绪：请挂载/下载对应 cache 或数据库"
                : "加载引擎信息中…"}
            </p>

            <Separator />

            <div className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Label>VCF / 变异输入（Monaco Editor）</Label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setText(SAMPLE_LINES)}
                    disabled={loading}
                  >
                    简行样例
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setText(SAMPLE_VCF)}
                    disabled={loading}
                  >
                    VCF 样例
                  </Button>
                </div>
              </div>
              <VariantEditor
                value={text}
                onChange={setText}
                language="vcf"
                height="420px"
              />
              <p className="text-xs text-muted-foreground">
                支持 <code>17:43092951 G&gt;A</code>，或含 <code>#CHROM</code> 的 VCF 正文。
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button onClick={onSubmit} disabled={loading}>
                {loading ? <Loader2 className="size-4 animate-spin" /> : null}
                运行注释
              </Button>
            </div>

            {error ? (
              <Alert variant="destructive">
                <AlertTitle>请求失败</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>结果</CardTitle>
            <CardDescription>表格主字段 + Monaco JSON 只读面板</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>input</TableHead>
                    <TableHead>gene</TableHead>
                    <TableHead>consequence</TableHead>
                    <TableHead>c.</TableHead>
                    <TableHead>p.</TableHead>
                    <TableHead>engine</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-muted-foreground">
                        尚无结果。提交后将显示在这里。
                      </TableCell>
                    </TableRow>
                  ) : (
                    results.map((row, idx) => (
                      <TableRow
                        key={`${row.engine}-${row.input}-${row.feature}-${idx}`}
                      >
                        <TableCell className="align-top">{row.input}</TableCell>
                        <TableCell className="align-top">
                          {row.gene ?? "—"}
                        </TableCell>
                        <TableCell className="align-top">
                          {row.consequence ?? "—"}
                        </TableCell>
                        <TableCell className="align-top">
                          {row.cdot ?? "—"}
                        </TableCell>
                        <TableCell className="align-top">
                          {row.protein ?? "—"}
                        </TableCell>
                        <TableCell className="align-top">
                          {row.engine ?? "—"}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {rawJson ? (
              <div className="space-y-2">
                <Label>原始 JSON（Monaco）</Label>
                <VariantEditor
                  value={rawJson}
                  onChange={() => undefined}
                  readOnly
                  language="json"
                  height="320px"
                />
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
