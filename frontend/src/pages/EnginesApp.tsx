import { useEffect, useState } from "react"

import { ApiKeyCard } from "@/components/ApiKeyCard"
import { AppShell } from "@/layouts/AppShell"
import { Badge } from "@/components/ui/badge"
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
import { fetchEngines, type EngineInfo } from "@/lib/api"

export default function EnginesApp() {
  const [engines, setEngines] = useState<EngineInfo[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchEngines()
      .then(setEngines)
      .catch((err: Error) => setError(err.message))
  }, [])

  return (
    <AppShell
      title="引擎与设置"
      description="查看注释引擎就绪状态，并配置本机 API Key。"
      crumbs={[
        { label: "工具", href: "/tools/annotate/" },
        { label: "引擎与设置" },
      ]}
    >
      <div className="space-y-6">
        <ApiKeyCard />

        <Card>
          <CardHeader>
            <CardTitle>注册引擎</CardTitle>
            <CardDescription>
              数据不就绪时，对应组合不可选，注释接口会返回错误。
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error ? (
              <p className="text-sm text-destructive">{error}</p>
            ) : !engines ? (
              <div className="space-y-3">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Engine</TableHead>
                    <TableHead>Version</TableHead>
                    <TableHead>Supported</TableHead>
                    <TableHead>Ready assemblies</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {engines.map((engine) => (
                    <TableRow key={engine.id}>
                      <TableCell className="font-medium">{engine.name}</TableCell>
                      <TableCell>{engine.version}</TableCell>
                      <TableCell>
                        {engine.supported_assemblies.join(", ")}
                      </TableCell>
                      <TableCell>
                        {engine.ready_assemblies.join(", ") || "—"}
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <Badge variant={engine.ready ? "default" : "secondary"}>
                            {engine.ready ? "Ready" : "Not ready"}
                          </Badge>
                          {engine.disabled_reason ? (
                            <p className="text-xs text-muted-foreground">
                              {engine.disabled_reason}
                            </p>
                          ) : null}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
