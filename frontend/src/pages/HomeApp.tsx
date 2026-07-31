import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export default function HomeApp() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 p-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">online-biotools</h1>
        <p className="mt-2 text-muted-foreground">
          Django + DRF · 前端 shadcn/ui（原版主题）+ Monaco Editor
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>开始使用</CardTitle>
          <CardDescription>统一网页入口与 REST API</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button asChild>
            <a href="/tools/annotate/">打开注释工具</a>
          </Button>
          <Button variant="outline" asChild>
            <a href="/api/v1/engines/">查看引擎 API</a>
          </Button>
          <Button variant="ghost" asChild>
            <a href="/health/ready">健康检查</a>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
