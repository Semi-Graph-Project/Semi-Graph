#!/usr/bin/env python3
"""Format the manually adjudicated first-20 answer reviews; no model calls."""

from copy import deepcopy
from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
import statistics
from zoneinfo import ZoneInfo

import yaml


OUTPUT = Path(__file__).resolve().parent
SOURCE = OUTPUT.parent
ROOT = SOURCE.parents[1]
REFERENCE = ROOT / "benchmark/datasets/sox74_repaired_v1/reference_review.yaml"
RUBRIC = ROOT / "docs/answer-review/index.html"
ORDER = ("vector", "graph", "agent_vector", "agent_graph", "text_to_cypher")
LABELS = {
    "vector": "Vector", "graph": "Graph", "agent_vector": "Agent + Vector",
    "agent_graph": "Agent + Graph", "text_to_cypher": "Text-to-Cypher",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path, value):
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")


def summary(rows):
    count = len(rows)
    correct = sum(row["answer_review"]["correct_points"] for row in rows)
    total = sum(row["answer_review"]["total_points"] for row in rows)
    hit = sum(row["answer_review"]["answer_hit"] for row in rows)
    fully = sum(row["answer_review"]["fully_correct"] for row in rows)
    return {
        "query_count": count,
        "reviewed_points": total,
        "correct_points": correct,
        "answer_hit_count": hit,
        "answer_hit": hit / count,
        "answer_recall_micro": correct / total,
        "answer_recall_macro": statistics.fmean(row["answer_review"]["answer_recall"] for row in rows),
        "main_point_hit": hit / count,
        "main_point_recall_micro": correct / total,
        "fully_correct_count": fully,
        "fully_correct_rate": fully / count,
        "partial_count": sum(0 < row["answer_review"]["correct_points"] < row["answer_review"]["total_points"] for row in rows),
        "zero_point_count": count - hit,
        "review_progress": 1.0,
    }


