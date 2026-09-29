# สภาพแวดล้อม Benchmark: Qwen บน RunPod

บันทึกเมื่อ 28 กันยายน 2026 เวลา 03:02–03:05 น. (Asia/Bangkok)

เอกสารนี้เป็น snapshot จาก Pod ที่กำลังเปิดบริการ, config ใน working tree และ metadata ของผล Benchmark ที่มีอยู่ ไม่ใช่หลักฐานว่าทุกรอบในอดีตใช้ค่าตรงกันทั้งหมด โดยเฉพาะ timeout และการแก้ JSON ที่เปลี่ยนระหว่างทดลอง

## 1. การแบ่งงานระหว่างเครื่อง

```text
เครื่อง local: evaluate_new_agent.py + Agent + Retrieval + Embedding/Reranker + Neo4j
    → HTTPS ผ่าน RunPod proxy
RunPod: vLLM → Qwen/Qwen2.5-7B-Instruct → NVIDIA L4
```

ตัวประเมินรันบนเครื่อง local ส่วน Pod รับคำขอ LLM แบบ OpenAI-compatible API ดังนั้นเวลารวมของ Benchmark รวมงานฝั่ง local และการสื่อสารเครือข่ายด้วย

## 2. RunPod: Hardware และระบบ

| รายการ | ค่าที่ตรวจพบ | หลักฐาน/ขอบเขต |
|---|---|---|
| Pod ID | `nbyaocnexus8yy` | SSH banner |
| Container hostname | `2c4ff55003b7` | SSH shell |
| OS ใน container | Ubuntu 24.04.3 LTS, x86_64 | `/etc/os-release`, `lscpu` |
| GPU | NVIDIA L4 จำนวน 1 ใบ | `nvidia-smi` |
| VRAM ที่ driver รายงาน | 23,034 MiB (ประมาณ 22.49 GiB) | `nvidia-smi` |
| NVIDIA driver | 570.195.03 | `nvidia-smi` |
| CUDA version ที่ driver รายงาน | 12.8 | ไม่ใช่ CUDA build ของ PyTorch |
| CPU ของ host | AMD EPYC 7542 32-Core Processor | `lscpu` เห็น host 2 sockets, 128 logical CPUs |
| CPU quota ของ container | 13.6 CPU equivalents | `cpu.max`: `1360000 100000`; ไม่ใช่ 128 CPU ที่จองให้ Pod |
| RAM limit ของ container | 93,999,996,928 bytes ≈ 87.54 GiB | `/sys/fs/cgroup/memory.max` |
| RAM ของ host ที่มองเห็น | 755 GiB | `free -h`; ไม่ใช่ RAM quota ของ Pod |

ตอนตรวจ GPU utilization เท่ากับ 0% และ VRAM usage 19,086 MiB ตัวเลขนี้เป็น snapshot ตอนนั้น ไม่ใช่ peak usage หรือค่าเฉลี่ยระหว่าง Benchmark

## 3. RunPod: Runtime ที่รันจริง

อ่านเวอร์ชันด้วย `/workspace/venv/bin/python` ซึ่งตรงกับ process ของ vLLM การใช้ `python` จาก system ให้เวอร์ชันบางตัวต่างกัน จึงต้องอ้างอิง virtual environment นี้

| รายการ | เวอร์ชัน/ค่า |
|---|---|
| Virtual environment | `/workspace/venv` |
| Python | 3.12.3, GCC 13.3.0 |
| vLLM | `0.30.0+cu129` |
| PyTorch | `2.13.0+cu129` |
| `torch.version.cuda` | `12.9` |
| Transformers | `5.17.0` |
| Triton | `3.7.1` |
| FlashInfer Python | `0.6.18.post1` |
| Model | `Qwen/Qwen2.5-7B-Instruct` |
| Hugging Face cached `refs/main` | `a09a35458c702b33eeacc393d103063234e8bc28` |

Cached revision ข้างต้นอ่านจาก cache ปัจจุบัน คำสั่ง serve ไม่ได้ pin `--revision` จึงยังไม่ใช่การรับรอง revision สำหรับทุกรอบในอดีต

### Environment variables ที่ตรวจพบใน process vLLM

```bash
VIRTUAL_ENV=/workspace/venv
HF_HOME=/dev/shm/huggingface
HF_HUB_CACHE=/dev/shm/huggingface/hub
```

