---
tags: [phase-d, agent, nodes, code-explained, debug]
purpose: อธิบาย nodes.py ของ Phase D แบบเน้นการไหลของ state, เหตุผลเชิงออกแบบ, และวิธี debug ทีละขั้น
status: living-doc
created: 2026-06-26
updated: 2026-06-26
related:
  - "[[Code_Explained_Phase_D_Agent_State]]"
  - "[[Plan Phase D - Agentic Engine]]"
  - "[[Agentic_Layer_Implementation]]"
---

# Code Explained — Phase D Nodes

> อธิบายไฟล์ `src/semigraph/agent/nodes.py` แบบลงไปถึงแก่นว่าแต่ละ node มีหน้าที่อะไร, helper แต่ละตัวช่วยแก้ปัญหาอะไร, และ state เดินอย่างไรจาก query ไปจนถึงคำตอบ

Cross-link: [[Code_Explained_Phase_D_Agent_State]] | [[Plan Phase D - Agentic Engine]] | [[Agentic_Layer_Implementation]]

---

## TL;DR

`nodes.py` คือ **สมองเชิงขั้นตอน** ของ agent

- `state.py` บอกว่า memory มีช่องอะไรบ้าง
- `graph.py` บอกว่า node ไหนต่อ node ไหน
- `nodes.py` บอกว่า "เมื่อถึง node นี้ ต้องอ่าน state อะไร แล้วคืนอะไรกลับไป"

ถ้าพูดแบบ First Principle:

1. User query ใหญ่เกินไปสำหรับ retrieval รอบเดียว
2. จึงต้องแตกเป็น subquery
3. แต่ละ subquery ต้องเลือก tool ให้เหมาะ
4. retrieval อย่างเดียวไม่พอ ต้องมีคนสรุปว่า evidence พูดว่าอะไร
5. แล้วต้องมีคนตัดสินว่า "พอจะตอบหรือยัง"
6. ถ้ายังไม่พอ ต้อง retry แบบมี feedback
7. ถ้าครบทุก subquery แล้ว ค่อยสังเคราะห์เป็นคำตอบสุดท้าย

`nodes.py` คือการแปลง logic 7 ข้อนี้ให้เป็น state machine ที่รันได้จริง

---

## ชั้น 1 — ภาพใหญ่ของไฟล์นี้

โครงสร้างหลักของ `nodes.py` แบ่งได้เป็น 3 ชั้น:

| ชั้น | มีอะไร | หน้าที่ |
|---|---|---|
| Node layer | `plan_node`, `tool_select_node`, `execute_node`, `observe_node`, `reflect_node`, `advance_subquery_node`, `synthesize_node` | ทำงานระดับ workflow |
| Helper layer | ฟังก์ชันขึ้นต้นด้วย `_...` | แยก logic ย่อยออกมาให้ node อ่านง่ายและ test ง่าย |
| Debug layer | `if __name__ == "__main__"` + `_run_*_debug_demo()` | รันจำลองทีละขั้นโดยไม่ต้องชน LLM/Neo4j จริง |

หลักออกแบบสำคัญ:

- node แต่ละตัวควรมี **หน้าที่เดียว**
- helper ควรเป็น **logic ที่ deterministic**
- state update ควรเป็น **partial update** ไม่เขียนทับทุกอย่าง
- trace ควรเป็น **append-only เท่าที่ทำได้** เช่น `tool_call_log`, `observation_history`, `reflection_history`

---

## ชั้น 2 — Dataflow ทั้งไฟล์

```text
original_query
  -> plan_node
       writes: subqueries, current_subquery_idx, round

  -> tool_select_node
       reads: current subquery, retry_query, reflection_feedback
       writes: next_tool

  -> execute_node
       reads: next_tool
       writes: latest_chunks, chunks_history, tool_call_log

  -> observe_node
       reads: latest_chunks
       writes: observation_text, observation_history

  -> reflect_node
       reads: observation_text, observation_history, tool_call_log
       writes: sufficient, reflection_reason, retry_query,
               reflection_feedback, round, reflection_history, stop_reason

  -> if sufficient and more subqueries
       advance_subquery_node
       writes: current_subquery_idx + resets round-local fields

  -> if sufficient and last subquery
       synthesize_node
       writes: final_answer, citation_map
```

แก่นจริง ๆ คือ:

