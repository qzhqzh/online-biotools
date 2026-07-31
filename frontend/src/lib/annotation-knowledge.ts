/**
 * Annotation comparison knowledge base.
 * Distinguishes: same | equivalent (nomenclature) | isoform (different transcript) | conflict.
 */

export type CompareKind = "same" | "equivalent" | "isoform" | "conflict" | "empty"

export type CompareFieldKey =
  | "gene"
  | "feature"
  | "cdot"
  | "protein"
  | "consequence"

/** Three-letter ↔ one-letter amino acid codes */
export const AA3_TO_1: Record<string, string> = {
  Ala: "A",
  Arg: "R",
  Asn: "N",
  Asp: "D",
  Cys: "C",
  Gln: "Q",
  Glu: "E",
  Gly: "G",
  His: "H",
  Ile: "I",
  Leu: "L",
  Lys: "K",
  Met: "M",
  Phe: "F",
  Pro: "P",
  Ser: "S",
  Thr: "T",
  Trp: "W",
  Tyr: "Y",
  Val: "V",
  Ter: "*",
  Stop: "*",
  Sec: "U",
  Pyl: "O",
  Xaa: "X",
  Asx: "B",
  Glx: "Z",
}

export const AA1_TO_3: Record<string, string> = Object.fromEntries(
  Object.entries(AA3_TO_1).map(([a3, a1]) => [a1, a3]),
)

/**
 * VEP ↔ ANNOVAR consequence crosswalk for UI + comparison.
 * `vep` / `annovar` list exact tokens after lowercasing / split on ,;|
 */
export type ConsequenceCrosswalk = {
  id: string
  label: string
  meaning: string
  vep: string[]
  annovar: string[]
  /** How ANNOVAR often composes Func + ExonicFunc in our parser output */
  annovarExample?: string
}

export const CONSEQUENCE_CROSSWALK: ConsequenceCrosswalk[] = [
  {
    id: "missense",
    label: "错义突变",
    meaning: "编码区氨基酸替换",
    vep: ["missense_variant", "missense"],
    annovar: [
      "nonsynonymous snv",
      "nonsynonymous_snv",
      "nonsynonymous",
      "exonic,nonsynonymous snv",
    ],
    annovarExample: "exonic,nonsynonymous SNV",
  },
  {
    id: "synonymous",
    label: "同义突变",
    meaning: "编码区碱基变了、氨基酸不变",
    vep: ["synonymous_variant", "synonymous"],
    annovar: [
      "synonymous snv",
      "synonymous_snv",
      "synonymous",
      "exonic,synonymous snv",
    ],
    annovarExample: "exonic,synonymous SNV",
  },
  {
    id: "stop_gained",
    label: "无义 / 获终止",
    meaning: "产生提前终止密码子",
    vep: ["stop_gained"],
    annovar: ["stopgain", "stop gain", "nonsense", "exonic,stopgain"],
    annovarExample: "exonic,stopgain",
  },
  {
    id: "stop_lost",
    label: "终止丢失",
    meaning: "原终止密码子被改变",
    vep: ["stop_lost"],
    annovar: ["stoploss", "stop loss", "exonic,stoploss"],
    annovarExample: "exonic,stoploss",
  },
  {
    id: "frameshift",
    label: "移码",
    meaning: "indel 导致阅读框改变",
    vep: ["frameshift_variant", "frameshift"],
    annovar: [
      "frameshift",
      "frameshift insertion",
      "frameshift deletion",
      "exonic,frameshift",
    ],
    annovarExample: "exonic,frameshift insertion",
  },
  {
    id: "splice",
    label: "剪接相关",
    meaning: "影响剪接位点或邻近区域",
    vep: [
      "splice_acceptor_variant",
      "splice_donor_variant",
      "splice_region_variant",
    ],
    annovar: ["splicing", "splice"],
    annovarExample: "splicing",
  },
  {
    id: "intron",
    label: "内含子",
    meaning: "落在内含子（非剪接关键位点）",
    vep: ["intron_variant"],
    annovar: ["intronic", "intron"],
    annovarExample: "intronic",
  },
  {
    id: "utr5",
    label: "5′ UTR",
    meaning: "基因上游非翻译区",
    vep: ["5_prime_utr_variant"],
    annovar: ["utr5", "5utr"],
    annovarExample: "UTR5",
  },
  {
    id: "utr3",
    label: "3′ UTR",
    meaning: "基因下游非翻译区",
    vep: ["3_prime_utr_variant"],
    annovar: ["utr3", "3utr"],
    annovarExample: "UTR3",
  },
  {
    id: "intergenic",
    label: "基因间区",
    meaning: "不落在注释基因区间",
    vep: ["intergenic_variant"],
    annovar: ["intergenic"],
    annovarExample: "intergenic",
  },
  {
    id: "upstream",
    label: "上游",
    meaning: "基因转录起点上游",
    vep: ["upstream_gene_variant"],
    annovar: ["upstream"],
    annovarExample: "upstream",
  },
  {
    id: "downstream",
    label: "下游",
    meaning: "基因转录终点下游",
    vep: ["downstream_gene_variant"],
    annovar: ["downstream"],
    annovarExample: "downstream",
  },
]