ตรวจเฉพาะตัวแปรที่เกี่ยวกับ runtime และไม่ใช่ secrets: ไม่พบ `CUDA_VISIBLE_DEVICES`, `VLLM_*`, `OMP_NUM_THREADS`, `TOKENIZERS_PARALLELISM` หรือ `PYTORCH_CUDA_ALLOC_CONF` ในรายการที่กรองจาก process นี้ การไม่ตั้งค่าไม่เท่ากับปิดความสามารถนั้น

### คำสั่ง serve ที่ตรวจจาก process

```bash
source /workspace/venv/bin/activate
export HF_HOME=/dev/shm/huggingface
export HF_HUB_CACHE=/dev/shm/huggingface/hub

vllm serve Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.88
```

บรรทัด activate/export ประกอบขึ้นจาก executable และ environment ที่ตรวจพบ ส่วน arguments ของ `vllm serve` ตรงกับ process ปัจจุบัน

| Engine setting | ค่าที่ตรวจพบ |
|---|---|
| Context limit | 32,768 tokens ต่อ sequence (input และ output รวมกัน) |
| GPU memory utilization setting | 0.88; เป็นค่ากำหนดหน่วยความจำ ไม่ใช่ GPU compute utilization |
| KV cache dtype setting | `auto` |
| Prefix caching | เปิด (`True`) |
| KV block size | 16 tokens |
| GPU blocks | 2,821 |
| KV cache capacity | 45,136 tokens |
| KV cache max concurrency metric | 1.37744140625; ความจุเทียบ sequence เต็ม context ไม่ใช่เพดานจำนวน requests |
| Quantization/dtype/parallelism flags | ไม่มีการระบุใน command; ยังไม่ได้ยืนยันค่าที่ resolve ของ engine ปัจจุบัน |

ค่าของ cache มาจาก `vllm:cache_config_info` ใน `/metrics`; context limit ยืนยันซ้ำจาก `/v1/models`

### Endpoint

```text
API base: https://nbyaocnexus8yy-8000.proxy.runpod.net/v1
Health:   https://nbyaocnexus8yy-8000.proxy.runpod.net/health
Metrics:  https://nbyaocnexus8yy-8000.proxy.runpod.net/metrics
Models:   https://nbyaocnexus8yy-8000.proxy.runpod.net/v1/models
```

URL เป็นของ Pod รอบนี้และอาจใช้ไม่ได้หลังหยุด/เปลี่ยน Pod; `/health` ใช้ตรวจสุขภาพ ไม่ใช่ API base สำหรับเรียกโมเดล

## 4. เครื่อง local ที่รันตัวประเมิน

| รายการ | ค่าที่ตรวจพบ |
|---|---|
| OS | Ubuntu 20.04.6 LTS, x86_64 |
| CPU | AMD Ryzen 7 5700U with Radeon Graphics, 8 cores / 16 threads |
| RAM / Swap ที่ OS เห็น | 5.6 GiB / 14 GiB |
| Project | `/home/kantinan/programming/project` |
| Conda environment | `senior_project_py312` |
| Python | 3.12.14 (Anaconda), GCC 14.3.0 |
| Git HEAD | `7a052af1b5724b9d2c2b32f3ba7af262ee28e16b` |
| Working tree | มีการแก้ไฟล์ที่ยังไม่ commit; HEAD อย่างเดียวสร้างสภาพทดลองนี้ซ้ำไม่ได้ |

แพ็กเกจหลักใน conda environment ที่ตรวจ ณ เวลาบันทึก:

```text
torch==2.13.0
transformers==4.57.6
langchain==1.3.18
langchain-core==1.6.1
langchain-openai==1.1.9
langchain-neo4j==0.10.0
langgraph==1.2.11
openai==1.109.1
httpx==0.28.1
neo4j==6.3.0
sentence-transformers==5.4.1
numpy==2.5.2
pydantic==2.13.5
PyYAML==6.0.3
```

นี่คือรายการแพ็กเกจหลัก ไม่ใช่ dependency lock ของทั้ง environment

## 5. Client และการสร้างคำตอบ

ค่าปัจจุบันจาก `config/default.yaml`:

