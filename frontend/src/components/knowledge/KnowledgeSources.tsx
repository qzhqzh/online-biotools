import type { ReactNode } from "react"
import { ExternalLink } from "lucide-react"

import { cn } from "@/lib/utils"

export type KnowledgeSource = {
  name: string
  href: string
  note: string
}

/** Official references users can open to verify knowledge-base content. */
export const GENE_KNOWLEDGE_SOURCES: KnowledgeSource[] = [
  {
    name: "NCBI MANE",
    href: "https://www.ncbi.nlm.nih.gov/refseq/MANE/",
    note: "MANE Select / Plus Clinical：ENST ↔ NM 官方一一对应说明",
  },
  {
    name: "MANE summary（FTP）",
    href: "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/",
    note: "批量下载 summary.txt.gz，可用于核对转录本映射表",
  },
  {
    name: "NCBI Gene（Homo sapiens gene_info）",
    href: "https://ftp.ncbi.nlm.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz",
    note: "人类基因符号、别名、染色体与类型等基础信息",
  },
  {
    name: "Ensembl MANE 说明",
    href: "https://www.ensembl.org/info/genome/genebuild/mane.html",
    note: "Ensembl 侧对 MANE 与默认转录本的解释",
  },
  {
    name: "Ensembl Browser",
    href: "https://www.ensembl.org/Homo_sapiens/Info/Index",
    note: "按基因 / ENST 查询转录本与 RefSeq 交叉引用",
  },
  {
    name: "NCBI Gene 搜索",
    href: "https://www.ncbi.nlm.nih.gov/gene",
    note: "按基因符号或 GeneID 核对基因基本信息",
  },
]

export const AMINO_ACID_KNOWLEDGE_SOURCES: KnowledgeSource[] = [
  {
    name: "IUPAC 氨基酸单字母码",
    href: "https://www.qmul.ac.uk/sbcs/iupac/AminoAcid/A2021.html",
    note: "标准单字母 / 三字母氨基酸缩写",
  },
  {
    name: "HGVS 蛋白序列变异命名（p.）",
    href: "https://hgvs-nomenclature.org/stable/recommendations/protein/substitution/",
    note: "p.Arg273His 等蛋白变异写法规范",
  },
  {
    name: "NCBI Amino Acid Explorer",
    href: "https://www.ncbi.nlm.nih.gov/Class/Structure/aa/aa_explorer.cgi",
    note: "氨基酸结构与缩写对照（辅助核对）",
  },
]

export function accessionLookupUrl(accession: string): string | null {
  const id = accession.replace(/\.\d+$/, "").trim()
  if (!id) return null
  if (/^ENS[GTP]\d+/i.test(id)) {
    return `https://www.ensembl.org/Homo_sapiens/Transcript/Summary?t=${id}`
  }
  if (/^(NM_|NR_|NP_|XM_|XR_|XP_)/i.test(id)) {
    return `https://www.ncbi.nlm.nih.gov/nuccore/${id}`
  }
  if (/^ENSG\d+/i.test(id)) {
    return `https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=${id}`
  }
  return null
}

export function geneLookupUrl(symbol: string): string | null {
  const s = symbol.trim()
  if (!s || s === "—") return null
  return `https://www.ncbi.nlm.nih.gov/gene/?term=${encodeURIComponent(s + "[Gene Name] AND Homo sapiens[Organism]")}`
}

type KnowledgeSourcesCardProps = {
  title?: string
  description?: string
  sources: KnowledgeSource[]
  className?: string
  /** Compact side-rail layout: link first, short note below */
  compact?: boolean
}

export function KnowledgeSourcesCard({
  title = "数据来源与核对",
  description = "以下为权威公开数据源。点击可跳转核对；本站知识库为本地缓存/种子，可能滞后于上游更新。",
  sources,
  className,
  compact = false,
}: KnowledgeSourcesCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-muted/20 px-4 py-3",
        compact && "px-3 py-2.5",
        className,
      )}
    >
      <div className="mb-2">
        <h2 className="text-sm font-semibold tracking-tight">{title}</h2>
        {description ? (
          <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
        ) : null}
      </div>
      <ul className={cn("space-y-2", compact && "space-y-2.5")}>
        {sources.map((src) => (
          <li
            key={src.href}
            className={cn(
              "flex flex-col gap-0.5 border-t border-border/60 pt-2 first:border-0 first:pt-0",
              !compact && "sm:flex-row sm:items-baseline sm:gap-3",
            )}
          >
            <a
              href={src.href}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline"
            >
              {src.name}
              <ExternalLink className="size-3.5 shrink-0 opacity-70" />
            </a>
            <span className="text-xs leading-snug text-muted-foreground">
              {src.note}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

type ExternalRefProps = {
  href: string
  children: ReactNode
  className?: string
}

export function ExternalRef({ href, children, className }: ExternalRefProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "inline-flex items-center gap-0.5 text-primary underline-offset-2 hover:underline",
        className,
      )}
    >
      {children}
      <ExternalLink className="size-3 opacity-60" />
    </a>
  )
}