- `plan` แตกงาน
- `tool_select` เลือกวิธีหา
- `execute` หา evidence
- `observe` ย่อย evidence เป็นข้อความสั้น
- `reflect` ใช้ข้อความสั้นนั้นตัดสินใจเรื่อง control flow
- `synthesize` รวม evidence ทั้งหมดเป็น answer

---

## Node by Node

## `plan_node(state)`

### ปัญหาที่มันแก้

query ของ user มักเป็น compound question เช่น:

```text
How do KLA yield improvements at TSMC affect AMD gross margin?
```

ถ้าโยนไป retrieval ตรง ๆ มี 3 งานปนกัน:

- KLA คือใคร
- TSMC เกี่ยวอะไร
- AMD gross margin โดนยังไง

planner จึงต้องทำให้ query กลายเป็นงานย่อยที่ retrieval หนึ่งรอบมีโอกาสสำเร็จ

### Input / Output

Input หลัก:

- `original_query`

Output:

```python
{
  "subqueries": [...],
  "current_subquery_idx": 0,
  "round": 0,
}
```

### Algorithmic Thinking

1. อ่าน `original_query`
2. เรียก LLM ด้วย `PLANNER_SYSTEM_PROMPT`
3. คาดหวัง JSON ที่มี `subqueries`
4. ตัดให้เหลือไม่เกิน 3 ข้อ
5. กรองค่าแปลก เช่น ว่าง, ไม่ใช่ string
6. ถ้า parse พัง ให้ fallback เป็น `[original_query]`

### หลักออกแบบ

- planner เป็นคน **init traversal state**
- planner ไม่ควรยุ่งกับ retrieval หรือ evidence
- planner ต้องมี fallback เสมอ เพราะถ้าเริ่ม run ไม่ได้ graph ทั้งเส้นล่มทันที

---

## `tool_select_node(state)`

### ปัญหาที่มันแก้

subquery แต่ละข้อไม่ได้ควรใช้ backend เดียวกัน

ตัวอย่าง:

- "latest FY2025 revenue" ควรไป `financial`
- "what AMD says about AI strategy" ควรไป `vector`
- "supplier chain between KLA, TSMC, AMD" ควรไป `graph`

### Input / Output

อ่าน:

- `subqueries`
- `current_subquery_idx`
- `retry_query`
- `reflection_feedback`

เขียน:

```python
{
  "next_tool": {
    "name": "...",
    "args": {"query": "...", "top_k_chunks": 5}
  }
}
```

### Algorithmic Thinking

1. หา `current_subquery`
2. ถ้ามี `retry_query` ให้ใช้เป็น candidate query ก่อน
3. ถ้ามี `reflection_feedback` แนบให้ router รู้ว่ารอบก่อนขาดอะไร
4. เรียก LLM แบบ function calling
5. ถ้า LLM ไม่คืน tool call ที่สมบูรณ์ ให้ fallback
6. ใช้ rule-based guard `_should_force_financial_tool(...)` บังคับไม่ให้ financial query หลุดไป `news` หรือ `vector`

### หลักออกแบบ

- routing ต้องมีทั้ง **LLM flexibility** และ **hard rule guard**
- logic บังคับ `financial` ถูกแยกเป็น helper เพื่อ test ได้ตรง ๆ
- node นี้ไม่รัน tool เอง หน้าที่มีแค่ "ตัดสินใจ"

---

## `execute_node(state)`

### ปัญหาที่มันแก้

เมื่อ router เลือก tool แล้ว ต้องมี node ที่ "โง่ให้พอ" คือทำแค่ dispatch ไป retriever และเก็บผลให้ครบ

### Input / Output

อ่าน:

- `next_tool`
- `subqueries`
- `current_subquery_idx`
- `chunks_history`
- `tool_call_log`

เขียน:

- `latest_chunks`
- `chunks_history`
- `tool_call_log`

### Algorithmic Thinking

1. อ่าน `next_tool.name` และ `next_tool.args`
2. ถ้าไม่มี `query` ใน args ให้ fallback ไป `current_subquery`
3. lookup retriever จาก `RETRIEVERS`
4. ถ้าไม่มี retriever ชื่อนั้น ให้ log error แล้วคืน `latest_chunks=[]`
5. ถ้ามี retriever ให้เรียกมัน
6. กรองเฉพาะผลที่เป็น `dict`
7. append เข้า `chunks_history`
8. append trace เข้า `tool_call_log`

### หลักออกแบบ

