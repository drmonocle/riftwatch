// Fails if the app version differs between package.json, tauri.conf.json and Cargo.toml.
import { readFileSync } from "node:fs";

const read = (p) => readFileSync(new URL(`../${p}`, import.meta.url), "utf8");
const pkg = JSON.parse(read("package.json")).version;
const tauri = JSON.parse(read("src-tauri/tauri.conf.json")).version;
const cargo = /^version\s*=\s*"([^"]+)"/m.exec(read("src-tauri/Cargo.toml"))?.[1];

const versions = { "package.json": pkg, "tauri.conf.json": tauri, "Cargo.toml": cargo };
if (new Set(Object.values(versions)).size !== 1) {
  console.error("Version mismatch:", versions);
  process.exit(1);
}
console.log(`Versions in sync: ${pkg}`);
