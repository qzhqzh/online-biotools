export type EngineInfo = {
  id: string
  name: string
  version: string
  supported_assemblies: string[]
  ready_assemblies: string[]
  ready: boolean
  default_assembly: string
  disabled_reason?: string
}

export type VariantResult = {
  input: string
  allele?: string | null
  gene?: string | null
  feature?: string | null
  consequence?: string | null
  impact?: string | null
  cdot?: string | null
  protein?: string | null
  biotype?: string | null
  canonical?: string | null
  engine?: string
}

const API_KEY_STORAGE = "biotools_api_key"

export function getApiKey(): string {
  return localStorage.getItem(API_KEY_STORAGE) || ""
}

export function setApiKey(key: string) {
  if (key) localStorage.setItem(API_KEY_STORAGE, key)
  else localStorage.removeItem(API_KEY_STORAGE)
}

function csrfToken(): string | undefined {
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : undefined
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  const token = csrfToken()
  if (token) headers["X-CSRFToken"] = token
  const apiKey = getApiKey()
  if (apiKey) headers["X-API-Key"] = apiKey
  return headers
}

export async function fetchEngines(): Promise<EngineInfo[]> {
  const res = await fetch("/api/v1/engines/")
  if (!res.ok) throw new Error(`engines failed: ${res.status}`)
  const data = (await res.json()) as { engines: EngineInfo[] }
  return data.engines
}

export async function annotateVariants(payload: {
  engine: string
  assembly: string
  variants: string[]
}): Promise<{ assembly: string; engine: string; results: VariantResult[] }> {
  const res = await fetch("/api/v1/annotations/", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) {
    const message =
      data?.error?.message || data?.detail || `annotation failed: ${res.status}`
    throw new Error(typeof message === "string" ? message : JSON.stringify(message))
  }
  return data
}