- node นี้ intentionally dumb
- ไม่ตัดสินคุณภาพ evidence
- ไม่เปลี่ยน query
- ทำหน้าที่เหมือน I/O boundary ของ agent

เหตุผล: ถ้า `execute_node` เริ่มฉลาดเอง จะทำให้ debug ยากว่าปัญหาอยู่ที่ router หรือ execute

---

## `observe_node(state)`

### ปัญหาที่มันแก้

retriever คืน chunk ดิบมา แต่ `reflect_node` ไม่ควรอ่าน chunk ดิบยาว ๆ ตรง ๆ ทุกรอบ เพราะ:

- prompt ยาวขึ้น
- ตัดสินใจยากขึ้น
- trace ที่เก็บไว้ไม่อ่านง่าย

จึงต้องมีชั้น "อ่าน evidence แล้วสรุปใจความ"

### Input / Output

อ่าน:

- `latest_chunks`
- `next_tool`
- `round`
- `current_subquery`

เขียน:

- `observation_text`
- `observation_history`

### Algorithmic Thinking

1. ถ้า `latest_chunks` ว่าง -> เขียน observation ว่า retrieval ไม่เจอ evidence
2. ถ้ามี chunk:
   - ย่อ chunk เป็นข้อความที่ส่งเข้า LLM ได้
   - แนบ subquery และ tool name
   - ให้ LLM สรุปว่า evidence พูดว่าอะไร
3. ถ้า observe LLM พัง -> ใช้ `_fallback_observation(...)`
4. append observation ใหม่เข้า history

### หลักออกแบบ

- observe แยก "evidence reading" ออกจาก "control decision"
- reflect จึงอ่าน summary สั้นแทน raw chunk
- debug ก็ง่ายขึ้น เพราะ history อ่านได้เหมือน note log

---

## `reflect_node(state)`

### ปัญหาที่มันแก้

retrieval หนึ่งรอบอาจ:

- พอแล้ว
- ยังไม่พอ
- หรือวนไปเรื่อย ๆ ไม่จบ

จึงต้องมี node ตัดสินใจเรื่อง sufficiency และ loop control

### Input / Output

อ่าน:

- `round`
- `observation_text`
- `observation_history`
- `tool_call_log`
- `current_subquery`

เขียน:

- `round`
- `sufficient`
- `reflection_reason`
- `reflection_feedback`
- `retry_query`
- `stop_reason`
- `reflection_history`

### Algorithmic Thinking

1. increment `round`
2. ถ้าเกิน `MAX_REFLECTION_ROUNDS`:
   - force stop
   - ตั้ง `sufficient=True`
   - `stop_reason="max_rounds"`
3. ถ้ายังไม่เกิน:
   - สร้าง reflection context จาก query, subqueries, observation, tool log
   - ให้ LLM ตอบ JSON
   - parse เป็น `sufficient/reason/retry_query/feedback`
4. ถ้า parse พัง:
   - fallback เป็น insufficient
   - ใช้ current query เป็น retry query
5. append history

### หลักออกแบบ

- `reflect_node` เป็น **control node** ไม่ใช่ answer node
- `sufficient=True` ไม่ได้แปลว่า "โลกนี้ตอบได้สมบูรณ์" เสมอไป
- ในกรณี `max_rounds` มันแปลว่า "หยุด loop ได้แล้ว แล้วค่อยให้ synthesize ตอบแบบระวัง"

---

## `advance_subquery_node(state)`

### ปัญหาที่มันแก้

Phase D ตอนนี้ไม่ได้มีแค่ retry ใน subquery เดิม แต่มี multi-subquery traversal ด้วย  
พอ subquery หนึ่งจบแล้ว ต้องขยับ pointer และ reset field ที่เป็น local state ของ subquery ก่อนหน้า

### Algorithmic Thinking

1. อ่าน `current_subquery_idx`
2. สร้าง completion record ผ่าน `_build_subquery_completion(state)`
3. append เข้า `completed_subqueries`
4. เลื่อนไป subquery ถัดไป
5. reset:
   - `round`
   - `retry_query`
   - `reflection_feedback`
   - `reflection_reason`
   - `next_tool`
   - `latest_chunks`
   - `observation_text`

### หลักออกแบบ

- local state ของ subquery ก่อนหน้าไม่ควรปนกับ subquery ถัดไป
- แต่ trace ควรถูกเก็บไว้ใน `completed_subqueries`

---

## `synthesize_node(state)`

### ปัญหาที่มันแก้

