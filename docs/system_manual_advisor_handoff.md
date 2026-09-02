# SemiGraph System Manual — Advisor Docker Handoff

คู่มือนี้ใช้สำหรับส่งต่อ SemiGraph ให้อาจารย์บน Windows โดยให้อาจารย์ทำงานผ่าน
PowerShell และ Docker Desktop เท่านั้น ไม่ต้องสร้าง Conda environment และไม่ต้องรัน
Unit Test เดิมก่อนใช้งาน

ขอบเขตที่รองรับ:

- เปิด Agent UI และ Four-Way Comparison UI
- รัน Smoke แบบไม่เรียก LLM และไม่แก้ฐานข้อมูล
- เลือกรัน Vector, Graph, Agent + Vector หรือ Agent + Graph Eval
- รัน Eval แบบสั้นหรือครบ 74 คำถาม
- เปิด shell, อ่านและแก้ Source code จาก Windows ได้ทันที
- รัน SEC-to-Neo4j ingestion ต่อได้

ระบบนี้เป็น Research Reference Runtime ไม่ใช่ Production Deployment และไม่ใช่ระบบ
แนะนำการลงทุน

## 1. ภาพรวมแบบสั้นที่สุด

อาจารย์ใช้เพียง repository นี้และ private images 5 ตัวจาก GHCR:

```text
Windows source code ──bind mount──> Python/Streamlit container
                                      │
                                      ├── Production Neo4j
                                      ├── Controlled Neo4j
                                      ├── FinReflectKG Neo4j (extended)
                                      └── PostgreSQL (extended)
```

คำสั่งหลักทั้งหมดอยู่ใน `handoff.ps1`:

```powershell
.\handoff.ps1 setup
.\handoff.ps1 start
.\handoff.ps1 smoke
```

หลัง `start` เปิด <http://localhost:8501>

## 2. สิ่งที่ต้องมีบนเครื่อง Windows

1. Windows 10/11 แบบ 64-bit
2. Docker Desktop และ Docker CLI
3. Git
4. สิทธิ์อ่าน private repository `Semi-Graph-Project/Semi-Graph`
5. สิทธิ์ `read:packages` สำหรับ private GHCR packages
6. พื้นที่ว่างใน Docker อย่างน้อย 15 GB สำหรับชุด default
7. ถ้าจะใช้ชุด `extended` แนะนำอย่างน้อย 25 GB

ขนาดพื้นที่ข้างต้นเป็นพื้นที่เผื่อสำหรับ images, named volumes, model cache และผล Eval
ไม่ใช่ขนาด image ที่ยืนยันจากการ build บนเครื่องพัฒนาเครื่องนี้

Docker Desktop อาจใช้ WSL2 เป็น Linux-container backend ภายใน แต่ขั้นตอนทั้งหมดในคู่มือนี้
ทำจาก PowerShell อาจารย์ไม่ต้องเปิด WSL, ไม่ต้องใช้ Linux shell และไม่ต้องติดตั้ง Python
ใน WSL

## 3. ติดตั้งครั้งแรก

### 3.1 Clone source

```powershell
git clone https://github.com/Semi-Graph-Project/Semi-Graph.git
cd Semi-Graph
```

ถ้า clone ผ่าน HTTPS ไม่ได้ ให้ตรวจสิทธิ์ private repository ก่อน

### 3.2 Login private GHCR

สร้าง GitHub Personal Access Token (classic) ที่มี `read:packages` แล้วรัน:

```powershell
docker login ghcr.io -u YOUR_GITHUB_USERNAME
```

