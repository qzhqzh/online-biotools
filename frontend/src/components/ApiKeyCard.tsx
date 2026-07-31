import { useState } from "react"
import { toast } from "sonner"

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
import { getApiKey, setApiKey } from "@/lib/api"

export function ApiKeyCard() {
  const [apiKey, setApiKeyState] = useState(() => getApiKey())

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">API Key</CardTitle>
        <CardDescription>
          当服务配置了接口鉴权时，注释与任务接口需携带密钥。密钥仅保存在本机浏览器，不会上传到服务器配置。
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="w-full space-y-2 sm:max-w-md">
          <Label htmlFor="api-key">X-API-Key</Label>
          <Input
            id="api-key"
            type="password"
            autoComplete="off"
            placeholder="未启用鉴权时可留空"
            value={apiKey}
            onChange={(e) => setApiKeyState(e.target.value)}
          />
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            setApiKey(apiKey.trim())
            toast.success(apiKey.trim() ? "已保存到本机" : "已清除本机密钥")
          }}
        >
          保存
        </Button>
      </CardContent>
    </Card>
  )
}
