# Text-to-SQL Benchmarks & State-of-the-Art Research (2025-2026)

> Compiled: 2026-02-15 | For BIAI Project (Vanna + RAG + Ollama)

---

## 1. Benchmark Overview Table

| Benchmark | Year | Size | Databases | Complexity | Focus | Metric |
|-----------|------|------|-----------|------------|-------|--------|
| **WikiSQL** | 2017 | 80,654 examples | 26,531 tables | Simple (single-table, no JOIN) | Single-table SQL | Execution Accuracy |
| **Spider** | 2018 | 10,181 questions, 5,693 SQL | 200 DBs, 138 domains | Complex (JOIN, nested, GROUP BY) | Cross-database generalization | Execution Accuracy (EX) |
| **SParC** | 2019 | 4,298 sequences, 12,000+ questions | 200 DBs | Complex + context | Context-dependent, multi-turn | Question Match, Interaction Match |
| **CoSQL** | 2019 | 3,007 dialogues, 30,000+ turns, 10,000 SQL | 200 DBs, 138 domains | Complex + conversational | Conversational Text-to-SQL | Dialogue State Accuracy |
| **SEDE** | 2021 | 12,023 SQL queries | Stack Exchange DB | Very complex, real-world | Naturally-occurring queries | PCM-F1 |
| **KaggleDBQA** | 2021 | 272 examples | 8 Kaggle DBs | Real-world, domain-specific | Real web databases | Execution Accuracy |
| **Dr.Spider** | 2023 | 17 perturbation types on Spider | 200 DBs (Spider) | Robustness testing | Perturbation robustness | Performance Drop % |
| **BIRD** | 2023 | 12,751 question-SQL pairs | 95 DBs (33.4 GB total) | Complex, large-scale | Large DBs, 37+ professional domains | Execution Accuracy (EX) |
| **CSpider** | 2019 | 9,691 questions | 166 DBs | Same as Spider, Chinese | Chinese Text-to-SQL | Exact Match, EX |
| **DuSQL** | 2020 | 23,797 question-SQL pairs | 200 DBs | Complex, Chinese | Chinese cross-domain | Exact Match, EX |
| **CHASE** | 2021 | 17,940 questions | 280 DBs | Complex, Chinese | Multi-turn Chinese Text-to-SQL | Exact Match |
| **Spider 2.0** | 2024 | 632 real-world problems | 1000+ columns per DB | Enterprise-level, multi-dialect | Real enterprise SQL workflows | Execution Accuracy (EX) |
| **BIRD-Interact** | 2025 | 600 examples | Multiple DBs | Interactive, multi-turn | Collaborative human-LLM interaction | Success Rate |
| **LiveSQLBench** | 2025 | 600 examples | Multiple DBs | Full SQL spectrum | All SQL operations + hierarchical KB | EX with test cases |
| **LogicCat** | 2025 | N/A | N/A | Complex reasoning | Chain-of-Thought SQL reasoning | EX |
| **LLMSQL** | 2025 | Upgraded WikiSQL | WikiSQL tables | Enhanced for LLM era | Modern WikiSQL with harder queries | EX |
| **SWE-SQL** | 2025 | N/A | Real applications | Real-world bug fixing | SQL debugging in real apps | NeurIPS 2025 |

---

## 2. Current SOTA Results (as of early 2026)

### Spider 1.0 Leaderboard (Test Set)

| Rank | Model/Method | Execution Accuracy | Type |
|------|-------------|-------------------|------|
| 1 | GPT-4 based methods | ~91.2% | Proprietary LLM |
| 2 | DAIL-SQL + GPT-4 | ~86.6% | In-context learning |
| 3 | DIN-SQL + GPT-4 | ~85.3% | Decomposed prompting |
| 4 | Llama3 8B fine-tuned | ~79.9% (dev) | Open model, fine-tuned |
| - | *Human performance* | ~86.8% | Human |

> Note: Spider 1.0 is considered largely "solved" by proprietary models. Focus has shifted to Spider 2.0 and BIRD.

### Spider 2.0 Leaderboard (ICLR 2025 Oral)