```yaml
llm:
  provider: openai
  model: Qwen/Qwen2.5-7B-Instruct
  temperature: 0.0
  reasoning: {}
  base_url: https://nbyaocnexus8yy-8000.proxy.runpod.net/v1
  json_mode: true
  timeout: 300.0
evaluation:
  answer_audit_enabled: false
```

- Client ตั้ง `max_retries=2` ใน `src/semigraph/connections.py`
- ก่อนแก้ timeout ใช้ 120 วินาที; 300 วินาทีเป็นค่าที่เพิ่งเพิ่มหลังพบ `APITimeoutError` จึงห้ามระบุว่าผลก่อนหน้านั้นใช้ 300 วินาที
- Config ที่ไม่ระบุ timeout ใช้ค่าเริ่มต้น 120 วินาที รวมถึง OpenRouter config เดิม
- การเรียก Pod ใช้ `OPENAI_API_KEY=unused` เป็น placeholder ของ client; เอกสารนี้ไม่บันทึก API keys จริง
- JSON mode ของ Agent ผูก `response_format={"type":"json_object"}` ที่ planner และ synthesis ตามโค้ดปัจจุบัน ไม่ได้ผูกทุก LLM call
- `temperature=0.0` เป็นค่าจาก client; constructor ไม่ได้ระบุ `max_tokens`
- Model cache มี `generation_config.json`: temperature 0.7, top_p 0.8, top_k 20, repetition_penalty 1.05, do_sample true; เป็นค่าของไฟล์โมเดล ไม่ใช่หลักฐาน effective request settings ทั้งหมด เพราะ client ส่งค่าบางตัวทับ

## 6. Retrieval และ Agent ฝั่ง local

| รายการ | ค่าปัจจุบันจาก config/code |
|---|---|
| Embedding | `BAAI/bge-base-en-v1.5`, 768 dimensions |
| Embedding runtime | CPU, batch size 32, normalize true |
| Cross-encoder | `jinaai/jina-reranker-v1-tiny-en` |
| Cross-encoder runtime | ONNX `onnx/model_quantized.onnx`, CPUExecutionProvider |
| Cross-encoder input/batch | max_length 2048, batch_size 2, มี lock ให้ inference ทีละครั้งต่อ process |
| Reranker offline mode | โค้ดใช้ `setdefault` ให้ HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE, HF_DATASETS_OFFLINE เป็น `1` |
| Vector profile | candidate_pool_k 20, rerank_mode company+fiscal_year |
| Graph profile | top_k_entities 20, top_k_triples 10, top_k_chunk_seeds 5 |
| Graph PPR | damping 0.3, seed_mode triple, ppr_seed_weight_mode similarity_specificity |
| Graph options | use_expansion false, candidate_pool_k 20, rerank_mode cross_encoder, triple_filter llm |
| Graph chunk seed index | chunk_embedding |
| Agent budgets | max_planned_tasks 10, max_parallel_tasks 4, top_k_chunks 10 |
| Agent retries | max_attempts_per_task 2, max_assessment_attempts 2, max_technical_retries 1 |
| Synthesis budget | max_synthesis_chunks 10 |
| Assessment/ontology | assess_context_max_chars 60000, max_num_ontology 8 |

ค่าเหล่านี้เป็น config ปัจจุบัน การอ้างว่ารอบใดใช้ profile นี้ครบต้องตรวจ trace/arguments ของรอบนั้นด้วย

Neo4j: `Config` ของ shell ที่ตรวจให้ URI `bolt://localhost:7687` และ Docker ปัจจุบันมี `semigraph-neo4j` (7687), `semigraph-finreflectkg` (7688), `semigraph-controlled` (7690) ซึ่งใช้ image `neo4j:2025.04-community` เหมือนกัน ยังไม่มีหลักฐานจาก process ของรอบที่จบไปว่าเคย override `NEO4J_URI` หรือไม่ จึงไม่ควรเหมารวมว่าทุกผลใช้ฐานที่ 7690; image tag ก็ไม่ใช่การยืนยัน version ของ Neo4j/GDS ที่รันภายใน

## 7. Benchmark และคำสั่งรัน

