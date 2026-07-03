# Re-Extract Graph Health & Quality Report

Generated: `2026-07-02`

Scope: `AMD`, `AVGO`, `ENTG`, `INTC`, `KLAC`, `MU`, `NVDA`, `RMBS`

## Executive Summary

การ re-extract รอบนี้ทำให้ graph พร้อมใช้กับ Phase T มากขึ้นในภาพรวม โดยเฉพาะ `Item_1A` เริ่มมี bridge จาก `RISK_FACTOR` ไปหา `PRODUCT`, `SEGMENT`, `FIN_METRIC` ครบทุกบริษัทที่ re-extract แล้ว แต่ยังมีจุดต้องระวังคือ `KLAC` relation volume ลดแรง และ `ENTG/KLAC/AVGO` ยังมี isolated entity สูงในกลุ่ม risk/product

| Metric | Value |
|---|---:|
| Chunks | 1,467 |
| Mentions | 19,660 |
| Distinct entities, summed by ticker | 9,863 |
| Isolated entities, summed by ticker | 2,391 |
| Weighted isolated rate | 24.24% |
| Informative relationships | 12,031 |
| Missing chunk/entity/triple embeddings/specificity | 0 |

## Health By Ticker

| Ticker | Entities | Isolated | Baseline Change | Rels | Rel Change | Orphan Chunks | Zero-Rel Chunks | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| AMD | 1,354 | 163 = 12.04% | Item 1A risk -8.38 pp | 2,063 | N/A | 2 | 32 | ดี |
| AVGO | 1,124 | 384 = 34.16% | -10.07 pp | 1,132 | +256 | 3 | 54 | ดีขึ้นชัด แต่ยังสูง |
| ENTG | 1,234 | 446 = 36.14% | +2.58 pp | 1,041 | +86 | 9 | 61 | ต้อง audit เพิ่ม |
| INTC | 1,501 | 180 = 11.99% | +1.30 pp | 2,377 | +142 | 2 | 13 | ดี |
| KLAC | 1,241 | 423 = 34.09% | +2.18 pp | 1,027 | -1,175 | 3 | 69 | ต้อง audit เพิ่ม |
| MU | 1,108 | 251 = 22.65% | -5.37 pp | 1,372 | +126 | 5 | 37 | ดีขึ้น |
| NVDA | 1,178 | 180 = 15.28% | No exact baseline | 2,002 | N/A | 2 | 20 | ดี |
| RMBS | 1,123 | 364 = 32.41% | -4.47 pp | 1,017 | -37 | 5 | 54 | ดีขึ้นเล็กน้อย |

Notes:
- Baseline ของ `AMD` ไม่มี ticker-level isolated แบบ exact เก็บไว้ จึงเทียบเฉพาะ `Item_1A RISK_FACTOR`: `28.29% -> 19.91%`
- Baseline ของ `NVDA` ก่อน re-extract ไม่ได้เก็บไว้ จึงรายงานเป็น current health
- `zero-rel chunks` หมายถึง chunk มี node/mentions ได้ แต่ไม่มี informative edge ให้ PPR เดินต่อจาก chunk นั้น

## Item 1A Quality Signal

นี่คือจุดสำคัญสุดของ schema expansion รอบนี้: `Item_1A` ไม่ได้มีแค่ risk ลอยๆ แล้ว แต่เริ่มเชื่อม risk เข้ากับ product/segment/financial metric ได้จริง

| Ticker | Risk Entities | Isolated Risk | Product Mentions | Segment Mentions | Fin Metric Mentions | Risk Bridge Edges |
|---|---:|---:|---:|---:|---:|---:|
| AMD | 442 | 88 = 19.91% | 59 | 22 | 141 | 124 |
| AVGO | 333 | 147 = 44.14% | 31 | 3 | 139 | 185 |
| ENTG | 350 | 163 = 46.57% | 9 | 9 | 117 | 135 |
| INTC | 332 | 64 = 19.28% | 59 | 35 | 116 | 106 |
| KLAC | 445 | 199 = 44.72% | 8 | 0 | 114 | 176 |
| MU | 395 | 142 = 35.95% | 31 | 0 | 101 | 117 |
| NVDA | 427 | 85 = 19.91% | 107 | 36 | 108 | 184 |
| RMBS | 405 | 159 = 39.26% | 14 | 3 | 129 | 214 |

