# Walkthrough: Prompt Optimization & RAG Accuracy Tuning

We have successfully optimized the system prompts for both the **Query Reformulator** and **Answer Generator** in the RAG pipeline. This tuning strategy improves response accuracy, formatting structures, and grounding context.

---

## 🔧 1. Prompts Optimized

### A. Query Reformulator (`src/query_engine.py`)
* **Objective**: Resolve conversational inputs into clean, standalone search queries containing the target fund context.
* **Upgrades**:
  - Structured standard rules directing the model to resolve all relative pronouns (like "it", "they", "this fund") into concrete mutual fund names.
  - Imposed a constraint to append the explicit fund scheme name (e.g., "SBI Bluechip Fund Growth") to the output query.
  - Added multi-turn **few-shot examples** showing how conversational pronouns are translated to exact search terms.
  - Stripped conversational fillers ("please let me know") from search tokens.

### B. Answer Generator (`src/query_engine.py`)
* **Objective**: Formulate highly precise, grounded answers without conversational metadata references.
* **Upgrades**:
  - Parameterized the instruction with the active `fund_id` to orient the model.
  - Enforced a rule to **bypassing meta-text references** like "according to the factsheet" to align with native financial advisor styling.
  - Added markdown formatting instructions to bold key data metrics (percentages, exit loads, dates) and utilize comparison tables.
  - Mandated source index citations (e.g., `[Source 1]`) at the end of assertions.

---

## 🧪 2. Verification & Execution Results

### A. Synthetic Compile Check
- Verified syntax correctness by compiling updated modules:
  ```bash
  python3 -m py_compile src/query_engine.py app.py
  # Result: Clean exit (0 errors)
  ```

### B. Live RAG Query Test (Semantic Grounding Validation)
We cleared the local semantic cache and ran a live query verifying search performance on the updated Qdrant dataset:
* **Test Query**: `"Who is currently the primary fund manager of the SBI Bluechip Fund?"`
* **Execution Path**: Dense Embedding Similarity Search + Sparse BM25 Keyword Search merged via Reciprocal Rank Fusion (RRF) -> Grounded Gemini Generation.
* **Grounded Answer Returned**:
  > "The primary fund manager of the SBI Bluechip Fund is **Mr. Saurabh Pant** [Source 4]. He has been managing the fund since **April 2024** and has over **18 years** of total experience [Source 4]."

* **Key Achievements Checked**:
  - [x] Identified **Mr. Saurabh Pant** correctly.
  - [x] Extracted dates (**April 2024**) and context (**18 years of experience**) precisely.
  - [x] Bolded key financial figures and names.
  - [x] Appended document citation anchors (`[Source 4]`).
  - [x] Formulated response natively, omitting boilerplate grounding references.

---

## 🚀 3. Git Push
All updates were committed and successfully pushed to the GitHub repository:
- **Modified File**: [src/query_engine.py](file:///Users/abhishekspillai/mf-rag-assistant/src/query_engine.py)
- **Commit Details**: `docs: optimize query reformulator and generator prompts for RAG accuracy` (Commit `bcc5ab8`)
