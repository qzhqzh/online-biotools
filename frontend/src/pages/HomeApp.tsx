import { useEffect, useState } from "react"
import { Activity, ArrowRight, FlaskConical, Server } from "lucide-react"

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
import { fetchEngines, type EngineInfo } from "@/lib/api"

export default function HomeApp() {
  const [engines, setEngines] = useState<EngineInfo[] | null>(null)

  useEffect(() => {
    fetchEngines()
      .then(setEngines)
      .catch(() => setEngines([]))
  }, [])

  return (
    <AppShell
      title="工作区总览"
      description="统一入口：变异注释、引擎就绪状态与 REST API。"
      crumbs={[{ label: "总览" }]}
    >
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>快捷入口</CardDescription>
            <CardTitle className="text-lg">变异注释</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              使用 Monaco 编辑 VCF/变异，调用 VEP 或 ANNOVAR。
            </p>
            <Button asChild>
              <a href="/tools/annotate/">
                打开工具
                <ArrowRight />
              </a>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>运维</CardDescription>
            <CardTitle className="text-lg">引擎状态</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              查看 VEP / ANNOVAR 的 assembly 就绪情况。
            </p>
            <Button variant="outline" asChild>
              <a href="/tools/engines/">
                <Activity />
                查看状态
              </a>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>集成</CardDescription>
            <CardTitle className="text-lg">API 说明</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              DRF 契约与示例请求，便于外部系统对接。
            </p>
            <Button variant="outline" asChild>
              <a href="/docs/">
                <Server />
                阅读文档
              </a>
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>引擎摘要</CardTitle>
          <CardDescription>来自 GET /api/v1/engines/</CardDescription>
        </CardHeader>
        <CardContent>
          {!engines ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : engines.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂时无法读取引擎信息。</p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {engines.map((engine) => (
                <div
                  key={engine.id}
                  className="flex items-start justify-between rounded-lg border p-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 font-medium">
                      <FlaskConical className="size-4 text-muted-foreground" />
                      {engine.name}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      v{engine.version} · 默认 {engine.default_assembly}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      就绪：{engine.ready_assemblies.join(", ") || "无"}
                    </p>
                  </div>
                  <Badge variant={engine.ready ? "default" : "secondary"}>
                    {engine.ready ? "Ready" : "Not ready"}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </AppShell>
  )
}