Interpretation:
- Strong: `AMD`, `INTC`, `NVDA`
- Acceptable but still noisy: `MU`, `RMBS`
- Needs audit: `AVGO`, `ENTG`, `KLAC`

## Quality Checks

| Check | Result |
|---|---|
| Missing chunk embeddings | PASS: 0 |
| Missing entity embeddings | PASS: 0 |
| Missing entity specificity | PASS: 0 |
| Missing triple embeddings | PASS: 0 |
| Relationship `source_chunk` missing | PASS: 0 |
| Self-loop informative relations | PASS: 0 found |
| Suspicious direction, e.g. `PRODUCT -> PRODUCES` | PASS: 0 found |
| Dense chunks | Mostly PASS: max mentions 43, max rels 40 |

Dense edge cases:
- `ENTG` has 1 chunk with mentions > 40
- `RMBS` has 1 chunk with mentions > 40
- `NVDA` has 1 chunk with rels = 40
- No ticker has rels > 40 after this re-extract set

## Weak Spots

| Ticker | Main Weak Spot |
|---|---|
| ENTG | Isolated rate worsened from 33.56% to 36.14%; `PRODUCT` isolated 52.44%, `RISK_FACTOR` isolated 46.57% |
| KLAC | Relations collapsed from 2,202 to 1,027; `RISK_FACTOR` isolated 44.72%, `PRODUCT` isolated 52.45% |
| AVGO | Improved a lot, but `RISK_FACTOR` isolated 44.14% and `PRODUCT` isolated 49.73% still high |
| RMBS | Overall improved, but `FIN_METRIC` isolated 41.25% is still high |

## Filing-Level Notes

| Ticker | Best Filing | Weakest Filing |
|---|---|---|
| AMD | FY2025: 6.29% isolated | FY2026: 12.71% isolated |
| AVGO | FY2025: 20.95% isolated | FY2023: 35.24% isolated |
| ENTG | FY2026: 32.04% isolated | FY2025: 33.56% isolated |
| INTC | FY2025: 8.56% isolated | FY2026: 11.09% isolated |
| KLAC | FY2025: 26.97% isolated | FY2024: 35.34% isolated |
| MU | FY2023: 16.62% isolated | FY2025: 21.58% isolated |
| NVDA | FY2026: 9.17% isolated | FY2025: 16.17% isolated |
| RMBS | FY2026: 22.72% isolated | FY2024: 31.86% isolated |

## Conclusion

Graph หลัง re-extract ชุดนี้ถือว่าเพียงพอสำหรับเดิน Phase T ต่อ โดยเฉพาะการ tune `PPR / No Expand PPR` เพราะโครง graph ไม่มี missing embedding, ไม่มี source provenance หาย, และ `Item_1A` bridge ดีขึ้นชัด

สิ่งที่ยังไม่ควรละเลยคืออย่าใช้ graph health อย่างเดียวตัดสิน retrieval quality เพราะ `AMD` เคย health ดีขึ้นแต่ ranking mixed ดังนั้นขั้นถัดไปควรวัด retrieval benchmark หลัง re-extract ชุดนี้ แล้วแยกดูว่า failure มาจาก seed, PPR walk, chunk mapping, หรือ fusion

Recommended next checks:
- Run Phase T benchmark ใหม่บน current graph
- Audit `KLAC` relation collapse ก่อนตัดสิน re-extract เพิ่มทั้ง corpus
- Spot-check `ENTG/KLAC/AVGO` Item 1A risk/product isolated examples
