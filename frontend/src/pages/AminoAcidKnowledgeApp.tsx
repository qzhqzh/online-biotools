import { useMemo, useState } from "react"
import { Search } from "lucide-react"

import {
  AMINO_ACID_KNOWLEDGE_SOURCES,
  ExternalRef,
  KnowledgeSourcesCard,
} from "@/components/knowledge/KnowledgeSources"
import { AppShell } from "@/layouts/AppShell"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { AA3_TO_1, normalizeProteinChange } from "@/lib/annotation-knowledge"

const AA_CN: Record<string, string> = {
  A: "丙氨酸",
  R: "精氨酸",
  N: "天冬酰胺",
  D: "天冬氨酸",
  C: "半胱氨酸",
  Q: "谷氨酰胺",
  E: "谷氨酸",
  G: "甘氨酸",
  H: "组氨酸",
  I: "异亮氨酸",
  L: "亮氨酸",
  K: "赖氨酸",
  M: "甲硫氨酸",
  F: "苯丙氨酸",
  P: "脯氨酸",
  S: "丝氨酸",
  T: "苏氨酸",
  W: "色氨酸",
  Y: "酪氨酸",
  V: "缬氨酸",
  "*": "终止",
  U: "硒代半胱氨酸",
  O: "吡咯赖氨酸",
  X: "未知",
  B: "Asx",
  Z: "Glx",
}

type AaRow = {
  one: string
  three: string
  cn: string
}

function buildRows(): AaRow[] {
  const byOne = new Map<string, string>()
  for (const [three, one] of Object.entries(AA3_TO_1)) {
    if (one === "*" && three === "Stop" && byOne.has("*")) continue
    if (!byOne.has(one) || three === "Ter") byOne.set(one, three)
  }
  return [...byOne.entries()]
    .map(([one, three]) => ({
      one,
      three,
      cn: AA_CN[one] || "—",
    }))
    .sort((a, b) => a.one.localeCompare(b.one))
}

export default function AminoAcidKnowledgeApp() {
  const rows = useMemo(() => buildRows(), [])
  const [q, setQ] = useState("")
  const [demo, setDemo] = useState("p.Arg273His")

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return rows
    return rows.filter(
      (r) =>
        r.one.toLowerCase().includes(needle) ||
        r.three.toLowerCase().includes(needle) ||
        r.cn.includes(q.trim()),
    )
  }, [q, rows])

  const normalizedDemo = normalizeProteinChange(demo)

  return (
    <AppShell
      title="氨基酸映射"
      description="三字母 / 单字母氨基酸对照，以及 HGVS p. 写法归一化（如 Arg273His → R273H）。"
      crumbs={[
        { label: "知识库" },
        { label: "氨基酸映射" },
      ]}
    >
      <div className="space-y-6">
        <KnowledgeSourcesCard sources={AMINO_ACID_KNOWLEDGE_SOURCES} />

        <Card>
          <CardHeader>
            <CardTitle>归一化试算</CardTitle>
            <CardDescription>
              粘贴 VEP/ANNOVAR 的 p. 字段，查看统一为单字母坐标形式后的结果。命名规范见{" "}
              <ExternalRef href="https://hgvs-nomenclature.org/stable/recommendations/protein/substitution/">
                HGVS protein substitution
              </ExternalRef>
              。
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="w-full space-y-2 sm:max-w-lg">
              <Input
                value={demo}
                onChange={(e) => setDemo(e.target.value)}
                placeholder="例如 ENSP00000269305.4:p.Arg273His"
                className="font-mono"
              />
            </div>
            <div className="rounded-md border bg-muted/30 px-3 py-2 font-mono text-sm">
              {normalizedDemo || "—"}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>氨基酸对照表</CardTitle>
            <CardDescription>
              标准{" "}
              <ExternalRef href="https://www.qmul.ac.uk/sbcs/iupac/AminoAcid/A2021.html">
                IUPAC
              </ExternalRef>{" "}
              单字母与三字母码。对比注释时 His 与 H 视为表述相同。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative w-full max-w-md">
              <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-8"
                placeholder="搜索 A / Ala / 组氨酸"
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>

            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-24">单字母</TableHead>
                    <TableHead className="w-28">三字母</TableHead>
                    <TableHead>中文名</TableHead>
                    <TableHead>示例 p.</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((row) => (
                    <TableRow key={row.one}>
                      <TableCell>
                        <Badge className="font-mono">{row.one}</Badge>
                      </TableCell>
                      <TableCell className="font-mono">{row.three}</TableCell>
                      <TableCell>{row.cn}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        p.{row.three}123{row.three === "Ter" ? "" : row.three} ↔ p.
                        {row.one}123{row.one}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