- Entry point: `eval_scripts/evaluate_new_agent.py`
- Dataset: `benchmark/freezes/sox74_retrieval_ablation_v1/inputs/finreflectkg_sox_strict74.yaml` จำนวน 74 คำถาม
- Dataset SHA-256: `374ada2d8c00b701577e3a55ed46851d5554231742e47402255165362f645f6f`
- Evaluator constants: `TOP_K=10`, `VECTOR_INDEX=gold_chunk_embedding`
- Metadata ในผล Agent+Graph ทั้ง `qwen_fast`, `qwen_full_graph`, `qwen_full_graph_fix` ระบุ `workers=4`, selection 1–50, query_count 50; ตัวเลขนี้คือจำนวนที่เลือก ไม่ได้ยืนยันว่ารันสำเร็จครบ 50
- `--workers 4` คือ 4 คำถามพร้อมกัน แต่ Agent แต่ละคำถามแตกงานได้อีก จึงไม่ใช่ขีดจำกัด 4 requests ที่เข้า vLLM

ตัวอย่างคำสั่งประกอบจากการตั้งค่าที่ใช้ (เปลี่ยน version_name ให้ใหม่ทุกครั้งเพื่อไม่ทับผลเก่า):

```bash
conda activate senior_project_py312
cd /home/kantinan/programming/project
OPENAI_API_KEY=unused python -u eval_scripts/evaluate_new_agent.py \
  --tool agent_graph --mode full_answer \
  --start 1 --end 50 --workers 4 \
  --version_name qwen_env_record_new
```

คำสั่งตัวอย่างนี้ยังไม่ได้รันในขั้นตอนจัดทำเอกสาร และไม่กำหนด NEO4J_URI เพิ่มเพราะยังต้องยืนยันฐานเป้าหมายของแต่ละชุดผล

ผลอยู่ที่ `benchmark/results2/controlled_<tool>_<scope>_<version_name>_<mode>.jsonl` และ `.yaml`

การวัดตาม metadata: latency เป็นเวลาต่อคำถามหลัง warm-up ไม่รวม executor queue, metric calculation และ trace writes แต่รวม internal lock waits; Agent retrieval รวม planning, assessment และ retries; token usage รวม LLM calls/retries ที่คืน usage ไม่รวม local embedding/reranking โดยรายงาน warm-up แยก

## 8. ข้อจำกัดในการอ้างอิงรายงาน

1. Log แนบเริ่มต้นที่ใช้ context 8192 และ GPU fraction 0.80 เป็นรอบที่ engine เปิดไม่สำเร็จจาก driver incompatibility ไม่ใช่ค่าของ server ที่กำลังรับ Benchmark ปัจจุบัน
2. Timeout และ JSON handling เปลี่ยนระหว่างรัน ต้องผูกแต่ละผลกับช่วงเวลาหรือ config ของรอบนั้น
3. ยังไม่ได้เก็บ RunPod template/image digest, installation lock ทั้งหมด, resolved model dtype/attention backend และ revision ของโมเดล local ทั้งหมด จึงยังไม่ใช่ environment lock ที่สร้างซ้ำได้ครบทุก byte
4. ยังต้องยืนยันฐาน Neo4j ของแต่ละรอบ และ runtime version ของ Neo4j/GDS ก่อนอ้างผลเปรียบเทียบในรายงาน
5. Current hardware/runtime snapshot ไม่พิสูจน์ utilization, throughput หรือ latency ระหว่างการทดลองที่ผ่านมา ต้องอ้าง trace และ metrics ที่เก็บตรงช่วงรัน

## 9. แหล่งตรวจสอบในรอบนี้

- SSH แบบ read-only เข้า Pod: `nvidia-smi`, `/etc/os-release`, `lscpu`, cgroup limits, process command/environment, package metadata ผ่าน executable ของ process, Hugging Face cache
- HTTP GET: `/v1/models`, `/metrics`
- Local: `config/default.yaml`, `src/semigraph/config.py`, `src/semigraph/connections.py`, `src/semigraph/online/cross_encoder_runtime.py`, `eval_scripts/evaluate_new_agent.py`
- ผล: `benchmark/results2/controlled_agent_graph_sox_smoke50_qwen_{fast,full_graph,full_graph_fix}_full_answer.yaml`
- ไม่ได้เปิด Benchmark ใหม่หรือเปลี่ยนการตั้งค่า server ระหว่างเก็บข้อมูลนี้
