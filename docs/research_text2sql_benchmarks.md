# Text-to-SQL: Benchmarks, Leaderboards, Techniques & Alternatives (February 2026)

> Comprehensive research report for the BIAI project. Covers all major benchmarks, current leaderboard standings, best techniques for SQL generation accuracy, and Vanna.ai alternatives.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Benchmarks Overview](#2-benchmarks-overview)
3. [Leaderboards — Top Models per Benchmark](#3-leaderboards)
4. [Best Local Models (<=70B) for Text-to-SQL](#4-best-local-models)
5. [Techniques That Improve Accuracy](#5-techniques)
6. [Vanna.ai Alternatives](#6-alternatives)
7. [Recommendations for BIAI](#7-recommendations)
8. [Sources](#8-sources)

---

## 1. Executive Summary

### Key Findings (February 2026)

| Finding | Detail |
|---------|--------|
| **BIRD SOTA** | Agentar-Scale-SQL: **81.67%** EX (test), AskData+GPT-4o: **81.95%** EX (test) |
| **Spider 1.0 SOTA** | MiniSeek: **91.2%** EX; DAIL-SQL+GPT-4+SC: **86.6%** EX |
| **Spider 2.0 SOTA** | QUVI-3+Gemini-3-pro: **94.15%** (Snow); QUVI-2.3+Claude-Opus-4.5: **65.81%** (Lite) |
| **Best local model** | MARS-SQL (7B, RL-tuned): **77.84%** BIRD-dev, **89.75%** Spider-test |
| **Best local model (single)** | Arctic-Text2SQL-R1-7B: **68.9%** BIRD-dev; XiYanSQL-QwenCoder-32B: **69.03%** BIRD-test |
| **Human ceiling (BIRD)** | **92.96%** (data engineers) |
| **Fine-tuned 7B vs GPT-4** | Fine-tuned 7B models reach 68-82% on Spider; GPT-4 zero-shot ~70%, with pipeline ~86% |
| **Most impactful technique** | Multi-candidate generation + execution-based selection (+5-15% accuracy) |
| **Best Vanna.ai alternative** | Wren AI (semantic layer, enterprise governance) for teams; DB-GPT for local multi-agent |

### Relevance for BIAI

BIAI currently uses Vanna.ai (RAG) with Ollama for local inference. Key improvements available:
1. **Switch to or add Arctic-Text2SQL-R1-7B / Qwen2.5-Coder-7B** for SQL generation (68-82% accuracy)
2. **Add multi-candidate generation** with execution-based filtering (Contextual-SQL approach)
3. **Add self-correction loop** with execution feedback (already partially implemented)
4. **Consider schema pruning** before SQL generation to reduce noise
5. **Wren AI's semantic layer concept** (MDL) can be adapted for business term consistency

---

## 2. Benchmarks Overview

### 2.1 Spider (Yale, 2018)

| Property | Value |
|----------|-------|
| **Type** | Cross-database, complex SQL |
| **Size** | 10,181 questions, 200 databases, 138 domains |
| **Metrics** | Exact Match (EM), Execution Accuracy (EX) |
| **Difficulty** | Easy/Medium/Hard/Extra Hard |
| **Status** | Leaderboard FROZEN since Feb 2024; test set released |
| **Link** | https://yale-lily.github.io/spider |

**What it measures**: Cross-domain generalization — models must generate SQL for databases never seen during training. Covers JOINs, subqueries, GROUP BY, HAVING, ORDER BY, nested queries.

**Limitation**: Considered "mostly solved" by LLMs (top scores >90% EX). Spider 2.0 was created to address this.

### 2.2 Spider 2.0 (ICLR 2025 Oral)

| Property | Value |
|----------|-------|
| **Type** | Enterprise-level, real-world SQL workflows |
| **Size** | 632 problems across 3 task variants |
| **Variants** | Spider2-Snow (547, Snowflake), Spider2-DBT (68, DuckDB), Spider2-Lite (547, multi-DB) |
| **Metrics** | Execution Accuracy (EX) |
| **Challenge** | >3,000 columns, multiple SQL dialects, documentation understanding |
| **Link** | https://spider2-sql.github.io/ |
| **Last update** | May 2025 (Spider2-DBT added) |

**What it measures**: Real enterprise data complexity. GPT-4o scores only **10.1%** on Spider 2.0 vs **86.6%** on Spider 1.0. Even o1-preview only **17.1%**.

### 2.3 BIRD (BIg Bench for LaRge-scale Database)

| Property | Value |
|----------|-------|
| **Type** | Large-scale, real databases, execution-based evaluation |
| **Size** | 12,751 question-SQL pairs, 95 databases (33.4 GB total) |
| **Domains** | 37+ (blockchain, hockey, healthcare, education, etc.) |
| **Metrics** | Execution Accuracy (EX), Reward-based Valid Efficiency Score (R-VES) |
| **Human ceiling** | 92.96% (data engineers) |
| **Link** | https://bird-bench.github.io/ |
| **Last update** | Nov 2025 (bird-sql-dev-1106 cleaner split) |

**What it measures**: Database content understanding — not just schema, but actual data values matter for correct SQL generation. Considered the current **gold standard** for Text-to-SQL evaluation.

**Extensions**:
- **BIRD-Interact** (ICLR 2026 Oral): Dynamic multi-turn interaction evaluation. Best model (o3-mini): 24.4% success rate.
- **BIRD-CRITIC** (NeurIPS 2025): SQL debugging benchmark (SWE-SQL).
- **LiveSQLBench** (Sep 2025): Real-time benchmark. Gemini-2.5-pro achieves only 28.67% on colloquial queries.

### 2.4 WikiSQL (Salesforce, 2017)

| Property | Value |
|----------|-------|
| **Type** | Simple, single-table SQL |
| **Size** | 80,654 NL questions, 77,840 SQL statements from Wikipedia |
| **Metrics** | Execution Accuracy |
| **Status** | Leaderboard has only submissions from 2021 or earlier |
| **Top score** | 93.0% (SeaD+Execution-Guided Decoding) |
| **Link** | https://github.com/salesforce/WikiSQL |

**What it measures**: Basic SQL generation for single tables. Considered **solved** — not useful for evaluating modern LLMs.

**Update**: **LLMSQL** (2025) is a modernized version with clean NL questions and full SQL queries.

### 2.5 CoSQL (Yale + Salesforce, 2019)

| Property | Value |
|----------|-------|
| **Type** | Conversational, multi-turn SQL |
| **Size** | 30,000+ turns, 10,000+ SQL queries, 3,000 dialogues, 200 databases |
| **Domains** | 138 |
| **Link** | https://yale-lily.github.io/spider |

**What it measures**: Multi-turn context-dependent SQL generation where conversation history matters. Relevant for chat-based systems like BIAI.

### 2.6 SParC (Yale, 2019)

| Property | Value |
|----------|-------|
| **Type** | Cross-domain, context-dependent semantic parsing |
| **Size** | 4,298 question sequences, 12,000+ unique questions, 200 databases |
| **Link** | https://yale-lily.github.io/spider |

**What it measures**: Context-dependent SQL generation within coherent question sequences.

### 2.7 KaggleDBQA (Microsoft, 2021)

| Property | Value |
|----------|-------|
| **Type** | Realistic, real-world databases from Kaggle |
| **Size** | 272 examples, 8 databases |
| **Link** | https://github.com/Chia-Hsuan-Lee/KaggleDBQA |

**What it measures**: Realistic evaluation with messy, real-world data. Using database documentation boosts accuracy by **13.2%**.

### 2.8 EHRSQL (NeurIPS 2022)

| Property | Value |
|----------|-------|
| **Type** | Healthcare/Electronic Health Records |
| **Size** | Large-scale, linked to MIMIC-III and eICU databases |
| **Link** | https://github.com/glee4810/EHRSQL |

**What it measures**: Practical healthcare SQL generation with domain-specific challenges (patient queries, clinical timing, medical terminology).

### 2.9 Archer (Bilingual)

| Property | Value |
|----------|-------|
| **Type** | Complex reasoning (arithmetic, commonsense, hypothetical) |
| **Size** | 1,042 English + 1,042 Chinese questions, 521 unique SQL queries |
| **Link** | https://sig4kg.github.io/archer-bench/ |

**What it measures**: Advanced reasoning beyond simple SQL translation — requires arithmetic, commonsense, and hypothetical reasoning.

### 2.10 BookSQL (Accounting Domain)

| Property | Value |
|----------|-------|
| **Type** | Financial/accounting domain |
| **Size** | 100K NL-SQL pairs, 1M records |

**What it measures**: Domain-specific SQL for accounting and financial data.

### 2.11 Dr.Spider (AWS, ICLR 2023)

| Property | Value |
|----------|-------|
| **Type** | Diagnostic robustness benchmark |
| **Size** | 17 perturbation types on databases, NL questions, SQL |
| **Link** | https://github.com/awslabs/diagnostic-robustness-text-to-sql |

**What it measures**: Model robustness under various perturbations. Even the best model drops **14.0%** overall, and **50.7%** on the hardest perturbation.

### 2.12 SEDE (Stack Exchange)

| Property | Value |
|----------|-------|
| **Type** | Real-world Stack Exchange queries |
| **Link** | https://github.com/hirupert/sede |

**What it measures**: Real user SQL queries from Stack Exchange Data Explorer.

### 2.13 CSpider (Chinese)

| Property | Value |
|----------|-------|
| **Type** | Chinese Text-to-SQL (translation of Spider) |

**What it measures**: Cross-lingual Text-to-SQL capability.

### 2.14 UNITE (AWS, 2023)

| Property | Value |
|----------|-------|
| **Type** | Unified evaluation with linguistic variations |
| **Size** | 120K+ additional examples vs Spider, 3x SQL patterns, 29K databases |
| **Variations** | Naive, Syntactic, Morphological, Lexical, Semantic, Missing Info |
| **Link** | https://github.com/awslabs/unified-text2sql-benchmark |

**What it measures**: Robustness across different linguistic formulations of the same question.

### 2.15 FinSQL (Financial)

| Property | Value |
|----------|-------|
| **Type** | Financial domain SQL |

**What it measures**: Domain-specific SQL for financial data analytics.

---

## 3. Leaderboards

### 3.1 BIRD Execution Accuracy (EX) — Test Set

*As of February 2026. Human ceiling: 92.96%*

| Rank | Model/Method | Dev | Test | Type |
|------|--------------|-----|------|------|
| 1 | AskData + GPT-4o | 77.64% | **81.95%** | Proprietary |
| 2 | Agentar-Scale-SQL | 74.90% | **81.67%** | Proprietary |
| 3 | MARS-SQL (7B, RL) | **77.84%** | — | **Open-source** |
| 4 | LongData-SQL | 74.32% | 77.53% | Proprietary |
| 5 | XiYan-SQL (ensemble) | — | **75.63%** | **Open-source** |
| 6 | Zhiwen-Lingsi-Agent | 73.53% | 76.63% | Proprietary |
| 7 | DeepEye-SQL | 73.53% | 76.58% | Proprietary |
| 8 | Q-SQL (AWS) | 72.99% | 76.47% | Proprietary |
| 9 | MIC2-SQL | 74.45% | 76.41% | Proprietary |
| 10 | SiriusAI-Text2SQL-Agent | 74.64% | 76.30% | Proprietary |
| 11 | CHASE-SQL + Gemini | — | 73.00% | Proprietary |
| 12 | Contextual-SQL (local) | ~73% | — | **Open-source** |
| 13 | Arctic-Text2SQL-R1-32B | 70.5% | — | **Open-source** |
| 14 | Arctic-Text2SQL-R1-14B | 70.1% | — | **Open-source** |
| 15 | XiYanSQL-QwenCoder-32B | — | 69.03% | **Open-source** |
| 16 | Arctic-Text2SQL-R1-7B | 68.9% | 68.5% | **Open-source** |
| 17 | Qwen2.5-Coder-32B (ExCoT) | 68.51% | 68.53% | **Open-source** |
| 18 | Llama-3.1-Arctic-ExCoT-70B | — | 68.53% | **Open-source** |
| 19 | OmniSQL-32B | 67.0% | — | **Open-source** |
| 20 | CHESS + GPT-4 | 65.0% | 66.69% | Proprietary |

### 3.2 BIRD R-VES (Reward-based Valid Efficiency Score)

| Rank | Model/Method | Score | Type |
|------|--------------|-------|------|
| 1 | OpenSearch-SQL v2 + GPT-4o | 69.36% | Proprietary |
| 2 | ExSL + granite-34b-code | 68.79% | **Open-source** |
| 3 | CHASE-SQL + Gemini | 68.44% | Proprietary |
| 4 | Distillery + GPT-4o | 67.41% | Proprietary |
| 5 | AskData + GPT-4o | 66.92% | Proprietary |

### 3.3 Spider 1.0 Execution Accuracy (EX) — Leaderboard Frozen

| Rank | Model/Method | EX | Type |
|------|--------------|-----|------|
| 1 | MiniSeek | **91.2%** | Proprietary |
| 2 | DAIL-SQL + GPT-4 + SC | 86.6% | Proprietary |
| 3 | DAIL-SQL + GPT-4 | 86.2% | Proprietary |
| 4 | DPG-SQL + GPT-4 + SC | 85.6% | Proprietary |
| 5 | DIN-SQL + GPT-4 | 85.3% | Proprietary |
| 6 | Hindsight CoT + GPT-4 | 83.9% | Proprietary |
| 7 | C3 + ChatGPT (zero-shot) | 82.3% | Proprietary |
| 8 | MARS-SQL (7B, RL) | — | **Open-source** (89.75% test) |
| 9 | Qwen2.5-Coder-7B | 82.0% | **Open-source** |
| 10 | RESDSQL-3B + NatSQL | 79.9% | **Open-source** |

### 3.4 Spider 2.0 Leaderboards

**Spider 2.0-Snow (Snowflake, 547 examples)**

| Rank | Model/Method | EX |
|------|--------------|-----|
| 1 | QUVI-3 + Gemini-3-pro-preview | **94.15%** |
| 2 | TCDataAgent-SQL + Contextual Scaling | 93.97% |
| 3 | Native mini | 92.50% |
| 4 | Prism Swarm + Claude-Sonnet-4.5 | 90.49% |
| 5 | QUVI-3 + Claude-Opus-4.6 | 86.28% |

**Spider 2.0-Lite (multi-DB, 547 examples)**

| Rank | Model/Method | EX |
|------|--------------|-----|
| 1 | QUVI-2.3 + Claude-Opus-4.5 | **65.81%** |
| 2 | EXA-SQL | 64.16% |
| 3 | ReFoRCE + o3 | 55.21% |
| 4 | CoFD-SQL + GPT-5 | 54.66% |
| 5 | AutoLink + DeepSeek-R1 | 52.28% |

**Spider 2.0-DBT (DuckDB, 68 examples)**

| Rank | Model/Method | EX |
|------|--------------|-----|
| 1 | Databao Agent | **44.11%** |
| 2 | Shadowfax-DBT-Agent + GPT-5 | 41.18% |
| 3 | Spider-Agent-Extended + GPT-5 | 39.71% |
| 4 | Symbiote Agent + GPT-5 | 35.29% |
| 5 | Chicory AI Agent + Claude Sonnet 4.5 | 35.29% |

---

## 4. Best Local Models (<=70B) for Text-to-SQL

### 4.1 Tier 1: Specialized SQL Models (Best Accuracy)

| Model | Size | BIRD-dev | Spider | Technique | Notes |
|-------|------|----------|--------|-----------|-------|
| **MARS-SQL** | 7B | **77.84%** | **89.75%** | Multi-agent RL (GRPO) | SOTA open-source; 3 agents (Grounding, Generation, Validation); trained on BIRD only |
| **Arctic-Text2SQL-R1** | 7B/14B/32B | 68.9/70.1/70.5% | — | RL (GRPO) + execution reward | Snowflake; matches DeepSeek-V3 (671B MoE) with 7B |
| **XiYanSQL-QwenCoder** | 32B | — | — | Multi-generator ensemble | 69.03% BIRD-test; based on Qwen2.5-Coder |
| **OmniSQL** | 7B/14B/32B | 67.0% (32B) | — | SynSQL-2.5M training data | Matches GPT-4o; trained on 2.5M synthetic samples |
| **SQLCoder** | 7B/15B/34B/70B | — | ~93% (70B) | Fine-tuned on 20K pairs | Defog.ai; SQLCoder-70B outperforms GPT-4 |
| **CodeS** | 1B/3B/7B/15B | ~60% (15B) | SOTA at release | SFT on StarCoder base | 10-100x smaller than competing LLMs |

### 4.2 Tier 2: General Code Models (Good SQL Capability)

| Model | Size | BIRD-dev | Spider-dev | Notes |
|-------|------|----------|------------|-------|
| **Qwen2.5-Coder** | 7B/32B | 68.51% (32B ExCoT) | 82.0% (7B) | Best general-purpose code model for SQL |
| **Qwen3-Coder** | 30B+ | Competitive | — | Newer; used in Contextual-SQL experiments |
| **DeepSeek-Coder-V2** | 16B/236B | Competitive | ~GPT-4-Turbo level | MoE architecture; strong code generation |
| **Llama 3.1** | 8B/70B | 68.53% (70B ExCoT) | 84.1% (70B SFT) | Meta; good base for fine-tuning |
| **Llama 3.1 8B** | 8B | — | 79.9% (dev) | Top-10 on frozen Spider leaderboard |

### 4.3 Key Insight: Pipeline Matters More Than Model Size

The **Contextual-SQL** research (Contextual AI, Feb 2025) demonstrated that:

1. A **local 32B model** with proper pipeline can match API-based GPT-4o systems
2. **Inference-time scaling** (generating N candidates at temperature=1, across M few-shot configs) is key
3. **Execution filtering + consistency voting + reward model** selection outperforms simple greedy decoding
4. Even 7B models become competitive when combined with proper candidate generation and ranking

**Pipeline impact on Qwen2.5-Coder-32B**:
- Greedy decoding: ~60% BIRD-dev
- + Multi-candidate generation: ~65%
- + Execution filtering + consistency: ~68%
- + Reward model ranking: ~73% (matching top proprietary systems)

### 4.4 Recommended Models for BIAI (Local Deployment)

| Priority | Model | Size (VRAM) | Why |
|----------|-------|-------------|-----|
| **#1** | Arctic-Text2SQL-R1-7B | ~5GB Q4 | Best accuracy/size ratio; 68.9% BIRD with 7B params |
| **#2** | Qwen2.5-Coder-7B-Instruct | ~5GB Q4 | 82% Spider; versatile; excellent for general SQL |
| **#3** | OmniSQL-7B | ~5GB Q4 | Trained on 2.5M samples; strong generalization |
| **#4** | Qwen2.5-Coder-32B-Instruct | ~20GB Q4 | 68.5% BIRD; best if VRAM allows |
| **#5** | SQLCoder-7B-2 | ~5GB Q4 | Surpasses GPT-3.5; good for simple schemas |

---

## 5. Techniques That Improve Accuracy

### 5.1 Multi-Candidate Generation + Selection (Highest Impact: +5-15%)

**Concept**: Generate multiple SQL candidates and select the best one.

| Method | Approach | Impact |
|--------|----------|--------|
| **Self-Consistency (SC-SQL)** | Generate N candidates, execute all, majority vote on results | +3-5% EX |
| **Contextual-SQL** | N candidates x M few-shot configs, execution filter + reward model | +10-15% EX |
| **CHASE-SQL** | Diverse generators (CoT, plan-based, synthetic examples) + pairwise ranking | +5-8% EX |
| **XiYan-SQL** | Multiple schema filters + multi-generator + selection model | +8-12% EX |

**Relevance for BIAI**: HIGH. BIAI's self-correction loop already retries on failure. Adding parallel candidate generation with execution-based voting would be a major accuracy boost.

### 5.2 Schema Linking & Pruning (Impact: +3-8%)

**Concept**: Identify relevant tables/columns before SQL generation, remove irrelevant ones.

| Method | Approach | Impact |
|--------|----------|--------|
| **Schema pruning** | Filter schema to top-K relevant tables/columns | +3-5% EX |
| **M-Schema format** | SQLAlchemy reflection with FK relationships + column examples | +2-4% EX |
| **LinkAlign** | Scalable multi-database schema linking with CoT + SC | +3-6% EX |
| **Solid-SQL** | Enhanced schema-linking based in-context learning | +2-5% EX |

**Note**: There is a debate ("The Death of Schema Linking?") suggesting that with powerful reasoning models (o1, o3), schema linking becomes less critical. However, for smaller local models (7B-32B), schema linking remains essential.

**Relevance for BIAI**: HIGH. BIAI already uses Vanna's RAG to retrieve relevant schema. Adding explicit schema pruning (filter to top-K tables) before generation would help, especially with large databases.

### 5.3 Chain-of-Thought (CoT) Reasoning (Impact: +2-5%)

**Concept**: Have the model reason step-by-step before generating SQL.

| Variant | Approach |
|---------|----------|
| **Standard CoT** | "Think step by step" before SQL |
| **Divide-and-conquer CoT** | Identify tables → match columns → build conditions → assemble SQL |
| **Execution-guided CoT (ExCoT)** | CoT + execution verification + DPO optimization |
| **Hindsight CoT** | Generate SQL first, then explain reasoning, re-generate |

**Relevance for BIAI**: MEDIUM. Can be added to Vanna's prompt template. ExCoT (Snowflake) is particularly effective for fine-tuned models.

### 5.4 DIN-SQL: Decomposed In-Context Learning (Impact: +3-7%)

**Concept**: Decompose Text-to-SQL into 4 sequential subtasks.

1. **Schema linking** → identify relevant tables/columns
2. **Classification & decomposition** → determine query complexity, break down
3. **SQL generation** → generate SQL with few-shot examples
4. **Self-correction** → verify and fix errors

Achieves **85.3% EX** on Spider with GPT-4.

**Relevance for BIAI**: MEDIUM. The 4-step pipeline adds latency but improves accuracy. BIAI's self-correction loop already covers step 4.

### 5.5 DAIL-SQL: Diverse-Aware In-Context Learning (Impact: +2-4%)

**Concept**: Select few-shot examples that are both semantically similar AND SQL-pattern diverse.

Achieves **86.6% EX** on Spider with GPT-4 + Self-Consistency (SOTA at time of submission).

**Relevance for BIAI**: HIGH. Vanna's RAG already retrieves examples. Improving example selection (semantic similarity + SQL diversity) is a direct improvement.

### 5.6 MAC-SQL: Multi-Agent Collaborative Framework (Impact: +5-10%)

**Concept**: Three specialized agents work together.

1. **Selector** — condenses database schema, keeps relevant parts
2. **Decomposer** — breaks complex questions into sub-problems
3. **Refiner** — validates and fixes SQL errors

Achieves **59.59% EX** on BIRD test, **86.75% EX** on Spider with GPT-4.

**Relevance for BIAI**: LOW-MEDIUM. Adds complexity and latency. The multi-agent approach is powerful but may be overkill for single-question chat.

### 5.7 CHESS: Contextual Harnessing for Efficient SQL Synthesis (Impact: +3-6%)

****: Entity & context retrieval → schema filtering → SQL generation + revision.

Achieves **65.0% dev / 66.69% test** on BIRD.

**Relevance for BIAI**: MEDIUM. The entity retrieval step (finding actual database values mentioned in questions) is directly applicable.

### 5.8 C3: Clear Prompting + Calibration + Consistency (Impact: +3-5%)

**Concept**: Three components addressing input, bias, and output.

1. **Clear Prompting (CP)** — optimized zero-shot prompt format
2. **Calibration with Hints (CH)** — mitigate model biases with schema hints
3. **Consistent Output (CO)** — sample multiple, vote on execution results

Achieves **82.3% EX** on Spider with ChatGPT (zero-shot).

**Relevance for BIAI**: HIGH. Zero-shot technique that requires no training. Can be applied directly to Vanna's pipeline.

### 5.9 Execution-Based Verification & Self-Correction (Impact: +3-8%)

| Method | Approach | Impact |
|--------|----------|--------|
| **RetrySQL** | Training with corrupted+corrected SQL pairs; 1.5B model matches GPT-4o-mini | +4% EX |
| **ExeSQL** | Self-taught with execution feedback; iterative DPO | +5-8% EX |
| **EMLC** | Multi-level correction: semantic detection + LLM correction | +3-5% EX |
| **MAGIC** | Self-correction guidelines generated from errors | +2-4% EX |

**Relevance for BIAI**: ALREADY IMPLEMENTED. BIAI's `SelfCorrectionLoop` retries up to 5 times with error feedback. Can be improved by training a local correction model.

### 5.10 RAG for SQL (Vanna.ai Approach)

**How Vanna works**:
1. Train schema DDL + example queries into ChromaDB vector store
2. For each user question, retrieve relevant DDL + examples
3. Build prompt with retrieved context + question
4. Generate SQL via LLM

**Advantages**: No fine-tuning needed; adapts to new schemas by re-training vectors; works with any LLM.

**Limitations**: Quality depends on example curation; no formal business logic; inconsistent interpretations across queries.

**Compared to alternatives**:
- **Fine-tuning** gives better accuracy (+5-15%) but requires training data and compute
- **Semantic layer** (Wren AI) gives consistency but requires upfront modeling
- **Best practice**: Combine RAG + fine-tuned model + execution verification

### 5.11 Fine-Tuning vs Prompting Summary

| Approach | Spider EX | BIRD EX | Latency | Cost | Setup |
|----------|-----------|---------|---------|------|-------|
| Zero-shot prompting (GPT-4) | ~70% | ~55% | Low | High (API) | Minimal |
| Few-shot prompting (GPT-4) | ~82% | ~65% | Low | High (API) | Examples needed |
| RAG + prompting (Vanna) | ~75-80% | ~60% | Medium | Low (local) | Schema training |
| Fine-tuned 7B | ~80% | ~65% | Low | Low (local) | Training data + GPU |
| Fine-tuned 7B + RL (MARS-SQL) | **89.75%** | **77.84%** | Low | Medium (training) | RL setup |
| Fine-tuned 32B + pipeline | ~85% | ~70% | Medium | Medium | Full pipeline |
| GPT-4 + full pipeline (DAIL-SQL) | **86.6%** | ~72% | High | Very High | Complex setup |

**Key insight**: Fine-tuned small models (7B) with proper RL training (MARS-SQL approach) now **surpass** prompting-based GPT-4 pipelines on both Spider and BIRD.

---

## 6. Vanna.ai Alternatives

### 6.1 Comparison Matrix

| Tool | Architecture | LLM Support | Open Source | License | Benchmark Accuracy | Active Dev | Best For |
|------|-------------|-------------|-------------|---------|-------------------|------------|----------|
| **Vanna.ai** | RAG (ChromaDB + LLM) | Any (Ollama, OpenAI, etc.) | Yes | MIT | No official benchmarks | Active (v2.0, 2025) | Developers, custom embedding |
| **Wren AI** | Semantic Layer (MDL) | OpenAI, custom | Yes | Apache 2.0 (core) | No official benchmarks | Very Active | Enterprise BI teams |
| **DB-GPT** | Multi-agent (AWEL) | Any (SMMF framework) | Yes | Apache 2.0 | DB-GPT-Hub benchmarks | Very Active | Local multi-agent workflows |
| **Chat2DB** | SQL Client + AI | 10+ LLMs (GPT-4o, Claude, Qwen, DeepSeek) | Yes | Apache 2.0 | No official | Very Active | Database management + AI |
| **BlazeSQL** | AI chatbot + dashboard | Proprietary | No | Commercial | No official | Active | Non-technical users |
| **Text2SQL.ai** | Cloud API | Proprietary | No | Commercial/Free tier | No official | Active | Quick queries |
| **AI2SQL** | Cloud NL-to-SQL | Proprietary | No | Commercial | No official | Active | Business users |

### 6.2 Detailed Comparisons

#### Wren AI vs Vanna.ai

| Aspect | Wren AI | Vanna.ai |
|--------|---------|----------|
| **Core approach** | Semantic layer (MDL) | RAG (vector retrieval) |
| **Business logic** | Formal definitions (metrics, dimensions) | Prompt engineering + examples |
| **Consistency** | Same question always = same SQL | May vary across queries |
| **Setup effort** | Higher (need MDL modeling) | Lower (train examples) |
| **Flexibility** | Lower (structured) | Higher (any LLM, any DB) |
| **Enterprise features** | RBAC, audit, governance built-in | Must build custom |
| **GitHub stars** | ~12K (since May 2024) | ~20K (since Jul 2023) |
| **Self-correction** | Built-in SQL validation | Via application code |
| **Deployment** | Self-hosted or Cloud | Library in your app |

**Verdict**: Wren AI is better for enterprise teams needing governance. Vanna is better for developers building custom solutions (like BIAI).

#### DB-GPT vs Vanna.ai

| Aspect | DB-GPT | Vanna.ai |
|--------|--------|----------|
| **Core approach** | Multi-agent framework (AWEL) | RAG library |
| **Architecture** | Agent orchestration, RAG, SFT hub | Simple generate-validate loop |
| **Model management** | SMMF (multi-model switching) | Single model per instance |
| **Text-to-SQL** | DB-GPT-Hub with SFT benchmarks | RAG-based generation |
| **Extensibility** | Agents, workflows, plugins | Custom LLM/vectorstore classes |
| **UI** | Built-in web UI | No UI (library only) |
| **Complexity** | High | Low |

**Verdict**: DB-GPT is more powerful but more complex. For BIAI (already Reflex-based), Vanna's simplicity is an advantage.

#### Chat2DB vs Vanna.ai

| Aspect | Chat2DB | Vanna.ai |
|--------|---------|----------|
| **Type** | Full SQL client | Python library |
| **AI features** | Text-to-SQL, SQL fix, dashboards | Text-to-SQL only |
| **Database support** | 10+ (MySQL, PG, Oracle, ClickHouse...) | Any via connectors |
| **UI** | Full desktop/web client | No UI |
| **LLM support** | GPT-4o, Claude, Qwen, DeepSeek, etc. | Any via adapters |
| **Custom training** | Enterprise feature | Core feature (RAG training) |

**Verdict**: Chat2DB is a complete product; Vanna is a building block. For BIAI, Vanna remains the right choice as we build our own UI.

### 6.3 Newer Alternatives (2025-2026)

| Tool | Description | Status |
|------|-------------|--------|
| **Datrics Text2SQL** | Open-source, tuned RAG pipeline with schema retrieval | Active |
| **MindsDB** | AI-in-database platform; SQL queries to AI models | Active, funded |
| **Dataherald** | Enterprise NL-to-SQL engine | Active |
| **NSQL** (NumbersStation) | Fine-tuned open-source SQL models | Research |

### 6.4 Techniques We Can Adopt from Alternatives

| From | Technique | Applicability to BIAI |
|------|-----------|----------------------|
| **Wren AI** | Semantic layer / business term definitions | HIGH — add MDL-like config for consistent metrics |
| **DB-GPT** | Multi-agent orchestration | MEDIUM — could split schema-linking from generation |
| **Contextual-SQL** | Multi-candidate generation + reward model | HIGH — major accuracy boost |
| **Chat2DB** | Multi-LLM switching | MEDIUM — already possible with Vanna adapters |
| **MARS-SQL** | RL-trained SQL agents | HIGH — but requires training infrastructure |
| **Arctic-Text2SQL** | Execution-based RL training (GRPO) | HIGH — pre-trained models available on HuggingFace |

---

## 7. Recommendations for BIAI

### 7.1 Quick Wins (Immediate, No Training Required)

| # | Action | Expected Impact | Effort |
|---|--------|----------------|--------|
| 1 | **Switch SQL model to Arctic-Text2SQL-R1-7B** | +10-15% accuracy vs current Qwen | Low (Ollama/HF) |
| 2 | **Add multi-candidate generation** (generate 5 candidates, vote) | +5-8% accuracy | Medium |
| 3 | **Improve schema context** (M-Schema format with FK + examples) | +2-4% accuracy | Low |
| 4 | **Add schema pruning** (top-K relevant tables only) | +2-3% accuracy | Medium |
| 5 | **Improve example selection** (semantic + SQL diversity, DAIL-SQL) | +2-3% accuracy | Medium |

### 7.2 Medium-Term Improvements (1-2 Weeks)

| # | Action | Expected Impact | Effort |
|---|--------|----------------|--------|
| 6 | **Add execution-based candidate selection** (run all candidates, keep valid) | +3-5% accuracy | Medium |
| 7 | **Implement C3-style consistency voting** | +2-3% accuracy | Medium |
| 8 | **Add entity retrieval** (find actual DB values in question) | +2-4% accuracy | High |
| 9 | **Semantic definitions file** (Wren-AI-inspired business terms) | Consistency improvement | Medium |

### 7.3 Long-Term (Requires Training)

| # | Action | Expected Impact | Effort |
|---|--------|----------------|--------|
| 10 | **Fine-tune Qwen2.5-Coder-7B on customer's DB schema** | +5-10% on domain | Very High |
| 11 | **Train reward model** for candidate ranking (Contextual-SQL approach) | +5-8% accuracy | Very High |
| 12 | **RL training** (MARS-SQL GRPO approach) | Potentially +15-20% | Very High |

### 7.3 Model Recommendation Summary

**For BIAI's current architecture (Vanna + Ollama):**

| Scenario | Model | Expected BIRD-level | Notes |
|----------|-------|-------------------|-------|
| **Default (8GB VRAM)** | Arctic-Text2SQL-R1-7B Q4 | ~65-68% | Best accuracy/size ratio |
| **With good GPU (16GB)** | Qwen2.5-Coder-32B Q4 | ~68-70% | Better general reasoning |
| **Maximum accuracy (24GB+)** | Arctic-Text2SQL-R1-32B + multi-candidate | ~70-73% | Best local setup possible |
| **Current model for comparison** | qwen2.5-coder:7b-instruct-q4 | ~55-60% | Baseline (general code model, not SQL-specialized) |

---

## 8. Sources

### Benchmarks
- [Spider (Yale)](https://yale-lily.github.io/spider)
- [Spider 2.0](https://spider2-sql.github.io/)
- [BIRD-bench](https://bird-bench.github.io/)
- [LiveSQLBench](https://livesqlbench.ai/)
- [BIRD-CRITIC](https://bird-critic.github.io/)
- [WikiSQL (Salesforce)](https://github.com/salesforce/WikiSQL)
- [UNITE (AWS)](https://github.com/awslabs/unified-text2sql-benchmark)
- [Dr.Spider (AWS)](https://github.com/awslabs/diagnostic-robustness-text-to-sql)
- [Archer](https://sig4kg.github.io/archer-bench/)
- [EHRSQL](https://github.com/glee4810/EHRSQL)
- [KaggleDBQA](https://github.com/Chia-Hsuan-Lee/KaggleDBQA)

### Leaderboards & Surveys
- [OpenLM.ai Text2SQL Leaderboard](https://openlm.ai/text2sql-leaderboard/)
- [AIMultiple Text-to-SQL Comparison 2026](https://research.aimultiple.com/text-to-sql/)
- [Papers With Code — Spider SOTA](https://paperswithcode.com/sota/text-to-sql-on-spider)
- [Awesome-LLM-based-Text2SQL (TKDE 2025 Survey)](https://github.com/DEEP-PolyU/Awesome-LLM-based-Text2SQL)
- [NL2SQL Handbook (HKUST)](https://github.com/HKUSTDial/NL2SQL_Handbook)

### Key Papers & Models
- [MARS-SQL: Multi-Agent RL for Text-to-SQL](https://arxiv.org/abs/2511.01008)
- [Arctic-Text2SQL-R1 (Snowflake)](https://huggingface.co/Snowflake/Arctic-Text2SQL-R1-7B)
- [Contextual-SQL (Open-source)](https://contextual.ai/blog/open-sourcing-the-best-local-text-to-sql-system)
- [CHASE-SQL (ICLR 2025)](https://arxiv.org/abs/2410.01943)
- [OmniSQL (VLDB 2025)](https://arxiv.org/abs/2503.02240)
- [XiYan-SQL (Alibaba)](https://github.com/XGenerationLab/XiYan-SQL)
- [CodeS (SIGMOD 2024)](https://github.com/RUCKBReasoning/codes)
- [SQLCoder (Defog.ai)](https://github.com/defog-ai/sqlcoder)
- [DIN-SQL](https://arxiv.org/abs/2304.11015)
- [DAIL-SQL](https://arxiv.org/abs/2308.15363)
- [MAC-SQL](https://arxiv.org/abs/2312.11242)
- [CHESS](https://arxiv.org/abs/2405.16755)
- [C3 (Zero-shot Text-to-SQL)](https://arxiv.org/abs/2307.07306)
- [RetrySQL](https://arxiv.org/abs/2507.02529)
- [ExCoT (Snowflake)](https://www.snowflake.com/en/engineering-blog/arctic-text2sql-excot-sql-generation-accuracy/)

### Tools & Alternatives
- [Vanna.ai](https://vanna.ai/)
- [Wren AI](https://www.getwren.ai/)
- [DB-GPT](https://github.com/eosphoros-ai/DB-GPT)
- [Chat2DB](https://github.com/CodePhiliaX/Chat2DB)
- [Wren AI vs Vanna Comparison](https://www.getwren.ai/post/wren-ai-vs-vanna-the-enterprise-guide-to-choosing-a-text-to-sql-solution)
- [Text2SQL.ai Tools Guide 2025](https://www.text2sql.ai/best-text-to-sql-tools-2025)

---

*Report generated: February 2026 | For BIAI project (Business Intelligence AI)*
