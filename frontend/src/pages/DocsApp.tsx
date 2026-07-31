import { AppShell } from "@/layouts/AppShell"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"

const ENDPOINTS = [
  {
    method: "GET",
    path: "/health/live",
    desc: "进程存活探测",
  },
  {
    method: "GET",
    path: "/health/ready",
    desc: "引擎与参考数据就绪状态",
  },
  {
    method: "GET",
    path: "/api/v1/engines/",
    desc: "列出 VEP / ANNOVAR 能力与 readiness",
  },
  {
    method: "POST",
    path: "/api/v1/annotations/",
    desc: "提交注释：engine=vep|annovar|both，assembly，variants[]",
  },
]

export default function DocsApp() {
  return (
    <AppShell
      title="API 说明"
      description="Django REST framework 对外契约（当前公开，后续将加鉴权）。"
      crumbs={[{ label: "API 说明" }]}
    >
      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Endpoints</CardTitle>
            <CardDescription>浏览器与程序化调用共用同一套路径。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {ENDPOINTS.map((item, index) => (
              <div key={item.path}>
                {index > 0 ? <Separator className="mb-4" /> : null}
                <div className="flex flex-wrap items-baseline gap-2">
                  <code className="rounded bg-muted px-1.5 py-0.5 text-xs font-semibold">
                    {item.method}
                  </code>
                  <code className="text-sm">{item.path}</code>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>注释请求示例</CardTitle>
            <CardDescription>Content-Type: application/json</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="overflow-x-auto rounded-lg border bg-muted/40 p-4 text-xs leading-relaxed">
{`curl -X POST http://<host>:8800/api/v1/annotations/ \\
  -H 'Content-Type: application/json' \\
  -d '{
    "engine": "vep",
    "assembly": "GRCh37",
    "variants": ["17:43092951 G>A"]
  }'`}
            </pre>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
