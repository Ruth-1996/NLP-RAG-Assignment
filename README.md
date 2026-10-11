# Thai Contextual RAG: Baseline vs Improved

**NLP Assignment — Retrieval-Augmented Generation (RAG)**  
ระบบต้นแบบอ้างอิงโค้ด Hands-on จาก [2025-authenticRAG](https://github.com/aekanun2020/2025-authenticRAG) และปรับการสร้างคำตอบให้ใช้ **Google Gemini 3.5 Flash Lite** ทั้งสองเวอร์ชัน

## 1. Project overview

โปรเจกต์นี้เปรียบเทียบระบบ RAG สำหรับตอบคำถามจากเอกสาร Markdown ภาษาไทยเกี่ยวกับโรคหัดเยอรมัน โดยแบ่งการทำงานเป็น:

1. **Hands-on 1 — Ingestion:** อ่านเอกสาร 4 ไฟล์จาก `corpus_input/`, แบ่งข้อความด้วย `MarkdownNodeParser(chunk_size=256)`, ใช้ Gemini สร้างบริบทเสริมให้แต่ละ chunk, สร้าง embedding ด้วย `BAAI/bge-m3` และจัดเก็บใน OpenSearch
2. **Hands-on 2 — Retrieval + Generation:** ใช้ BM25 (Sparse Search) และ k-NN Vector Search (Dense Search), รวมอันดับด้วย Reciprocal Rank Fusion (RRF), เลือกเอกสาร Top 5 และให้ Gemini สร้างคำตอบ
3. **Improvement:** ปรับการค้นข้อความภาษาไทยโดยใช้ Character N-gram Analyzer และปรับสูตรจัดอันดับเป็น Weighted RRF

การทดลองนำเอกสารเข้า OpenSearch **53 chunks** และใช้คำถามทดสอบ **5 ข้อ** โดยคงเอกสาร, embedding model และ Gemini รุ่นเดิมในทั้งสองเวอร์ชัน

## 2. Architecture

```text
Markdown documents (4 files)
          |
   MarkdownNodeParser
     chunk_size=256
          |
  Gemini contextualization
          |
  BGE-M3 text embeddings
          |
        OpenSearch
        /       \
  BM25 index   Vector index
        \       /
     Fusion / Ranking
          |
       Top 5 chunks
          |
  Gemini 3.5 Flash Lite
          |
         Answer
```

**Baseline:** Standard Analyzer + BM25 / Dense Search + Equal-weight RRF  
**Improved:** Thai Character N-gram (2–3 characters) + BM25 / Dense Search + Weighted RRF (BM25 0.4, Dense 0.6)

## 3. Project files

| File / folder | Description |
|---|---|
| `authenticRAG_baseline.py` | โหลดเอกสาร แบ่ง chunks สร้าง context และ embedding จัดเก็บใน OpenSearch (รวมการทดสอบตามโค้ดต้นฉบับ) |
| `onlysearchAuthenticRAG_baseline.py` | ค้นคืนและตอบคำถามด้วย Baseline RAG |
| `create_thai_bm25_index.py` | สร้าง Thai N-gram Index ใหม่ แล้ว reindex จาก BM25 Index เดิม |
| `onlysearchAuthenticRAG_improved.py` | ค้นคืนและตอบคำถามด้วย Thai N-gram BM25 + Weighted RRF |
| `corpus_input/` | ไฟล์ข้อมูลต้นฉบับ `1.md`, `2.md`, `44.md`, `5555.md` |
| `authentic_rag_search_results_baseline.json` | ผลทดสอบ Baseline จำนวน 5 คำถาม |
| `authentic_rag_search_results_improved.json` | ผลทดสอบ Improved ล่าสุดจำนวน 5 คำถาม |
| `requirements.txt` | รายชื่อ Python dependencies |
| `.gitignore` | ป้องกันการอัปโหลดไฟล์ลับและ virtual environment |

> ชื่อ OpenSearch indices คือ `anthropic-vector-index`, `anthropic-bm25-index` และ `anthropic-bm25-thai-index` โดยข้อมูลของ OpenSearch เก็บใน Docker ไม่ได้ถูกอัปโหลดขึ้น GitHub ผ่านโค้ดชุดนี้

## 4. Setup (Windows / PowerShell)

**Requirements:** Python 3.11, Docker Desktop, Internet สำหรับดาวน์โหลด `BAAI/bge-m3`, Google Gemini API Key และ OpenSearch 2.19.1

### 4.1 Create virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --timeout 120 --retries 5 -r requirements.txt
```

หาก PowerShell ป้องกันการ Activate สามารถอนุญาตเฉพาะ session ปัจจุบันก่อน:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 4.2 Add Gemini API Key

สร้างไฟล์ `.env` **ในโฟลเดอร์โปรเจกต์** (ไม่ใช่ใน Terminal):

```dotenv
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

**อย่า commit หรือแชร์ไฟล์ `.env`** และห้ามใส่ API Key จริงลงใน source code

### 4.3 Start OpenSearch

เปิด Docker Desktop ก่อน จากนั้นถ้ามี container ชื่อ `opensearch` อยู่แล้ว:

```powershell
docker start opensearch
```

ถ้ายังไม่มี container ให้สร้างแบบทดลองบนเครื่องตัวเอง (Security Plugin disabled และเปิด port เฉพาะ localhost):

```powershell
docker run -d --name opensearch -p 127.0.0.1:9200:9200 -p 127.0.0.1:9600:9600 -e "discovery.type=single-node" -e "DISABLE_SECURITY_PLUGIN=true" -e "network.host=0.0.0.0" opensearchproject/opensearch:2.19.1
```

ตรวจสอบ:

```powershell
Invoke-RestMethod -Uri "http://localhost:9200"
```

> การปิด Security Plugin เหมาะกับการทดลอง **ในเครื่องส่วนตัวเท่านั้น** ไม่ควรเปิดพอร์ตนี้ต่ออินเทอร์เน็ต

## 5. How to run

ขั้นตอนต่อไปนี้ใช้กับการตั้งค่าระบบใหม่ที่ยังไม่ได้ ingest เอกสาร หากมี indices และ 53 chunks อยู่แล้ว **ข้ามขั้นตอน ingestion ได้**

### 5.1 Hands-on 1 — Ingestion

```powershell
python authenticRAG_baseline.py
```

โมเดล BGE-M3 มีขนาดใหญ่และการโหลดครั้งแรกอาจใช้เวลานาน การสร้าง context ยังเรียก Gemini ประมาณหนึ่งครั้งต่อ chunk และขึ้นอยู่กับโควตา API

ตรวจจำนวนเอกสาร:

```powershell
Invoke-RestMethod -Uri "http://localhost:9200/_cat/indices/anthropic-*?v"
```

ผลทดสอบชุดนี้: `anthropic-vector-index` = 53 เอกสาร และ `anthropic-bm25-index` = 53 เอกสาร

### 5.2 Hands-on 2 — Baseline search

```powershell
python onlysearchAuthenticRAG_baseline.py
```

ผลจะถูกสร้างในไฟล์ `authentic_rag_search_results.json` ตามโค้ด Baseline; สามารถสำรองด้วย:

```powershell
Copy-Item .\authentic_rag_search_results.json .\authentic_rag_search_results_baseline.json
```

### 5.3 Improved RAG

สร้าง Thai N-gram index จาก BM25 Index เดิม:

```powershell
python create_thai_bm25_index.py
```

คาดว่าจะเห็น `Reindexed: 53`, `Failures: []`, `Document count: 53`

รัน Improved Search:

```powershell
python onlysearchAuthenticRAG_improved.py
```

ผลจะถูกบันทึกเป็น `authentic_rag_search_results_improved.json` ตามโค้ด Improved

## 6. Changes made in Improved RAG

| Component | Baseline | Improved | Reason |
|---|---|---|---|
| Document chunking | MarkdownNodeParser, 256 | เหมือนเดิม | ควบคุมตัวแปรทดลอง |
| Embedding | BGE-M3 | เหมือนเดิม | ใช้ embeddings ชุดเดียวกัน |
| BM25 analyzer | `standard` | custom character n-gram (2–3) | ทำให้ค้นข้อความย่อยภาษาไทยได้ แม้ไม่มีการแบ่งคำที่เหมาะสม |
| Dense retrieval | k-NN vector | เหมือนเดิม | ควบคุมตัวแปรทดลอง |
| Rank fusion | RRF แบบน้ำหนักเท่ากัน | Weighted RRF (BM25 0.4, Dense 0.6) | ทดลองปรับการถ่วงน้ำหนักของแหล่งค้นคืน |
| Generator | Gemini 3.5 Flash Lite | Gemini 3.5 Flash Lite | รักษาเงื่อนไข Assignment ที่ห้ามเปลี่ยน LLM |

สูตรในโปรแกรมมี `rank` เริ่มจาก 0 ตาม `enumerate(results)` และ `k=60`:

```text
Baseline: score(d) = Σ [1 / (60 + rank_i(d))]
Improved: score(d) = Σ [weight_i / (60 + rank_i(d))]
BM25 weight = 0.4, Dense weight = 0.6
```

## 7. Evaluation — 5 test questions

เปรียบเทียบอันดับ **Top 5** จากไฟล์ผลลัพธ์ JSON จริง โดยเลข `1` หมายถึง `doc_1`

| Q | Question topic | Baseline Top 5 | Improved Top 5 | Shared documents |
|---|---|---|---|---:|
| 1 | หัดกับหัดเยอรมันต่างกันอย่างไร | 1, 2, 3, 7, 6 | 3, 2, 1, 6, 13 | 4/5 |
| 2 | สาเหตุและการป้องกัน | 2, 0, 15, 1, 13 | 13, 3, 0, 6, 10 | 2/5 |
| 3 | อันตรายต่อหญิงตั้งครรภ์ | 6, 1, 2, 13, 11 | 6, 9, 13, 11, 3 | 3/5 |
| 4 | ฉีดวัคซีนแล้วยังติดเชื้อได้หรือไม่ | 13, 2, 11, 1, 10 | 13, 11, 3, 10, 2 | 4/5 |
| 5 | ผลกระทบต่อสาธารณสุขและเศรษฐกิจ | 1, 2, 6, 3, 10 | 6, 3, 2, 1, 10 | 5/5 |

**Observed retrieval outcomes**

- อันดับ Top 5 เปลี่ยนใน **5/5 คำถาม**
- เอกสารที่ปรากฏใน Top 5 ร่วมกันระหว่างสองระบบรวม **18 จาก 25 รายการ** (นับความซ้ำกันของเอกสารต่อคำถาม)
- เอกสารอันดับแรกเปลี่ยนใน **3/5 คำถาม**
- ในคำถามเรื่องผลกระทบสาธารณสุขและเศรษฐกิจ มีบันทึกว่า Baseline BM25 พบ **0** เอกสาร ขณะที่ Improved Thai N-gram BM25 พบ **10** เอกสาร โดย Dense พบ **10** และผล fusion รวมเป็น **14 เอกสารที่ไม่ซ้ำกัน** ก่อนเลือก Top 5

**Answer quality (qualitative)**

- ผลการค้นคืนมีการเปลี่ยนแปลงที่วัดได้ แต่ไม่ได้ยืนยันว่า **ความถูกต้องของคำตอบดีขึ้นทุกคำถาม**
- เช่น คำถามเกี่ยวกับสาเหตุและการป้องกัน: Baseline มีข้อมูลสาเหตุจาก `doc_2` ขณะที่ Improved เลื่อนเอกสารเกี่ยวกับการป้องกัน (`doc_13`) ขึ้นอันดับแรก และ `doc_2` หลุดจาก Top 5
- คำถามเกี่ยวกับผลกระทบต่อระบบสาธารณสุขและเศรษฐกิจ: ทั้งสองระบบระบุว่าเอกสารไม่เพียงพอต่อการสรุปผลกระทบเฉพาะเรื่อง

**Interpretation and limitations**

ผลการทดลองสนับสนุนว่า Thai N-gram ทำให้ BM25 คืนเอกสารภาษาไทยได้ในคำถามที่ทดสอบ และการปรับ retrieval/ranking ส่งผลต่ออันดับจริง อย่างไรก็ตาม งานนี้ปรับทั้ง analyzer และ ranking weights พร้อมกัน จึง **ยังแยกผลของแต่ละการเปลี่ยนแปลงไม่ได้** อีกทั้งไม่มี ground-truth relevance labels หรือคะแนนประเมินความถูกต้องโดยผู้เชี่ยวชาญ ผล Top 5 ที่เปลี่ยนจึงไม่เท่ากับหลักฐานว่าคุณภาพดีขึ้นโดยรวม ควรทดสอบคำถามและตัวชี้วัดเพิ่ม เช่น Precision@5 และ MRR ก่อนสรุปความเหนือกว่าเชิงปริมาณ

## 8. References / Acknowledgment

- โค้ดและ Hands-on ต้นแบบ: [aekanun2020/2025-authenticRAG](https://github.com/aekanun2020/2025-authenticRAG)
- [OpenSearch documentation](https://docs.opensearch.org/)
- [BAAI/bge-m3 model](https://huggingface.co/BAAI/bge-m3)
- [Gemini API documentation](https://ai.google.dev/gemini-api/docs)

*Academic demonstration only. Content in the sample documents is used to evaluate document retrieval, not to provide medical advice.*
