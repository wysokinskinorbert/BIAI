# Western & Open-Source LLM Models for Local SQL Generation & Analytics

> Research date: February 2026 | For BIAI project (Vanna + Ollama)
> Focus: Models runnable locally via Ollama/llama.cpp for Text-to-SQL, code generation, and BI analytics

---

## Table of Contents

1. [Meta Llama Family](#1-meta-llama-family)
2. [Mistral AI Family](#2-mistral-ai-family)
3. [Microsoft Phi Family](#3-microsoft-phi-family)
4. [Google Gemma Family](#4-google-gemma-family)
5. [SQL-Specialized Models](#5-sql-specialized-models)
6. [Code-Specialized Models](#6-code-specialized-models)
7. [Enterprise & MoE Models](#7-enterprise--moe-models)
8. [Hybrid Architecture Models](#8-hybrid-architecture-models)
9. [Other Notable Models](#9-other-notable-models)
10. [Comparative Summary Tables](#10-comparative-summary-tables)
11. [Recommendations for BIAI](#11-recommendations-for-biai)

---

## 1. Meta Llama Family

### 1.1 Llama 4 Scout (April 2025)

| Property | Details |
|---|---|
| **Creator** | Meta |
| **Architecture** | MoE (Mixture of Experts) — 16 experts |
| **Total Parameters** | 109B |
| **Active Parameters** | 17B per token |
| **Context Window** | 10M tokens (industry record); practical 128K for inference |
| **License** | Llama 4 Community License (April 2025) |

**VRAM Requirements:**
| Quantization | VRAM | Notes |
|---|---|---|
| FP16 | ~218 GB | Multi-GPU cluster required |
| Q8_0 | ~113 GB | 2x H100 or similar |
| Q4_K_M | ~60-65 GB | Single H100 80GB |
| 1.78-bit (Unsloth) | ~33.8 GB | Fits in 24GB VRAM GPU, ~20 tok/s |

**Benchmarks:**
- General: Competitive with GPT-4o class models
- Throughput: ~109 tokens/second
- SQL-specific benchmarks not widely published yet

**Availability:**
- Ollama: `ollama run llama4:scout` (official tag)
- GGUF: Available via Unsloth, community quantizations on HuggingFace
- HuggingFace: `meta-llama/Llama-4-Scout-17B-16E-Instruct`

**Key Notes:** The 1.78-bit Unsloth quantization makes this feasible on consumer 24GB GPUs (RTX 4090/3090), but quality loss at extreme quantization should be evaluated. The MoE architecture means 109B total but only 17B active, making it more efficient than dense 109B models.

---

### 1.2 Llama 4 Maverick (April 2025)

| Property | Details |
|---|---|
| **Creator** | Meta |
| **Architecture** | MoE — 128 experts |
| **Total Parameters** | 400B |
| **Active Parameters** | 17B per token |
| **Context Window** | 1M tokens |
| **License** | Llama 4 Community License |

**VRAM Requirements:**
| Quantization | VRAM | Notes |
|---|---|---|
| FP16 | ~800 GB | Data center only |
| FP8 | ~400 GB | Single DGX H100 node |
| Q4_K_M | ~200+ GB | Still impractical for consumer |

**Benchmarks:**
- Throughput: ~126 tokens/second
- Outperforms Llama 4 Scout across all benchmarks

**Availability:**
- Ollama: `ollama run llama4:maverick` (limited deployment)
- GGUF: Available but extremely large files
- HuggingFace: `meta-llama/Llama-4-Maverick-17B-128E-Instruct`

**Verdict for BIAI:** NOT practical for local consumer deployment. Server-grade hardware required.

---

### 1.3 Llama 3.3 70B (December 2024)

| Property | Details |
|---|---|
| **Creator** | Meta |
| **Architecture** | Dense Transformer |
| **Parameters** | 70B |
| **Context Window** | 128K tokens |
| **License** | Llama 3.3 Community License |

**VRAM Requirements:**
| Quantization | VRAM | Notes |
|---|---|---|
| FP16 | ~140 GB | Multi-GPU |
| Q8_0 | ~70 GB | 2x RTX 4090 or A100 |
| Q4_K_M | ~35-40 GB | Single 48GB GPU (A6000, RTX 6000) or 2x 24GB |
| Q3_K_M | ~28 GB | Single 32GB GPU |

**Benchmarks:**
- Performance comparable to Llama 3.1 405B
- Strong reasoning and coding capabilities
- 128K context with good performance

**Availability:**
- Ollama: `ollama run llama3.3:70b`
- GGUF: Widely available (bartowski, etc.)

**Key Notes:** Best dense Llama model for local deployment at 70B. Requires high-end consumer hardware (2x RTX 4090 for good speed). Strong general-purpose model for SQL generation.

---

### 1.4 Llama 3.1 (8B, 70B, 405B) (July 2024)

| Size | VRAM (Q4_K_M) | Context | Ollama Tag |
|---|---|---|---|
| 8B | ~6-7 GB | 128K | `llama3.1:8b` |
| 70B | ~35-40 GB | 128K | `llama3.1:70b` |
| 405B | ~200+ GB | 128K | `llama3.1:405b` |

**Benchmarks:**
- 8B: Good for prototyping, fast inference on consumer GPUs
- 70B: Strong coding/SQL, 128K context
- 405B: Near GPT-4 level, server-grade only

**Availability:** All sizes on Ollama, extensive GGUF ecosystem.

**License:** Llama 3.1 Community License (permissive, similar to Apache 2.0 but with usage restrictions above 700M MAU).

---

### 1.5 CodeLlama (7B, 13B, 34B, 70B)

| Property | Details |
|---|---|
| **Creator** | Meta |
| **Architecture** | Dense Transformer (based on Llama 2) |
| **Training** | 500B tokens of code (7B/13B/34B), 1T tokens (70B) |
| **Context Window** | 16K tokens (100K with rope scaling) |
| **License** | Llama 2 Community License |

**VRAM Requirements (Q4_K_M):**
| Size | VRAM | RAM |
|---|---|---|
| 7B | ~4 GB | 8 GB+ |
| 13B | ~7.8 GB | 16 GB+ |
| 34B | ~20 GB | 32 GB+ |
| 70B | ~35-40 GB | 64 GB+ |

**Benchmarks:**
- 34B HumanEval: 53.7%, MBPP: 56.2%
- Supports Python, JavaScript, Java, C++, SQL, and many more
- Instruct variants available for chat/instruction following

**Availability:**
- Ollama: `ollama run codellama:7b`, `:13b`, `:34b`, `:70b`
- GGUF: Extensive community quantizations

**Key Notes:** Older model (Aug 2023), superseded by newer alternatives. Still usable but not recommended for new deployments when better options exist.

---

## 2. Mistral AI Family

### 2.1 Mistral Large 3 (December 2025)

| Property | Details |
|---|---|
| **Creator** | Mistral AI |
| **Architecture** | Sparse MoE |
| **Total Parameters** | 675B |
| **Active Parameters** | 41B per token |
| **Context Window** | 256K tokens |
| **License** | Apache 2.0 |

**VRAM Requirements:**
| Quantization | VRAM | Notes |
|---|---|---|
| FP16 | ~1.3 TB | Data center only |
| Q8_0 | ~130 GB | Multi-GPU high-end |
| Q4_K_M | ~73 GB | Still beyond consumer GPUs |

**Benchmarks:**
- #2 open model on LMArena, #6 overall
- Outperforms Kimi-K2 and DeepSeek-3.1 on key benchmarks
- Strong coding, math, and reasoning

**Availability:**
- Ollama: `ollama run mistral-large` (requires significant hardware)
- GGUF: Available (Unsloth, bartowski)

**Verdict for BIAI:** NOT practical for consumer local deployment. The MoE architecture helps but 73GB Q4 is still too large.

---

### 2.2 Mistral Large 2 (July 2024)

| Property | Details |
|---|---|
| **Creator** | Mistral AI |
| **Architecture** | Dense Transformer |
| **Parameters** | 123B |
| **Context Window** | 128K tokens |
| **License** | Mistral Research License (non-commercial) |

**VRAM Requirements:**
| Quantization | VRAM | Notes |
|---|---|---|
| Q4_K_M | ~70-80 GB | 2x A100 40GB or similar |

**Benchmarks:**
- Competitive with GPT-4o, Claude 3 Opus, Llama 3 405B
- Strong multilingual support (12+ languages)
- Good SQL generation per Text-to-SQL comparisons

**Availability:**
- Ollama: `ollama run mistral-large`
- GGUF: Available on HuggingFace

**Verdict for BIAI:** NOT practical for consumer local, but strong performance if you have server hardware.

---

### 2.3 Mistral Nemo 12B (July 2024)

| Property | Details |
|---|---|
| **Creator** | Mistral AI + NVIDIA |
| **Architecture** | Dense Transformer |
| **Parameters** | 12B |
| **Context Window** | 128K tokens |
| **License** | Apache 2.0 |

**VRAM Requirements:**
| Quantization | VRAM | Notes |
|---|---|---|
| FP16 | ~24 GB | Single RTX 4090 |
| Q8_0 | ~12 GB | Single RTX 3080 12GB |
| Q4_K_M | ~7 GB | RTX 3060 12GB or above |

**Benchmarks:**
- State-of-the-art for 12B class models
- Strong summarization, code generation, sentiment analysis
- Outperforms Mistral 7B and Mixtral 8x7B on many tasks

**Availability:**
- Ollama: `ollama run mistral-nemo:12b`
- GGUF: Widely available

**Key Notes:** Excellent value — 128K context, Apache 2.0 license, fits on a single consumer GPU. Good candidate for BIAI if 12B is sufficient.

---

### 2.4 Codestral 25.01 (January 2025)

| Property | Details |
|---|---|
| **Creator** | Mistral AI |
| **Architecture** | Dense Transformer |
| **Parameters** | 22B |
| **Context Window** | 256K tokens (record for coding models) |
| **License** | Mistral Non-Production License |

**Benchmarks:**
- HumanEval: 86.6% (joint 1st with Claude 3.5 Sonnet)
- 80+ programming languages
- #1 on Copilot Arena leaderboard

**VRAM Requirements:**
| Quantization | VRAM |
|---|---|
| Q4_K_M | ~13 GB |
| Q8_0 | ~22 GB |

**Availability:**
- Ollama: `ollama run codestral:22b`
- GGUF: Available

**Key Notes:** Excellent for code generation tasks including SQL. The 256K context is valuable for large schema prompts. Non-production license limits commercial use.

---

### 2.5 Codestral Mamba (July 2024)

| Property | Details |
|---|---|
| **Creator** | Mistral AI |
| **Architecture** | Mamba2 (State Space Model) |
| **Parameters** | 7.3B |
| **Context Window** | 256K tokens (theoretically infinite) |
| **License** | Apache 2.0 |

**Benchmarks:**
- HumanEval: 75.0%
- MBPP: 68.5%
- **Spider (SQL): 58.8%** — strong SQL generation
- CruxE: 57.8%

**VRAM Requirements:**
| Quantization | VRAM |
|---|---|
| Q4_K_M | ~4.5 GB |
| FP16 | ~15 GB |

**Availability:**
- HuggingFace: `mistralai/Mamba-Codestral-7B-v0.1`
- GGUF: Community quantizations available
- Ollama: Community model files

**Key Notes:** Linear time inference (vs quadratic for Transformers). Excellent for long-context SQL with large schemas. Apache 2.0 license. Very lightweight VRAM requirements. The Mamba architecture offers unique advantages for handling long code/schema sequences.

---

### 2.6 Devstral Small 2 (December 2025)

| Property | Details |
|---|---|
| **Creator** | Mistral AI |
| **Architecture** | Dense Transformer |
| **Parameters** | 24B |
| **Context Window** | 256K tokens |
| **License** | Apache 2.0 |

**Benchmarks:**
- SWE-Bench Verified: 68% (surpasses GPT-4.1-mini by 20%+)
- Designed for agentic software engineering

**VRAM Requirements:**
| Quantization | VRAM |
|---|---|
| Q4_K_M | ~14 GB |
| FP16 | ~48 GB |

**Availability:**
- Ollama: `ollama run devstral:24b`
- GGUF: Available
- HuggingFace: `mistralai/Devstral-Small-2-24B-Instruct-2512`

**Key Notes:** Optimized for navigating, analyzing, and modifying entire codebases. Fits on RTX 4090 or Mac 32GB. Good for complex SQL generation requiring codebase context.

---

### 2.7 Mixtral 8x22B (April 2024)

| Property | Details |
|---|---|
| **Creator** | Mistral AI |
| **Architecture** | MoE — 8 experts, 22B each |
| **Total Parameters** | 176B |
| **Active Parameters** | ~44B |
| **Context Window** | 64K tokens |
| **License** | Apache 2.0 |

**VRAM Requirements:**
| Quantization | VRAM |
|---|---|
| Q4_K_M | ~80 GB |
| Q8_0 | ~176 GB |

**Benchmarks:**
- GSM8K: 90.8% (math)
- Strong coding and reasoning
- Multilingual support

**Availability:**
- Ollama: `ollama run mixtral:8x22b`

**Verdict for BIAI:** Too large for consumer hardware at Q4. 2x A100 required.

---

## 3. Microsoft Phi Family

### 3.1 Phi-4 14B (December 2024)

| Property | Details |
|---|---|
| **Creator** | Microsoft |
| **Architecture** | Dense Transformer |
| **Parameters** | 14B |
| **Context Window** | 16K tokens |
| **License** | MIT |

**VRAM Requirements:**
| Quantization | VRAM |
|---|---|
| Q4_K_M | ~10 GB |
| Q8_0 | ~16 GB |
| FP16 | ~28 GB |

**Benchmarks:**
- HumanEval/HumanEval+: Highest among open-weight models at 14B
- Strong mathematical reasoning
- SQL: Uses CTEs extensively, tends to over-decompose queries (can generate verbose but correct SQL)
- MMLU: Strong performance

**Availability:**
- Ollama: `ollama run phi4:14b`
- GGUF: Available with Q4/Q8 variants

**Key Notes:** MIT license is maximally permissive. 16K context is relatively short for large schemas. Good code generation quality but SQL style tends toward verbose CTE-heavy queries.

---

### 3.2 Phi-4-Reasoning / Phi-4-Reasoning-Plus (May 2025)

| Property | Details |
|---|---|
| **Creator** | Microsoft |
| **Architecture** | Dense Transformer (fine-tuned Phi-4) |
| **Parameters** | 14B |
| **Context Window** | 32K tokens |
| **License** | MIT |

**Benchmarks:**
- AIME 2025: 82.5% (Reasoning-Plus), 71.4% (Reasoning)
- Comparable to DeepSeek-R1 (671B) on many benchmarks
- Better than o1-mini on most tasks

**Availability:**
- Ollama: `ollama run phi4-reasoning`
- HuggingFace: `microsoft/Phi-4-reasoning`, `microsoft/Phi-4-reasoning-plus`

**Key Notes:** Extended 32K context for reasoning chains. Thinking/reasoning model similar to DeepSeek-R1 but much smaller. Could be useful for complex SQL reasoning tasks.

---

### 3.3 Phi-3.5 (August 2024)

| Variant | Parameters | Context | Architecture |
|---|---|---|---|
| Mini | 3.8B | 128K | Dense |
| MoE | 6.6B active / 42B total | 128K | MoE |
| Vision | 4.2B | 128K | Dense + ViT |

**Benchmarks:**
- MoE outperforms Llama 3.1 8B, Gemma 2 9B
- Mini: Good for constrained environments
- Strong multilingual capabilities

**VRAM (Mini Q4_K_M):** ~3 GB
**VRAM (MoE Q4_K_M):** ~25 GB

**Availability:**
- Ollama: `ollama run phi3.5` (Mini), community models for MoE

---

## 4. Google Gemma Family

### 4.1 Gemma 3 (March 2025)

| Variant | Parameters | Context | Training Data |
|---|---|---|---|
| 270M | 270M | 32K | 6T tokens |
| 1B | 1B | 32K | 2T tokens |
| 4B | 4B | 128K | 4T tokens |
| 12B | 12B | 128K | 12T tokens |
| 27B | 27B | 128K | 14T tokens |

**VRAM Requirements (Q4_K_M):**
| Size | VRAM |
|---|---|
| 1B | ~1-2 GB |
| 4B | ~3 GB |
| 12B | ~8 GB |
| 27B | ~16 GB |

**Benchmarks:**
- 27B: LMSys Elo 1338 (surpasses Llama 3.1 405B Elo 1269!)
- 4B matches Gemma 2 27B on many tasks
- Strong on MATH, HiddenMath, MMLU-Lite

**Availability:**
- Ollama: `ollama run gemma3:27b`, `:12b`, `:4b`, `:1b`
- GGUF: Widely available

**Key Notes:** Exceptional performance-to-size ratio. Gemma 3 27B is the standout — fits on a single RTX 3090/4090 at Q4, outperforms models 15x its size. 128K context. Excellent candidate for BIAI.

---

### 4.2 Gemma 2 (June 2024)

| Variant | Parameters | Context | VRAM (Q4_K_M) |
|---|---|---|---|
| 2B | 2B | 8K | ~2 GB |
| 9B | 9B | 8K | ~5.7 GB |
| 27B | 27B | 8K | ~16 GB |

**Benchmarks:**
- 27B surpasses models 2x its size
- 9B: Knowledge distillation from larger teacher model
- Competitive on MMLU, code generation

**Availability:**
- Ollama: `ollama run gemma2:27b`, `:9b`, `:2b`

**Key Notes:** Superseded by Gemma 3 which offers 128K context vs 8K. Gemma 3 preferred for new deployments.

---

### 4.3 CodeGemma (April 2024)

| Property | Details |
|---|---|
| **Creator** | Google |
| **Parameters** | 7B (base + instruct) |
| **Context Window** | 8K tokens |
| **Training** | 500B tokens (English, code, math) |
| **License** | Gemma Terms of Use |

**Benchmarks:**
- HumanEval: ~48% (instruct variant)
- Supports Python, JS, Java, Kotlin, C++, Rust, Go, SQL

**VRAM (Q4_K_M):** ~4.5 GB

**Availability:**
- Ollama: `ollama run codegemma:7b`

**Key Notes:** Superseded by Gemma 3 series. 8K context is limiting. Not recommended for new BIAI deployment.

---

## 5. SQL-Specialized Models

### 5.1 Arctic-Text2SQL-R1 (Snowflake, May 2025) -- TOP RECOMMENDATION

| Variant | Parameters | Base Model | BIRD-dev | BIRD-test | Cross-Benchmark Avg |
|---|---|---|---|---|---|
| **7B** | 7B | Qwen-based | 68.9% | 68.5% | 57.2% |
| **14B** | 14B | Qwen-based | — | — | 59.0% |
| **32B** | 32B | Qwen-based | — | — | 59.5% |

| Property | Details |
|---|---|
| **Creator** | Snowflake AI Research |
| **Architecture** | Dense Transformer + RL training |
| **Training** | Execution-aligned Reinforcement Learning |
| **License** | Apache 2.0 |

**Key Achievement:** The 7B model outperforms DeepSeek-V3 (671B MoE) with 57.2% vs 55.6% cross-benchmark average. At 68.47% on BIRD leaderboard, it matches ExCoT-70B (10x larger).

**VRAM Requirements (7B Q4_K_M):** ~5 GB

**Availability:**
- Ollama: Community model `a-kore/Arctic-Text2SQL-R1-7B`
- HuggingFace: `Snowflake/Arctic-Text2SQL-R1-7B`
- GGUF: Available

**Why Recommended for BIAI:** Best Text-to-SQL accuracy per parameter. Apache 2.0. Tiny VRAM footprint. Purpose-built for SQL generation with RL-based training that optimizes for execution correctness, not just syntactic similarity.

---

### 5.2 OmniSQL (RUC, March 2025) -- TOP RECOMMENDATION

| Variant | Parameters | BIRD-dev | BIRD-dev (MV) | Spider | EHRSQL |
|---|---|---|---|---|---|
| **7B** | 7B | — | — | — | — |
| **14B** | 14B | — | — | — | — |
| **32B** | 32B | — | 67.0% | Competitive | 46.8% (beats GPT-4o) |

| Property | Details |
|---|---|
| **Creator** | RUC (Renmin University of China) |
| **Training** | SynSQL-2.5M dataset (2.5M text-SQL pairs) |
| **License** | Apache 2.0 |

**Key Achievement:** Surpasses GPT-4o and DeepSeek-V3 on many datasets. Single model without schema linking or SQL revision modules.

**Availability:**
- HuggingFace: `seeklhy/OmniSQL-7B`, `seeklhy/OmniSQL-14B`, `seeklhy/OmniSQL-32B`
- GGUF: OmniSQL-7B-GGUF available (3.1-15.3 GB variants)
- Ollama: Via custom model file with GGUF

**VRAM (7B Q4_K_M):** ~5 GB
**VRAM (14B Q4_K_M):** ~10 GB
**VRAM (32B Q4_K_M):** ~20 GB

---

### 5.3 SQLCoder (Defog)

| Variant | Parameters | Base Model | Accuracy |
|---|---|---|---|
| SQLCoder-7B-2 | 7B | Llama 2 / CodeLlama 7B | Outperforms GPT-3.5-turbo |
| SQLCoder-15B | 15B | StarCoder | SoTA for 15B class |
| SQLCoder-34B-Alpha | 34B | CodeLlama 34B | Strong BIRD performance |
| SQLCoder-70B-Alpha | 70B | CodeLlama 70B | 93% on Defog SQL-Eval |

| Property | Details |
|---|---|
| **Creator** | Defog.ai |
| **Training** | 20,000+ human-curated SQL Q&A pairs |
| **License** | Apache 2.0 (7B/15B); CC-BY-SA (34B/70B) |

**Benchmarks:**
- SQLCoder-70B: 93% accuracy (outperforms GPT-4 on text-to-SQL)
- Fine-tuned on individual schemas can match GPT-4
- BIRD: SQLCoder-34B surpasses InternLM-70B and CodeLlama-34B

**VRAM (Q4_K_M):**
| Size | VRAM |
|---|---|
| 7B | ~5 GB |
| 15B | ~10 GB |
| 34B | ~20 GB |
| 70B | ~41 GB |

**Availability:**
- Ollama: `pxlksr/defog_sqlcoder-7b-2` (community)
- GGUF: Available for all sizes
- HuggingFace: `defog/sqlcoder-7b-2`, `defog/sqlcoder-34b-alpha`, `defog/sqlcoder-70b-alpha`

**Key Notes:** Mature ecosystem, well-tested. The 7B model is good for prototyping. 70B is exceptional but requires high-end hardware. Pioneer in the Text-to-SQL space.

---

### 5.4 NSQL / DuckDB-NSQL (Numbers Station + MotherDuck)

| Property | Details |
|---|---|
| **Creator** | Numbers Station AI + MotherDuck |
| **Parameters** | 7B |
| **Base Model** | Llama 2 7B |
| **Training** | General SQL + DuckDB-specific text-to-SQL pairs |
| **Context Window** | 4K tokens |
| **License** | Apache 2.0 |

**VRAM (Q4_K_M):** ~5 GB

**Availability:**
- Ollama: `ollama run duckdb-nsql` (official library)
- GGUF: Q3_K_M, Q4_0, Q5_0 variants

**Key Notes:** Specialized for DuckDB SQL dialect. Limited context window (4K). Good for simple queries but outclassed by newer SQL-specialized models. Historical significance as early Text-to-SQL fine-tune.

---

### 5.5 Prem-1B-SQL (PremAI, 2025)

| Property | Details |
|---|---|
| **Parameters** | 1B |
| **BIRD Test** | 51.54% |
| **License** | Apache 2.0 |

**VRAM:** ~1 GB

**Key Notes:** Ultra-lightweight, runs on virtually any hardware. Good for edge/mobile deployment. For prototyping or low-resource environments only.

---

### 5.6 XiYan-SQL (2025)

| Property | Details |
|---|---|
| **Approach** | Multi-generator ensemble (ICL + SFT) |
| **Spider Test** | 89.65% |
| **BIRD Dev** | 72.23% |
| **SQL-Eval** | 69.86% |

**Key Notes:** Framework/technique rather than single model. Combines in-context learning with supervised fine-tuning. State-of-the-art results but requires orchestration infrastructure.

---

### 5.7 Chat2DB-SQL-7B

| Property | Details |
|---|---|
| **Creator** | Chat2DB project |
| **Parameters** | 7B |
| **Base Model** | CodeLlama |
| **Context** | 16K |
| **License** | Apache 2.0 |

**Key Notes:** Fine-tuned specifically for NL-to-SQL conversion. Supports various SQL dialects. Part of the Chat2DB ecosystem.

---

### 5.8 DataGPT-SQL-7B

| Property | Details |
|---|---|
| **Parameters** | 7B |
| **Spider-dev** | 87.2% (EX), 83.5% (TS) |

**Key Notes:** Specialized model demonstrating that fine-tuned 7B models can significantly outperform general-purpose models for SQL generation.

---

## 6. Code-Specialized Models

### 6.1 StarCoder2 (BigCode, February 2024)

| Variant | Parameters | Training | Context |
|---|---|---|---|
| 3B | 3B | 600+ languages, 4T+ tokens | 16K |
| 7B | 7B | 600+ languages | 16K |
| 15B | 15B | 600+ languages, 4T+ tokens | 16K |

**VRAM Requirements:**
| Size | Q4_K_M |
|---|---|
| 3B | ~1.1 GB |
| 7B | ~4.5 GB |
| 15B | ~10 GB |

**Benchmarks:**
- 15B matches 33B+ models on many evaluations
- 3B matches StarCoder1-15B
- Strong on low-resource languages

**Availability:**
- Ollama: `ollama run starcoder2:3b`, `:7b`, `:15b`

**Key Notes:** Good general code model but not SQL-specialized. 16K context is limiting for large schemas. Being superseded by newer alternatives.

---

### 6.2 WizardCoder (2023)

| Variant | Parameters | Base |
|---|---|---|
| 15B-V1.0 | 15B | StarCoder |
| 34B | 34B | CodeLlama 34B |

**Benchmarks:**
- Uses Evol-Instruct for complex instruction fine-tuning
- HumanEval, MBPP, DS-1000, MultiPL-E

**Key Notes:** Older model, now superseded. The Evol-Instruct technique was influential but newer models have surpassed it.

---

### 6.3 Magicoder (2023-2024)

| Property | Details |
|---|---|
| **Parameters** | 7B (CL/DS variants) |
| **Technique** | OSS-Instruct (training on open-source code snippets) |

**Benchmarks:**
- Magicoder-S-CL: HumanEval 70.7% (on par with ChatGPT's 72.6%)
- HumanEval+ 66.5% (surpasses ChatGPT's 65.9%)
- 7B model matches/exceeds WizardCoder-34B on multilingual tasks

**Key Notes:** Demonstrates that high-quality training data > parameter count. Impressive for 7B. Academic research model, limited production support.

---

### 6.4 Granite Code (IBM, May 2024)

| Variant | Parameters | License |
|---|---|---|
| 3B | 3B | Apache 2.0 |
| 8B | 8B | Apache 2.0 |
| 20B | 20B | Apache 2.0 |
| 34B | 34B | Apache 2.0 |

**Benchmarks:**
- Outperforms models 2x their size on many benchmarks
- Strong on Python, JS, Java, Go, C++, Rust
- 20B model specifically tuned for NL-to-SQL generation

**Availability:**
- HuggingFace: `ibm-granite/granite-code-*` family

**Key Notes:** Apache 2.0 license. The 20B model's SQL tuning is particularly interesting for BIAI. IBM enterprise backing provides confidence in quality and maintenance.

---

## 7. Enterprise & MoE Models

### 7.1 DBRX (Databricks, March 2024)

| Property | Details |
|---|---|
| **Creator** | Databricks |
| **Architecture** | Fine-grained MoE |
| **Total Parameters** | 132B |
| **Active Parameters** | 36B |
| **Context Window** | 32K tokens |
| **License** | Databricks Open Model License |

**Benchmarks:**
- Competitive with GPT-4 quality for SQL and code
- Surpasses GPT-3.5, Mixtral, LLaMA2-70B, Grok-1
- Spider: Strong SQL generation
- 2x faster inference than LLaMA2-70B

**VRAM (Q4_K_M):** ~70 GB (still large for consumer)

**Availability:**
- HuggingFace: `databricks/dbrx-instruct`
- GGUF: Community quantizations

**Key Notes:** Built by Databricks specifically for data/SQL workloads. Very strong SQL generation but requires server-grade hardware.

---

### 7.2 Snowflake Arctic (April 2024)

| Property | Details |
|---|---|
| **Creator** | Snowflake |
| **Architecture** | MoE |
| **Total Parameters** | 480B |
| **Context Window** | Not specified |
| **License** | Apache 2.0 |

**Benchmarks:**
- Spider: 79%
- HumanEval: 64.3%
- Designed specifically for enterprise SQL/coding

**VRAM:** Extremely large, server-grade only

**Key Notes:** Snowflake pivoted to smaller, specialized models (Arctic-Text2SQL-R1) which are more practical. The 480B model is historical.

---

### 7.3 Command R+ / Command R (Cohere)

| Variant | Parameters | License |
|---|---|---|
| Command R | 35B | CC-BY-NC-4.0 |
| Command R+ | 104B | CC-BY-NC-4.0 |

| Property | Details |
|---|---|
| **Specialization** | RAG, tool use, enterprise tasks |
| **Multilingual** | 10 key business languages |
| **Context** | 128K tokens |

**VRAM (Command R, Q4_K_M):** ~20 GB

**Availability:**
- Ollama: `command-r`, `command-r-plus` (community)

**Key Notes:** Non-commercial license limits use. Strong RAG capabilities could benefit schema retrieval. Not SQL-specialized but good general enterprise model.

---

### 7.4 Aya 23 (Cohere, May 2024)

| Variant | Parameters | Multilingual MMLU |
|---|---|---|
| 8B | 8B | 48.2% |
| 35B | 35B | 58.2% |

| Property | Details |
|---|---|
| **Languages** | 23 languages including **Polish** |
| **License** | CC-BY-NC-4.0 |

**Key Notes:** **Supports Polish** — relevant for BIAI's multilingual needs. Non-commercial license. Good for understanding Polish questions before SQL generation.

---

## 8. Hybrid Architecture Models

### 8.1 Jamba 1.5 (AI21, August 2024)

| Variant | Active Params | Total Params | Context |
|---|---|---|---|
| Mini | 12B | 52B | 256K |
| Large | 94B | 398B | 256K |

| Property | Details |
|---|---|
| **Architecture** | Hybrid Mamba-Transformer + MoE |
| **License** | Jamba Open Model License |

**Benchmarks:**
- Mini: Arena Hard 46.1 (beats Mixtral 8x22B, Command-R+)
- Large: Arena Hard 65.4 (beats Llama 3.1 70B and 405B)
- 2.5x faster on long contexts vs comparable Transformer models

**VRAM (Mini Q4_K_M):** ~30 GB (52B total, MoE)

**Availability:**
- Ollama: `jamba` (community models)
- HuggingFace: `ai21labs/AI21-Jamba-1.5-Mini`

**Key Notes:** Unique architecture with linear inference scaling for long contexts. Interesting for handling large SQL schemas in context. The Mini variant is most practical.

---

### 8.2 NVIDIA Nemotron 3 (2025-2026)

| Variant | Active Params | Total Params | Architecture |
|---|---|---|---|
| Nano | 3.2B | 31.6B | Hybrid Mamba-Transformer MoE |
| Super | ~10B | ~100B | Hybrid Mamba-Transformer MoE |
| Ultra | ~50B | ~500B | Hybrid Mamba-Transformer MoE |

| Property | Details |
|---|---|
| **Training** | 428B high-quality code tokens |
| **SQL Integration** | Direct SQL Server 2025 integration (Nemotron RAG) |
| **Release** | Nano: 2025; Super/Ultra: H1 2026 |

**Benchmarks (Nano):**
- More accurate than GPT-OSS-20B and Qwen3-30B-A3B
- Best-in-class for reasoning, coding, tools, agentic tasks

**Key Notes:** NVIDIA's enterprise push into SQL + RAG. Direct SQL Server integration is notable. Nano (3.2B active) could be very efficient for BIAI. Super/Ultra pending release.

---

### 8.3 IBM Granite 4.0 (2025)

| Variant | Parameters | Architecture |
|---|---|---|
| Nano (350M-1.5B) | 350M-1.5B | Hybrid Mamba-2/Transformer |
| Micro | 3B | Hybrid Mamba-2/Transformer |
| Small | 32B | Hybrid Mamba-2/Transformer |

| Property | Details |
|---|---|
| **License** | Apache 2.0 |
| **Context** | Long-context support |

**Key Features:**
- 70% lower memory requirements than comparable Transformer models
- 2x faster inference speeds
- Outperforms Granite 3.3 8B despite being half the size

**Key Notes:** Apache 2.0 license. Hybrid Mamba architecture is very efficient. The Small (32B) model is strong competitor. Enterprise-focused with SQL/code intelligence capabilities.

---

## 9. Other Notable Models

### 9.1 Falcon 3 (TII, December 2024)

| Variant | Parameters | Ollama | VRAM (Q4_K_M) |
|---|---|---|---|
| 1B | 1B | `falcon3:1b` | ~1 GB |
| 3B | 3B | `falcon3:3b` | ~2 GB |
| 7B | 7B | `falcon3:7b` | ~5 GB |
| 10B | 10B | `falcon3:10b` | ~6 GB |

**Benchmarks:**
- 3B outperforms Llama 3.1 8B and Minitron 4B
- 10B: SoTA in under-13B category
- #1 on Hugging Face LLM leaderboard at release
- GSM8K: 83.1% (10B)

**License:** Apache 2.0

**Key Notes:** Trained on 14T tokens. GGUF, GPTQ-Int4/Int8, AWQ, 1.58-bit variants available. Excellent small-model option.

---

### 9.2 OLMo 2/3 (AI2, 2025)

| Variant | Parameters | Training |
|---|---|---|
| OLMo 2 1B | 1B | 6T tokens |
| OLMo 2 7B | 7B | 6T tokens |
| OLMo 2 13B | 13B | 6T tokens |
| OLMo 2 32B | 32B | 6T tokens |
| OLMo 3 7B | 7B | — |
| OLMo 3 32B | 32B | — |

**Benchmarks:**
- OLMo 2 7B outperforms Llama 3.1 8B
- OLMo 2 13B outperforms Qwen 2.5 7B
- OLMo 3-Think 7B matches Qwen 3 8B on MATH
- OLMo 3-Think leads on HumanEvalPlus for coding

**License:** Apache 2.0 (fully open — code, data, training)

**Availability:**
- Ollama: `ollama run olmo2`

**Key Notes:** The most truly open model — all training data, code, and weights released. Good for research and customization. Strong coding performance in latest versions.

---

### 9.3 GPT-OSS (OpenAI, August 2025)

| Variant | Total Params | Active Params | Architecture | VRAM (Q4) |
|---|---|---|---|---|
| **gpt-oss-20b** | 21B | 3.6B | MoE | ~16 GB RAM (edge) |
| **gpt-oss-120b** | 117B | 5.1B | MoE | Single 80GB GPU |

| Property | Details |
|---|---|
| **Creator** | OpenAI |
| **License** | Apache 2.0 |
| **Context** | 128K tokens |
| **Training** | OpenAI proprietary pipeline |

**Benchmarks:**
- gpt-oss-120b achieves near-parity with OpenAI o4-mini on core reasoning benchmarks
- gpt-oss-20b delivers similar results to o3-mini on common benchmarks
- Strong tool use and function calling capabilities

**Availability:**
- Ollama: `ollama run gpt-oss:20b`, `ollama run gpt-oss:120b`
- HuggingFace: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`
- LM Studio, vLLM, llama.cpp: Supported

**Key Notes:** OpenAI's first open-weight release. The MoE architecture (5.1B active out of 117B) means excellent inference efficiency. The 20B variant can run on edge devices with 16GB RAM. Apache 2.0 license for full commercial use. Strong candidate for general reasoning and SQL tasks.

---

### 9.4 Ministral 3 (Mistral AI, December 2025)

| Variant | Parameters | Architecture | VRAM (Q4_K_M) |
|---|---|---|---|
| 3B | 3B | Dense | ~2 GB |
| 8B | 8B | Dense | ~5 GB |
| 14B | 14B | Dense | ~9 GB |

| Property | Details |
|---|---|
| **Creator** | Mistral AI |
| **License** | Apache 2.0 |
| **Context** | 128K tokens |
| **Variants** | Base, Instruct, Reasoning (per size) |

**Benchmarks:**
- 14B Reasoning: 85% on AIME '25 (state-of-the-art for weight class)
- Comparable to or exceeding Gemma 3 and Phi-4 in the same size range
- Can run on 4GB VRAM (3B variant)

**Availability:**
- Ollama: `ollama run ministral:3b`, `:8b`, `:14b`
- All variants available in GGUF

**Key Notes:** The Reasoning variants are optimized for complex logic and analytical tasks — excellent for SQL decomposition. Apache 2.0 license. The 14B Reasoning variant is particularly interesting for BIAI: fits on a single consumer GPU with strong analytical capabilities.

---

### 9.5 Devstral 2 (Mistral AI, 2025)

| Property | Details |
|---|---|
| **Creator** | Mistral AI |
| **Architecture** | Dense Transformer |
| **Parameters** | 123B |
| **Context Window** | 256K tokens |
| **License** | Apache 2.0 |

**Benchmarks:**
- SWE-Bench: Top performer for agentic coding
- Designed for exploring codebases and orchestrating changes across multiple files
- Maintains architecture-level context understanding

**VRAM:** ~70 GB Q4_K_M — server-grade hardware required

**Key Notes:** While too large for typical consumer local deployment, the 256K context and codebase understanding make it potentially very strong for complex schema analysis. Server-grade only.

---

### 9.6 Falcon H1R 7B (TII, January 2026)

| Property | Details |
|---|---|
| **Creator** | TII Abu Dhabi |
| **Architecture** | Hybrid Transformer + Mamba2 |
| **Parameters** | 7B |
| **Context Window** | 256K tokens |
| **License** | TII Falcon License |

**Benchmarks:**
- AIME 24: 88.1% (matches/exceeds 14B-47B reasoning models)
- AIME 25: 83.1%
- LiveCodeBench v6: 68.6%
- ~1,000-1,500 tokens/sec per GPU at batch 32-64

**VRAM (Q4_K_M):** ~5 GB

**Key Notes:** Remarkable reasoning performance for 7B. The hybrid Mamba2 architecture provides near-linear inference scaling with context length — very valuable for long SQL schemas. Throughput nearly double Qwen3-8B. However, no SQL-specific benchmarks published yet.

---

### 9.7 Upstage Solar (2025-2026)

| Variant | Parameters | Active | Architecture |
|---|---|---|---|
| Solar Open 100B | 102.6B | 12B | MoE (129 experts) |
| Solar Pro 2 | 31B | — | Dense |
| Solar Pro 3 | ~31B | — | Dense |

| Property | Details |
|---|---|
| **Creator** | Upstage (Korea) |
| **Context** | 128K (Open 100B), 64K (Pro 2/3) |
| **Training** | 19.7T tokens (Open 100B) |
| **License** | Varies — check per release |

**Benchmarks:**
- Solar Pro 2 scored 58 in Intelligence Index
- Reasoning Mode for complex multi-step problems
- Available on HuggingFace

**Key Notes:** Korean company producing competitive models. Solar Open 100B's MoE architecture (12B active) is interesting for efficiency. Solar Pro 2/3 at 31B are feasible for local deployment (~20 GB Q4). Limited SQL-specific evaluation data.

---

### 9.8 Grok-1 / Grok-2.5 (xAI)

| Variant | Parameters | Architecture |
|---|---|---|
| Grok-1 | 314B (86B active) | MoE |
| Grok-2 | ~500 GB download | Dense/MoE |
| Grok-2.5 | Similar | Dense/MoE |

**License:** Apache 2.0 (Grok-1); Grok 2 Community License (Grok 2.5 — no training other AI)

**Key Notes:** Extremely large, requires 8x GPUs with 40GB+ each. NOT practical for consumer/local deployment. Interesting architecture but impractical for BIAI use case.

---

## 10. Comparative Summary Tables

### 10.1 SQL-Specialized Models Ranking (by BIRD-dev accuracy)

| Rank | Model | Size | BIRD-dev | BIRD-test | Practical for BIAI? |
|---|---|---|---|---|---|
| 1 | XiYan-SQL (framework) | varies | 72.23% | — | Requires orchestration |
| 2 | Arctic-Text2SQL-R1-7B | 7B | 68.9% | 68.5% | **YES** (5 GB VRAM) |
| 3 | OmniSQL-32B | 32B | 67.0% (MV) | — | YES (20 GB VRAM) |
| 4 | SQLCoder-70B | 70B | — | — | Borderline (41 GB) |
| 5 | Arctic-Text2SQL-R1-32B | 32B | — | — | YES (20 GB VRAM) |
| 6 | OmniSQL-14B | 14B | — | — | **YES** (10 GB VRAM) |
| 7 | Prem-1B-SQL | 1B | — | 51.54% | YES (1 GB VRAM) |

### 10.2 Best Models by VRAM Budget

| VRAM Budget | Best General Model | Best SQL Model | Best Code Model |
|---|---|---|---|
| **4 GB** | Gemma 3 1B / Ministral 3B | Prem-1B-SQL | StarCoder2 3B |
| **6 GB** | Llama 3.1 8B / Ministral 8B | Arctic-Text2SQL-R1-7B | Codestral Mamba 7B / Falcon H1R 7B |
| **8 GB** | Gemma 3 4B | OmniSQL-7B | CodeGemma 7B |
| **10 GB** | Phi-4 14B / Ministral 14B-Reasoning | OmniSQL-14B | Codestral 22B (Q3) |
| **12 GB** | Gemma 3 12B | OmniSQL-14B | Codestral 22B |
| **16 GB** | Gemma 3 27B (Q4) / GPT-OSS-20B | Arctic-Text2SQL-R1-14B | Devstral 24B (Q4) |
| **24 GB** | Gemma 3 27B (Q8) | OmniSQL-32B | Devstral 24B |
| **48 GB** | Llama 3.3 70B | SQLCoder-70B | Llama 3.3 70B |
| **80 GB** | GPT-OSS-120B | GPT-OSS-120B | GPT-OSS-120B |

### 10.3 Best Models by Use Case (BIAI-specific)

| Use Case | Recommended Model | Reason |
|---|---|---|
| **SQL Generation (primary)** | Arctic-Text2SQL-R1-7B | Best SQL accuracy per VRAM |
| **SQL Generation (quality)** | OmniSQL-32B | Beats GPT-4o on some benchmarks |
| **General + SQL combo** | Gemma 3 27B | Top general model, good code/SQL |
| **Description generation** | Gemma 3 12B | Strong text, fits 12GB |
| **Reasoning-heavy SQL** | Phi-4-Reasoning-Plus | Complex query decomposition |
| **Long schema context** | Codestral Mamba 7B | 256K context, linear scaling |
| **Polish language support** | Aya 23 35B | 23 languages including Polish |
| **Minimal VRAM** | Prem-1B-SQL | 1B, runs on anything |
| **Max local quality** | Llama 3.3 70B + Arctic-R1-7B | Two-model approach |

### 10.4 License Comparison

| License | Models |
|---|---|
| **Apache 2.0** | Arctic-Text2SQL-R1, OmniSQL, Gemma 3, Falcon 3, OLMo, Granite Code/4.0, Codestral Mamba, StarCoder2, DBRX, Devstral Small 2, Mistral Nemo, Mistral Large 3, Mixtral |
| **MIT** | Phi-4, Phi-3.5 |
| **Llama License** | Llama 4 Scout/Maverick, Llama 3.3, Llama 3.1, CodeLlama |
| **CC-BY-NC** | Command R/R+, Aya 23 (non-commercial only) |
| **Restrictive** | Codestral 25.01 (non-production), Mistral Large 2 (research) |

---

## 10.5 Polish Language Support Assessment

**Key Finding:** A comprehensive Polish LLM benchmark (LLMzSzL — "LLMs Behind the School Desk") was published in January 2025, based on Polish national exams covering 154 domains with ~19K questions. Key findings:

| Model | Polish Performance | Notes |
|---|---|---|
| Qwen 3 (119 languages) | Good | Best multilingual coverage |
| Gemma 3 27B | Good | 140+ languages, strong multilingual |
| Llama 3.3 70B | Good | Solid multilingual capabilities |
| Aya 23 35B | **Excellent** | Explicitly trained for Polish |
| Mistral Large 3 | Good | 12+ languages |
| Phi-4 14B | Moderate | Primarily English-focused |
| PLLuM (Polish national model) | **Native** | Specifically designed for Polish |

**For BIAI (Polish users querying databases):**
- SQL generation models (Arctic-Text2SQL-R1, OmniSQL) are language-agnostic for SQL output
- Polish understanding for natural language questions requires a model with Polish support
- **Recommendation:** Use Gemma 3 27B or Qwen 3 for Polish NL understanding; SQL-specialized model for generation

## 10.6 Contextual AI Text-to-SQL Pipeline

**Key Discovery:** Contextual AI held the overall #1 spot on BIRD benchmark in February 2025 with a fully local system. Their open-source pipeline (contextual-sql) uses a 2-stage approach:
1. **Generate candidates** — diverse SQL candidate generation with informative context
2. **Select best** — filtering and ranking to identify the best candidate

This pipeline captures two principles: (1) good context matters, (2) inference-time scaling helps. Currently in top 5 on BIRD (behind API-based Gemini/GPT-4o systems).

**Available:** Open-source at `github.com/ContextualAI/bird-sql`

**Relevance for BIAI:** Could be adapted to work with local models (Arctic-Text2SQL-R1 or OmniSQL) for candidate generation + ranking, significantly improving SQL accuracy.

---

## 11. Recommendations for BIAI

### 11.1 Primary Configuration (RTX 4090 24GB / RTX 3090 24GB)

**Option A: Dual-model approach (RECOMMENDED)**
1. **Arctic-Text2SQL-R1-7B** (Q4_K_M, ~5 GB) — SQL generation via Vanna
2. **Gemma 3 12B** (Q4_K_M, ~8 GB) — Text descriptions, chart analysis, general reasoning
3. Total VRAM: ~13 GB, leaves room for context

**Option B: Single powerful model**
1. **Gemma 3 27B** (Q4_K_M, ~16 GB) — All tasks
2. Strong general performance + SQL, but no SQL specialization

**Option C: Maximum SQL quality**
1. **OmniSQL-14B** (Q4_K_M, ~10 GB) — SQL generation
2. **Phi-4 14B** (Q4_K_M, ~10 GB) — Descriptions, analysis
3. Total VRAM: ~20 GB

### 11.2 Budget Configuration (RTX 4060 8GB / RTX 3060 12GB)

1. **Arctic-Text2SQL-R1-7B** (Q4_K_M, ~5 GB) — SQL generation
2. For descriptions: share the same model or use a separate lightweight model like Gemma 3 4B

### 11.3 High-End Configuration (2x RTX 4090 48GB total)

1. **OmniSQL-32B** (Q4_K_M, ~20 GB) — Best SQL generation
2. **Gemma 3 27B** (Q8_0, ~27 GB) — Descriptions, analysis
3. Alternatively: **Llama 3.3 70B** (Q4_K_M) for a single do-it-all model

### 11.4 Key Implementation Notes

1. **Vanna dialect must match model training**: Arctic-Text2SQL-R1 and OmniSQL are dialect-agnostic (trained on diverse SQL). SQLCoder was primarily PostgreSQL-evaluated.

2. **Schema context budget**: Arctic-Text2SQL-R1-7B has standard context (~4-8K effective), while Codestral Mamba offers 256K. For very large schemas, consider Codestral Mamba or Gemma 3 (128K).

3. **Ollama integration**: All recommended models have Ollama support (official or community). Use `ollama run <model>` for quick testing.

4. **Two-model architecture**: BIAI can benefit from separate models for SQL generation (specialized) and text/chart description (general). This maximizes quality in both tasks.

5. **Reinforcement Learning models (Arctic-R1) vs SFT models (OmniSQL)**: RL models optimize for execution correctness; SFT models optimize for syntactic similarity. For production SQL, RL-based models may be more reliable.