| Rank | Model/Method | Execution Accuracy | Notes |
|------|-------------|-------------------|-------|
| 1 | DAIL-SQL + GPT-4o | ~5.68% | Best reported method |
| 2 | o1-preview | ~17.1% | On full Spider 2.0 tasks |
| 3 | GPT-4o | ~10.1% | Baseline |

> Spider 2.0 is dramatically harder than Spider 1.0 — enterprise-level complexity with 1000+ columns, multi-dialect, 100+ line queries.

### BIRD Leaderboard (Test Set)

| Rank | Model/Method | Execution Accuracy | Type |
|------|-------------|-------------------|------|
| 1 | **Agentar-Scale-SQL** | **81.67%** | Agentic, test-time scaling |
| 2 | AskData + GPT-4o | ~75%+ | Proprietary |
| 3 | LongData-SQL | ~74%+ | Long-context |
| 4 | CHASE-SQL + Gemini | ~73%+ | Multi-agent |
| 5 | XiYan-SQL | ~72%+ | Multi-stage |
| - | Gemini-SQL (single model) | Top single-model | Single model |
| - | Databricks RLVR 32B | Top open single-model | RL-trained |
| - | Sophon-Text2SQL-32B | Top open single-model | Fine-tuned |
| - | Arctic-Text2SQL-R1-32B | Top open single-model | RL-trained |

> BIRD is now the primary benchmark for Text-to-SQL evaluation. Human performance ~92.5%.

### BIRD-Interact (Released Aug 2025)

| Model | Success Rate |
|-------|-------------|
| Best LLM | 16.33% |
| c-interact / a-interact portions | 10.0% |

### LiveSQLBench (Released Sep 2025)

| Model | Colloquial Queries | Normal Queries |
|-------|-------------------|----------------|
| Gemini-2.5-pro | 28.67% | 35.67% |

### Enterprise Benchmarks (BIRD-Ent, Spider-Ent)

| Benchmark | Best Model Score | Drop from Academic |
|-----------|-----------------|-------------------|
| BIRD-Ent | 36.9% | -52.4% |
| Spider-Ent | 57.8% | -42.7% |

---

## 3. Benchmark Deep Dives

### Spider 1.0 (Yale, 2018)
- **What:** 10,181 questions across 200 databases spanning 138 domains
- **Why important:** Gold standard for cross-database generalization
- **SQL complexity:** GROUP BY, ORDER BY, HAVING, nested queries, JOINs
- **Split:** Train (8,659) / Dev (1,034) / Test (held-out)
- **Status:** Largely saturated by GPT-4 class models (~91% EX)
- **Limitations:** Clean, curated schema; unrealistic for enterprise use

### Spider 2.0 (ICLR 2025 Oral)
- **What:** 632 real-world enterprise text-to-SQL problems
- **Databases:** Often 1000+ columns, real enterprise data
- **Dialects:** BigQuery, Snowflake, SQLite (multi-dialect)
- **Operations:** Transformation, analytics, 100+ line queries
- **Requirements:** Schema navigation, dialect docs, project-level codebase understanding
- **Variants:**
  - Spider 2.0-Lite: Self-contained, prepared metadata, text-in/text-out
  - Spider 2.0-Snow: 547 examples on Snowflake
  - Spider 2.0-DBT: 68 examples requiring project code understanding
- **Key insight:** Best models achieve only ~5-17% accuracy — massive gap from Spider 1.0

### BIRD (2023)
- **What:** 12,751 question-SQL pairs across 95 databases (33.4 GB total)
- **Domains:** 37+ professional domains (blockchain, healthcare, education, etc.)
- **Why important:** More realistic than Spider, larger databases, domain knowledge needed
- **External knowledge:** Some questions require domain-specific knowledge beyond schema
- **Mini-dev:** Smaller evaluation set available on GitHub
- **BIRD-Interact (ICLR 2026 Oral):** Interactive variant with human-LLM collaboration
- **BIRD-CRITIC (NeurIPS 2025):** SWE-SQL — SQL debugging in real applications
- **Current SOTA:** 81.67% (Agentar-Scale-SQL)

### WikiSQL (2017)
- **What:** 80,654 NL-SQL pairs from Wikipedia tables
- **Limitations:** Single-table only, no JOINs, no nested queries, annotation issues
- **Status:** Largely deprecated for serious evaluation
- **Update:** LLMSQL (2025) upgrades WikiSQL for the LLM era with harder queries

