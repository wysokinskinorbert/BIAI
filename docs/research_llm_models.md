# LLM Models for BIAI: Comprehensive Research & Recommendations

> **Date:** February 2026
> **Current stack:** Ollama + Qwen3-Coder:30b-a3b + Vanna.ai RAG
> **Databases:** PostgreSQL, Oracle
> **Hardware baseline:** NVIDIA consumer GPU (8-24 GB VRAM), Windows 11

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Model Landscape Overview](#2-model-landscape-overview)
3. [Top Models for BIAI (Ranked)](#3-top-models-for-biai-ranked)
4. [Specialized SQL Models](#4-specialized-sql-models)
5. [Inference Server Comparison](#5-inference-server-comparison)
6. [Text-to-SQL Techniques](#6-text-to-sql-techniques)
7. [Multi-Model Strategy](#7-multi-model-strategy)
8. [Hardware Requirements](#8-hardware-requirements)
9. [Polish Language Support](#9-polish-language-support)
10. [Roadmap & Recommendations](#10-roadmap--recommendations)
11. [Appendix A: Full Model Catalog](#appendix-a-full-model-catalog)
12. [Appendix B: Benchmark Leaderboards](#appendix-b-benchmark-leaderboards)
13. [Appendix C: Sources](#appendix-c-sources)

---

## 1. Executive Summary

### Key Findings

We researched **65+ LLM models** from 20+ organizations across Chinese/Asian, Western, and specialized SQL families, evaluated **23 inference servers**, and analyzed the latest **Text-to-SQL benchmarks** (BIRD, Spider, Spider 2.0). Here are the conclusions most relevant to BIAI:

1. **Fine-tuned 7B SQL models now rival GPT-4.** MARS-SQL (7B, RL-trained) achieves 77.84% on BIRD-dev and 89.75% on Spider-test. Arctic-Text2SQL-R1-7B achieves 68.9% on BIRD-dev while requiring only ~5 GB VRAM. These dramatically outperform general-purpose models of any size in zero-shot mode.

2. **Pipeline matters more than model size.** The Contextual-SQL research showed that a local 32B model with multi-candidate generation + execution filtering + reward model ranking matches GPT-4o-based proprietary systems on BIRD (~73%).

3. **Ollama remains the right choice for BIAI** (single-user, Windows, simple setup), but adding OpenAI-compatible backend support (~20 lines of code) would unlock access to vLLM, TabbyAPI/ExLlamaV3, LM Studio, and all other inference servers.

4. **MoE architecture dominates 2025-2026.** Models like Qwen3-Coder-30B-A3B (3.3B active / 30B total) and GLM-4.7-Flash (3.6B active / 30B total) deliver excellent performance at 17-18 GB VRAM by activating only a fraction of parameters per token.

5. **Reinforcement Learning training (GRPO) for SQL is a breakthrough.** Both MARS-SQL and Arctic-Text2SQL-R1 use RL with execution-based rewards, producing models that optimize for correct query results rather than surface-level SQL similarity.

### Top 3 Recommendations for Immediate Adoption

| # | Action | Expected Impact | Effort |
|---|--------|----------------|--------|
| 1 | **Test Arctic-Text2SQL-R1-7B** for SQL generation | +10-15% accuracy vs current Qwen, only 5 GB VRAM | Low |
| 2 | **Add multi-candidate generation** (5 candidates, execution vote) | +5-8% accuracy on top of any model | Medium |
| 3 | **Test GLM-4.7-Flash** as alternative to Qwen3-Coder-30B-A3B | Comparable VRAM, 59.2% SWE-bench, MIT license | Low |

### Top 3 Recommendations for Future Consideration

| # | Action | Expected Impact | Effort |
|---|--------|----------------|--------|
| 1 | **Add OpenAI-compatible backend** in `vanna_client.py` | Unlocks ALL inference servers and model formats | Low-Medium |
| 2 | **Implement Contextual-SQL pipeline** (multi-candidate + reward model) | +10-15% accuracy, matching proprietary systems | High |
| 3 | **Fine-tune Qwen2.5-Coder-7B on customer schema** (Fireworks AI RFT) | 2.4x accuracy improvement on domain-specific SQL | High |

---

## 2. Model Landscape Overview

### 2.1 Models Researched

| Region / Family | Count | Key Players |
|----------------|-------|-------------|
| Chinese / Asian | 40+ models from 14 families | Qwen (Alibaba), DeepSeek, GLM (Zhipu AI), Kimi (Moonshot), Yi (01.AI), ERNIE (Baidu), InternLM, MiniMax, Hunyuan (Tencent), TeleChat, Baichuan, Skywork, Aquila, XVERSE |
| Western / Open-source | 25+ models from 10 families | Llama (Meta), Mistral, Phi (Microsoft), Gemma (Google), Falcon (TII), OLMo (AI2), Grok (xAI), Granite (IBM), DBRX (Databricks), Jamba (AI21) |
| SQL-specialized | 10+ models | Arctic-Text2SQL-R1, OmniSQL, XiYanSQL, SQLCoder, NSQL, Prem-1B-SQL, DataGPT-SQL, Chat2DB-SQL, CodeS, MARS-SQL |
| Hybrid / Research | 5+ models | Nemotron (NVIDIA), Granite 4.0 (IBM), PowerInfer, Codestral Mamba |

**Total: 65+ distinct models evaluated across 30+ organizations.**

### 2.2 Market Trends in 2025-2026

1. **MoE (Mixture of Experts) is now standard for large models.** Qwen3-Coder-30B (128 experts, 8 active), GLM-4.7-Flash (similar), DeepSeek V3 (671B/37B active), Llama 4 Scout (109B/17B active) all use MoE to deliver high quality at reduced inference cost.

2. **Long context windows are ubiquitous.** 128K is the new baseline. Codestral offers 256K, Gemini supports 1M. This eliminates context-window bottlenecks for large database schemas.

3. **Reinforcement Learning from execution feedback** is replacing supervised fine-tuning for SQL models. MARS-SQL (GRPO), Arctic-Text2SQL-R1 (GRPO), and ExCoT all train models to produce SQL that executes correctly, not just SQL that looks correct.

4. **Thinking/reasoning modes** are built into modern models. Qwen3, DeepSeek-R1, Phi-4-Reasoning, and QwQ all support toggling chain-of-thought reasoning, which helps with complex analytical queries.

5. **Open-weight models are closing the gap with proprietary.** The best open 7B SQL model (MARS-SQL) at 77.84% BIRD-dev surpasses many GPT-4-based systems, while the human ceiling is 92.96%.

### 2.3 Key Architectural Shifts

| Shift | Implication for BIAI |
|-------|---------------------|
| MoE → lower active params | 30B-class models fit on 24GB consumer GPUs |
| 128K+ context standard | Full schema DDL fits in prompt without truncation |
| RL-trained SQL models | Purpose-built models far exceed general coding models for SQL |
| Structured output (JSON mode) | Better integration with Vanna's SQL extraction pipeline |
| Hybrid Mamba-Transformer | Linear inference scaling for long schemas (Jamba, Nemotron, Granite 4.0) |

---

## 3. Top Models for BIAI (Ranked)

### Tier 1: Immediate Use (Works with Current Ollama Setup)

These models can be tested today with `ollama run <tag>` — no code changes required.

| Rank | Model | Size | Active Params | VRAM (Q4) | Ollama Tag | BIRD EX | Spider EX | Pros | Cons |
|------|-------|------|--------------|-----------|------------|---------|-----------|------|------|
| **1** | **Arctic-Text2SQL-R1-7B** | 7B | 7B (dense) | ~5 GB | `a-kore/Arctic-Text2SQL-R1-7B` (community) | **68.9% dev** / 68.5% test | — | Best SQL accuracy per VRAM; RL-trained for execution correctness; Apache 2.0 | Community Ollama only; Snowflake-focused training |
| **2** | **Qwen2.5-Coder-7B** | 7B | 7B (dense) | ~5 GB | `qwen2.5-coder:7b` | 68.51% (ExCoT, 32B) | **82.0% dev** | Proven on Spider; dual-use (SQL + code); 128K context | Requires fine-tuning or pipeline for best BIRD scores |
| **3** | **GLM-4.7-Flash** | 30B | ~3.6B (MoE) | ~18 GB | `glm-4.7-flash` | — | — | 59.2% SWE-bench; 79.5% tool-use; MIT license; 200K context; 120-220 tok/s on 4090 | No published SQL-specific benchmarks |
| **4** | **Qwen3-Coder-30B-A3B** | 30B | 3.3B (MoE) | ~18 GB | `qwen3-coder:30b` | — | — | **Current BIAI model**; strong agentic coding; 256K context; thinking mode | MoE overhead; no SQL-specific benchmarks |
| **5** | **Qwen2.5-Coder-14B** | 14B | 14B (dense) | ~8 GB | `qwen2.5-coder:14b` | — | — | Better quality than 7B; still fits 12GB GPUs at Q4 | No published SQL benchmarks at 14B specifically |
| **6** | **Yi-Coder-9B** | 9B | 9B (dense) | ~6 GB | `yi-coder:9b` | — | — | 85.4% HumanEval; 128K context; Apache 2.0; NL2SQL cookbook | Older model (2024); limited SQL benchmarks |
| **7** | **Gemma 3 27B** | 27B | 27B (dense) | ~16 GB | `gemma3:27b` | — | — | Elo 1338 (surpasses Llama 3.1 405B); 128K context | No SQL specialization; Google terms of use |
| **8** | **DeepSeek-Coder-V2-Lite** | 16B | 2.4B (MoE) | ~10 GB | `deepseek-coder-v2:16b` | — | — | Very efficient (2.4B active); 128K context; outperforms GPT-4 Turbo on coding | Older architecture (2024) |
| **9** | **Phi-4-Reasoning** | 14B | 14B (dense) | ~10 GB | `phi4-reasoning` | — | — | Matches DeepSeek-R1 on reasoning; MIT; 32K context | Verbose CTE-heavy SQL style; limited context |
| **10** | **Mistral Nemo 12B** | 12B | 12B (dense) | ~7 GB | `mistral-nemo:12b` | — | — | 128K context; Apache 2.0; NVIDIA co-developed | No SQL specialization |

### Tier 2: Better with Infrastructure Change

These models require GGUF conversion, a different inference server, or non-Ollama deployment.

| Model | Size | VRAM (Q4) | Infrastructure Change | BIRD EX | Expected Quality Gain |
|-------|------|-----------|----------------------|---------|----------------------|
| **XiYanSQL-QwenCoder-32B** | 32B | ~20 GB | Convert to GGUF, create Ollama Modelfile | **69.03% test** (SOTA single model) | +5-10% vs general Qwen |
| **OmniSQL-7B/14B/32B** | 7-32B | 5-20 GB | GGUF available; Ollama via Modelfile | 67.0% dev (32B) | +5% vs general models |
| **MARS-SQL (7B, RL)** | 7B | ~5 GB | Research model; weights on HuggingFace | **77.84% dev** | +15-20% (if weights are deployable) |
| **Codestral 25.01** | 22B | ~13 GB | Available on Ollama; non-production license | Spider 58.8% (Mamba variant) | Good code/SQL; 256K context |
| **Devstral Small 2** | 24B | ~14 GB | `devstral:24b` on Ollama; Apache 2.0 | 68% SWE-bench | Strong codebase navigation |
| **Llama 4 Scout** | 109B | ~33 GB (1.78-bit) | Extreme quantization needed; quality loss risk | — | MoE with 17B active; 10M context |
| **ExLlamaV3 + TabbyAPI** | Any | Lower than GGUF | Switch to TabbyAPI server; EXL3 format | 98% FP16 quality at 4-bit | 50% VRAM reduction; best quality-per-bit |

**Architecture changes needed for Tier 2:**
- Add OpenAI-compatible backend support in `vanna_client.py` (~20 lines)
- For EXL3 models: install ExLlamaV3 + TabbyAPI (NVIDIA CUDA only)
- For non-Ollama GGUF: install llama-cpp-python as alternative backend

### Tier 3: Future / Experimental

| Model | Size | Why Interesting | Barrier |
|-------|------|----------------|---------|
| **Qwen3-Coder-480B-A35B** | 480B total, 35B active | Largest open coding MoE | ~250 GB VRAM; server-only |
| **DeepSeek V3.2** | 685B total, 37B active | Top proprietary-class SQL quality | ~250 GB; impractical for consumer |
| **GLM-4.7** (full) | 358B total, ~35B active | 73.8% SWE-bench; 200K context | ~130 GB; server-only |
| **MiniMax-M2.5** | 456B total, 45.9B active | SOTA on agent/coding tasks | ~300 GB; server-only |
| **Kimi K2.5** | 1T+ | Agent swarm paradigm | 240 GB minimum; impractical |
| **DeepSeek-R2** (upcoming) | ~1.2T (rumored) | Next-gen reasoning MoE | Not yet released |
| **Nemotron Nano** | 31.6B total, 3.2B active | Hybrid Mamba-Transformer; SQL Server integration | Pending wider availability |
| **Granite 4.0 Small** | 32B | Hybrid Mamba-2; 70% less memory; Apache 2.0 | Early release; limited benchmarks |

**Distilled variants to watch:**
- DeepSeek-R1-Distill-Qwen-14B (~9 GB VRAM) — reasoning capabilities in a small package
- Any future distillation of MARS-SQL or DeepSeek-R2

---

## 4. Specialized SQL Models

### 4.1 Purpose-Built Text-to-SQL Models

These models are fine-tuned specifically for SQL generation and dramatically outperform general-purpose models of the same size.

| Model | Creator | Base | Sizes | BIRD EX | Spider EX | Training | License | Ollama |
|-------|---------|------|-------|---------|-----------|----------|---------|--------|
| **MARS-SQL** | Research | Qwen-based | 7B | **77.84% dev** | **89.75% test** | Multi-agent RL (GRPO) | Research | No (HF only) |
| **Arctic-Text2SQL-R1** | Snowflake | Qwen-based | 7B/14B/32B | 68.9/70.1/70.5% dev; 68.5% test (7B) | — | RL (GRPO) + execution reward | Apache 2.0 | Community |
| **XiYanSQL-QwenCoder** | Alibaba XGen | Qwen2.5-Coder | 3B/7B/14B/32B | 69.03% test (32B) | — | SFT, multi-dialect | Open | Custom GGUF |
| **OmniSQL** | RUC | Qwen2.5-Coder | 7B/14B/32B | 67.0% dev (32B, MV@16) | ~87% (32B) | SynSQL-2.5M dataset | Apache 2.0 | Via GGUF |
| **SQLCoder** | Defog.ai | CodeLlama/Llama 2 | 7B/15B/34B/70B | — | ~93% (70B) | 20K human-curated pairs | Apache 2.0 (7B/15B) | Community |
| **CodeS** | RUC | StarCoder | 1B/3B/7B/15B | ~60% (15B) | SOTA at release | SFT | Research | No |
| **Prem-1B-SQL** | PremAI | DeepSeek-1.3B | 1.3B | ~51.5% test | — | SFT | Apache 2.0 | Community |
| **DataGPT-SQL** | Research | Unknown | 7B | — | 87.2% dev | SFT | Research | No |
| **Chat2DB-SQL** | Chat2DB | CodeLlama | 7B | — | — | NL-to-SQL SFT | Apache 2.0 | No |
| **NSQL/DuckDB-NSQL** | NumbersStation | Llama 2 7B | 7B | — | — | DuckDB-specific SFT | Apache 2.0 | `duckdb-nsql` |

### 4.2 Performance Comparison: Specialized vs General Models

| Model | Size | BIRD-dev | Method | Note |
|-------|------|----------|--------|------|
| MARS-SQL | 7B | **77.84%** | Multi-agent RL | Best open-source; research model |
| Arctic-Text2SQL-R1 | 7B | **68.9%** | RL (GRPO) | Best *deployable* open-source at 7B |
| XiYanSQL-QwenCoder | 32B | ~68.5% | SFT ensemble | Multi-dialect; production-ready |
| Qwen2.5-Coder (ExCoT) | 32B | 68.51% | ExCoT pipeline | General model + specialized pipeline |
| OmniSQL | 32B | 67.0% | SynSQL-2.5M | Broad generalization (9 datasets) |
| Qwen2.5-Instruct (zero-shot) | various | ~44% | Zero-shot | What you get without RAG or fine-tuning |
| DeepSeek-V3 (zero-shot) | 671B | ~49% | Zero-shot | Even 671B struggles without pipeline |

**Key insight:** A fine-tuned 7B model (Arctic-R1, 68.9%) outperforms a general 671B model (DeepSeek-V3, ~49%) by nearly 20 percentage points. Model specialization matters far more than raw size for SQL generation.

### 4.3 Recommended SQL Models for BIAI

**Primary (Default SQL Model):**
- **Arctic-Text2SQL-R1-7B** — Best accuracy per VRAM. 68.9% BIRD at only 5 GB.
- Convert GGUF from HuggingFace, create Ollama Modelfile, test against current Qwen3-Coder.

**Secondary (Quality, If VRAM Allows):**
- **OmniSQL-14B** (~10 GB) or **XiYanSQL-QwenCoder-14B** (~10 GB) for higher accuracy.
- **Arctic-Text2SQL-R1-32B** or **OmniSQL-32B** (~20 GB) for maximum local quality.

**Fallback (Minimal VRAM):**
- **Prem-1B-SQL** (~1 GB) — Runs on CPU; 51.5% BIRD. For edge/mobile/demo.

---

## 5. Inference Server Comparison

### 5.1 Feature Matrix

| Platform | Formats | GPU Support | API | Windows Native | Setup (1-5) | Stars | Best For |
|----------|---------|-------------|-----|----------------|-------------|-------|----------|
| **Ollama** | GGUF | CUDA, ROCm, Metal | OpenAI-compat | Yes | 1 | 163K | Single-user, simplicity |
| **vLLM** | SafeTensors, GPTQ, AWQ, FP8 | CUDA, ROCm | OpenAI-compat | WSL/Docker | 3 | 70K | Production, multi-user |
| **llama.cpp** | GGUF | CUDA, Vulkan, Metal, ROCm, SYCL, CPU | REST | Yes | 2 | 85K | Max performance, broad HW |
| **LM Studio** | GGUF, MLX | CUDA, Metal, Vulkan | OpenAI-compat | Yes | 1 | N/A | GUI, experimentation |
| **LocalAI** | GGUF, GPTQ, AWQ, SafeTensors | CUDA, ROCm, Vulkan, Metal | Full OpenAI-compat | Docker/Binary | 2 | 30K | Multi-format, drop-in |
| **ExLlamaV3 + TabbyAPI** | EXL3 | CUDA only | OpenAI-compat | Partial | 3 | 3K | Best quality-per-bit |
| **SGLang** | SafeTensors, GPTQ, AWQ, FP8 | CUDA | OpenAI-compat | WSL/Docker | 3 | 20K | Structured output, throughput |
| **Xinference** | All (via backends) | CUDA, ROCm, Metal | OpenAI-compat | Yes | 2 | 8K | Multi-model management |
| **llama-cpp-python** | GGUF | CUDA, Vulkan, Metal, CPU | OpenAI-compat | Yes | 2 | 8K | Python-native, function calling |
| **Jan.ai** | GGUF | CUDA, Vulkan, Metal | OpenAI-compat | Yes | 1 | 30K | Offline chatbot |
| **GPT4All** | GGUF | CPU primary | Custom REST | Yes | 1 | 72K | CPU-only, privacy |
| **Aphrodite** | GPTQ, AWQ, GGUF, EXL2, FP8+ | CUDA | OpenAI-compat | WSL | 3 | 4K | Most quant formats |
| **TensorRT-LLM** | TRT engines | CUDA (NVIDIA only) | Custom + OpenAI | WSL/beta native | 5 | 10K | Maximum NVIDIA perf |

### 5.2 Performance Benchmarks

**Single-User Throughput (RTX 4090, ~7B model, Q4_K_M):**

| Server | tok/s | Notes |
|--------|-------|-------|
| ExLlamaV3 (EXL3) | ~70-80 | Fastest on consumer GPU |
| llama.cpp | ~50-60 | Baseline |
| Ollama | ~40-50 | 10-30% overhead vs llama.cpp |
| vLLM (FP16) | ~45-55 | Optimized for batch, not single-user |

**High-Concurrency Throughput (H100 GPU, 8B model):**

| Server | Total tok/s | Relative |
|--------|-------------|----------|
| SGLang | 16,215 | 1.29x vLLM |
| vLLM | 12,553 | 1.0x baseline |
| TGI | ~5,000 | 0.4x |
| llama.cpp | ~350 | 0.03x |
| Ollama | ~300 | 0.02x |

### 5.3 Model Format Comparison

| Format | Quality (vs FP16) | Speed | VRAM | Supported By |
|--------|-------------------|-------|------|-------------|
| **GGUF Q4_K_M** | 92% | Medium | Low | Ollama, llama.cpp, LM Studio, Jan, LocalAI |
| **GGUF Q5_K_M** | 95% | Medium | Medium | Same as above |
| **GGUF Q6_K** | 98% | Medium | Medium-High | Same as above |
| **AWQ 4-bit** | 95% | Fast (Marlin) | Medium | vLLM, Aphrodite, LocalAI, SGLang |
| **EXL3 4-bit** | **98%** | **Fastest (CUDA)** | **Very Low** | ExLlamaV3, TabbyAPI |
| **GPTQ 4-bit** | 90% | Fast (GPU) | Medium | vLLM, ExLlama, TGI |
| **FP8** | 99% | Very Fast | Medium | vLLM, TensorRT-LLM, SGLang |

### 5.4 Quantization Guide for BIAI

| Quantization | Bits/Weight | Size (7B) | Perplexity Impact | Recommended For |
|-------------|-------------|-----------|-------------------|-----------------|
| Q3_K_M | ~3.4 | ~3.3 GB | +0.24 ppl | Tight VRAM only |
| **Q4_K_M** | ~4.5 | ~4.1 GB | +0.05 ppl | **General-purpose (Ollama default)** |
| **Q5_K_M** | ~5.3 | ~5.1 GB | +0.03 ppl | **SQL generation (quality matters)** |
| Q6_K | ~6.0 | ~5.5 GB | +0.01 ppl | When VRAM allows |
| Q8_0 | ~8.0 | ~7.2 GB | ~0 ppl | Indistinguishable from FP16 |

**Recommendation for BIAI SQL generation:** Use **Q5_K_M or Q6_K** for the SQL model (quality matters for correct queries) and Q4_K_M for the description model (fluency is more forgiving).

### 5.5 Recommendation for BIAI

**Phase 1 (Current):** Stay with Ollama. It works perfectly for single-user Windows deployment.

**Phase 2 (Enhancement):** Add OpenAI-compatible backend support in `vanna_client.py`. This is a ~20-line change:

```python
# Current: Ollama-specific
import ollama
response = ollama.chat(model="model", messages=[...])

# New: Any OpenAI-compatible server
from openai import OpenAI
client = OpenAI(base_url="http://localhost:PORT/v1", api_key="not-needed")
response = client.chat.completions.create(model="model", messages=[...])
```

This unlocks: vLLM, llama-cpp-python, LM Studio, TabbyAPI, LocalAI, Xinference, SGLang.

**Phase 3 (Production):** For multi-user: vLLM via Docker/WSL2 (35x more throughput). For best quality-per-bit: ExLlamaV3 + TabbyAPI (98% quality at 4-bit).

---

## 6. Text-to-SQL Techniques

### 6.1 Current Best Practices (February 2026)

The BIRD benchmark (gold standard, human ceiling 92.96%) shows a clear hierarchy of techniques:

| Approach | BIRD EX | Spider EX | Latency | BIAI Applicability |
|----------|---------|-----------|---------|-------------------|
| Zero-shot prompting (GPT-4) | ~55% | ~70% | Low | Already surpassed |
| **RAG + prompting (Vanna, BIAI current)** | ~60% | ~75-80% | Medium | **Current approach** |
| Few-shot prompting (GPT-4) | ~65% | ~82% | Low | Example improvement possible |
| Fine-tuned 7B (SFT) | ~65% | ~80% | Low | Model swap |
| Fine-tuned 7B + RL (MARS-SQL) | **77.84%** | **89.75%** | Low | Best if model available |
| Fine-tuned 32B + pipeline | ~70% | ~85% | Medium | OmniSQL, XiYanSQL |
| GPT-4 + full pipeline (DAIL-SQL) | ~72% | **86.6%** | High | Cloud fallback |
| Multi-candidate + reward model (Contextual-SQL) | ~73% | — | High | **Highest ROI for BIAI** |

### 6.2 Techniques Mapped to BIAI's Architecture

**Currently implemented in BIAI:**
- RAG retrieval of schema DDL and example queries (Vanna + ChromaDB)
- Self-correction loop with error feedback (up to 5 retries)
- SQL validation with sqlglot AST + dialect transpilation
- Refusal detection and fresh generation fallback

**Techniques to add for better accuracy (ordered by impact/effort ratio):**

#### 1. Multi-Candidate Generation + Execution Voting (+5-15% accuracy)
Generate N SQL candidates (e.g., 5) at temperature=1.0, execute all against the database, and select the most common correct result.

```
User question
  → Generate 5 SQL candidates (temperature=1.0)
  → Execute all 5 against DB
  → Filter: remove syntax errors, empty results, errors
  → Vote: most common result set wins
  → Return winning SQL
```

**Impact:** Single highest-impact technique. The Contextual-SQL approach adds +10-15% to any base model.

#### 2. Schema Pruning (+3-8% accuracy)
Before SQL generation, filter the schema to only relevant tables/columns based on the user's question. This reduces noise and focuses the model.

**Implementation:** Use embedding similarity between the question and table/column names+descriptions to select top-K tables.

#### 3. Improved Example Selection (+2-3% accuracy)
Currently Vanna retrieves examples by semantic similarity. DAIL-SQL shows that selecting examples that are both semantically similar AND SQL-pattern diverse improves results.

#### 4. Entity Retrieval (+2-4% accuracy)
When the user mentions specific values (e.g., "sales in Warsaw"), look up actual database values to include in the prompt. This grounds the SQL in real data.

#### 5. Chain-of-Thought SQL Generation (+2-5% accuracy)
Have the model reason step-by-step: identify tables, match columns, build conditions, then assemble SQL. Models with thinking mode (Qwen3, DeepSeek-R1) naturally do this.

#### 6. Business Term Definitions (+consistency)
Inspired by Wren AI's semantic layer (MDL): define business terms (e.g., "revenue" = `SUM(order_total)`, "active customer" = `WHERE last_order_date > CURRENT_DATE - 90`) in a config file that gets injected into every prompt.

### 6.3 BIAI's Self-Correction Loop: How to Improve

Current: Sequential retry with error message fed back to the model.

Improved: Parallel generation + execution-based filtering:

```
Current:                              Improved:
Question → Generate SQL               Question → Generate 5 SQL candidates
  → Validate                            → Execute all 5
  → Execute                             → Filter valid results
  → Error? → Retry with error msg       → Consistency vote
  → Up to 5 retries                     → Return best candidate
                                         (If all fail → retry with errors)
```

The improved approach generates better SQL on the first pass in most cases, reserving the retry mechanism for genuinely hard queries.

---

## 7. Multi-Model Strategy

### 7.1 Different Models for Different Tasks

BIAI performs several distinct AI tasks that have different requirements:

| Task | Requirements | Best Model Category | Recommended |
|------|-------------|-------------------|-------------|
| **SQL Generation** | Precision, correct syntax, dialect awareness | SQL-specialized | Arctic-Text2SQL-R1-7B (5 GB) |
| **Description/Report Generation** | Fluency, Polish language, natural text | General instruct | Gemma 3 12B (8 GB) or Qwen3:8b (5 GB) |
| **Schema Understanding** | Reasoning about table relationships | Reasoning model | Phi-4-Reasoning (10 GB) or DeepSeek-R1-Distill-14B (9 GB) |
| **Chart Type Selection** | Heuristic + classification | Small, fast model | Qwen3:4b (3 GB) or current heuristic |
| **Process Detection** | Pattern recognition in schema | General code model | Current model (reuse SQL model) |

### 7.2 Dual-Model Architecture (Recommended)

The simplest multi-model setup for BIAI:

```
User question
  ├─→ SQL Model (Arctic-Text2SQL-R1-7B, 5 GB)
  │     → Generate SQL
  │     → Execute against database
  │     → Return DataFrame
  │
  └─→ Description Model (Gemma 3 12B or Qwen3:8b, 5-8 GB)
        → Generate natural language description
        → Explain the results
        → Answer in Polish if needed

Total VRAM: ~10-13 GB (both models loaded simultaneously)
```

### 7.3 Implementation in BIAI

Ollama already supports loading multiple models. The change needed is in `vanna_client.py` and `chat.py`:

1. Configure `SQL_MODEL` and `DESCRIPTION_MODEL` in settings
2. Use `SQL_MODEL` for Vanna's `generate_sql()` call
3. Use `DESCRIPTION_MODEL` for `generate_description()` streaming
4. Both models served by same Ollama instance

### 7.4 Model Routing (Advanced)

For a future hybrid local+cloud setup:

```
User question → Complexity Classifier (rule-based or small model)
  → Simple query → Local SQL model (free, fast)
  → Medium query → Local large model or Groq API ($0.10/1K queries)
  → Complex query → Claude Sonnet API (highest accuracy, $5/1K queries)
```

Research ("Towards Optimizing SQL Generation via LLM Routing") shows this approach can maintain 90%+ accuracy while reducing cloud costs by 80-95%.

---

## 8. Hardware Requirements

### 8.1 VRAM Table for Recommended Models

| Model | Q4_K_M | Q5_K_M | Q6_K | Q8_0 | FP16 | Min GPU |
|-------|--------|--------|------|------|------|---------|
| Prem-1B-SQL | ~1 GB | ~1.2 GB | ~1.5 GB | ~2 GB | ~3 GB | Any |
| Arctic-Text2SQL-R1-7B | **~5 GB** | ~5.5 GB | ~6 GB | ~7.5 GB | ~14 GB | RTX 3060 8GB |
| Qwen2.5-Coder-7B | ~5 GB | ~5.5 GB | ~6 GB | ~7.5 GB | ~14 GB | RTX 3060 8GB |
| OmniSQL-7B | ~5 GB | ~5.5 GB | ~6 GB | ~7.5 GB | ~14 GB | RTX 3060 8GB |
| Yi-Coder-9B | ~6 GB | ~6.5 GB | ~7 GB | ~9 GB | ~18 GB | RTX 3060 12GB |
| Mistral Nemo 12B | ~7 GB | ~8 GB | ~8.5 GB | ~12 GB | ~24 GB | RTX 3060 12GB |
| Qwen2.5-Coder-14B | ~8 GB | ~9 GB | ~10 GB | ~16 GB | ~28 GB | RTX 4060 Ti 16GB |
| OmniSQL-14B | ~10 GB | ~11 GB | ~12 GB | ~16 GB | ~28 GB | RTX 3060 12GB |
| Gemma 3 27B | ~16 GB | ~18 GB | ~20 GB | ~27 GB | ~54 GB | RTX 4090 24GB |
| GLM-4.7-Flash (30B MoE) | ~18 GB | ~20 GB | ~22 GB | ~30 GB | ~60 GB | RTX 4090 24GB |
| Qwen3-Coder-30B-A3B (MoE) | ~18 GB | ~20 GB | ~22 GB | ~30 GB | ~60 GB | RTX 4090 24GB |
| Qwen2.5-Coder-32B | ~20 GB | ~22 GB | ~24 GB | ~32 GB | ~64 GB | RTX 4090 24GB |
| OmniSQL-32B | ~20 GB | ~22 GB | ~24 GB | ~32 GB | ~64 GB | RTX 4090 24GB |
| Llama 3.3 70B | ~40 GB | ~45 GB | ~48 GB | ~70 GB | ~140 GB | 2x RTX 4090 |

### 8.2 BIAI Configuration Profiles

**Budget (8 GB VRAM — RTX 3060 8GB, RTX 4060):**

| Slot | Model | VRAM | Purpose |
|------|-------|------|---------|
| SQL | Arctic-Text2SQL-R1-7B Q4 | 5 GB | SQL generation |
| Text | Shared (same model) | — | Descriptions (reuse SQL model) |
| Total | | ~5 GB | |

**Standard (12 GB VRAM — RTX 3060 12GB, RTX 4070):**

| Slot | Model | VRAM | Purpose |
|------|-------|------|---------|
| SQL | Arctic-Text2SQL-R1-7B Q5 | 5.5 GB | SQL generation (higher quality quant) |
| Text | Qwen3:4b Q4 | 3 GB | Descriptions, Polish |
| Total | | ~8.5 GB | |

**Recommended (24 GB VRAM — RTX 4090, RTX 3090):**

| Slot | Model | VRAM | Purpose |
|------|-------|------|---------|
| SQL | Arctic-Text2SQL-R1-7B Q6 | 6 GB | SQL generation (near-original quality) |
| Text | Gemma 3 12B Q4 | 8 GB | Descriptions, analysis, Polish |
| Total | | ~14 GB | Room for context + second model hot-swap |

**Alternative Recommended (24 GB, single powerful model):**

| Slot | Model | VRAM | Purpose |
|------|-------|------|---------|
| All | GLM-4.7-Flash Q4 | 18 GB | SQL + descriptions + everything; MoE, 200K context |
| Total | | ~18 GB | Simpler setup, one model for all tasks |

**Power (24 GB, maximum SQL quality):**

| Slot | Model | VRAM | Purpose |
|------|-------|------|---------|
| SQL | OmniSQL-14B Q4 or XiYanSQL-14B Q4 | 10 GB | Best SQL at 14B |
| Text | Phi-4 14B Q4 | 10 GB | Descriptions, reasoning |
| Total | | ~20 GB | |

**High-End (48 GB — 2x RTX 4090):**

| Slot | Model | VRAM | Purpose |
|------|-------|------|---------|
| SQL | OmniSQL-32B Q4 | 20 GB | Best local SQL quality |
| Text | Gemma 3 27B Q8 | 27 GB | Near-original quality descriptions |
| Total | | ~47 GB | |

### 8.3 CPU-Only Viable Options

For systems without a GPU or with insufficient VRAM:

| Model | RAM Required | tok/s (CPU) | Quality |
|-------|-------------|-------------|---------|
| Prem-1B-SQL Q4 | ~2 GB | ~15-20 | Basic SQL (51.5% BIRD) |
| Qwen2.5-Coder-1.5B Q4 | ~2 GB | ~10-15 | Light SQL + code |
| Arctic-Text2SQL-R1-7B Q4 | ~8 GB | ~2-5 | Good SQL but slow |

CPU inference is possible but slow. For interactive use, GPU is strongly recommended.

### 8.4 Multi-GPU Considerations

| Setup | Supported By | BIAI Benefit |
|-------|-------------|-------------|
| 2x GPU tensor parallelism | vLLM, llama.cpp, ExLlamaV3 | Run 70B models (Llama 3.3 70B) |
| GPU + CPU offloading | llama.cpp, Ollama | Run larger models on limited VRAM (slower) |
| Ollama multi-GPU | Ollama (automatic split) | Works but no fine-grained control |

---

## 9. Polish Language Support

### 9.1 Which Models Handle Polish Well?

| Model | Polish Quality | Evidence |
|-------|---------------|----------|
| **Qwen 2.5 / 3 family** | Good | Polish included in 29-language training; community reports solid Polish |
| **Gemma 3** | Good | Trained on many languages; Google's multilingual data |
| **Llama 3.1 / 3.3** | Moderate | English-centric but handles Polish adequately |
| **Mistral Large 2/3** | Good | Explicitly multilingual (12+ languages) |
| **Aya 23 (Cohere)** | **Excellent** | Specifically trained on 23 languages including Polish; 58.2% multilingual MMLU (35B) |
| **GLM-4.x** | Moderate | Strong Chinese+English; other languages variable |
| **DeepSeek** | Moderate | Primarily Chinese+English; Polish is secondary |

### 9.2 Polish in BIAI's Context

BIAI needs Polish support for two tasks:
1. **Understanding Polish questions** — translating user intent to SQL
2. **Generating Polish descriptions** — explaining query results in natural Polish

**For task 1 (SQL generation):** The SQL model receives the Polish question but generates universal SQL. Most models handle this adequately because SQL syntax is language-independent. The question understanding relies on the model's multilingual capability.

**For task 2 (descriptions):** This requires good Polish text generation. Qwen 2.5/3 and Gemma 3 handle this well. For the best Polish, consider Aya 23 (but non-commercial license).

### 9.3 Strategies for Better Polish Support

1. **Bilingual prompt engineering:** Include both Polish and English in the system prompt. E.g., "Odpowiedz po polsku. Describe the query results in Polish."

2. **English-first SQL, Polish-second description:** Generate SQL using English-optimized prompts (better accuracy), then generate the description in Polish using a separate prompt.

3. **Few-shot examples in Polish:** Add Polish question-SQL pairs to Vanna's training data to improve question understanding.

4. **Translation layer (future):** For maximum SQL accuracy, translate the Polish question to English before SQL generation, then translate the description back to Polish.

---

## 10. Roadmap & Recommendations

### Phase 1: Quick Wins (No Code Changes or Minimal Changes)

**Timeline: Immediate**

| # | Action | Impact | Effort | Notes |
|---|--------|--------|--------|-------|
| 1 | Test Arctic-Text2SQL-R1-7B on Ollama | +10-15% SQL accuracy | Low | Download GGUF from HuggingFace, create Modelfile |
| 2 | Test GLM-4.7-Flash as alternative runtime | Comparable to Qwen3-Coder-30B | Low | `ollama run glm-4.7-flash` |
| 3 | Use Q5_K_M or Q6_K for SQL model | +2-3% accuracy from better quantization | Low | Just change the model tag in Ollama |
| 4 | Add SQL-specialized prompt to Vanna | +2-3% accuracy | Low | Add C3-style clear prompting hints |
| 5 | Add more Polish Q-SQL examples to Vanna training | Better Polish question understanding | Low | Manually curate 20-50 examples |

### Phase 2: Infrastructure Improvements (Minor Code Changes)

**Timeline: 1-2 weeks**

| # | Action | Impact | Effort | Notes |
|---|--------|--------|--------|-------|
| 6 | Add OpenAI-compatible backend in `vanna_client.py` | Unlock all inference servers | Medium | ~20 lines; use `openai` Python package |
| 7 | Add multi-candidate SQL generation (5 candidates, execution vote) | +5-8% accuracy | Medium | Modify `SelfCorrectionLoop` |
| 8 | Add schema pruning (top-K tables) | +3-5% accuracy on large schemas | Medium | Embedding-based table selection |
| 9 | Dual-model support (SQL model + description model) | Better quality for both tasks | Medium | Add `SQL_MODEL` / `DESCRIPTION_MODEL` settings |
| 10 | Add business term definitions file | Consistency across queries | Low | JSON config injected into prompt |

### Phase 3: Advanced Features (Significant Changes)

**Timeline: 1-2 months**

| # | Action | Impact | Effort | Notes |
|---|--------|--------|--------|-------|
| 11 | Implement Contextual-SQL pipeline | +10-15% accuracy (matching proprietary) | High | Multi-candidate x multi-config + reward model |
| 12 | Add entity retrieval from database | +2-4% accuracy | High | Look up actual DB values mentioned in question |
| 13 | Evaluate Vanna 2.0 migration | Agent framework, security, streaming | High | Breaking API changes from v1 |
| 14 | Cloud fallback for complex queries | 90%+ accuracy on hard queries | Medium | Claude Sonnet / DeepSeek API integration |
| 15 | Model selector in BIAI UI | User choice of local models | Medium | Dropdown in settings page |

### Phase 4: Cutting Edge (Long-Term)

**Timeline: 3-6 months**

| # | Action | Impact | Effort | Notes |
|---|--------|--------|--------|-------|
| 16 | Fine-tune Qwen2.5-Coder-7B on customer schema (Fireworks AI RFT) | 2.4x accuracy on domain SQL | Very High | Requires training data curation |
| 17 | Implement query complexity router | 80-95% cost reduction for cloud | High | Auto-route simple/medium/complex |
| 18 | Multi-model serving with Xinference or vLLM | Multi-user production | High | Docker/WSL deployment |
| 19 | Agentic SQL generation (multi-agent: schema linker → generator → validator) | Top-tier accuracy | Very High | MAC-SQL / MARS-SQL architecture |
| 20 | Wren AI semantic layer integration | Enterprise consistency | Very High | Full architecture addition |

### Summary: Expected Accuracy Progression

| Phase | Configuration | Expected BIRD-level Accuracy |
|-------|-------------|----------------------------|
| Current | Qwen3-Coder-30B + Vanna RAG | ~55-60% |
| Phase 1 | Arctic-Text2SQL-R1-7B + Vanna RAG | ~65-68% |
| Phase 2 | Arctic-R1-7B + multi-candidate + schema pruning | ~70-73% |
| Phase 3 | Contextual-SQL pipeline + cloud fallback | ~75-78% |
| Phase 4 | Fine-tuned model + full pipeline | ~78-82% |
| Human ceiling | Professional data engineers | 92.96% |

---

## Appendix A: Full Model Catalog

### A.1 Chinese / Asian Models

#### Qwen Family (Alibaba) — Apache 2.0 / Qwen License

| Model | Params | Active | Architecture | VRAM (Q4) | Context | Ollama Tag |
|-------|--------|--------|-------------|-----------|---------|------------|
| Qwen2.5 0.5B-72B | 0.5-72B | Dense | Transformer | 1-42 GB | 128K | `qwen2.5:Xb` |
| Qwen2.5-Coder 0.5B-32B | 0.5-32B | Dense | Transformer | 1-20 GB | 128K | `qwen2.5-coder:Xb` |
| Qwen3 0.6B-235B | 0.6-235B | Dense/MoE | Transformer | 1-143 GB | 32-128K | `qwen3:Xb` |
| **Qwen3-Coder-30B-A3B** | 30.5B | 3.3B | MoE (128E/8A) | ~18 GB | 262K | `qwen3-coder:30b` |
| QwQ-32B | 32B | 32B | Dense | ~20 GB | 128K | `qwq:32b` |

#### DeepSeek Family — DeepSeek License

| Model | Params | Active | VRAM (Q4) | Context | Ollama |
|-------|--------|--------|-----------|---------|--------|
| DeepSeek-V3/V3.1/V3.2 | 671-685B | 37B | ~245-250 GB | 128K | Available |
| DeepSeek-R1 (full) | 671B | 37B | ~245 GB | 128K | `deepseek-r1:671b` |
| DeepSeek-R1 Distill 1.5-70B | 1.5-70B | Dense | 2-42 GB | 128K | `deepseek-r1:Xb` |
| DeepSeek-Coder-V2-Lite | 16B | 2.4B | ~10 GB | 128K | `deepseek-coder-v2:16b` |

#### GLM Family (Zhipu AI) — MIT License

| Model | Params | Active | VRAM (Q4) | Context | Ollama |
|-------|--------|--------|-----------|---------|--------|
| GLM-4-9B | 9B | 9B | ~5 GB | 128K | Available |
| GLM-4.5 | ~355B | MoE | Large | 128K | Available |
| GLM-4.6 | 357B | MoE | Large | 200K | `glm-4.6` |
| **GLM-4.7** | 358B | ~35B | ~130 GB | 200K | `glm-4.7` |
| **GLM-4.7-Flash** | 30B | ~3.6B | ~18 GB | 200K | `glm-4.7-flash` |

#### Other Asian Models

| Model | Creator | Params | VRAM (Q4) | Context | BIAI Verdict |
|-------|---------|--------|-----------|---------|-------------|
| Kimi K2/K2.5 | Moonshot AI | 1T+ | 200+ GB | 128K | Too large for consumer |
| MiniMax-M1/M2.5 | MiniMax | 456B | 300+ GB | 4M | Too large for consumer |
| Yi-Coder-9B | 01.AI | 9B | ~6 GB | 128K | Good alternative, Apache 2.0 |
| InternLM 2.5/3 | Shanghai AI Lab | 1.8-20B | 2-12 GB | 32K | Good for data extraction |
| ERNIE 4.5 | Baidu | 0.3-424B | Varies | Varies | PaddlePaddle required, skip |
| Hunyuan-A13B | Tencent | 80B (13B act) | ~50 GB | Varies | Needs dual GPU, skip |
| TeleChat2 | China Telecom | 3-115B | Varies | 8K | Context too short, skip |
| Baichuan 2 | Baichuan AI | 7-13B | 4-8 GB | 4K | Context too short, outdated |
| Skywork-OR1 | Inspur | 7-32B | 5-20 GB | Varies | Niche reasoning, skip |
| Aquila2 | BAAI | 7-70B | Varies | 4K | Outdated, skip |
| XVERSE | Yuanxiang | 7-65B | Varies | 16K | Outdated, no Ollama |

### A.2 Western / Open-Source Models

#### Meta Llama Family

| Model | Params | Active | VRAM (Q4) | Context | Ollama |
|-------|--------|--------|-----------|---------|--------|
| Llama 4 Scout | 109B | 17B (16E MoE) | ~60 GB (Q4) / ~34 GB (1.78-bit) | 10M | `llama4:scout` |
| Llama 4 Maverick | 400B | 17B (128E MoE) | 200+ GB | 1M | `llama4:maverick` |
| Llama 3.3 70B | 70B | Dense | ~40 GB | 128K | `llama3.3:70b` |
| Llama 3.1 8B/70B/405B | 8-405B | Dense | 6-200 GB | 128K | `llama3.1:Xb` |
| CodeLlama 7-70B | 7-70B | Dense | 4-40 GB | 16K | `codellama:Xb` |

#### Mistral AI Family

| Model | Params | VRAM (Q4) | Context | License | Ollama |
|-------|--------|-----------|---------|---------|--------|
| Mistral Large 3 | 675B (41B act) | ~73 GB | 256K | Apache 2.0 | `mistral-large` |
| Mistral Nemo 12B | 12B | ~7 GB | 128K | Apache 2.0 | `mistral-nemo:12b` |
| Codestral 25.01 | 22B | ~13 GB | 256K | Non-production | `codestral:22b` |
| Codestral Mamba | 7.3B | ~4.5 GB | 256K | Apache 2.0 | Community |
| Devstral Small 2 | 24B | ~14 GB | 256K | Apache 2.0 | `devstral:24b` |
| Mixtral 8x22B | 176B (44B act) | ~80 GB | 64K | Apache 2.0 | `mixtral:8x22b` |

#### Microsoft Phi Family — MIT License

| Model | Params | VRAM (Q4) | Context | Ollama |
|-------|--------|-----------|---------|--------|
| Phi-4 14B | 14B | ~10 GB | 16K | `phi4:14b` |
| Phi-4-Reasoning | 14B | ~10 GB | 32K | `phi4-reasoning` |
| Phi-3.5 Mini/MoE | 3.8-42B | 3-25 GB | 128K | `phi3.5` |

#### Google Gemma Family

| Model | Params | VRAM (Q4) | Context | Ollama |
|-------|--------|-----------|---------|--------|
| Gemma 3 1B-27B | 1-27B | 1-16 GB | 32-128K | `gemma3:Xb` |
| Gemma 2 2B-27B | 2-27B | 2-16 GB | 8K | `gemma2:Xb` |
| CodeGemma 7B | 7B | ~4.5 GB | 8K | `codegemma:7b` |

#### Other Western Models

| Model | Creator | Params | VRAM (Q4) | License | Ollama |
|-------|---------|--------|-----------|---------|--------|
| Falcon 3 1-10B | TII | 1-10B | 1-6 GB | Apache 2.0 | `falcon3:Xb` |
| OLMo 2/3 | AI2 | 1-32B | 1-20 GB | Apache 2.0 | `olmo2` |
| Granite Code 3-34B | IBM | 3-34B | 2-20 GB | Apache 2.0 | HuggingFace |
| Granite 4.0 Nano-Small | 350M-32B | Hybrid Mamba | 1-20 GB | Apache 2.0 | Pending |
| DBRX | Databricks | 132B (36B act) | ~70 GB | Databricks OSS | HuggingFace |
| Snowflake Arctic | Snowflake | 480B | Server | Apache 2.0 | N/A |
| Command R/R+ | Cohere | 35-104B | 20-60 GB | CC-BY-NC | Community |
| Aya 23 | Cohere | 8-35B | 5-20 GB | CC-BY-NC | N/A |
| Jamba 1.5 Mini/Large | AI21 | 52-398B | 30-200 GB | Custom | Community |
| Nemotron Nano | NVIDIA | 31.6B (3.2B act) | Pending | Pending | Pending |
| StarCoder2 3-15B | BigCode | 3-15B | 1-10 GB | Apache 2.0 | `starcoder2:Xb` |
| Grok-1 | xAI | 314B (86B act) | 8x 40GB+ | Apache 2.0 | Impractical |

---

## Appendix B: Benchmark Leaderboards

### B.1 BIRD Execution Accuracy (EX) — Test Set (February 2026)

Human ceiling: **92.96%**

| Rank | Model/Method | Dev | Test | Type |
|------|-------------|-----|------|------|
| 1 | AskData + GPT-4o | 77.64% | **81.95%** | Proprietary |
| 2 | Agentar-Scale-SQL | 74.90% | **81.67%** | Proprietary |
| 3 | MARS-SQL (7B, RL) | **77.84%** | — | **Open-source** |
| 4 | LongData-SQL | 74.32% | 77.53% | Proprietary |
| 5 | XiYan-SQL (ensemble) | — | **75.63%** | **Open-source** |
| 6 | CHASE-SQL + Gemini | — | 73.00% | Proprietary |
| 7 | Contextual-SQL (local) | ~73% | — | **Open-source** |
| 8 | Arctic-Text2SQL-R1-32B | 70.5% | — | **Open-source** |
| 9 | Arctic-Text2SQL-R1-7B | 68.9% | 68.5% | **Open-source** |
| 10 | XiYanSQL-QwenCoder-32B | — | 69.03% | **Open-source** |
| 11 | Qwen2.5-Coder-32B (ExCoT) | 68.51% | 68.53% | **Open-source** |
| 12 | OmniSQL-32B | 67.0% | — | **Open-source** |
| 13 | CHESS + GPT-4 | 65.0% | 66.69% | Proprietary |
| 14 | DeepSeek-V3 (zero-shot) | ~49% | — | Open-source |
| 15 | Qwen2.5-Instruct (zero-shot) | ~44% | — | Open-source |

### B.2 Spider 1.0 Execution Accuracy (Leaderboard Frozen Feb 2024)

| Rank | Model/Method | EX | Type |
|------|-------------|-----|------|
| 1 | MiniSeek | **91.2%** | Proprietary |
| 2 | MARS-SQL (7B, RL) | **89.75%** test | **Open-source** |
| 3 | DAIL-SQL + GPT-4 + SC | 86.6% | Proprietary |
| 4 | OmniSQL-32B | ~87% dev | **Open-source** |
| 5 | DIN-SQL + GPT-4 | 85.3% | Proprietary |
| 6 | Qwen2.5-Coder-7B (SPS-SQL) | 82.0% dev | **Open-source** |
| 7 | Llama 3.1-8B (SPS-SQL) | 80.5% dev | **Open-source** |
| 8 | GLM-4-9B (SPS-SQL) | 79.0% test | **Open-source** |
| 9 | RESDSQL-3B + NatSQL | 79.9% | **Open-source** |

### B.3 Spider 2.0 (Enterprise-Level, February 2026)

**Spider 2.0-Snow (Snowflake, 547 examples):**

| Rank | Method | EX |
|------|--------|-----|
| 1 | QUVI-3 + Gemini-3-pro | **94.15%** |
| 2 | TCDataAgent + Contextual Scaling | 93.97% |
| 3 | Prism Swarm + Claude-Sonnet-4.5 | 90.49% |

**Spider 2.0-Lite (multi-DB, 547 examples):**

| Rank | Method | EX |
|------|--------|-----|
| 1 | QUVI-2.3 + Claude-Opus-4.5 | **65.81%** |
| 2 | EXA-SQL | 64.16% |
| 3 | AutoLink + DeepSeek-R1 | 52.28% |

### B.4 Benchmark Summary

| Benchmark | What It Measures | SOTA | Status |
|-----------|-----------------|------|--------|
| **BIRD** | Real database content understanding (gold standard) | 81.95% | Active |
| **Spider 1.0** | Cross-domain SQL generalization | 91.2% | Frozen (Feb 2024) |
| **Spider 2.0** | Enterprise-level real-world SQL | 94.15% (Snow) | Active |
| **BIRD-Interact** | Multi-turn conversational SQL | 24.4% (o3-mini) | Active |
| **WikiSQL** | Single-table SQL (solved) | 93.0% | Inactive |
| **CoSQL** | Conversational multi-turn SQL | — | Active |
| **KaggleDBQA** | Real-world messy databases | — | Active |
| **EHRSQL** | Healthcare domain SQL | — | Active |
| **Dr.Spider** | Robustness under perturbation | — | Active |

---

## Appendix C: Sources

### Benchmarks & Leaderboards
- [BIRD-bench](https://bird-bench.github.io/)
- [Spider](https://yale-lily.github.io/spider) / [Spider 2.0](https://spider2-sql.github.io/)
- [OpenLM.ai Text2SQL Leaderboard](https://openlm.ai/text2sql-leaderboard/)
- [AIMultiple Text-to-SQL Comparison 2026](https://research.aimultiple.com/text-to-sql/)
- [Papers With Code — Spider SOTA](https://paperswithcode.com/sota/text-to-sql-on-spider)

### Key Papers
- [MARS-SQL: Multi-Agent RL](https://arxiv.org/abs/2511.01008)
- [Arctic-Text2SQL-R1 (Snowflake)](https://huggingface.co/Snowflake/Arctic-Text2SQL-R1-7B)
- [Contextual-SQL](https://contextual.ai/blog/open-sourcing-the-best-local-text-to-sql-system)
- [OmniSQL (VLDB 2025)](https://arxiv.org/abs/2503.02240)
- [CHASE-SQL (ICLR 2025)](https://arxiv.org/abs/2410.01943)
- [DIN-SQL](https://arxiv.org/abs/2304.11015) / [DAIL-SQL](https://arxiv.org/abs/2308.15363)
- [C3 Zero-shot Text-to-SQL](https://arxiv.org/abs/2307.07306)
- [ExCoT (Snowflake)](https://www.snowflake.com/en/engineering-blog/arctic-text2sql-excot-sql-generation-accuracy/)
- [LLM Routing for SQL](https://arxiv.org/abs/2411.04319)

### Models & Platforms
- [Ollama Model Library](https://ollama.com/library)
- [HuggingFace Models](https://huggingface.co/models)
- [XiYanSQL (Alibaba)](https://github.com/XGenerationLab/XiYan-SQL)
- [SQLCoder (Defog)](https://github.com/defog-ai/sqlcoder)
- [OmniSQL (RUC)](https://github.com/RUCKBReasoning/OmniSQL)

### Inference Servers
- [Ollama](https://ollama.com/)
- [vLLM](https://github.com/vllm-project/vllm)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [ExLlamaV3](https://github.com/turboderp/exllamav3)
- [SGLang](https://github.com/sgl-project/sglang)
- [LocalAI](https://github.com/mudler/LocalAI)

### Text-to-SQL Frameworks
- [Vanna.ai](https://vanna.ai/)
- [Wren AI](https://www.getwren.ai/)
- [DB-GPT](https://github.com/eosphoros-ai/DB-GPT)
- [Chat2DB](https://github.com/CodePhiliaX/Chat2DB)

### Cloud Pricing
- [Claude API](https://platform.claude.com/docs/en/about-claude/pricing)
- [DeepSeek API](https://api-docs.deepseek.com/quick_start/pricing)
- [Groq Pricing](https://groq.com/pricing)
- [Gemini API](https://ai.google.dev/gemini-api/docs/pricing)

---

*Synthesized from 4 specialist research reports (Asian models, Western models, inference servers, Text-to-SQL benchmarks). February 2026.*
*For BIAI project — Business Intelligence AI (Vanna + Ollama, PostgreSQL/Oracle).*
