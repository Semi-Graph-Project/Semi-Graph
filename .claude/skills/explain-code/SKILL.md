---
description: Explain a Python code file using First Principles Thinking — break it down into the constraints that forced each design choice, then show how the code composes back from those axioms. 4 sections: constraints, decision tree, end-to-end flow with typed I/O, and counterfactuals. Saves to Obsidian Vault.
arguments:
  - file_path
allowed-tools: Read, Write
---

## Task

Read the Python file at `$0`, then generate a deep-dive explanation following the structure below, and save it to the Obsidian Vault.

## Output File Path

Compute the output path as:

```
/home/kantinan/Documents/Obsidian Vault/Agentic GraphRAG/Code_Explained_<basename>.md
```

Where `<basename>` is the source file name without `.py` extension. If the source file is in a subdirectory like `src/semigraph/offline/kg_store.py`, use just `kg_store` as the basename.

If a file with the same name already exists, append `_v2`, `_v3` etc.

## Required Structure (ความยาวรวมประมาณ 1.5–2 หน้ากระดาษ)

The output document MUST have these 4 sections in this exact order:

### Section 1: Constraint ของปัญหา (First Principles starting point)

- 2-3 ประโยคบอกว่า code นี้ทำอะไร + ปัญหาอะไรที่บังคับให้ต้องมี
- **ตาราง Constraint** ระบุข้อเท็จจริงที่ฝืนไม่ได้ที่ขับ design (อย่างน้อย 3 ข้อ — เช่น hardware limit, library spec, protocol requirement, data size, latency budget)
  - คอลัมน์: `#`, `Constraint`, `ที่มา` (hardware/library/protocol/spec)
- ตำแหน่งใน pipeline ใหญ่ — รับ input จากใคร ส่ง output ไปไหน, อยู่ Phase ไหน

**ห้ามใช้ analogy แบบ "เหมือนพนักงาน...", "นึกภาพว่า..."** — ถ้าจะใส่ analogy ต้องตรง mechanism 1:1 (ไม่ใช่แค่ feel เหมือน)

### Section 2: Decision Tree (ทำไมเลือกแบบนี้ ไม่เลือกแบบอื่น)

แสดง 2-4 design decisions ใหญ่ที่ code ตัดสิน — แต่ละ decision รูปแบบ:

```markdown
#### D<N>: <ชื่อ decision>

| Option | กลไก | Verdict |
|---|---|---|
| Option A | อธิบาย mechanism สั้น | ✅/❌ + เหตุผลที่ผูกกับ Constraint #X |
| Option B | ... | ... |

**Counterfactual:** ถ้าเลือกที่ตัดทิ้ง → จะพังตอนไหน เป็นตัวเลข/หน่วยอะไร
```

Decisions ควรครอบคลุม: library choice, data structure, IO pattern, error handling — เลือกเฉพาะที่มี alternative ชัดเจนเท่านั้น (ไม่ใช่ทุกบรรทัด)

### Section 3: Flow End-to-End (Pipeline)

แสดง execution trace ตั้งแต่จุดเริ่มต้นจนสิ้นสุด — public API → internal calls → side effects

**กฎเหล็ก:** ทุก step ต้องมี Input / Process / Output แบบ **typed** ชัดเจน

รูปแบบของแต่ละ step:

```markdown
#### Step N: <ชื่อ step> — `function_or_method_name()`

**Constraint ที่ enforce:** <constraint # หรือสรุปสั้น ที่บังคับให้ step นี้ทำงานแบบนี้ ไม่ใช่แบบอื่น>

| | |
|---|---|
| **Input** | `parameter_name: TypeAnnotation` พร้อมคำอธิบาย + ขนาด/range ที่ valid |
| **Process** | 1-2 ประโยค — *ทำอะไร* + *ทำไมต้องทำขั้นนี้ก่อน/หลังขั้นอื่น* |
| **Output** | `return_type: TypeAnnotation` พร้อมคำอธิบาย + invariant ที่ output ต้อง satisfy |
| **Failure mode** | ถ้า input violate constraint → output เป็นอะไร (raise / return None / etc.) |

ตัวอย่างการเรียก:
\`\`\`python
result = function_name(arg1, arg2)
\`\`\`
```

ลำดับ step ต้องสะท้อน flow จริง — ถ้ามี loop หรือ branch ให้แสดงด้วย indent หรือ ASCII arrow

ลงท้ายด้วย ASCII pipeline diagram สรุป:

```
input ──► [Step 1] ──► intermediate ──► [Step 2] ──► output
              ↑                              ↓
              └─── side-effect / log ────────┘
```

### Section 4: Counterfactuals + Recap

- **ตาราง "ห้ามทำ"** อย่างน้อย 4 ข้อ — แต่ละข้อรูปแบบ:
  - `ห้ามทำ` | `เหตุผลทาง mechanism (ไม่ใช่ "best practice")`