### SParC (2019)
- **What:** 4,298 question sequences (12,000+ individual questions) on 200 databases
- **Focus:** Context-dependent, multi-turn semantic parsing
- **Key feature:** Questions build on previous context within a conversation

### CoSQL (2019)
- **What:** 3,007 dialogues, 30,000+ turns, 10,000 expert-labeled SQL queries
- **Focus:** Conversational SQL — most realistic dialogue setting
- **Key feature:** Dialog acts, clarification questions, ambiguity handling

### SEDE (2021)
- **What:** 12,023 naturally-occurring SQL queries from Stack Exchange Data Explorer
- **Focus:** Real-world SQL complexity — written by actual users
- **Key insight:** Models strong on Spider (86.3% PCM-F1) drop to 50.6% on SEDE
- **Diversity:** 10x more SQL templates than other benchmarks

### KaggleDBQA (2021)
- **What:** 272 examples across 8 real Kaggle databases
- **Focus:** Domain-specific data types, unrestricted questions, real web databases
- **Key feature:** Small but realistic — questions not designed for benchmarking

### Dr.Spider (2023)
- **What:** 17 perturbation types applied to Spider (DB, NL, SQL perturbations)
- **Focus:** Robustness — how models handle variations
- **Key finding:** Even best models see 14% average drop, up to 50.7% on hardest perturbations
- **Perturbation types:** Schema renaming, synonym substitution, value changes, etc.

---

## 4. New 2025-2026 Benchmarks

| Benchmark | Conference | Key Innovation |
|-----------|-----------|----------------|
| **Spider 2.0** | ICLR 2025 Oral | Enterprise-level SQL workflows, multi-dialect |
| **BIRD-Interact** | ICLR 2026 Oral | Interactive human-LLM collaboration for SQL |
| **SWE-SQL / BIRD-CRITIC** | NeurIPS 2025 | SQL debugging in real applications |
| **LiveSQLBench** | 2025 | Full SQL spectrum, hierarchical knowledge base, test cases |
| **LogicCat** | 2025 | Complex reasoning, Chain-of-Thought SQL |
| **LLMSQL** | 2025 | Upgraded WikiSQL for LLM era |
| **BenchPress** | VLDB/CIDR 2026 | Human-in-the-loop annotation system for SQL benchmarks |

### Key Trends in Benchmarking (2025-2026):
1. **Enterprise realism** — Moving from academic to real enterprise databases
2. **Multi-dialect** — BigQuery, Snowflake, PostgreSQL, Oracle, etc.
3. **Interactivity** — Multi-turn, clarification, human-in-the-loop
4. **Robustness** — Perturbation resistance, adversarial testing
5. **Full SQL spectrum** — Beyond SELECT: DDL, DML, stored procedures
6. **Hierarchical knowledge** — Domain-specific knowledge bases needed
7. **Dramatic difficulty increase** — Spider 2.0 (5-17%) vs Spider 1.0 (91%) shows the gap between academic and real-world

---

## 5. Evaluation Metrics

| Metric | Description | Used By |
|--------|-------------|---------|
| **Execution Accuracy (EX)** | SQL produces correct results when executed | Spider, BIRD, most modern benchmarks |
| **Exact Match (EM)** | SQL exactly matches gold standard | Legacy, less used now |
| **Valid Efficiency Score (VES)** | Execution accuracy weighted by efficiency | BIRD |
| **PCM-F1** | Partial Component Matching F1 | SEDE |
| **Question Match (QM)** | Per-question accuracy | SParC |
| **Interaction Match (IM)** | Per-interaction accuracy | SParC |
| **Test Suite Accuracy** | Multiple test cases per question | Spider (alternative) |
| **FLEX** | Expert-level False-Less Execution metric | NAACL 2025 |

### Metric Recommendations for BIAI:
- **Primary:** Execution Accuracy (EX) — does the SQL return correct results?
- **Secondary:** Valid SQL rate — does the SQL parse and execute without errors?
- **Practical:** User satisfaction — does the answer make business sense?
- **Efficiency:** Query execution time — is the SQL reasonably optimized?

---

*Note: This document covers benchmark research. Techniques, model performance, and BIAI-specific recommendations are covered in separate research documents.*