def main():
    reference_document = yaml.safe_load(REFERENCE.read_text())
    references = reference_document["queries"][:20]
    assert len(references) == 20
    assert sum(len(row["answer_points"]) for row in references) == 51
    decisions_path = OUTPUT / "decisions.json"
    decisions = json.loads(decisions_path.read_text())
    sources = {}
    for path in sorted(SOURCE.glob("controlled_*.yaml")):
        document = yaml.safe_load(path.read_text())
        method = document["measurement"]["tool"]
        assert method not in sources
        sources[method] = (path, document)
    assert set(sources) == set(decisions) == set(ORDER)

    metadata = {
        "reviewed_at": datetime.now(ZoneInfo("Asia/Bangkok")).isoformat(),
        "reference_dataset_revision": "sox74_repaired_v1",
        "reference_file": str(REFERENCE),
        "reference_sha256": digest(REFERENCE),
        "rubric_html": str(RUBRIC),
        "rubric_sha256": digest(RUBRIC),
        "decisions_sha256": digest(decisions_path),
        "reviewer": "Codex assistant applying the Human Verify rubric; not an independent human review",
        "selection": {"start": 1, "end": 20, "queries_per_experiment": 20, "experiment_count": 5},
        "answer_generation_rerun": False,
        "retrieval_rerun": False,
        "scoring_rule": "Binary semantic coverage per repaired reference point; no partial credit within a point, no unsure or excluded points.",
        "averaging": "Primary Answer Recall is micro: total correct points / total reference points, as in the HTML.",
        "point_roles": "All 51 points in the repaired first-20 reference are MAIN; Main metrics equal Answer metrics.",
        "policy": reference_document["metadata"]["answer_point_policy"],
        "adjudication_notes": [
            "Read and adjudicated each of the 100 saved Final Answers against its repaired reference; decisions are authored judgments, not keyword-based grading.",
            "Preserve signs, units, periods and metric identities. Missing million on a monetary amount fails that amount point; correctly computed dimensionless ratios can pass.",
            "Accept equivalent wording, documented alternative examples and mathematically equivalent rounding. Do not fill in unstated calculations or requested facts from citations.",
            "Reference exhibit identifiers are treated as important parts of the filing route. Publication timing and incidental titles not separately requested are not additional requirements.",
            "Each point containing several requested facts must cover those facts. A statement about DTL alone does not cover the additional valuation-allowance balance in the repaired compliance question.",
        ],
        "scope_note": "Saved answers were generated for original questions/retrievals; repaired questions and Gold can differ. This is a cross-revision reference-coverage review, not a new end-to-end run on Repair.",
        "incorrect_label_note": "Incorrect includes omissions, unit errors, refusals and changed-question mismatches; it does not always mean a false factual statement.",
        "no_faithfulness_claim": "These scores measure reference-point coverage, not a separate claim-by-claim faithfulness or hallucination audit.",
    }

    outputs = {}
    summaries = []
    per_query = []
    for method in ORDER:
        path, document = sources[method]
        selected = document["results"][:20]
        judgments = decisions[method]
        assert len(selected) == len(judgments) == 20
        rows = []
        for number, (original, ref, judgment) in enumerate(zip(selected, references, judgments), 1):
            assert original["id"] == ref["id"] == judgment["id"]
            assert original["answer_points"] == [point.removeprefix(f"POINT {i}: ") for i, point in enumerate(ref["answer_points"], 1)]
            assert len(judgment["reasons"]) == len(ref["answer_points"])
            assert len(judgment["correct"]) == len(set(judgment["correct"]))
            assert set(judgment["correct"]) <= set(range(1, len(ref["answer_points"]) + 1))
            row = deepcopy(original)
            reviews = []
            for point_number, (text, reason, evidence) in enumerate(zip(ref["answer_points"], judgment["reasons"], ref["point_evidence"]), 1):
                evidence_ids = list(dict.fromkeys(evidence["evidence_chunk_ids"] + evidence.get("context_chunk_ids", [])))
                reviews.append({
                    "point": point_number,
                    "role": "MAIN",
                    "reference": text,
                    "status": "correct" if point_number in judgment["correct"] else "incorrect",
                    "reason_th": reason,
                    "reference_evidence_chunk_ids": evidence_ids,
                    "reference_evidence_not_in_saved_retrieval": [chunk for chunk in evidence_ids if chunk not in original["top_chunk_ids"]],
                })
            correct = len(judgment["correct"])
            total = len(reviews)
            row["answer_review"] = {
                "number": number,
                "reference_query": ref["query"],
                "correct_point_numbers": judgment["correct"],
                "statuses": [review["status"] for review in reviews],
                "correct_points": correct,
                "total_points": total,
                "answer_hit": int(correct > 0),
                "answer_recall": correct / total,
                "fully_correct": correct == total,
                "points": reviews,
            }
            rows.append(row)
            per_query.append({
                "configuration": method,
                "number": number,
                "id": row["id"],
                **{key: value for key, value in row["answer_review"].items() if key not in {"number", "points", "reference_query"}},
            })
        scores = summary(rows)
        output_name = path.stem + "_answer_review_first20.yaml"
        payload = {
            "summary": scores,
            "results": rows,
            "measurement": {
                "tool": method,
                "mode": "posthoc_answer_review",
                "selection": {"start": 1, "end": 20, "query_count": 20},
                "source_file": str(path),
                "source_sha256": digest(path),
                "source_mode": document["measurement"]["mode"],
                "reference_dataset_revision": "sox74_repaired_v1",
                "answers_evaluated": True,
                "answers_recomputed": False,
            },
            "review_metadata": metadata,
            "source_summary_full50": document["summary"],
            "source_measurement_full50": document["measurement"],
        }
        write_yaml(OUTPUT / output_name, payload)
        outputs[method] = payload
        summaries.append({"configuration": method, **scores, "result_file": output_name, "source_sha256": digest(path)})
    write_yaml(OUTPUT / "summary.yaml", {"review_metadata": metadata, "configurations": summaries})
    write_yaml(OUTPUT / "per_query_metrics.yaml", {"review_metadata": metadata, "results": per_query})

    lines = ["# ตรวจ Final Answer 20 ข้อแรก — Human Verify 2 Fast × Repair", "",
             "ตรวจโดย Codex ตามเกณฑ์ Human Verify ไม่ใช่การรับรองจากผู้ตรวจมนุษย์อิสระ", "",
             "ใช้ Final Answer เดิม 20 ข้อแรกของทั้ง 5 การทดลอง รวม 100 คำตอบ / 255 Points โดยเทียบกับ Repair และไม่ตัด Point ออก", "",
             "| การทดลอง | Answer Hit | Answer Recall (micro) | ผ่านครบ |",
             "|---|---:|---:|---:|"]
    for item in summaries:
        lines.append(f"| {LABELS[item['configuration']]} | {item['answer_hit_count']}/20 ({item['answer_hit']:.2%}) | {item['correct_points']}/51 ({item['answer_recall_micro']:.2%}) | {item['fully_correct_count']}/20 ({item['fully_correct_rate']:.2%}) |")
    lines.extend(["", "| ข้อ | ID | Vector | Graph | Agent + Vector | Agent + Graph | Text-to-Cypher |", "|---:|---|---:|---:|---:|---:|---:|"])
    for index, ref in enumerate(references):
        scores = [f"{outputs[method]['results'][index]['answer_review']['correct_points']}/{len(ref['answer_points'])}" for method in ORDER]
        lines.append(f"| {index+1} | {ref['id']} | " + " | ".join(scores) + " |")
    lines.extend(["", "Answer Hit = มี Point ผ่านอย่างน้อยหนึ่งข้อ; Recall = จำนวน Points ที่ผ่านหาร Points ทั้งหมด; ผ่านครบ = ทุก Point ผ่าน", "",
                  "MAIN ทุก Point ตาม Repair จึงได้ Main Point metrics เท่ากับ Answer metrics", "",
                  "คำตอบรันจากคำถามและผลค้นเดิม ส่วนเฉลยเป็น Repair คะแนนจึงรวมผลของโจทย์และ Gold ที่เปลี่ยนไป ไม่ใช่ผลรันใหม่บน Repair", "",
                  "ดูคำถามเดิม คำถาม Repair Final Answer และเหตุผลราย Point ครบทุกคำตอบได้ใน review.html หรือ YAML รายการทดลอง", "",
                  "สร้างรายงานซ้ำ: python benchmark/human_verify_2_fast_repaired/answer_review_first20/build_report.py", ""])
    (OUTPUT / "report.md").write_text("\n".join(lines), encoding="utf-8")

    esc = html.escape
    parts = ['<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>ตรวจคำตอบ 20 ข้อแรก × 5 การทดลอง</title>',
             '''<style>
body{font:15px/1.65 system-ui,sans-serif;color:#17212c;background:#f5f7f9;margin:0}main{max-width:1200px;margin:auto;padding:24px}section,details.case{background:white;border:1px solid #dce1e6;padding:18px;margin:16px 0;border-radius:12px}h1{font-size:27px}.warning{background:#fff1d5;padding:12px;border-left:4px solid #b67b00}table{width:100%;border-collapse:collapse}th,td{padding:7px;border-bottom:1px solid #dce1e6;text-align:left}.scroll{overflow-x:auto}summary{font-weight:650;cursor:pointer}.questions{display:grid;grid-template-columns:1fr 1fr;gap:18px}.answer{white-space:pre-wrap;overflow-wrap:anywhere}.point{padding:12px;border-left:5px solid #b43c3c;background:#fff2f2;margin:10px 0}.point.correct{border-color:#16825a;background:#edf9f3}.muted{font-size:13px;color:#637080}input,select{font:inherit;padding:8px;margin:0 8px 8px 0}@media(max-width:700px){main{padding:10px}.questions{grid-template-columns:1fr}}
</style><main><section><h1>ตรวจ Final Answer 20 ข้อแรก × 5 การทดลอง</h1>''',
             '<p>ครบ 100 คำตอบ / 255 Points · ตรวจโดย Codex ตามเกณฑ์ Human Verify · ไม่มี unsure หรือการตัด Point ออก</p>',
             '<p class="warning">คำตอบมาจากคำถามและผลค้นเดิม ส่วนเฉลยมาจาก Repair คะแนนนี้รวมผลจากโจทย์/Gold ที่เปลี่ยน ไม่ใช่การรันใหม่บน Repair และไม่ใช่การตรวจโดยมนุษย์อิสระ</p>',
             '<div class="scroll"><table><tr><th>การทดลอง</th><th>Answer Hit</th><th>Answer Recall (micro)</th><th>ผ่านครบ</th></tr>']
    for item in summaries:
        parts.append(f"<tr><td>{LABELS[item['configuration']]}</td><td>{item['answer_hit_count']}/20 · {item['answer_hit']:.2%}</td><td>{item['correct_points']}/51 · {item['answer_recall_micro']:.2%}</td><td>{item['fully_correct_count']}/20 · {item['fully_correct_rate']:.2%}</td></tr>")
    parts.extend(['</table></div><p class="muted">Answer Hit นับเมื่อผ่านอย่างน้อยหนึ่ง Point · MAIN ทั้ง 51 Points · ไม่ผ่านรวมทั้งขาดรายละเอียด ขาดหน่วย ปฏิเสธตอบ และคำถามเปลี่ยน</p>',
                  '<details><summary>เกณฑ์การตรวจ</summary><ul>'])
    for note in metadata['adjudication_notes'] + metadata['policy']:
        parts.append('<li>' + esc(note) + '</li>')
    parts.extend(['</ul></details></section><section class="scroll"><h2>คะแนนรายข้อ</h2><table><tr><th>ข้อ</th><th>ID</th>' + ''.join(f'<th>{LABELS[method]}</th>' for method in ORDER) + '</tr>'])
    for index, ref in enumerate(references):
        parts.append(f"<tr><td>{index+1}</td><td>{ref['id']}</td>")
        for method in ORDER:
            review = outputs[method]['results'][index]['answer_review']
            parts.append(f"<td><a href=\"#{method}-{ref['id']}\">{review['correct_points']}/{review['total_points']}</a></td>")
        parts.append('</tr>')
    parts.extend(['</table></section><section><input id="search" placeholder="ค้น ID หรือเลขข้อ"><select id="method"><option value="all">ทุกการทดลอง</option>' + ''.join(f'<option value="{method}">{LABELS[method]}</option>' for method in ORDER) + '</select><select id="status"><option value="all">ทุกผล</option><option value="full">ผ่านครบ</option><option value="partial">ผ่านบางส่วน</option><option value="zero">ไม่ผ่านทุก Point</option></select><p id="visible"></p></section>'])
    for method in ORDER:
        for row in outputs[method]['results']:
            review = row['answer_review']
            kind = 'full' if review['fully_correct'] else 'zero' if review['correct_points'] == 0 else 'partial'
            parts.extend([f"<details class=\"case\" id=\"{method}-{row['id']}\" data-method=\"{method}\" data-number=\"{review['number']}\" data-kind=\"{kind}\">",
                          f"<summary>{LABELS[method]} · {review['number']}. {row['id']} — {review['correct_points']}/{review['total_points']}</summary>",
                          f"<div class=\"questions\"><div><h3>คำถามเดิม</h3>{esc(row['query'])}</div><div><h3>คำถาม Repair</h3>{esc(review['reference_query'])}</div></div>",
                          f"<h3>Final Answer เดิม</h3><div class=\"answer\">{esc(row['final_answer'])}</div><h3>ผลราย Point</h3>"])
            for point in review['points']:
                label = 'ถูก' if point['status'] == 'correct' else 'ไม่ผ่าน'
                parts.append(f"<div class=\"point {point['status']}\"><b>P{point['point']} · MAIN · {label}</b><p>{esc(point['reference'])}</p><p>{esc(point['reason_th'])}</p></div>")
            parts.append('</details>')
    parts.append('''<script>
function filterCases(){const q=document.getElementById('search').value.trim().toLowerCase(),m=document.getElementById('method').value,k=document.getElementById('status').value;let n=0;document.querySelectorAll('.case').forEach(el=>{const show=(!q||el.id.toLowerCase().includes(q)||el.dataset.number===q)&&(m==='all'||m===el.dataset.method)&&(k==='all'||k===el.dataset.kind);el.hidden=!show;if(show)n++});document.getElementById('visible').textContent='แสดง '+n+' / 100 คำตอบ'}
['search','method','status'].forEach(id=>document.getElementById(id).addEventListener(id==='search'?'input':'change',filterCases));document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>{const el=document.getElementById(a.getAttribute('href').slice(1));if(el){el.hidden=false;el.open=true}}));filterCases();
</script></main></html>''')
    (OUTPUT / "review.html").write_text("\n".join(parts), encoding="utf-8")
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