- **3-5 หลักการที่ code นี้บังคับ** — สรุปเป็น axiom ที่อ่านเข้าใจใน 1 ประโยคต่อข้อ (ห้ามขึ้นด้วย "นึกภาพว่า..." / "เปรียบเทียบเป็น...")
- **Defense-style Q&A** (optional, 2-3 ข้อ) — คำถามที่กรรมการ/code reviewer อาจถามตอนเห็น code นี้ครั้งแรก พร้อมคำตอบที่ขับด้วย mechanism

## Style Requirements

ตาม [CLAUDE.md](../../../CLAUDE.md) > Response Style (First Principles):

1. **เริ่มจาก constraint จริง ไม่ใช่ pattern ที่คุ้นเคย** — ทุกการเลือกของ code ต้องตอบได้ว่า constraint อะไรบังคับ
2. **Layered explanation** — fact → consequence → engineering decision (ไม่ใช่ analogy)
3. **ทุก decision ต้องตอบได้ "อะไรพังถ้าทำตรงข้าม"** พร้อมหน่วยที่วัดได้ (เวลา, RAM, ค่า API, recall)
4. **ภาษาไทยกึ่งทางการ + อังกฤษเฉพาะทับศัพท์ที่จำเป็น** — ใช้ได้: ชื่อ library/tool, technical term ที่แปลแล้วเสียความ. ห้าม: "implement", "process", "approach" ถ้ามีไทยเทียบเท่า
5. **ห้ามทับศัพท์คำที่ควรอธิบาย** — ผิด: "ทำไมต้อง APOC — Cypher pure ไม่ allow parameterize relationship type" / ถูก: "ทำไมต้อง APOC? เพราะ Cypher ตัวเปล่าบังคับให้ชื่อ relationship เป็น literal ตอน parse — ใส่ตัวแปรไม่ได้ APOC ใช้ runtime call ของ procedure ข้ามข้อจำกัดนี้"
6. **ใช้ตาราง / bullet** เมื่อเปรียบเทียบหลายมิติ ดีกว่า prose ยาว
7. **กระชับ** — ความยาวประมาณ 1.5–2 หน้ากระดาษ ไม่ยืดเกิน

## Document Header Template

ใช้ header นี้ทุกครั้ง:

```markdown
# Code Explained — `<original_filename_with_ext>`

> เอกสารนี้อธิบาย code file ที่ `<full_path>` แบบ First Principles — เริ่มจาก constraint, ตามด้วย decision tree, flow แบบ typed I/O, และ counterfactuals
> Generated by `/explain-code` skill
>
> Cross-link: [[CLAUDE]] | (เพิ่ม link อื่นๆ ที่เกี่ยวข้องถ้ามี — เช่น Pipeline_Review, Concept_Library_Wrapper, Agentic_Layer_Implementation)

---
```

## Steps to Execute

1. Read the source file at `$0`
2. Identify:
   - **Constraints** — hardware limits, library specs, protocol requirements, data size, latency budgets ที่ขับ design
   - **Major design decisions** ที่มี alternative ชัดเจน (model choice, library choice, IO pattern, error handling)
   - **Public API surface** + internal flow + key types/dependencies
3. Compute the output path (avoid overwriting existing notes — append `_v2` etc.)
4. Write the document following the structure above — เริ่มทุก section จาก constraint ไม่ใช่จาก analogy
5. Confirm to the user with:
   - Output file path
   - 1-line summary of what was explained
   - Suggest next file to document if there's an obvious related one

## Pitfalls to Avoid

- ❌ **ห้ามใช้ analogy ที่ไม่ตรง mechanism** — "เหมือนพนักงานเสิร์ฟ", "นึกภาพว่า memory เป็นตู้เก็บของ" — ไร้ค่าสำหรับ engineer ที่ต้อง debug จริง
- ❌ **ห้าม appeal to authority** — "เพราะเป็น best practice", "Google ทำแบบนี้" — ต้องบอกเหตุผลทาง mechanism
- ❌ **ห้าม dump code ทั้งหมด** — ใส่เฉพาะ snippet สั้น ๆ ที่ illustrate decision เท่านั้น
- ❌ **ห้าม skip Section 4 (Counterfactuals + Recap)** — เป็นส่วนที่บอก "อะไรพังถ้าทำตรงข้าม"
- ❌ **ห้ามให้ Section 3 ขาด typed I/O** — ทุก step ต้องมี Input/Process/Output + Failure mode ชัดเจน
- ❌ **ห้าม Decision ที่ไม่มี Counterfactual** — ทุก decision ต้องบอกได้ว่าทางที่ตัดทิ้งจะพังตอนไหน เป็นหน่วยอะไร
- ❌ **ห้ามเขียนยาวเกิน 2 หน้ากระดาษ** — กระชับเป็น priority
- ❌ **ห้ามอังกฤษพร่ำเพรื่อ** — "implement", "process", "approach" ถ้ามีคำไทยเทียบเท่า
