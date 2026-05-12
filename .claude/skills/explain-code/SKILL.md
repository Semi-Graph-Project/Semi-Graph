---
description: Explain a Python code file using deep First Principles Thinking — bind every constraint to a fundamental theory (Big-O, CAP, Memory Hierarchy, Shannon, Network I/O), separate Structure vs Semantics decisions, identify the breaking point of the current code (not just alternatives), and project bottlenecks under 100× input growth. Saves output to Obsidian Vault as a PKM-friendly note with YAML frontmatter + auto-discovered related files.
arguments:
  - file_path
allowed-tools: Read, Write, Bash, Grep, Glob
---

## Task

Read the Python file at `$0`, then generate a deep-dive explanation following the structure below, and **save it to the Obsidian Vault** (path below).

Use `Read` for source file + `Grep`/`Glob` for discovering upstream/downstream callers, `Bash` for quick complexity probes (line counts, dependency graph, function call sites) when needed.

## Output File Path (MANDATORY — Obsidian Vault)

ใช้ `Write` tool save ไปที่ path นี้เท่านั้น:

```
/home/kantinan/Documents/Obsidian Vault/Agentic GraphRAG/Code_Explained_<basename>.md
```

`<basename>` = source file name without `.py` extension (e.g. `src/semigraph/offline/kg_store.py` → `kg_store`).

ถ้า file มีอยู่แล้วใน path ดังกล่าว → append `_v2`, `_v3` etc. (ห้าม overwrite note เดิม)

## Output Document Header — MANDATORY YAML Frontmatter

ห้ามใช้ blockquote header แบบเก่า — ต้องเป็น YAML frontmatter ที่ PKM ใช้ index ได้:

```yaml
---
tags: [code-explained, <phase-tag>, <domain-tag>]
target_file: <relative path from project root>
phase: <A | B1 | B2 | B3 | C1 | ... | unknown>
complexity_time: <Big-O, e.g. O(N) | O(N log N) | O(N²) | O(1)>
complexity_space: <Big-O>
core_mechanisms: [<2-5 keywords>]
upstream_dependencies: [<file or external system>]
downstream_consumers: [<file or external system>]
breaking_point: <one-line stress condition + threshold>
generated_by: explain-code skill
generated_at: <YYYY-MM-DD>
---

# Code Explained — `<filename_with_ext>`

> First Principles deep-dive of `<full_path>` — constraints → theory → decisions → flow → stress test
>
> Cross-link: [[CLAUDE]] | (link อื่น ๆ ที่เกี่ยวข้อง)
```

`tags` ควรครอบคลุม:
- `code-explained` (เสมอ)
- domain (เช่น `graphrag`, `embedding`, `retrieval`, `ingestion`, `agent`)
- mechanism kind (เช่น `data-pipeline`, `vector-search`, `graph-traversal`, `prompt-engineering`)

## Required Structure (1.5–2 หน้ากระดาษ — กระชับ)

### Section 1: Constraint ของปัญหา + Theory Binding

- 2-3 ประโยคบอกว่า code นี้ทำอะไร + ปัญหาอะไรที่บังคับให้ต้องมี
- **ตาราง Constraint** — อย่างน้อย 3 ข้อ คอลัมน์:
  | `#` | `Constraint` | `ที่มา` | **`Theory binding`** |
  - **Theory binding (บังคับ)** — ผูกข้อจำกัดกับทฤษฎี/หลักการพื้นฐาน เช่น:
    - `Big-O complexity` (เช่น O(N²) pairwise compare)
    - `Memory hierarchy` (L1/L2/RAM/SSD latency คนละ order)
    - `CAP theorem` (consistency vs availability vs partition tolerance)
    - `Shannon entropy / information theory` (encoding length minimum)
    - `Network I/O` (round-trip latency, bandwidth ceiling)
    - `Floating-point representation` (IEEE 754 precision, underflow)
    - `Cache coherence` (read/write amplification)
    - `Amdahl's law` (parallelization upper bound)
    - `Zipfian distribution` (long-tail data shape)
    - `JIT/AOT compilation` (warmup cost)
- ถ้าระบุไม่ได้ว่าทฤษฎีอะไร → ห้ามตอบ "hardware limit" ลอย ๆ — ต้องเจาะลง physical/mathematical mechanism จริง
- ตำแหน่งใน pipeline ใหญ่ + Phase

**ห้ามใช้ analogy** ที่ไม่ตรง mechanism

### Section 2: Decision Tree (Structure vs Semantics)

แสดง 2-4 design decisions — **แต่ละ decision ต้อง tag ว่าเป็น Structure หรือ Semantics:**

- **[STRUCTURE]** — decision ที่จัดการ data structure / topology / capacity (เช่น ลด degree, batch size, index type)
- **[SEMANTICS]** — decision ที่จัดการ meaning / weighting / interpretation (เช่น cosine threshold, edge type filter, prompt rule)

