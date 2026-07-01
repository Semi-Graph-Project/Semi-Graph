# Re-Extract Health Report: AMD, NVDA, AVGO, RMBS

Generated: `2026-07-01`

## Summary

การ re-extract ด้วย schema ที่ขยาย `Item_1A` ให้เห็น `PRODUCT`, `SEGMENT`, และ `FIN_METRIC` ช่วยให้ graph ต่อกันดีขึ้นชัดเจน โดยเฉพาะ AVGO และ NVDA ส่วน AMD ดีขึ้นใน signal เฉพาะจุด แต่ retrieval ranking หลัง re-extract ยัง mixed จึงไม่ควรสรุปจาก graph health อย่างเดียว

| Ticker | Chunks | Entities | Isolated | Informative rels | Verdict |
|---|---:|---:|---:|---:|---|
| AMD | 191 | 1,354 | 162 / 1,354 = 11.96% | 2,063 | Graph health ดีมาก แต่ retrieval mixed |
| NVDA | 173 | 1,178 | 177 / 1,178 = 15.03% | 2,002 | Healthy มาก |
| AVGO | 163 | 1,124 | 382 / 1,124 = 33.99% | 1,132 | ดีขึ้นชัดจาก baseline |
| RMBS | 185 | 1,123 | 361 / 1,123 = 32.15% | 1,017 | ดีขึ้นปานกลาง |

Missing checks: ทุกบริษัทมี `chunk embedding`, `entity embedding`, `specificity`, และ `triple embedding` ครบ ไม่เจอ missing ใน scope นี้

## Baseline Comparison

| Ticker | Baseline isolated | Current isolated | Change |
|---|---:|---:|---:|
| AMD | Item 1A risk: 127 / 449 = 28.29% | Item 1A risk: 87 / 442 = 19.68% | -8.61 pp |
| NVDA | ไม่มี exact pre-reextract baseline เก็บไว้ | 177 / 1,178 = 15.03% | N/A |
| AVGO | 521 / 1,178 = 44.23% | 382 / 1,124 = 33.99% | -10.24 pp |
| RMBS | 464 / 1,258 = 36.88% | 361 / 1,123 = 32.15% | -4.73 pp |

## Item 1A Schema Signal

ก่อน schema ใหม่ บริษัทที่ยังไม่ได้ re-extract แทบไม่มี `PRODUCT`, `SEGMENT`, `FIN_METRIC` ใน `Item_1A` ทำให้ risk node จำนวนมากลอยเดี่ยว หลัง re-extract สัญญาณ bridge ดีขึ้นดังนี้

| Ticker | Risk mentions | Product | Segment | Fin Metric | Risk bridge edges |
|---|---:|---:|---:|---:|---:|
| AMD | 564 | 59 | 22 | 141 | 124 |
| NVDA | 500 | 107 | 36 | 108 | 184 |
| AVGO | 405 | 31 | 3 | 139 | 185 |
| RMBS | 507 | 14 | 3 | 129 | 214 |

## Filing-Level Notes

| Ticker | Best current filing | Weakest current filing | Note |
|---|---|---|---|
| AMD | FY2025: 6.46% isolated | FY2026: 12.56% isolated | โดยรวม healthy แล้ว |
| NVDA | FY2026: 9.00% isolated | FY2025: 15.77% isolated | สม่ำเสมอและดี |
| AVGO | FY2025: 20.95% isolated | FY2023: 35.24% isolated | ดีขึ้นมาก โดยเฉพาะ FY2025 |
| RMBS | FY2026: 21.75% isolated | FY2024: 31.69% isolated | FY2024 ยังควร audit เพิ่ม |

## Dense Chunk Check

| Ticker | Max mentions/chunk | Max rels/chunk | Concern |
|---|---:|---:|---|
| AMD | 40 | 39 | ไม่มี rel chunk >= 40 |
| NVDA | 38 | 40 | มี 1 chunk แตะ 40 rels |
| AVGO | 40 | 33 | ไม่มี rel chunk >= 40 |
| RMBS | 41 | 32 | มี 1 chunk mentions > 40 เล็กน้อย |

## Conclusion

สำหรับ graph health โดยรวม การ re-extract รอบนี้ผ่านเกณฑ์ที่จะเดิน Phase T ต่อได้ โดยเฉพาะถ้าเป้าหมายคือ tune PPR/No Expand PPR บน graph ที่มี entity bridge ดีขึ้นแล้ว

ข้อควรระวังหลักคือ AMD เคยมี retrieval ranking แย่ลงเล็กน้อยหลัง re-extract แม้ graph health ดีขึ้น แปลว่า Phase T ควร tune retrieval parameters ต่อ ไม่ใช่ re-extract ทั้ง corpus เพื่อแก้ทุกอย่างทันที