/** Flat alias map used by compareFieldValues (group id → all tokens). */
export const CONSEQUENCE_GROUPS: Record<string, string[]> = Object.fromEntries(
  CONSEQUENCE_CROSSWALK.map((row) => [
    row.id,
    [...row.vep, ...row.annovar].map((s) => s.toLowerCase()),
  ]),
)

/**
 * Seed transcript crosswalk (Ensembl ↔ RefSeq).
 * Expand via scripts/import_transcript_map.py from Ensembl MANE / RefSeq match tables.
 * Note: ENST00000269305 MANE-matches NM_000546, NOT NM_001126115 (different isoform).
 */
export type TranscriptRecord = {
  gene?: string
  ensembl?: string[]
  refseq?: string[]
  mane?: boolean
  note?: string
}

export const TRANSCRIPT_MAP: Record<string, TranscriptRecord> = {
  ENST00000269305: {
    gene: "TP53",
    refseq: ["NM_000546"],
    mane: true,
    note: "MANE Select / Ensembl canonical",
  },
  NM_000546: {
    gene: "TP53",
    ensembl: ["ENST00000269305"],
    mane: true,
  },
  ENSP00000269305: {
    gene: "TP53",
    refseq: ["NP_000537"],
    mane: true,
  },
  NM_001126115: {
    gene: "TP53",
    ensembl: ["ENST00000619186"],
    mane: false,
    note: "RefSeq transcript variant 5; not MANE Select",
  },
  ENST00000619186: {
    gene: "TP53",
    refseq: ["NM_001126115"],
    mane: false,
  },
}

export function stripAccessionVersion(id: string): string {
  return id.replace(/\.\d+$/, "").trim()
}

export function extractAccession(raw?: string | null): string | null {
  if (!raw) return null
  const m = raw.match(/\b((?:ENST|ENSP|NM_|NR_|NP_|XM_|XR_|XP_)\d+)(?:\.\d+)?\b/i)
  return m ? normalizeAccession(m[1]) : null
}

/** Normalize accession casing; strip version. */
export function normalizeAccession(raw: string): string {
  const s = stripAccessionVersion(raw.trim())
  const upper = s.toUpperCase()
  if (upper.startsWith("NM")) return `NM_${upper.replace(/^NM_?/, "")}`
  if (upper.startsWith("NP")) return `NP_${upper.replace(/^NP_?/, "")}`
  if (upper.startsWith("NR")) return `NR_${upper.replace(/^NR_?/, "")}`
  if (upper.startsWith("XM")) return `XM_${upper.replace(/^XM_?/, "")}`
  if (upper.startsWith("XP")) return `XP_${upper.replace(/^XP_?/, "")}`
  if (upper.startsWith("XR")) return `XR_${upper.replace(/^XR_?/, "")}`
  return upper
}

export function aa3To1(token: string): string {
  if (token.length === 1) return token.toUpperCase()
  const key = token[0].toUpperCase() + token.slice(1).toLowerCase()
  return AA3_TO_1[key] || token.toUpperCase()
}

/** p.Arg273His / p.R273H / ENSP...:p.Arg273His → R273H */
export function normalizeProteinChange(raw?: string | null): string | null {
  if (!raw) return null
  const pIdx = raw.toLowerCase().lastIndexOf("p.")
  const body = pIdx >= 0 ? raw.slice(pIdx + 2) : raw
  const m3 = body.match(/^([A-Za-z]{3})(\d+)([A-Za-z]{3}|\*)$/)
  if (m3) {
    return `${aa3To1(m3[1])}${m3[2]}${m3[3] === "*" ? "*" : aa3To1(m3[3])}`
  }
  const m1 = body.match(/^([A-Za-z*])(\d+)([A-Za-z*])$/)
  if (m1) {
    return `${m1[1].toUpperCase()}${m1[2]}${m1[3].toUpperCase()}`
  }
  return body.replace(/\s+/g, "").toUpperCase() || null
}

/** Protein change without position: R273H → RH (from/to only) */
export function proteinChangeLetters(normalized: string | null): string | null {
  if (!normalized) return null
  const m = normalized.match(/^([A-Z*])\d+([A-Z*])$/)
  return m ? `${m[1]}${m[2]}` : null
}