รูปแบบ:

```markdown
#### D<N>: [STRUCTURE|SEMANTICS] <ชื่อ decision>

| Option | กลไก | Verdict |
|---|---|---|
| Option A | mechanism สั้น | ✅/❌ + ผูกกับ Constraint #X |
| Option B | ... | ... |

**Counterfactual:** ถ้าเลือกที่ตัดทิ้ง → จะพังตอนไหน เป็นตัวเลข/หน่วยอะไร

**Boundary limit ของ option ที่เลือก:** ตัวเลือกปัจจุบันจะพังที่ scale/condition ไหน
(เช่น "O(N²) matmul ดีถึง N=10,000 — เกินนี้ RAM > 16 GB", "Cosine threshold 0.85 ตึงเกินเมื่อ corpus ข้าม 5 ภาษา")
```

**กฎเหล็ก:**
- ทุก decision **ต้องมี Counterfactual** (อะไรพังถ้าทำตรงข้าม)
- ทุก decision **ต้องมี Boundary limit** (ตัวเลือกปัจจุบันพังที่จุดไหน)
- ตัด decision ที่ไม่มี alternative ชัดเจนออก — focus เฉพาะ decisions ที่มี trade-off จริง

### Section 3: Flow End-to-End + Upstream/Downstream Contracts

**ก่อนเริ่ม Step 1 ต้องมีตาราง Contract:**

```markdown
#### Contracts (Caller ↔ This Code ↔ Callee)

| Direction | Counterpart | Invariant ที่คาดหวัง / รับประกัน |
|---|---|---|
| **Upstream** (caller → this) | <caller file/system> | <what caller must guarantee — e.g. "Input list sanitized, no None"> |
| **Upstream** (depends on) | <external state> | <what state must exist — e.g. "Neo4j must have :Entity nodes with `embedding`"> |
| **Downstream** (this → callee) | <callee file/system> | <what this guarantees to callee — e.g. "Returns L2-normalized vectors"> |
| **Side-effects** | <DB/file/log> | <what state changes after this runs> |
```

จากนั้น flow steps เดิม — แต่ละ step ยังมี typed I/O + เพิ่ม **Trade-off** ที่ step นั้น "แลก":

```markdown
#### Step N: <ชื่อ step> — `function_name()`

**Constraint ที่ enforce:** <ref Section 1>

| | |
|---|---|
| **Input** | `param: Type` พร้อม range/size |
| **Process** | 1-2 ประโยค — ทำอะไร + ทำไม |
| **Output** | `Type` + invariant ที่ output ต้อง satisfy |
| **Failure mode** | ถ้า input ผิด → raise / None / silent log |
| **Trade-off** | <ทรัพยากรที่ใช้ — เช่น "Compute time +500ms แลก network I/O ลด 10×", "RAM +100 MB แลก disk I/O ตัด"> |
```

จบด้วย ASCII pipeline diagram + side-effect arrows

### Section 4: Stress Test + Counterfactuals + Recap

**4.1 Complexity Analysis (บังคับ):**

```markdown
| มิติ | ค่าปัจจุบัน | ที่มา |
|---|---|---|
| Time complexity | O(?) | <where the dominant cost is> |
| Space complexity | O(?) | <where memory peaks> |
| I/O complexity | O(?) | <network round-trips, disk seeks> |
```

**4.2 Stress projection ที่ 100× input:**

```markdown
| N ปัจจุบัน | N × 100 | คอขวดแรกที่จะเจอ | Mitigation ระยะสั้น |
|---|---|---|---|
| <e.g. 3,620 entities> | <362,000> | <e.g. "Cypher MATCH all + collect() → OOM ที่ ~100K rows"> | <e.g. "Process in batches of 10K via SKIP/LIMIT"> |
```

**4.3 ตาราง "ห้ามทำ"** (≥ 4 ข้อ) — ทุกข้อต้องระบุ mechanism, ไม่ใช่ "best practice"

**4.4 หลักการ 3-5 ข้อที่ code นี้บังคับ** — เป็น axiom 1 ประโยค/ข้อ

**4.5 Defense-style Q&A** (2-3 ข้อ) — กรรมการ/reviewer จะถามอะไร + คำตอบ mechanism-driven

### Section 5 (ใหม่): Implicit Connections — Auto-discovered Related Files

ใช้ `Grep` / `Glob` หา:
1. ไฟล์ที่ **import** module นี้ (downstream consumers)
2. ไฟล์ที่ **module นี้ import** (upstream dependencies)
3. ไฟล์อื่น ๆ ในโปรเจกต์ที่จัดการ concept เดียวกัน (เช่น ถ้าเป็น embedding ไฟล์ → list ไฟล์ embedding อื่น)
4. Obsidian notes ที่ tag เกี่ยวข้อง (search ใน Vault)

แสดงเป็นตาราง:

```markdown
| Connection | File / Note | ทำไม link |
|---|---|---|
| **Caller** | `src/X.py:42` | imports `compute_specificity()` from this file |
| **Callee** | `src/Y.py` | this file calls `Y.get_driver()` |
| **Sibling** | `src/embed_chunks.py` | จัดการ embedding เหมือนกัน — different target node |
| **Conceptual** | `[[PPR_explain]]` | downstream consumer ที่ใช้ specificity เป็น seed weight |
| **Cross-link** | `[[Code_Explained_kg_store]]` | upstream — สร้าง :Entity node ก่อนหน้า |
```

**Discovery technique (บังคับ):**
```bash
# upstream/downstream imports
grep -rn "from semigraph.offline.<modname>" src/ scripts/ tests/
grep -rn "import <modname>" src/ scripts/

# sibling files by concept
ls src/semigraph/offline/  # then identify which match the same concern

# Vault concept matching (ถ้าจำเป็น)
ls /home/kantinan/Documents/Obsidian\ Vault/Agentic\ GraphRAG/ | grep -i <concept>
```

## Style Requirements (First Principles per CLAUDE.md)

1. **Constraint จริง → theory binding → mechanism → decision** — ทุกการเลือกของ code ต้องไล่ห่วงโซ่นี้ครบ
2. **Layered explanation** — fact → consequence → engineering decision
3. **Counterfactual + Boundary** — ทุก decision ตอบได้ "อะไรพังถ้าทำตรงข้าม" + "ตัวเลือกปัจจุบันพังเมื่อไหร่"
4. **Structure vs Semantics tag** — ทุก decision ใน Section 2 ต้อง tag ชัดเจน
5. **Trade-off explicit** — Section 3 ทุก step ต้องบอก "แลกอะไรกับอะไร"
6. **ภาษาไทยกึ่งทางการ + อังกฤษเฉพาะทับศัพท์ที่จำเป็น** — ห้าม "implement", "process", "approach" ถ้ามีไทยเทียบเท่า
7. **กระชับ** — 1.5–2 หน้ากระดาษ — ห้ามยืดเกิน

## Steps to Execute

1. **Read source file** ที่ `$0` ครบทุกบรรทัด
2. **Discover connections** (Section 5 input):
   - `grep -rn "from <module path>"` หา downstream
   - `grep -E "^from|^import" <source>` หา upstream
   - `ls` directory เดียวกัน หา siblings
3. **Identify**:
   - Theory ที่ผูกแต่ละ constraint (Big-O, CAP, Memory Hierarchy, Shannon, ...)
   - Decisions ใหญ่ + tag Structure vs Semantics
   - Time/Space/I/O complexity
   - Breaking point ของ current implementation
4. **Compute output path** — `/home/kantinan/Documents/Obsidian Vault/Agentic GraphRAG/Code_Explained_<basename>.md` (avoid overwrite — append `_v2`)
5. **Write YAML frontmatter ก่อน** — แล้วค่อยเขียน sections (1-5)
6. **Save via `Write` tool** ลง path ใน step 4 (Obsidian Vault path เท่านั้น — ห้าม save ที่อื่น)
7. **Confirm** to user with: output path + 1-line summary + 1 suggested next file

## Pitfalls to Avoid

- ❌ **ห้าม save ผิด path** — ต้อง Obsidian Vault `/home/kantinan/Documents/Obsidian Vault/Agentic GraphRAG/` เท่านั้น
- ❌ **ห้าม theory binding แบบลอย ๆ** — ถ้าบอก "Big-O" ต้องระบุ O(N), O(N²) ฯลฯ + ที่ไหนในโค้ดที่ dominant cost
- ❌ **ห้าม decision ไม่มี Counterfactual + Boundary limit** — 2 อันต้องครบ
- ❌ **ห้าม flow step ไม่มี Trade-off** — ทุก step ต้องชัดว่าแลกอะไร
- ❌ **ห้าม skip Section 5 (Implicit Connections)** — ใช้ Grep/Glob discovery จริง ไม่ใช่เดา
- ❌ **ห้าม YAML frontmatter ขาด field** — `complexity_time`, `breaking_point`, `core_mechanisms` ต้องมี
- ❌ **ห้าม analogy ที่ไม่ตรง mechanism** — "เหมือนพนักงานเสิร์ฟ" ตัดทิ้ง
- ❌ **ห้าม appeal to authority** — "best practice" / "Google ทำแบบนี้" — ต้องบอก mechanism
- ❌ **ห้าม dump code เกิน 5 บรรทัด** — snippet + file:line reference เท่านั้น
- ❌ **ห้ามเขียนยาวเกิน 2 หน้ากระดาษ** — concise > comprehensive
- ❌ **ห้ามอังกฤษพร่ำเพรื่อ** — "implement", "process", "approach" ถ้ามีไทยเทียบเท่า