export type ManeMeta = {
  version?: string
  assembly?: string
  assembly_note?: string
  refseq_annotation?: string | null
  ensembl_release?: string | null
  mane_select?: number
  mane_plus_clinical?: number
  accession_keys?: number
  ftp_current?: string
  summary_url?: string
  docs?: { ncbi?: string; ensembl?: string }
}

type ManeVersionNoteProps = {
  mane?: ManeMeta | null
  className?: string
}

type ManeVersionNotePropsFull = ManeVersionNoteProps & {
  /** Compact side-rail summary */
  compact?: boolean
}

/** Explain MANE assembly / set / release versioning for users. */
export function ManeVersionNote({
  mane,
  className,
  compact = false,
}: ManeVersionNotePropsFull) {
  const version = mane?.version || "1.5"
  const selectN = mane?.mane_select
  const plusN = mane?.mane_plus_clinical
  const ncbi = mane?.docs?.ncbi || "https://www.ncbi.nlm.nih.gov/refseq/MANE/"
  const ensembl =
    mane?.docs?.ensembl ||
    "https://www.ensembl.org/info/genome/genebuild/mane.html"
  const ftp =
    mane?.ftp_current ||
    "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/current/"

  if (compact) {
    return (
      <div className={cn("rounded-xl border bg-card px-3 py-2.5", className)}>
        <h2 className="text-sm font-semibold tracking-tight">MANE</h2>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          v{version} · 仅 {mane?.assembly || "GRCh38"}
          {typeof selectN === "number"
            ? ` · Select ${selectN.toLocaleString()}`
            : ""}
          {typeof plusN === "number"
            ? ` · Plus Clinical ${plusN.toLocaleString()}`
            : ""}
        </p>
        <p className="mt-1.5 text-xs leading-snug text-muted-foreground">
          无官方 GRCh37/hg19 MANE；Select 为每基因常用转录本。
        </p>
        <p className="mt-2 flex flex-col gap-1 text-xs">
          <ExternalRef href={ncbi}>NCBI MANE</ExternalRef>
          <ExternalRef href={ensembl}>Ensembl 说明</ExternalRef>
          <ExternalRef href={ftp}>FTP current</ExternalRef>
        </p>
      </div>
    )
  }

  return (
    <div className={cn("rounded-xl border bg-card px-4 py-3", className)}>
      <h2 className="text-sm font-semibold tracking-tight">MANE 版本说明</h2>
      <p className="mt-1 text-xs text-muted-foreground">
        MANE（Matched Annotation from NCBI and EMBL-EBI）定义「常用转录本」时的
        ENST ↔ NM 对应关系。本站已导入数据以页面 / API 元数据为准。
      </p>
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        <div className="rounded-md border bg-muted/20 px-3 py-2">
          <dt className="text-xs text-muted-foreground">参考基因组组装</dt>
          <dd className="mt-0.5 font-medium">
            {mane?.assembly || "GRCh38"}（仅此组装）
          </dd>
          <dd className="mt-1 text-xs text-muted-foreground">
            {mane?.assembly_note ||
              "无官方 GRCh37 / hg19 MANE；hg19 注释只能间接参考同一 NM/ENST。"}
          </dd>
        </div>
        <div className="rounded-md border bg-muted/20 px-3 py-2">
          <dt className="text-xs text-muted-foreground">发布版</dt>
          <dd className="mt-0.5 font-medium">MANE v{version}</dd>
          <dd className="mt-1 text-xs text-muted-foreground">
            {[
              mane?.ensembl_release ? `Ensembl ${mane.ensembl_release}` : null,
              mane?.refseq_annotation
                ? `RefSeq ${mane.refseq_annotation}`
                : null,
            ]
              .filter(Boolean)
              .join(" · ") || "见 NCBI current FTP README_versions.txt"}
          </dd>
        </div>
        <div className="rounded-md border bg-muted/20 px-3 py-2 sm:col-span-2">
          <dt className="text-xs text-muted-foreground">集合类型</dt>
          <dd className="mt-1 space-y-1 text-xs text-muted-foreground">
            <p>
              <span className="font-medium text-foreground">MANE Select</span>
              ：每个蛋白编码基因一条高置信常用转录本
              {typeof selectN === "number"
                ? `（本库 ${selectN.toLocaleString()} 条）`
                : ""}
              。
            </p>
            <p>
              <span className="font-medium text-foreground">
                MANE Plus Clinical
              </span>
              ：临床报告所需的额外转录本
              {typeof plusN === "number"
                ? `（本库 ${plusN.toLocaleString()} 条）`
                : ""}
              。
            </p>
          </dd>
        </div>
      </dl>
      <p className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs">
        <ExternalRef href={ncbi}>NCBI MANE</ExternalRef>
        <ExternalRef href={ensembl}>Ensembl MANE 说明</ExternalRef>
        <ExternalRef href={ftp}>MANE FTP current</ExternalRef>
      </p>
    </div>
  )
}