เมื่อ Docker ถาม Password ให้วาง token แทนรหัสผ่าน GitHub ถ้าองค์กรเปิด SSO ต้อง
authorize token ให้กับองค์กรก่อน ดูรายละเอียดจาก
[GitHub Container Registry authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

### 3.3 สร้าง `.env`

```powershell
.\handoff.ps1 setup
notepad .env
```

อย่างน้อยให้เปลี่ยนค่าต่อไปนี้:

```env
OPENROUTER_API_KEY=your-own-key
NEO4J_PASSWORD=your-new-local-password
POSTGRES_PASSWORD=your-new-local-password
POSTGRES_AGENT_PASSWORD=your-new-local-password
EDGAR_EMAIL=your-email@example.com
EDGAR_ORGANIZATION=KMUTNB
```

ห้ามนำ `.env` เข้า Git ค่า password เป็น password ใหม่ของ runtime เครื่องอาจารย์
เพราะชุดส่งมอบไม่รวม `system.dump` หรือบัญชีเดิมจากเครื่องผู้พัฒนา

### 3.4 Pull และเปิดชุด default

```powershell
.\handoff.ps1 start
```

คำสั่งนี้ทำสามอย่าง:

1. Pull application, Production Neo4j และ Controlled Neo4j images
2. เปิด containers ด้วย `--no-build`
3. แสดงสถานะ service

เปิด Agent UI ที่ <http://localhost:8501>

## 4. คำสั่งประจำวัน

| งาน | คำสั่ง |
|---|---|
| ดูสถานะ | `.\handoff.ps1 status` |
| Smoke แบบอ่านอย่างเดียว | `.\handoff.ps1 smoke` |
| เปิด Four-Way Comparison UI | `.\handoff.ps1 comparison` |
| เข้า shell ของ Python container | `.\handoff.ps1 shell` |
| ดู App log | `.\handoff.ps1 logs` |
| ดูพื้นที่ Docker | `.\handoff.ps1 disk` |
| เปิด FinReflectKG + PostgreSQL | `.\handoff.ps1 extended` |
| ปิด containers แต่เก็บข้อมูล | `.\handoff.ps1 stop` |

`stop` ไม่ลบ named volumes เมื่อเปิดใหม่ข้อมูลและผลที่เขียนลงฐานข้อมูลยังอยู่

## 5. Demo UI

### 5.1 Agent UI — port 8501

เปิดพร้อมชุด default:

```powershell
.\handoff.ps1 start
```

UI นี้มาจาก `app.py` และเลือกได้สามแบบ:

- Full Agent Routing
- Agent Locked Vector
- Agent Locked Graph

Agent จะวางแผน Retrieval Task, เรียก Tool, ประเมินหลักฐาน, retry เมื่อจำเป็น และ
สังเคราะห์คำตอบพร้อม citation

### 5.2 Four-Way Comparison UI — port 8502

```powershell
.\handoff.ps1 comparison
```

UI นี้มาจาก `Demo/Mock_Result.py` และเปรียบเทียบ:

- Vector-only
- Graph-only
- Agent + Vector
- Agent + Graph

Service นี้ใช้ application image เดียวกับ Agent UI จึงไม่เพิ่ม image ซ้ำบน Disk
แต่ใช้ RAM เพิ่มขณะเปิดพร้อมกัน

## 6. Smoke และ Eval

### 6.1 Smoke ที่ไม่ใช้ API key

```powershell
.\handoff.ps1 smoke
```

`scripts/handoff_smoke.py` จะตรวจ Production และ Controlled Neo4j แบบอ่านอย่างเดียว:

- เชื่อมต่อ Bolt ได้
- อ่านจำนวน node และ relationship ได้
- APOC ใช้งานได้
- GDS ใช้งานได้

Smoke นี้ไม่สร้างหรือลบ node ใด ๆ

### 6.2 Eval ทดลองสั้น ๆ

Vector retrieval-only ไม่เรียก LLM:

```powershell
.\handoff.ps1 eval-smoke -Tool vector -Limit 3 -Workers 2 -VersionName advisor_smoke
```

Graph ตามค่า `config/default.yaml` ปัจจุบันใช้ LLM triple filter จึงต้องมี
`OPENROUTER_API_KEY`:

```powershell
.\handoff.ps1 eval-smoke -Tool graph -Limit 3 -Workers 2 -VersionName advisor_graph_smoke
```

Agent modes ใช้ LLM สำหรับ PlanRoute และ Assess แม้เลือก `retrieve_only`

### 6.3 Eval ครบ 74 คำถาม

```powershell
.\handoff.ps1 eval -Tool vector -Mode retrieve_only -Workers 4 -VersionName advisor_vector
.\handoff.ps1 eval -Tool graph -Mode retrieve_only -Workers 4 -VersionName advisor_graph
.\handoff.ps1 eval -Tool agent_vector -Mode retrieve_only -Workers 4 -VersionName advisor_agent_vector
.\handoff.ps1 eval -Tool agent_graph -Mode retrieve_only -Workers 4 -VersionName advisor_agent_graph
```

ถ้าต้องการสร้าง final answer เปลี่ยนเป็น:

```powershell
.\handoff.ps1 eval -Tool agent_graph -Mode full_answer -Workers 2 -VersionName advisor_agent_graph_answer
```

`full_answer` มีค่าใช้จ่ายและใช้เวลามากกว่า แนะนำเริ่ม `Workers 2` ก่อน ผลลัพธ์เขียนลง:

```text
benchmark/results/controlled_<tool>_sox74_<version>_<mode>.jsonl
benchmark/results/controlled_<tool>_sox74_<version>_<mode>.yaml
```

Eval แบบ `-Limit 3` ใช้ชื่อ scope `sox_smoke3` เพื่อไม่ปะปนกับผลครบ 74 ข้อ

### 6.4 รัน CLI โดยไม่ผ่าน PowerShell helper

```powershell
docker compose --env-file .env -f compose.handoff.yaml exec app `
  python eval_scripts/evaluate.py --help
```

ตัวเลือกหลักของ `evaluate.py`:

- `--tool`: `vector`, `graph`, `agent_vector`, `agent_graph`
- `--mode`: `retrieve_only`, `full_answer`
- `--workers`: จำนวนคำถามที่ทำพร้อมกัน
- `--limit`: จำนวนคำถามแรกสำหรับ Smoke
- `--version_name`: ชื่อกำกับไฟล์ผลลัพธ์

## 7. Ingestion

เส้นทางจริงคือ:

```text
SEC EDGAR
  → ingest.py ดาวน์โหลด filing
  → preprocess.py แยกและทำความสะอาด section
  → chunker.py สร้าง Chunk
  → kg_extract.py สกัด node/relationship ตาม ontology
  → kg_store.py เขียน Neo4j พร้อม provenance
  → embed scripts สร้าง vector/triple embeddings
  → compute_specificity.py
  → ตรวจจำนวนข้อมูลและ sync ticker config
```

### 7.1 ดูตัวเลือกโดยไม่รันจริง

```powershell
docker compose --env-file .env -f compose.handoff.yaml exec app `
  python scripts/pilot.py --help
```

### 7.2 ตรวจ Controlled corpus โดยไม่เขียนและไม่เรียก LLM

```powershell
docker compose --env-file .env -f compose.handoff.yaml exec app `
  python eval_scripts/Pilot_eval.py --limit 1 --load-only
```

### 7.3 Onboard ticker จริง

```powershell
.\handoff.ps1 ingest -Ticker NVDA -Workers 2
```

คำสั่งนี้เขียน Production Neo4j, ดาวน์โหลด SEC filing, เรียก LLM และสร้างไฟล์ใน
`data/` จึงควรทำหลัง Smoke ผ่านและตรวจ API key แล้ว การใช้ `Workers` สูงจะเพิ่ม RAM
และจำนวน LLM requests พร้อมกัน

ตัวเลือกที่ใช้บ่อย:

```powershell
docker compose --env-file .env -f compose.handoff.yaml exec app `
  python scripts/pilot.py --ticker NVDA --workers 2 --skip-download
```

รายละเอียดของแต่ละ phase อยู่ใน `scripts/pilot.py` และ `docs/offline_pipeline.md`

## 8. แผนที่ Code สำหรับอ่านต่อ

### 8.1 Eval

| จุดอ่าน | หน้าที่ |
|---|---|
| `eval_scripts/evaluate.py::evaluate_sox_queries` | วงรอบ SOX74, concurrency, Hit/Recall/MRR, trace output |
| `eval_scripts/evaluate.py::_run_agent` | แปลงผล Agent ให้เป็น evidence chunks สำหรับให้คะแนน |
| `eval_scripts/eval_agent.py::_build_eval_graph` | สร้าง Agent ที่ lock Vector หรือ Graph |
| `eval_scripts/eval_agent.py::generate_final_answer` | สร้างคำตอบจาก evidence ใน non-agent full-answer mode |
| `benchmark/freezes/sox74_retrieval_ablation_v1/` | ชุดข้อมูลและหลักฐานการทดลองที่ freeze ไว้ |

Eval วัด retrieval กับ answer แยกกัน อย่าใช้ Hit/Recall ของ retrieval ไปอ้างว่า
final answer ถูกต้องโดยอัตโนมัติ

### 8.2 Retrieval Algorithms

| จุดอ่าน | หน้าที่ |
|---|---|
| `src/semigraph/online/vector_search.py::trace_vector_search` | query embedding → vector candidates → metadata rerank → chunks |
| `src/semigraph/online/graph_search.py::_select_seeds` | เลือก triple/node/chunk seeds และ optional LLM triple filter |
| `src/semigraph/online/graph_search.py::trace_graph_search` | คุม Graph retrieval ทั้งเส้นและบันทึก stage trace |
| `src/semigraph/online/ppr.py::ensure_projection` | สร้างหรือ reuse GDS projection |
| `src/semigraph/online/ppr.py` | resolve source nodes และ `gds.pageRank.stream` |
| `src/semigraph/online/rerank.py` | ปรับ ranking ด้วย company/fiscal-year metadata |
| `src/semigraph/offline/specificity.py::compute_specificity` | คำนวณ Node Specificity สำหรับ seed weighting |
| `config/default.yaml::agent_retrieval` | ค่าที่ควบคุม candidate budget, seed mode, damping, graph mode และ filter |

แก่นของ Graph Search คือไม่ได้ให้ PPR อ่านข้อความโดยตรง แต่แปลง query เป็น seed ก่อน
แล้วให้ PPR กระจายน้ำหนักบน Entity + Chunk topology จากนั้นค่อยคืน Chunk ที่มีหลักฐาน

### 8.3 Agent Algorithms

| จุดอ่าน | หน้าที่ |
|---|---|
| `src/semigraph/agent/graph.py::build_agent` | ประกอบ LangGraph และเงื่อนไขเดิน node |
| `src/semigraph/agent/nodes.py::plan_route_node` | แตกคำถามเป็น Retrieval Tasks และ Evidence Requirements |
| `src/semigraph/agent/nodes.py::execute_attempt_node` | เรียก retrieval tool และบันทึก Attempt |
| `src/semigraph/agent/nodes.py::assess_node` | ประเมินหลักฐานและกำหนด Evidence Retry |
| `src/semigraph/agent/nodes.py::synthesize_attempts_node` | รวม Accepted Evidence เป็นคำตอบพร้อม citation |
| `src/semigraph/agent/tools.py` | adapter ของ Vector, Graph, Financial และ News |
| `src/semigraph/agent/ledger.py` | Attempt Ledger, trace และการเลือก synthesis context |

### 8.4 Ingestion และ Ontology

| จุดอ่าน | หน้าที่ |
|---|---|
| `src/semigraph/offline/ingest.py` | SEC EDGAR download และค้น filing path |
| `src/semigraph/offline/preprocess.py` | document streaming, HTML cleanup และ section extraction |
| `src/semigraph/offline/chunker.py` | token-aware chunk และ deterministic chunk ID |
| `src/semigraph/offline/kg_extract.py::extract_chunk` | LLM extraction และ ontology validation |
| `src/semigraph/offline/kg_store.py::KGStore` | MERGE graph/provenance เข้า Neo4j |
| `src/semigraph/ontology/schema.py::OntologyRegistry` | Single source of truth ของ ontology |
| `scripts/pilot.py::main` | ตัวคุม ingestion ทุก phase |

ถ้าจะเพิ่ม entity หรือ relationship type ให้แก้ `schema.py` ก่อน ห้าม hard-code label
ใหม่กระจายตาม call site

## 9. แก้ Code แล้วรันต่ออย่างไร

Repository ถูก mount เข้า `/workspace` ของ application container:

```yaml
volumes:
  - .:/workspace
```

ดังนั้นเมื่อแก้ `.py`, YAML หรือ Streamlit file จาก VS Code บน Windows container จะเห็น
ไฟล์ใหม่ทันที ไม่ต้อง build image ใหม่

```powershell
.\handoff.ps1 shell
python eval_scripts/evaluate.py --help
```

กรณีที่ต้องสร้าง application image ใหม่จริง ๆ:

- เพิ่ม/เปลี่ยน Python dependency
- เปลี่ยน base image หรือ OS package
- เปลี่ยน embedding model ที่ preload

งานเหล่านี้ให้ผู้ดูแล publish tag ใหม่ผ่าน GitHub Actions ไม่ควรให้อาจารย์ build เอง

## 10. Environment และ Service Topology

### 10.1 ตัวแปรสำคัญ

| ตัวแปร | ใช้เมื่อใด |
|---|---|
| `OPENROUTER_API_KEY` | Graph ที่ใช้ LLM filter, Agent, extraction และ full-answer Eval |
| `EDGAR_EMAIL`, `EDGAR_ORGANIZATION` | SEC EDGAR ingestion |
| `NEO4J_USER`, `NEO4J_PASSWORD` | Neo4j ทุก corpus |
| `POSTGRES_*` | extended PostgreSQL |
| `FINNHUB_API_KEY` | Financial/News supporting tools |
| `SEMIGRAPH_*_IMAGE` | tag ของ private GHCR images |

`PRODUCTION_NEO4J_URI`, `CONTROLLED_NEO4J_URI` และ DSN ภายในถูก Compose กำหนดให้
application container แล้ว ไม่ต้องใส่เองใน `.env`

### 10.2 Ports และ profiles

| Service | Profile | Windows URL/port | ใช้ทำอะไร |
|---|---|---|---|
| `app` | default | `http://localhost:8501` | Agent UI และ CLI container |
| `comparison-demo` | comparison | `http://localhost:8502` | Four-Way Comparison UI |
| `neo4j-production` | default | Browser `7474`, Bolt `7687` | Demo และ ingestion หลัก |
| `neo4j-controlled` | default | Browser `7477`, Bolt `7690` | SOX74 Eval |
| `neo4j-finreflectkg` | extended | Browser `7475`, Bolt `7688` | แหล่ง FinReflectKG เต็ม |
| `postgres` | extended | `5433` | Financial supporting data |

ใน container ให้ใช้ชื่อ service เช่น `bolt://neo4j-controlled:7687` ห้ามใช้
`localhost:7690` เพราะ `localhost` ภายใน container หมายถึง container ตัวเอง

## 11. Data persistence และ Disk

ฐานข้อมูลใช้ Docker named volumes ส่วน source, Eval results และ ingestion artifacts อยู่
ใน repository ฝั่ง Windows

ตรวจพื้นที่:

```powershell
.\handoff.ps1 disk
```

แนวทางประหยัด Disk:

1. ใช้ชุด default ก่อน
2. เปิด `extended` เฉพาะเมื่อใช้ FinReflectKG หรือ PostgreSQL
3. ใช้ `eval-smoke -Limit 3` ก่อนรันครบ
4. ตรวจ `benchmark/results/`, `data/raw/` และ `data/processed/` หลัง ingestion
5. ปิด UI ที่ไม่ใช้เพื่อลด RAM แม้ไม่ได้ลด image disk

คำสั่งที่ไม่ควรใช้โดยไม่สำรองข้อมูล:

```text
docker compose ... down -v
docker system prune -a --volumes
```

ทั้งสองคำสั่งอาจลบฐานข้อมูลหรือ images ที่ต้อง pull ใหม่ `handoff.ps1` จงใจไม่มีคำสั่ง
reset หรือ prune

Database image จะ seed ข้อมูลเฉพาะตอน named volume ว่าง ถ้าเปลี่ยน image tag แต่ใช้ volume
เดิม ระบบจะรักษาข้อมูลเดิมไว้ ไม่ overwrite

## 12. Troubleshooting

### `denied` หรือ `unauthorized` ตอน pull

- login `ghcr.io` ใหม่
- token ต้องมี `read:packages`
- ถ้าองค์กรใช้ SSO ให้ authorize token
- ผู้ดูแลต้องให้บัญชีอาจารย์เข้าถึง repository/package

### Docker engine is not ready

เปิด Docker Desktop รอจนสถานะ Engine running แล้วเปิด PowerShell ใหม่

### PowerShell ไม่อนุญาตให้รัน `handoff.ps1`

อนุญาตเฉพาะ PowerShell session ปัจจุบัน แล้วลองใหม่:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\handoff.ps1 start
```

### Port is already allocated

ปิด Compose ชุดเดิมหรือโปรแกรมที่ใช้ port `8501`, `8502`, `7474`, `7475`, `7477`,
`7687`, `7688`, `7690` หรือ `5433`

```powershell
docker ps
.\handoff.ps1 stop
```

### App unhealthy หรือ UI เปิดไม่ได้

```powershell
.\handoff.ps1 status
.\handoff.ps1 logs
```

### Eval แจ้งว่า API key หาย

แก้ `OPENROUTER_API_KEY` ใน `.env` แล้ว restart application container:

```powershell
docker compose --env-file .env -f compose.handoff.yaml restart app
```

### แก้ dependency แล้ว import ไม่เจอ

Source mount เปลี่ยน code ได้ทันที แต่ไม่ได้ติดตั้ง dependency ใหม่ ให้ผู้ดูแลเพิ่ม version ใน
`requirements-handoff.txt` แล้ว publish application image tag ใหม่

## 13. ส่วนผู้ดูแล: เตรียมและ Publish Images

ส่วนนี้ไม่ใช่งานของอาจารย์

### 13.1 Export database assets

ต้องมีพื้นที่ว่างอย่างน้อย 4 GB และยอมรับว่า Neo4j Community แต่ละตัวจะ offline ชั่วคราว:

```bash
bash scripts/export_handoff_snapshots.sh
```

Script จะสร้าง:

```text
handoff-assets/advisor-data-v1/
├── production.neo4j.dump
├── controlled.neo4j.dump
├── finreflectkg.neo4j.dump
├── semigraph.postgres.sql.gz
└── SHA256SUMS
```

Script ไม่ export `system.dump`, ไม่รวม user/password เดิม และไม่ overwrite asset เก่า
ห้าม copy Neo4j store files ขณะ database ทำงาน Neo4j Community รองรับ
`neo4j-admin database dump` เมื่อ DBMS offline ตาม
[Neo4j Operations Manual](https://neo4j.com/docs/operations-manual/current/backup-restore/offline-backup/)

### 13.2 สร้าง private Release สำหรับ snapshot assets

```bash
gh release create advisor-data-v1 \
  handoff-assets/advisor-data-v1/* \
  --title "SemiGraph advisor data v1" \
  --notes "Private database assets for the advisor handoff" \
  --latest=false
```

Release อยู่ใน private repository และใช้เป็น input ชั่วคราวให้ workflow ไม่ต้อง commit
binary dumps เข้า Git

### 13.3 Build/Push บน GitHub Actions

1. Push source และ workflow ขึ้น private GitHub repository
2. เปิด Actions → `Publish advisor handoff images`
3. เลือก `Run workflow`
4. ใส่ `image_tag=advisor-v1`
5. ใส่ `snapshot_release=advisor-data-v1`
6. รอให้ทั้ง 5 images publish สำเร็จ
7. ตรวจว่า packages เป็น private และอาจารย์มี Read access

Workflow ใช้ `GITHUB_TOKEN` ที่มี `contents: read` และ `packages: write` ไม่ต้องสร้าง
registry password เพิ่มใน repository secrets ดู permission contract จาก
[GitHub Packages workflow documentation](https://docs.github.com/en/packages/managing-github-packages-using-github-actions-workflows/publishing-and-installing-a-package-with-github-actions)

### 13.4 Checklist ก่อนส่งจริง

- [ ] Source commit/tag ที่ต้องการส่งถูก push แล้ว
- [ ] Snapshot checksums ผ่าน
- [ ] GitHub Actions publish images ทั้ง 5 ตัวผ่าน
- [ ] `.env.handoff.example` ชี้ image tag เดียวกับที่ publish
- [ ] ทดลอง clone ใหม่บน Windows ที่ไม่มี Python project environment
- [ ] `handoff.ps1 start` ผ่านโดยไม่มี local build
- [ ] `handoff.ps1 smoke` ผ่าน
- [ ] Agent UI และ Comparison UI เปิดได้
- [ ] Vector Eval smoke ผ่าน
- [ ] Graph/Agent Eval smoke ผ่านด้วย key ของผู้ทดสอบ
- [ ] ไม่พบ `.env`, API keys หรือ `system.dump` ใน Git/Release/images

## 14. สถานะการตรวจของชุดเอกสารนี้

ตรวจบนเครื่องพัฒนาโดยไม่ build image จริงตามข้อจำกัด Disk:

- Docker Compose default, comparison และ extended parse ได้
- Dockerfile application ผ่าน BuildKit `--check`
- Python และ shell scripts ผ่าน syntax check
- Eval/Demo tests ที่เกี่ยวข้องผ่าน
- Demo, Eval และ ingestion CLI `--help` เปิดได้

สิ่งที่ยังต้องทำก่อนส่งให้อาจารย์จริงคือรัน workflow build/publish และทดสอบ pull บน clean
Windows ตาม checklist ข้างบน การตรวจแบบไม่ build ไม่ใช่หลักฐานว่า image ทุก layer ติดตั้งและ
start ได้จริง
