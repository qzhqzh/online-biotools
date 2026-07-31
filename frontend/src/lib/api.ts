export type EngineInfo = {
  id: string
  name: string
  version: string
  supported_assemblies: string[]
  ready_assemblies: string[]
  ready: boolean
  default_assembly: string
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

function csrfToken(): string | undefined {
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : undefined
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
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  const token = csrfToken()
  if (token) headers["X-CSRFToken"] = token

  const res = await fetch("/api/v1/annotations/", {
    method: "POST",
    headers,
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