export function normalizeCdnaChange(raw?: string | null): string | null {
  if (!raw) return null
  const cIdx = raw.toLowerCase().lastIndexOf("c.")
  const body = (cIdx >= 0 ? raw.slice(cIdx + 2) : raw).replace(/\s+/g, "")
  return body.toLowerCase() || null
}

export function consequenceGroup(raw?: string | null): string | null {
  if (!raw) return null
  const parts = raw
    .toLowerCase()
    .split(/[,;|]/)
    .map((p) => p.trim())
    .filter(Boolean)
  for (const [group, aliases] of Object.entries(CONSEQUENCE_GROUPS)) {
    for (const part of parts) {
      if (aliases.includes(part)) return group
    }
  }
  return parts.sort().join("|")
}

export function transcriptsRelated(a?: string | null, b?: string | null): CompareKind {
  const aa = a ? normalizeAccession(extractAccession(a) || a) : null
  const bb = b ? normalizeAccession(extractAccession(b) || b) : null
  if (!aa || !bb) return !aa && !bb ? "empty" : "conflict"
  if (aa === bb) return "same"

  const recA = TRANSCRIPT_MAP[aa]
  const recB = TRANSCRIPT_MAP[bb]
  const aRefs = new Set([
    aa,
    ...(recA?.ensembl || []).map(normalizeAccession),
    ...(recA?.refseq || []).map(normalizeAccession),
  ])
  const bRefs = new Set([
    bb,
    ...(recB?.ensembl || []).map(normalizeAccession),
    ...(recB?.refseq || []).map(normalizeAccession),
  ])
  for (const x of aRefs) {
    if (bRefs.has(x)) return "equivalent"
  }

  // Same gene in map but not cross-linked → different isoforms
  if (recA?.gene && recB?.gene && recA.gene === recB.gene) return "isoform"
  // Both look like transcript IDs for comparison UI
  if (/^(ENST|NM_|NR_|XM_)/i.test(aa) && /^(ENST|NM_|NR_|XM_)/i.test(bb)) {
    return "isoform"
  }
  return "conflict"
}

export function compareFieldValues(
  field: CompareFieldKey,
  values: Array<string | null | undefined>,
): CompareKind {
  const filled = values.map((v) => (v ?? "").trim()).filter(Boolean)
  if (filled.length === 0) return "empty"
  if (filled.length === 1) return "same"

  if (field === "gene") {
    const norms = filled.map((v) => v.toUpperCase())
    return new Set(norms).size === 1 ? "same" : "conflict"
  }

  if (field === "consequence") {
    const groups = filled.map((v) => consequenceGroup(v))
    if (groups.every((g) => g && g === groups[0])) {
      const rawSame = new Set(filled.map((v) => v.toLowerCase())).size === 1
      return rawSame ? "same" : "equivalent"
    }
    return "conflict"
  }

  if (field === "feature") {
    let worst: CompareKind = "same"
    for (let i = 0; i < filled.length; i++) {
      for (let j = i + 1; j < filled.length; j++) {
        const k = transcriptsRelated(filled[i], filled[j])
        if (k === "conflict") return "conflict"
        if (k === "isoform") worst = "isoform"
        else if (k === "equivalent" && worst === "same") worst = "equivalent"
      }
    }
    return worst
  }

  if (field === "protein") {
    const norms = filled.map((v) => normalizeProteinChange(v))
    if (norms.every((n) => n && n === norms[0])) {
      const rawSame = new Set(filled.map((v) => v.toLowerCase())).size === 1
      return rawSame ? "same" : "equivalent"
    }
    const letters = norms.map((n) => proteinChangeLetters(n))
    if (letters.every((l) => l && l === letters[0])) {
      // Same AA substitution on different coordinates → isoform numbering
      return "isoform"
    }
    return "conflict"
  }

  if (field === "cdot") {
    const norms = filled.map((v) => normalizeCdnaChange(v))
    if (norms.every((n) => n && n === norms[0])) {
      const rawSame = new Set(filled.map((v) => v.toLowerCase())).size === 1
      return rawSame ? "same" : "equivalent"
    }
    // Different c. on same gene often isoform; leave as isoform if accessions differ
    const acc = filled.map((v) => extractAccession(v))
    if (acc[0] && acc[1] && transcriptsRelated(acc[0], acc[1]) !== "same") {
      return "isoform"
    }
    return "conflict"
  }

  const norms = filled.map((v) => v.toLowerCase())
  return new Set(norms).size === 1 ? "same" : "conflict"
}

export const COMPARE_KIND_LABEL: Record<CompareKind, string | null> = {
  same: null,
  empty: null,
  equivalent: "表述不同",
  isoform: "不同转录本",
  conflict: "不一致",
}