เมื่อครบทุก subquery แล้ว เราไม่ได้อยากใช้ chunk ทั้งหมดตรง ๆ เพราะ:

- มีซ้ำ
- บาง chunk เป็น noise
- บาง chunk ถูกดึงจากคนละ subquery แต่สำคัญ

จึงต้องมีขั้น evidence selection ก่อนตอบ

### Algorithmic Thinking

1. รวม progress ของ subqueries ผ่าน `_collect_subquery_progress`
2. คำนวณ overall stop reason ผ่าน `_derive_overall_stop_reason`
3. เลือก chunk สำหรับ synthesis ผ่าน `_select_chunks_for_synthesis`
4. dedupe chunk ผ่าน `_dedupe_chunks_for_synthesis`
5. format เป็น numbered context ผ่าน `_format_chunks_for_synthesis`
6. เรียก LLM สร้าง final answer
7. ตัด citation index ที่ไม่มีจริงด้วย `_remove_invalid_citations`
8. สร้าง `citation_map` จากเลขที่ LLM cite จริง

### หลักออกแบบ

- synthesis ต้อง grounded กับ evidence จริง
- citation ต้อง trace กลับ chunk ได้
- context packing เป็น retrieval-quality stage หนึ่ง ไม่ใช่แค่ formatting stage

---

## Helper Functions — แบ่งตามหน้าที่

## กลุ่ม Router helpers

### `_get_current_subquery(state)`

โจทย์: node หลายตัวต้องรู้ว่า "ตอนนี้กำลังทำข้อไหน"  
วิธี: อ่าน `current_subquery_idx` แล้วหยิบจาก `subqueries`; ถ้าไม่พร้อมให้ fallback ไป `original_query`

### `_normalize_router_text(*parts)`

โจทย์: query, retry query, feedback มาจากหลายแหล่งและ spacing มั่วได้  
วิธี: รวมข้อความ -> collapse whitespace -> lowercase  
ผล: regex intent checks ทำงานนิ่งขึ้น

### `_matches_any_pattern(text, patterns)`

โจทย์: ต้องเช็ก intent หลาย pattern ซ้ำ ๆ  
วิธี: วน regex list แล้วคืน `True` ถ้าเจออย่างน้อยหนึ่งอัน

### `_has_financial_metric_intent`, `_has_financial_period_intent`, `_has_recency_marker`, `_has_explicit_news_intent`

โจทย์: แยก intent ย่อยออกเป็น boolean เล็ก ๆ  
เหตุผลเชิงออกแบบ: ทำให้ rule หลัก `_should_force_financial_tool()` อ่านง่ายและ test ง่าย

### `_should_force_financial_tool(*parts)`

โจทย์: financial query หลุดไป `news` ได้ง่ายถ้ามีคำว่า `latest`  
วิธี:

1. normalize text
2. ถ้า explicit news -> ห้าม force financial
3. ถ้ามี metric intent -> force financial
4. หรือถ้ามี recency + period intent พร้อมกัน -> force financial

นี่คือ rule guard ที่สำคัญมากของ router

---

## กลุ่ม Observation / Reflection helpers

### `_format_chunks_for_observation(chunks, ...)`

เป้าหมาย: แปลง chunk ดิบให้เป็น prompt-friendly block  
วิธี:

1. จำกัดจำนวน chunk
2. truncate text ถ้ายาวเกิน
3. ใส่ metadata ที่ช่วยอ่าน เช่น `chunk_id`, `ticker`, `fiscal_year`, `section`

### `_format_reflection_context(state)`

เป้าหมาย: ทำ context string ให้ reflect node เห็น history ที่พอเหมาะ  
วิธี:

1. original query
2. planned subqueries
3. current position
4. latest observation
5. observation history 3 รายการล่าสุด
6. tool log 3 รายการล่าสุด

หลักคิดคือ reflect ต้องเห็น "สั้นแต่พอ"

### `_parse_reflection_response(raw)`

เป้าหมาย: รับ raw LLM output แล้ว parse JSON อย่าง defensive  
กติกาสำคัญ:

- `sufficient` ต้องเป็น boolean จริง
- field อื่นแปลงเป็น string ได้
- ถ้าไม่มี `{...}` หรือ JSON เสีย ให้ throw เพื่อให้ caller fallback

### `_route_after_reflect(state)`

โจทย์: reflect จบแล้ว graph ควรไปไหนต่อ  
logic:

- `sufficient/max_rounds` + ยังมี subquery -> `advance_subquery`
- `sufficient/max_rounds` + ไม่มี subquery เหลือ -> `synthesize`
- อื่น ๆ -> `tool_select`

### `_has_remaining_subqueries(state)`

helper เล็ก ๆ แต่สำคัญ เพราะ route logic ใช้บ่อยและไม่ควรกระจายสูตร index compare ไปหลายจุด

---

## กลุ่ม Subquery progress helpers

### `_build_subquery_completion(state)`

สร้าง summary record ของ subquery ปัจจุบัน:

- index
- text
- stop reason
- reflection reason
- round

### `_collect_subquery_progress(state)`

เป้าหมาย: เวลาจะ synthesize ต้องรู้ progress ทั้งหมด  
วิธี:

1. เริ่มจาก `completed_subqueries`
2. สร้าง current completion
3. ถ้ายังไม่เคย append current subquery ให้เติมเข้าไป

ผล: แม้จะยังไม่ได้ `advance_subquery_node` ก็ยังสรุป progress ปัจจุบันได้

### `_derive_overall_stop_reason(subquery_progress)`

ถ้ามี subquery ไหนจบเพราะ `max_rounds` ให้ overall stop reason เป็น `max_rounds` ทันที  
เพราะมันบอกว่า answer สุดท้ายควร hedge มากขึ้น

### `_format_subquery_progress(subquery_progress)`

เป้าหมาย: แปลง progress เป็นข้อความที่ LLM อ่านง่าย  
นี่เป็น bridge ระหว่าง structured trace กับ prompt text

---

## กลุ่ม Synthesis helpers

### `_fallback_observation(...)`

สำรองเวลา observe LLM ล้ม โดยใช้ chunk แรกมาสร้าง note แบบ deterministic

### `_chunk_identity_key(chunk)`

เป้าหมาย: นิยาม "chunk นี้คือชิ้นเดียวกันไหม"  
ลำดับคิด:

1. ถ้ามี `chunk_id` ใช้เลย เพราะ stable ที่สุด
2. ถ้าไม่มี `chunk_id` ใช้ fingerprint จาก metadata + text

### `_dedupe_chunks_for_synthesis(chunk_history)`

วน chunk history ตามลำดับเดิม แล้วเก็บเฉพาะ key ที่ยังไม่เคยเห็น  
ผลคือ dedupe โดยไม่เสีย order

### `_safe_int(value, default)`

helper ป้องกัน crash เวลา `round` หรือ `n_chunks` มาเป็น string/None

### `_annotate_chunk_for_synthesis(chunk, batch)`

เพิ่ม metadata ภายใน เช่น:

- `_retrieval_tool`
- `_retrieval_round`
- `_retrieval_subquery`

เหตุผล: synthesis ควรรู้ว่า chunk นี้มาจากการค้นรอบไหนและเพื่อ subquery ไหน

### `_strip_internal_chunk_keys(chunk)`

ตอนคืน `citation_map` ให้ UI/consumer ไม่ควรมี field ภายในพวก `_retrieval_*`

### `_build_retrieval_batches(state)`

นี่คือ helper สำคัญสุดกลุ่มหนึ่ง

โจทย์:
- `chunks_history` เป็น flat list
- `tool_call_log` เป็น flat trace
- แต่เราต้องรู้ว่า chunk ไหนมาจาก tool call รอบไหน

วิธี:

1. ใช้ `tool_call_log` เป็น skeleton
2. ใช้ `n_chunks` เดิน cursor บน `chunks_history`
3. slice chunk กลับไปเป็น batch ต่อ tool call
4. ถ้ามี chunk เหลือท้าย list ที่ไม่ได้ map -> ใส่ batch `"tool": "unknown"`

นี่คือการ reconstruct provenance ระดับ retrieval batch จาก state ที่ถูก flatten ไว้

### `_get_preferred_round_for_subquery(reflection_history, subquery)`

เป้าหมาย: หา retrieval round ที่น่าจะเป็น evidence รอบที่ดีที่สุดของ subquery นี้  
กติกา:

1. ถ้ามี reflection ที่จบด้วย `sufficient/max_rounds` ให้ใช้รอบนั้นก่อน
2. ถ้าไม่มีก็ใช้รอบล่าสุดของ subquery

### `_select_chunks_for_synthesis(state, ...)`

นี่คือ heart ของ evidence packing

Algorithm:

