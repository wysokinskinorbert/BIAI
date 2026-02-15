# Asian/Chinese LLM Models for Local Deployment — Comprehensive Research (Feb 2026)

> Research conducted for BIAI project: Business Intelligence AI using local LLM inference.
> Focus: Text-to-SQL, data analytics, report generation, code/schema understanding.

---

## Table of Contents

1. [Executive Summary & Top Recommendations](#executive-summary--top-recommendations)
2. [Qwen Family (Alibaba)](#1-qwen-family-alibaba)
3. [DeepSeek Family](#2-deepseek-family)
4. [GLM Family (Zhipu AI / Z.ai)](#3-glm-family-zhipu-ai--zai)
5. [Kimi Family (Moonshot AI)](#4-kimi-family-moonshot-ai)
6. [Yi Family (01.AI)](#5-yi-family-01ai)
7. [MiniMax Family](#6-minimax-family)
8. [InternLM Family (Shanghai AI Lab)](#7-internlm-family-shanghai-ai-lab)
9. [Baichuan Family (Baichuan AI)](#8-baichuan-family-baichuan-ai)
10. [XVERSE Family (Yuanxiang Technology)](#9-xverse-family-yuanxiang-technology)
11. [Skywork Family (Kunlun Tech)](#10-skywork-family-kunlun-tech)
12. [MiMo Family (Xiaomi)](#11-mimo-family-xiaomi)
13. [Seed Family (ByteDance)](#12-seed-family-bytedance)
14. [StepFun Family](#13-stepfun-family)
15. [Hunyuan Family (Tencent)](#14-hunyuan-family-tencent)
16. [MAP-Neo (M-A-P)](#15-map-neo-m-a-p)
17. [Marco-o1 (AIDC-AI / Alibaba)](#16-marco-o1-aidc-ai--alibaba)
18. [Comparative Tables](#comparative-tables)
19. [Text-to-SQL Benchmark Results](#text-to-sql-benchmark-results)
20. [VRAM Requirements Reference](#vram-requirements-reference)
21. [Recommendations for BIAI](#recommendations-for-biai)

---

## Executive Summary & Top Recommendations

### Best Models for BIAI (SQL + Analytics) on Consumer Hardware

| Rank | Model | Why | VRAM (Q4) | Ollama |
|------|-------|-----|-----------|--------|
| 1 | **Qwen3-30B-A3B** | Best MoE efficiency, strong SQL, Apache 2.0 | ~18 GB | Yes |
| 2 | **Qwen2.5-Coder-32B** | Top Text-to-SQL scores (Spider 82%, BIRD 68%) | ~20 GB | Yes |
| 3 | **DeepSeek-R1-Distill-Qwen-32B** | Strong reasoning for complex SQL | ~18 GB | Yes |
| 4 | **Qwen3-Coder-30B-A3B** | Code-focused MoE, tool calling | ~18 GB | Yes |
| 5 | **GLM-4.7-Flash (30B-A3B)** | Strong coding, efficient MoE | ~17 GB | Yes |
| 6 | **Qwen3-8B** | Best quality/size ratio for 8B class | ~6 GB | Yes |
| 7 | **DeepSeek-R1-Distill-Qwen-14B** | Good reasoning, runs on 16GB GPU | ~8 GB | Yes |
| 8 | **Qwen2.5-Coder-7B** | Proven Text-to-SQL (Spider 82%) | ~5 GB | Yes |

### Key Takeaway
For BIAI's SQL generation use case, **Qwen family dominates** due to:
- Explicit Text-to-SQL training data and benchmarks
- Apache 2.0 license (commercial use)
- Excellent Ollama/llama.cpp support
- MoE variants run on consumer GPUs (24GB VRAM)

---

## 1. Qwen Family (Alibaba)

### Overview
The most comprehensive open-source LLM ecosystem from China. Apache 2.0 license across all models.

### Qwen3 — Core Models (Apr 2025)

| Model | Type | Total Params | Active Params | Context | License |
|-------|------|-------------|---------------|---------|---------|
| Qwen3-235B-A22B | MoE | 235B | 22B | 128K | Apache 2.0 |
| Qwen3-32B | Dense | 32B | 32B | 128K | Apache 2.0 |
| Qwen3-14B | Dense | 14B | 14B | 128K | Apache 2.0 |
| Qwen3-8B | Dense | 8B | 8B | 128K | Apache 2.0 |
| Qwen3-4B | Dense | 4B | 4B | 128K | Apache 2.0 |
| Qwen3-1.7B | Dense | 1.7B | 1.7B | 128K | Apache 2.0 |
| Qwen3-0.6B | Dense | 0.6B | 0.6B | 128K | Apache 2.0 |
| **Qwen3-30B-A3B** | **MoE** | **30B** | **3B** | **128K** | **Apache 2.0** |

**Key Features:**
- Thinking mode (CoT) + non-thinking mode switchable
- Qwen3-30B-A3B outperforms QwQ-32B with 10x fewer activated parameters
- Qwen3-4B rivals Qwen2.5-72B-Instruct in many benchmarks
- All sizes available on Ollama: `ollama run qwen3:30b-a3b`

### Qwen3-Coder (Jul 2025)

| Model | Type | Total Params | Active Params | Context | Trained On |
|-------|------|-------------|---------------|---------|------------|
| Qwen3-Coder-480B-A35B | MoE | 480B | 35B | 256K (1M ext.) | 7.5T tokens (70% code) |
| Qwen3-Coder-30B-A3B | MoE | 30B | 3B | 256K | Code-focused |
| Qwen3-Coder-Next (80B-A3B) | MoE | 80B | 3B | 256K | Hybrid attention |

**Coding Benchmarks:**
- SWE-Bench Verified: 70%+ (Coder-Next with SWE-Agent)
- Coder-Next (3B active) matches models with 10-20x more active params

### Qwen2.5-Coder (Sep 2024 — still highly relevant)

| Model | Params | Context | Text-to-SQL Spider | Text-to-SQL BIRD |
|-------|--------|---------|-------------------|-----------------|
| Qwen2.5-Coder-32B | 32B | 128K | ~82% (ExCoT) | 68.5% (ExCoT) |
| Qwen2.5-Coder-14B | 14B | 128K | ~80% | ~62% |
| Qwen2.5-Coder-7B | 7B | 128K | 82.0% | ~57% |
| Qwen2.5-Coder-3B | 3B | 128K | N/A | N/A |
| Qwen2.5-Coder-1.5B | 1.5B | 128K | N/A | N/A |
| Qwen2.5-Coder-0.5B | 0.5B | 128K | N/A | N/A |

**Critical for BIAI:** Qwen2.5-Coder was explicitly trained with synthetic Text-to-SQL data. The 7B model achieves 82% on Spider — best-in-class for its size.

### QwQ-32B (Reasoning, Mar 2025)

| Model | Params | Type | Context | Key Benchmarks |
|-------|--------|------|---------|----------------|
| QwQ-32B | 32B | Dense | 128K | AIME 50%, MATH-500 90.6%, LiveCodeBench 50% |

**Strengths:** Deep chain-of-thought reasoning, competitive with DeepSeek-R1 (671B) despite being 32B dense.

### Qwen3 Specialized Models

| Category | Models | Sizes |
|----------|--------|-------|
| Vision-Language | Qwen3-VL | 235B-A22B, 30B-A3B, smaller |
| Embedding | Qwen3-Embedding | 0.6B, 4B, 8B |
| Reranking | Qwen3-Reranker | 0.6B, 4B, 8B |
| Speech | Qwen3-ASR, Qwen3-TTS | 0.6B, 1.7B |

### VRAM Requirements (Qwen3-30B-A3B)

| Quantization | Size on Disk | VRAM (approx) |
|-------------|-------------|---------------|
| Q8_0 | 31 GB | ~33 GB |
| Q6_K | 24 GB | ~26 GB |
| Q5_K_M | 21 GB | ~23 GB |
| **Q4_K_M** | **18 GB** | **~20 GB** |
| Q3_K | 14 GB | ~16 GB |
| Q2_K | 11 GB | ~13 GB |

**Ollama support:** Full. `ollama run qwen3:30b-a3b`, `ollama run qwen3:8b`, etc.
**Other servers:** vLLM, SGLang, llama.cpp, LMStudio, KTransformers.

### Language Support
Strong Chinese, English, Japanese, Korean. Reasonable multilingual including European languages. Polish support is adequate but not specialized.

---

## 2. DeepSeek Family

### Overview
Leading Chinese AI lab known for MoE innovation. MIT License on most models. Extremely strong reasoning.

### DeepSeek-V3 Series

| Model | Release | Total Params | Active Params | Context | Architecture |
|-------|---------|-------------|---------------|---------|-------------|
| DeepSeek-V3 | Dec 2024 | 671B | 37B | 128K | MoE + MLA |
| DeepSeek-V3-0324 | Mar 2025 | 671B | 37B | 128K | Improved post-training |
| DeepSeek-V3.1 | Aug 2025 | 671B | 37B | 128K | Hybrid thinking/non-thinking |
| DeepSeek-V3.2-Exp | Sep 2025 | 671B | 37B | 128K+ | Sparse Attention |

**V3.1 Key Innovation:** Dual-mode — can switch between V3-style fast answers and R1-style thinking mode. One model for both use cases.

**Local Deployment Reality:** Full model requires 8x H100/H200 GPUs or ~400GB VRAM+RAM minimum at Q4. **Not practical for consumer hardware.**

### DeepSeek-R1 (Reasoning, Jan 2025)

| Model | Total Params | Active Params | Context | License |
|-------|-------------|---------------|---------|---------|
| DeepSeek-R1 | 685B | 37B | 128K | MIT |
| DeepSeek-R1-0528 | 685B | 37B | 128K | MIT |

**R1-0528 Improvements:**
- AIME 2025: 87.5% (up from 70%)
- Hallucination rate reduced ~45-50%
- Added JSON output and function calling support

### DeepSeek-R1 Distilled Models (CRITICAL for local use)

| Model | Base Model | Params | VRAM (Q4) | Ollama |
|-------|-----------|--------|-----------|--------|
| DeepSeek-R1-Distill-Qwen-1.5B | Qwen2.5-1.5B | 1.5B | ~1 GB | Yes |
| DeepSeek-R1-Distill-Qwen-7B | Qwen2.5-7B | 7B | ~4 GB | Yes |
| DeepSeek-R1-Distill-Llama-8B | Llama-3.1-8B | 8B | ~5 GB | Yes |
| DeepSeek-R1-Distill-Qwen-14B | Qwen2.5-14B | 14B | ~8 GB | Yes |
| **DeepSeek-R1-Distill-Qwen-32B** | **Qwen2.5-32B** | **32B** | **~18 GB** | **Yes** |
| DeepSeek-R1-Distill-Llama-70B | Llama-3.3-70B | 70B | ~40 GB | Yes |

**Key for BIAI:** The 32B distilled model brings R1-level reasoning to consumer GPUs (RTX 4090). Excellent for complex multi-join SQL queries.

### DeepSeek-Coder-V2

| Model | Total Params | Active Params | Context | HumanEval |
|-------|-------------|---------------|---------|-----------|
| DeepSeek-Coder-V2 (Full) | 236B | 21B | 128K | 90.2% |
| **DeepSeek-Coder-V2-Lite** | **16B** | **2.4B** | **128K** | **65.6%** |

**Coder-V2-Lite:** Excellent efficiency — only 2.4B active params from 16B total. Supports 338 programming languages. Runs on a single 40GB GPU in BF16.

### DeepSeek Other Specialized Models

| Model | Purpose | Params |
|-------|---------|--------|
| DeepSeek-Prover-V2 | Formal theorem proving (Lean 4) | 7B, 671B |
| DeepSeek-OCR | Image-to-text / OCR | 3B |
| Janus (multimodal) | Vision understanding + generation | Various |

### Quantization & Formats
- GGUF (llama.cpp, Ollama): Full support for distilled models
- GPTQ, AWQ, EXL2: Available on HuggingFace
- FP8: Supported by vLLM, SGLang for full-size models
- 1.58-bit dynamic (Unsloth): R1 in 160GB VRAM (2x H100)

---

## 3. GLM Family (Zhipu AI / Z.ai)

### Overview
One of China's most prominent AI labs. Recent models (GLM-4.7, GLM-5) under MIT license.

### GLM-5 (Feb 2026 — LATEST)

| Spec | Value |
|------|-------|
| Total Parameters | 745B (744B) |
| Active Parameters | 44B (40B) |
| Architecture | MoE, 256 experts, 8 active per token |
| License | MIT |
| Training | Trained entirely on Huawei Ascend chips |

**Key Achievement:** Competes with Claude Opus 4.5, GPT-5.2, and Gemini 3.0 Pro. Record-low hallucination rate using novel "Slime" RL technique.

**Local Deployment:** Requires enterprise-grade hardware (similar to DeepSeek-V3). Not practical for consumer GPUs.

### GLM-4.7 (Dec 2025)

| Model | Type | Total Params | Active Params | Context |
|-------|------|-------------|---------------|---------|
| GLM-4.7 | MoE | 384B (355B) | ~35B | 128K |
| **GLM-4.7-Flash** | **MoE** | **30B** | **~3B** | **128K** |

**GLM-4.7 Coding Benchmarks:**
- SWE-bench: 73.8% (+5.8%)
- LiveCodeBench V6: 84.9 (open-source SOTA, surpassing Claude Sonnet 4.5)

**GLM-4.7-Flash VRAM:**
- 4K context: ~17 GB
- 8K context: ~18 GB
- 16K context: ~19 GB
- Sweet spot: Single RTX 3090/4090 (24 GB)

**Ollama:** `ollama run glm-4.7` and `ollama run glm-4.7-flash`

### GLM-4 (Earlier, 2024)

| Model | Params | Focus |
|-------|--------|-------|
| GLM-4-9B-Chat | 9B | General chat |
| GLM-4-9B-Code | 9B | Code generation |
| GLM-4-9B-Air | 9B | Lightweight |

**Ollama:** `ollama run glm4`

### Language Support
Strong Chinese + English. GLM-4.7 optimized for multilingual coding and terminal tasks.

---

## 4. Kimi Family (Moonshot AI)

### Overview
Known for extremely long context and agentic capabilities. Models are very large (1T+ params).

### Kimi K2.5 (Jan 2026 — LATEST)

| Spec | Value |
|------|-------|
| Total Parameters | 1 Trillion |
| Active Parameters | 32B |
| Architecture | MoE, 61 layers, 384 experts, 8 active per token |
| Context | 256K (K2-Thinking: up to 256K) |
| Training | 15 trillion tokens (mixed visual + textual) |
| License | Modified MIT (K2), check K2.5 |

### Kimi K2 Variants

| Model | Release | Key Feature |
|-------|---------|-------------|
| Kimi-K2-Instruct | Jul 2025 | Base instruction model |
| Kimi-K2-Thinking | Nov 2025 | Reasoning with interleaved CoT + tool calls |
| Kimi-K2.5 | Jan 2026 | Native multimodal + agent swarm |

### Local Deployment Reality

| Quantization | Size | VRAM Needed | Practical? |
|-------------|------|-------------|------------|
| Full (BF16) | ~1.09 TB | 200+ GB | No (consumer) |
| UD-Q2_K_XL | ~230 GB | 24GB GPU + 256GB RAM | Marginal |
| UD-TQ1_0 (1.8-bit) | ~200 GB | 24GB GPU + MoE offload to RAM | Slow (~5 tok/s) |

**Verdict for BIAI:** Too large for practical local deployment on consumer hardware. Great via API, impractical locally.

---

## 5. Yi Family (01.AI)

### Overview
Founded by Kai-Fu Lee. Focuses on efficiency and multilingual support. Development appears slower in 2025-2026.

### Available Models

| Model | Params | Context | Focus | License |
|-------|--------|---------|-------|---------|
| Yi-1.5-34B | 34B | 4K-32K | General | Apache 2.0 |
| Yi-1.5-9B | 9B | 4K | General | Apache 2.0 |
| Yi-1.5-6B | 6B | 4K | General | Apache 2.0 |
| Yi-Coder-9B | 9B | 128K | Coding | Apache 2.0 |
| Yi-Coder-1.5B | 1.5B | 128K | Coding | Apache 2.0 |

### VRAM Requirements

| Model | FP16 | INT8 | INT4 |
|-------|------|------|------|
| Yi-1.5-34B | ~68 GB | ~34 GB | ~20 GB |
| Yi-Coder-9B | ~18 GB | ~9 GB | ~5 GB |
| Yi-Coder-1.5B | ~3 GB | ~1.5 GB | ~1 GB |

**Ollama:** `ollama run yi-coder:9b`

### Assessment for BIAI
Yi-Coder-9B is decent but has been surpassed by Qwen2.5-Coder-7B on Text-to-SQL benchmarks. Yi family has not released major updates in 2025-2026, making it less competitive.

---

## 6. MiniMax Family

### Overview
Novel Lightning Attention architecture with extreme context lengths (4M tokens).

### MiniMax-Text-01 (Jan 2025)

| Spec | Value |
|------|-------|
| Total Parameters | 456B |
| Active Parameters | 45.9B |
| Architecture | MoE, 32 experts per layer, Top-2 routing |
| Attention | Hybrid: 7 Lightning Attention + 1 SoftMax per 8 layers |
| Context | 1M training, 4M inference |
| Layers | 80 |
| License | Open-source |

### Local Deployment
Requires multiple high-end GPUs. INT8 quantization recommended. Not suitable for consumer hardware due to 45.9B active params.

### Assessment for BIAI
The 4M context is impressive but unnecessary for SQL generation. Active param count (45.9B) is too large for single consumer GPU. Not recommended for local BIAI deployment.

---

## 7. InternLM Family (Shanghai AI Lab)

### Overview
Academic-oriented models from Shanghai AI Laboratory. Good but limited size range.

### Available Models

| Model | Params | Context | Release |
|-------|--------|---------|---------|
| InternLM3-8B-Instruct | 8B | 32K | Jan 2025 |
| InternLM2.5-20B | 20B | 32K (1M variant) | 2024 |
| InternLM2.5-7B | 7B | 32K (1M variant) | 2024 |
| InternLM2.5-1.8B | 1.8B | 32K | 2024 |

### Key Features
- InternLM3-8B supports deep thinking mode (long chain-of-thought) and normal response mode
- GGUF quantization available via llama.cpp
- LMDeploy toolkit for serving

### Assessment for BIAI
Decent 8B-20B options but no specialized SQL/coding focus. Surpassed by Qwen3 and DeepSeek-R1-Distill in most benchmarks. Low priority for BIAI.

---

## 8. Baichuan Family (Baichuan AI)

### Overview
Focused on domain-specific applications: law, finance, medicine, classical Chinese.

### Available Models

| Model | Params | Focus | License |
|-------|--------|-------|---------|
| Baichuan 2-7B | 7B | General, bilingual | Open |
| Baichuan 2-13B | 13B | General, bilingual | Open |
| Baichuan-M2-32B | 32B | Medical/Healthcare | Open |
| Baichuan 3 | 1T+ (closed) | Domain-specific | Proprietary |
| Baichuan 4 | Unknown | Domain-specific | Proprietary |

### Assessment for BIAI
Baichuan 2 models (7B, 13B) are outdated compared to Qwen3 and DeepSeek. The newer Baichuan 3/4 are proprietary. Medical focus (M2-32B) is irrelevant for BIAI. **Not recommended.**

---

## 9. XVERSE Family (Yuanxiang Technology)

### Overview
Multilingual models with fine-grained MoE architecture from Shenzhen.

### Available Models

| Model | Total Params | Active Params | Architecture | Context |
|-------|-------------|---------------|-------------|---------|
| XVERSE-65B | 65B (dense) | 65B | Dense Transformer | 16K |
| XVERSE-65B-2 | 65B (dense) | 65B | Dense Transformer | 16K |
| XVERSE-MoE-A36B | 255B | 36B | MoE (fine-grained) | 16K |
| XVERSE-MoE-A4.2B | 25.8B | 4.2B | MoE (fine-grained) | 16K |

### Key Architecture Detail
Fine-grained experts: each expert is 1/4 the size of a standard FFN, with both shared and non-shared experts.

### Assessment for BIAI
Models are from 2024 and have not been updated. Limited community support. 16K context is restrictive. **Not recommended** — Qwen3-30B-A3B (also MoE) is strictly superior.

---

## 10. Skywork Family (Kunlun Tech)

### Overview
Research-focused MoE models. Known for training technique innovations.

### Available Models

| Model | Total Params | Active Params | Architecture |
|-------|-------------|---------------|-------------|
| Skywork-MoE | 146B | 22B | MoE, 16 experts |
| MiMo-V2-Flash (Skywork ecosystem) | 309B | 15B | MoE (Xiaomi, see below) |

**Skywork-MoE Technical Innovations:**
- Gating Logit Normalization for expert diversification
- Adaptive Auxiliary Loss Coefficients for layer-specific tuning
- Runs on 8x4090 at FP8

### Assessment for BIAI
Research-quality model. Performance comparable to Deepseek-V2 but no Text-to-SQL focus. Limited Ollama support. **Low priority.**

---

## 11. MiMo Family (Xiaomi)

### Overview
Xiaomi's entry into open-source AI. MIT License. Strong reasoning focus.

### Available Models

| Model | Release | Total Params | Active Params | Architecture | Context |
|-------|---------|-------------|---------------|-------------|---------|
| MiMo-7B | Apr 2025 | 7B | 7B | Dense | 32K |
| **MiMo-V2-Flash** | **Dec 2025** | **309B** | **15B** | **MoE** | **56K** |

### MiMo-V2-Flash Key Features
- Hybrid Attention: SWA + GA (5:1 ratio, 128-token window) — 6x KV-cache reduction
- Multi-Token Prediction: 3x generation speed via speculative decoding
- SWE-Bench Verified: #1 among open-source models
- 150 tokens/sec inference speed
- MIT License

### Local Deployment
Full model requires enterprise hardware (15B active is manageable but 309B total requires significant storage + MoE offloading). GGUF quantizations likely available.

### Assessment for BIAI
MiMo-7B is interesting for edge deployment. MiMo-V2-Flash is strong but large. Not SQL-focused. **Medium priority** — worth watching but Qwen3-30B-A3B is more practical for BIAI.

---

## 12. Seed Family (ByteDance)

### Overview
ByteDance's open-source AI initiative. Apache 2.0 License.

### Available Models

| Model | Release | Params | Context | Architecture |
|-------|---------|--------|---------|-------------|
| Seed-OSS-36B-Instruct | Aug 2025 | 36B (dense) | 512K | Dense Transformer |
| Seed-OSS-36B-Base | Aug 2025 | 36B | 512K | Dense |
| Seed-Coder-8B | 2025 | 8B | Various | Dense |
| BAGEL (multimodal) | 2025 | 14B (7B active) | Various | MoT |
| Seed1.5-VL | 2025 | 20B active (MoE) | Various | MoE |

### Seed-OSS-36B Key Features
- 512K context — longest among dense 36B models
- Dynamic reasoning length control (`thinking_budget=N`)
- Optimized for i18n use cases
- GQA, RMSNorm, SwiGLU, 64 layers

### Assessment for BIAI
The 36B dense model with 512K context is impressive but requires ~20GB+ VRAM even at Q4. No specific SQL/coding focus. **Low-medium priority.**

---

## 13. StepFun Family

### Overview
Shanghai-based AGI startup. Known for Step-2 (1T params).

### Available Models

| Model | Total Params | Active Params | Architecture | Open Source |
|-------|-------------|---------------|-------------|------------|
| Step-2 | ~1T | Unknown | MoE | API only (closed) |
| Step-3.5-Flash | 196B | 11B | MoE | Yes |

### Step-3.5-Flash
- Released for agent scenarios
- 11B active parameters — efficient
- MoE Transformer architecture
- Strong reasoning and fast response

### Assessment for BIAI
Step-3.5-Flash (11B active) could be interesting for local deployment but limited community adoption and Ollama support. **Low priority.**

---

## 14. Hunyuan Family (Tencent)

### Overview
Tencent's multi-modal AI suite. Primarily focused on image/video generation, with some LLM models.

### Language Models

| Model | Total Params | Active Params | Architecture | Context |
|-------|-------------|---------------|-------------|---------|
| Hunyuan-Large | 389B | 52B | MoE | 256K |
| Hunyuan 2.0 | 406B | 32B | MoE | Various |
| Hunyuan-MT-7B | 7B | 7B | Dense | Various |

### Assessment for BIAI
Hunyuan LLMs are large (require enterprise hardware). The 7B translation model is specialized. No SQL/coding focus. **Not recommended** for BIAI.

---

## 15. MAP-Neo (M-A-P)

### Overview
Fully transparent bilingual (English + Chinese) research model.

| Spec | Value |
|------|-------|
| Parameters | 7B |
| Training Data | 4.5T tokens |
| Architecture | Dense Transformer decoder |
| License | Open (research-focused) |

### Assessment for BIAI
A 7B research model from 2024 with no updates. Significantly outperformed by Qwen3-8B. **Not recommended.**

---

## 16. Marco-o1 (AIDC-AI / Alibaba)

### Overview
Reasoning model with Monte Carlo Tree Search (MCTS) and chain-of-thought fine-tuning.

### Available Models

| Model | Release | Params | Key Innovation |
|-------|---------|--------|---------------|
| Marco-o1 v1 | Nov 2024 | 7B | MCTS + CoT + Reflection |
| Marco-o1 v2 | Feb 2026 | 7B | Self-built data, DPO, math optimization |

**Performance:**
- MGSM English: +6.17% accuracy improvement
- MGSM Chinese: +5.60% accuracy improvement
- First LRM applied to Machine Translation

### Assessment for BIAI
7B reasoning model with MCTS is interesting for complex queries but limited to 7B scale. Better reasoning models exist (QwQ-32B, DeepSeek-R1-Distill-32B). **Low priority** unless MCTS reasoning proves valuable for SQL planning.

---

## Comparative Tables

### Size vs Performance (SQL-relevant models)

| Model | Active Params | Spider (est.) | BIRD (est.) | HumanEval | VRAM (Q4) | Ollama |
|-------|-------------|---------------|-------------|-----------|-----------|--------|
| Qwen2.5-Coder-7B | 7B | **82.0%** | ~57% | 88.4% | ~5 GB | Yes |
| Qwen2.5-Coder-14B | 14B | ~80% | ~62% | 89.7% | ~9 GB | Yes |
| Qwen2.5-Coder-32B | 32B | ~82% | **68.5%** | 92.7% | ~20 GB | Yes |
| Qwen3-8B | 8B | ~78% | ~55% | ~85% | ~6 GB | Yes |
| Qwen3-30B-A3B | 3B (active) | ~76% | ~52% | ~80% | ~18 GB | Yes |
| Qwen3-32B | 32B | ~80% | ~60% | ~88% | ~20 GB | Yes |
| DeepSeek-R1-Distill-7B | 7B | ~75% | ~50% | ~70% | ~4 GB | Yes |
| DeepSeek-R1-Distill-32B | 32B | ~80% | ~60% | ~80% | ~18 GB | Yes |
| GLM-4.7-Flash | 3B (active) | ~74% | ~48% | ~78% | ~17 GB | Yes |
| Yi-Coder-9B | 9B | ~72% | ~48% | ~75% | ~6 GB | Yes |

*Note: Spider/BIRD estimates for models without explicit Text-to-SQL benchmarks are approximated from coding benchmarks and model capabilities.*

### Architecture Comparison

| Model | Type | Total/Active | Context | License | Consumer GPU? |
|-------|------|-------------|---------|---------|--------------|
| Qwen3-30B-A3B | MoE | 30B/3B | 128K | Apache 2.0 | Yes (24GB) |
| Qwen3-8B | Dense | 8B/8B | 128K | Apache 2.0 | Yes (8GB) |
| Qwen2.5-Coder-7B | Dense | 7B/7B | 128K | Apache 2.0 | Yes (8GB) |
| Qwen2.5-Coder-32B | Dense | 32B/32B | 128K | Apache 2.0 | Yes (24GB, Q4) |
| DeepSeek-R1-Distill-32B | Dense | 32B/32B | 128K | MIT | Yes (24GB, Q4) |
| DeepSeek-Coder-V2-Lite | MoE | 16B/2.4B | 128K | MIT | Yes (16GB) |
| GLM-4.7-Flash | MoE | 30B/3B | 128K | MIT | Yes (24GB) |
| Kimi-K2.5 | MoE | 1T/32B | 256K | Modified MIT | No |
| DeepSeek-V3.1 | MoE | 671B/37B | 128K | MIT | No |
| GLM-5 | MoE | 745B/44B | 128K+ | MIT | No |

---

## Text-to-SQL Benchmark Results

### Spider Benchmark (Test Execution Accuracy)

| Model | Method | Spider EX |
|-------|--------|-----------|
| MiniSeek | Specialized | 91.2% |
| Qwen2.5-Coder-7B | SPS-SQL | 82.1% |
| Qwen2.5-Coder-7B | Direct | 82.0% |
| Qwen2.5-Coder-32B | ExCoT | ~82% |
| Q-SQL | Specialized | 76.5% |

### BIRD Benchmark (Test Execution Accuracy)

| Model | Method | BIRD EX |
|-------|--------|---------|
| Qwen2.5-Coder-32B | ExCoT | 68.5% |
| Qwen2.5-Coder-14B | Direct | ~62% |
| Qwen2.5-Coder-7B | Direct | ~57% |

### Spider 2.0 (Enterprise-level, much harder)

| Model | Method | Score |
|-------|--------|-------|
| ReFoRCE + o3 | Specialized | ~37% |
| o1-preview | Direct | 17.1% |

**Key insight:** Text-to-SQL remains challenging even for SOTA models. For local models, Qwen2.5-Coder family leads decisively.

---

## VRAM Requirements Reference

### Consumer GPU Tiers

| GPU | VRAM | Best Models for BIAI |
|-----|------|---------------------|
| RTX 3060 12GB | 12 GB | Qwen2.5-Coder-7B (Q4), DeepSeek-R1-Distill-7B |
| RTX 3070 Ti 8GB | 8 GB | Qwen3-8B (Q4), Yi-Coder-9B (Q4) |
| RTX 3080 10GB | 10 GB | Qwen2.5-Coder-14B (Q4) |
| RTX 3090 24GB | 24 GB | Qwen3-30B-A3B (Q4), GLM-4.7-Flash, Qwen2.5-Coder-32B (Q3) |
| **RTX 4090 24GB** | **24 GB** | **Qwen3-30B-A3B (Q4), DeepSeek-R1-Distill-32B (Q4)** |
| 2x RTX 4090 | 48 GB | Qwen2.5-Coder-32B (Q8), DeepSeek-R1-Distill-70B (Q3) |

### Model Size Quick Reference (Q4_K_M quantization)

| Model | Disk Size | VRAM (Q4) | Tokens/sec (RTX 4090) |
|-------|-----------|-----------|----------------------|
| Qwen3-0.6B | ~0.5 GB | ~1 GB | 100+ |
| Qwen3-1.7B | ~1.2 GB | ~2 GB | 80+ |
| Qwen3-4B | ~2.5 GB | ~4 GB | 60+ |
| Qwen3-8B | ~5 GB | ~6 GB | 40+ |
| Qwen3-14B | ~9 GB | ~11 GB | 25+ |
| Qwen3-30B-A3B | ~18 GB | ~20 GB | 34+ |
| Qwen3-32B | ~20 GB | ~22 GB | 15+ |
| DeepSeek-R1-Distill-32B | ~18 GB | ~20 GB | 15+ |
| GLM-4.7-Flash | ~17 GB | ~19 GB | 30+ |

---

## Recommendations for BIAI

### Primary Recommendation: Qwen2.5-Coder-7B or 32B

**Why:**
1. **Explicitly trained for Text-to-SQL** with synthetic data
2. **Spider 82.0%** at 7B — best-in-class for size
3. **BIRD 68.5%** at 32B with ExCoT — excellent for complex queries
4. **Apache 2.0 License** — full commercial use
5. **Native Ollama support** — drop-in replacement for current model
6. **Low VRAM** — 7B runs on any modern GPU (5GB Q4)

### Secondary Recommendation: Qwen3-30B-A3B (MoE)

**Why:**
1. Only 3B active parameters but 30B total knowledge
2. ~18GB at Q4 — fits RTX 3090/4090
3. 34+ tok/s on consumer GPU
4. Thinking mode for complex queries
5. Newest architecture (Apr 2025)

### Tertiary: DeepSeek-R1-Distill-Qwen-32B

**Why:**
1. R1-level reasoning for complex multi-table JOINs
2. Excellent at step-by-step SQL construction
3. MIT License, full Ollama support
4. 18GB at Q4

### Model Selection Strategy for BIAI

```
Simple queries (1-2 tables):
  → Qwen2.5-Coder-7B (fast, 5GB VRAM)

Complex queries (multi-table, aggregation):
  → Qwen2.5-Coder-32B or Qwen3-30B-A3B (better reasoning)

Oracle dialect + complex queries:
  → DeepSeek-R1-Distill-32B (deep reasoning for dialect nuances)

Data description / report generation:
  → Qwen3-8B or Qwen3-14B (good general + Polish support)
```

### Models to AVOID for BIAI

| Model | Reason |
|-------|--------|
| DeepSeek-V3/V3.1 (full) | Requires 8x H100 — not consumer-grade |
| Kimi K2/K2.5 | 1T params — requires 200+ GB RAM |
| GLM-5 | 745B — enterprise only |
| MiniMax-Text-01 | 45.9B active — too large for single GPU |
| Baichuan 3/4 | Proprietary, no SQL focus |
| XVERSE (any) | Outdated, no community support |

---

## Appendix: Where to Download

| Source | URL | Notes |
|--------|-----|-------|
| Ollama Library | https://ollama.com/library | Easiest for local deployment |
| HuggingFace | https://huggingface.co | GGUF, GPTQ, AWQ, full weights |
| ModelScope | https://modelscope.cn | Chinese mirror, faster in Asia |
| Unsloth | https://huggingface.co/unsloth | Dynamic quantized GGUF models |

## Appendix: Inference Servers

| Server | Best For | GPU Support |
|--------|----------|-------------|
| Ollama | Simplest local setup | NVIDIA, AMD, Apple Silicon |
| llama.cpp | Maximum flexibility, CPU+GPU | NVIDIA, AMD, Apple, CPU |
| vLLM | Production serving, high throughput | NVIDIA, AMD |
| SGLang | Best for MoE models, optimized | NVIDIA, AMD |
| LMStudio | Desktop GUI | NVIDIA, Apple Silicon |
| KTransformers | MoE offloading (CPU+GPU) | NVIDIA + CPU |

---

*Research date: February 14, 2026*
*Prepared for: BIAI (Business Intelligence AI) project*
