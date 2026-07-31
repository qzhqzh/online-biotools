import { useEffect, useState } from "react"
import { History, Loader2 } from "lucide-react"

import { AppShell } from "@/layouts/AppShell"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  fetchAnnotationJob,
  listAnnotationJobs,
  type AnnotationJob,
} from "@/lib/api"

const STATUS_LABEL: Record<AnnotationJob["status"], string> = {
  queued: "排队中",
  running: "运行中",
  succeeded: "成功",
  failed: "失败",
}

function formatTime(iso?: string | null): string {
  if (!iso) return "—"
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function statusVariant(
  status: AnnotationJob["status"],
): "default" | "secondary" | "destructive" | "outline" {
  if (status === "succeeded") return "default"
  if (status === "failed") return "destructive"
  if (status === "running") return "outline"
  return "secondary"
}

export default function JobsApp() {
  const [jobs, setJobs] = useState<AnnotationJob[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<AnnotationJob | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  async function refresh() {
    setError(null)
    try {
      const list = await listAnnotationJobs(50)
      setJobs(list)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setJobs([])
    }
  }

  useEffect(() => {
    void refresh()
    const timer = window.setInterval(() => {
      void refresh()
    }, 5000)
    return () => window.clearInterval(timer)
  }, [])

  async function openJob(id: string) {
    setLoadingDetail(true)
    try {
      const detail = await fetchAnnotationJob(id)
      setSelected(detail)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoadingDetail(false)
    }
  }

  return (
    <AppShell
      title="任务历史"
      description="后台注释任务队列与历史记录。注释页提交后会在此留档。"
      crumbs={[
        { label: "工具", href: "/tools/annotate/" },
        { label: "任务历史" },
      ]}
      actions={
        <Button type="button" variant="outline" size="sm" onClick={() => void refresh()}>
          刷新
        </Button>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="size-4" />
              最近任务
            </CardTitle>
            <CardDescription>
              默认展示最近 50 条。运行中任务会自动刷新状态。
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error ? (
              <p className="mb-3 text-sm text-destructive">{error}</p>
            ) : null}
            {!jobs ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : jobs.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                暂无任务。请到「变异注释」提交一次。
              </p>
            ) : (
              <div className="overflow-x-auto rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>时间</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>基因组</TableHead>
                      <TableHead>工具</TableHead>
                      <TableHead>位点</TableHead>
                      <TableHead />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobs.map((job) => (
                      <TableRow key={job.id}>
                        <TableCell className="whitespace-nowrap text-xs">
                          {formatTime(job.created_at)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={statusVariant(job.status)}>
                            {STATUS_LABEL[job.status]}
                          </Badge>
                        </TableCell>
                        <TableCell>{job.assembly}</TableCell>
                        <TableCell className="text-xs">
                          {(job.engines || []).join(", ")}
                        </TableCell>
                        <TableCell>{job.variant_count}</TableCell>
                        <TableCell>
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            onClick={() => void openJob(job.id)}
                          >
                            详情
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>任务详情</CardTitle>
            <CardDescription>点击左侧「详情」查看完整结果摘要。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {loadingDetail ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                加载中…
              </div>
            ) : !selected ? (
              <p className="text-muted-foreground">尚未选择任务。</p>
            ) : (
              <>
                <div className="space-y-1">
                  <p>
                    <span className="text-muted-foreground">ID：</span>
                    <code className="text-xs">{selected.id}</code>
                  </p>
                  <p>
                    <span className="text-muted-foreground">状态：</span>
                    {STATUS_LABEL[selected.status]}
                  </p>
                  <p>
                    <span className="text-muted-foreground">基因组：</span>
                    {selected.assembly}
                  </p>
                  <p>
                    <span className="text-muted-foreground">工具：</span>
                    {(selected.engines || []).join(", ")}
                  </p>
                  <p>
                    <span className="text-muted-foreground">创建：</span>
                    {formatTime(selected.created_at)}
                  </p>
                  <p>
                    <span className="text-muted-foreground">结束：</span>
                    {formatTime(selected.finished_at)}
                  </p>
                </div>
                {selected.error ? (
                  <p className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-destructive">
                    {selected.error}
                  </p>
                ) : null}
                {selected.variants?.length ? (
                  <div>
                    <p className="mb-1 text-muted-foreground">输入位点</p>
                    <pre className="max-h-40 overflow-auto rounded-md border bg-muted/30 p-2 text-xs">
                      {selected.variants.join("\n")}
                    </pre>
                  </div>
                ) : null}
                {selected.result?.runs?.length ? (
                  <div className="space-y-2">
                    <p className="text-muted-foreground">引擎结果摘要</p>
                    {selected.result.runs.map((run) => (
                      <div key={run.engine} className="rounded-md border p-3">
                        <div className="mb-1 flex items-center gap-2 font-medium">
                          {run.engine}
                          <Badge
                            variant={run.status === "ok" ? "default" : "destructive"}
                          >
                            {run.status === "ok" ? "ok" : "error"}
                          </Badge>
                        </div>
                        {run.error ? (
                          <p className="text-xs text-destructive">{run.error}</p>
                        ) : (
                          <p className="text-xs text-muted-foreground">
                            {run.results?.length ?? 0} 条注释行
                            {run.results?.[0]
                              ? ` · 例：${run.results[0].gene || "—"} / ${run.results[0].consequence || "—"}`
                              : ""}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : null}
                <Button variant="outline" asChild>
                  <a href="/tools/annotate/">返回注释页</a>
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