1. แปลง history เป็น retrieval batches
2. หา ordered subqueries
3. หา preferred round ของแต่ละ subquery
4. วนทีละ subquery แล้วหยิบ chunk จาก preferred batch ก่อน
5. จำกัดจำนวน chunk ต่อ subquery
6. ถ้ายังไม่ถึง target total ค่อยเติมจาก batch อื่น
7. dedupe ระหว่างหยิบ

ผลทาง design:

- ไม่ bias ไปที่ chunk แรก ๆ ใน history อย่างเดียว
- พยายามให้ทุก subquery มีตัวแทน evidence

### `_format_chunks_for_synthesis(chunks, ...)`

แปลง chunk ที่เลือกแล้วให้เป็น numbered context `[1]`, `[2]`, ... พร้อม metadata  
พร้อมกันนั้นสร้าง `citation_lookup` ที่ map เลขอ้างอิงกลับไป metadata จริง

### `_extract_citation_indices(answer)`

ดึงเลข citation ที่ LLM ใช้ออกมาแบบไม่เอาซ้ำ

### `_remove_invalid_citations(answer, valid_indices)`

ถ้า LLM cite `[9]` แต่ context มีแค่ `[1]-[3]` ต้องลบทิ้งก่อน  
ขั้นนี้สำคัญมากเพราะช่วยให้ answer grounded ขึ้นและ UI ไม่หลงจับคู่ผิด

---

## Debug Harness ที่เพิ่มใน `if __name__ == "__main__"`

ตอนนี้ `nodes.py` รัน debug ได้ 3 โหมดโดยไม่ต้องชน LLM/Neo4j จริง

```bash
python -m semigraph.agent.nodes
python -m semigraph.agent.nodes all
python -m semigraph.agent.nodes helpers
python -m semigraph.agent.nodes flow
```

ความหมาย:

- `helpers`:
  print ผลของ helper เกือบทั้งหมดทีละตัว
- `flow`:
  จำลอง state machine ตั้งแต่ `plan -> tool_select -> execute -> observe -> reflect -> advance_subquery -> synthesize`
- `all`:
  รันสองอย่างรวมกัน

หลักการของ harness:

1. ใช้ `_DebugFakeLLM`
2. ใช้ `_debug_fake_retriever`
3. patch `get_llm`, `get_config`, และ `RETRIEVERS` ชั่วคราว
4. รัน node function ของจริงทีละตัว
5. print state/result แบบ step by step
6. restore ของจริงใน `finally`

ดังนั้น harness นี้ไม่ใช่ unit test แบบ pytest แต่เป็น **algorithmic walkthrough executable**

---

## วิธีอ่าน trace ตอนรัน

เวลารัน `flow` ให้ดู 3 อย่างพร้อมกัน:

1. `state.before / state.after_*`
   ใช้ดูว่าฟิลด์ไหนถูกเขียนเพิ่มหรือ reset
2. `*.result`
   ใช้ดู output contract ของ node แต่ละตัว
3. `route_after_reflect`
   ใช้ดูว่า control flow ตัดสินใจไปทางไหน

ถ้า debug ปัญหา loop:

- ดู `round`
- ดู `retry_query`
- ดู `stop_reason`
- ดู `reflection_history`

ถ้า debug ปัญหา answer/citation:

- ดู `_build_retrieval_batches`
- ดู `_select_chunks_for_synthesis`
- ดู `_format_chunks_for_synthesis.lookup`
- ดู `citation_map`

---

## สรุปเชิงออกแบบ

แก่นของ `nodes.py` ไม่ได้อยู่ที่ "เรียก LLM หลายรอบ"  
แต่อยู่ที่การแยกปัญหาให้เป็น state transition ที่ตรวจสอบได้

ลำดับคิดทั้งหมดของไฟล์นี้คือ:

1. แตก query ใหญ่เป็นงานย่อย
2. ตัดสินใจเลือกเครื่องมือ
3. เก็บผล retrieval แบบ traceable
4. สรุป evidence ให้สั้นลง
5. ใช้ summary นั้นตัดสินใจควบคุม loop
6. พอครบทุก subquery ค่อย pack evidence และตอบ

ถ้ามองแบบ algorithm:

```text
query
 -> decompose
 -> choose tool
 -> retrieve
 -> summarize evidence
 -> check sufficiency
 -> retry or advance
 -> synthesize with citations
```

`nodes.py` คือ implementation ของ algorithm นี้แบบแยก concern ชัดพอที่จะแก้คุณภาพทีละชั้นได้
