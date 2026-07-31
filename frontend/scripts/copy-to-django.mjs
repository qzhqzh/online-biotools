import { cpSync, mkdirSync, rmSync } from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
const src = path.join(root, "dist")
const dest = path.join(root, "../apps/portal/static/portal/dist")

mkdirSync(path.dirname(dest), { recursive: true })
rmSync(dest, { recursive: true, force: true })
cpSync(src, dest, { recursive: true })
console.log(`Copied frontend dist -> ${dest}`)
