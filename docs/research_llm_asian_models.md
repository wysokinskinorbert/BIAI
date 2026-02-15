# Research: Chinese/Asian LLM Models for Local SQL Generation & Analytics

> **Date:** February 2026
> **Context:** BIAI project — local AI-powered BI chatbot (Vanna + Ollama) querying Oracle/PostgreSQL
> **Current model:** Qwen3-Coder:30b via Ollama
> **Goal:** Identify ALL viable Asian/Chinese LLMs for local text-to-SQL, coding, and analytics

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Qwen Family (Alibaba)](#1-qwen-family-alibaba)
3. [DeepSeek Family](#2-deepseek-family)
4. [GLM Family (Zhipu AI / Z.AI)](#3-glm-family-zhipu-ai--zai)
5. [Kimi K2 Family (Moonshot AI)](#4-kimi-k2-family-moonshot-ai)
6. [MiniMax Family](#5-minimax-family)
7. [Yi Family (01.AI)](#6-yi-family-01ai)
8. [ERNIE Family (Baidu)](#7-ernie-family-baidu)
9. [InternLM Family (Shanghai AI Lab)](#8-internlm-family-shanghai-ai-lab)
10. [Hunyuan Family (Tencent)](#9-hunyuan-family-tencent)
11. [TeleChat Family (China Telecom)](#10-telechat-family-china-telecom)
12. [Baichuan Family (Baichuan AI)](#11-baichuan-family-baichuan-ai)
13. [Skywork Family (Inspur/TianGong)](#12-skywork-family-inspurtiangong)
14. [Aquila Family (BAAI)](#13-aquila-family-baai)
15. [XVERSE Family](#14-xverse-family)
16. [Specialized Text-to-SQL Models](#15-specialized-text-to-sql-models)
17. [Text-to-SQL Benchmark Summary](#16-text-to-sql-benchmark-summary)
18. [Recommendations for BIAI](#17-recommendations-for-biai)

---

## Executive Summary

As of February 2026, China accounts for ~1,509 of ~3,755 publicly released LLMs worldwide. The landscape is dominated by **Alibaba (Qwen)**, **DeepSeek**, and **Zhipu AI (GLM)** — all three offering state-of-the-art open-weight models with strong coding/SQL capabilities and Ollama support.

**Key findings for BIAI (text-to-SQL on consumer hardware):**

| Rank | Model | Why | VRAM (Q4) | SQL Perf |
|------|-------|-----|-----------|----------|
| 1 | **Qwen2.5-Coder-7B** | Best text-to-SQL at 7B class: 81.7% Spider EX | ~5 GB | Excellent |
| 2 | **Qwen3-Coder-30B-A3B** | Current BIAI model, strong agentic coding | ~18 GB | Very Good |
| 3 | **GLM-4.7-Flash (30B-A3B)** | 59.2% SWE-bench, 79.5% tool-use, fast on 24GB | ~18 GB | Very Good |
| 4 | **Qwen2.5-Coder-32B** | 92.7% HumanEval, 69% BIRD (fine-tuned XiYanSQL) | ~20 GB | Excellent |
| 5 | **DeepSeek-Coder-V2-Lite (16B/2.4B active)** | Efficient MoE, strong coding, 128K context | ~10 GB | Good |
| 6 | **XiYanSQL-QwenCoder-14B** | Purpose-built for text-to-SQL, multi-dialect | ~10 GB | Excellent |
| 7 | **Yi-Coder-9B** | 85.4% HumanEval, 128K context, Apache 2.0 | ~6 GB | Good |
| 8 | **DeepSeek-R1-Distill-Qwen-14B** | Reasoning + coding distilled from R1 | ~10 GB | Good |

---

## 1. Qwen Family (Alibaba)

**Creator:** Alibaba Cloud / Qwen Team
**License:** Apache 2.0 (most sizes), Qwen License (3B, 72B)

### Qwen 2.5 (Base/Instruct)

| Size | Parameters | VRAM (Q4_K_M) | VRAM (FP16) | Context | Ollama Tag |
|------|-----------|---------------|-------------|---------|------------|
| 0.5B | 0.5B | ~1 GB | ~2 GB | 128K | `qwen2.5:0.5b` |
| 1.5B | 1.5B | ~2 GB | ~4 GB | 128K | `qwen2.5:1.5b` |
| 3B | 3B | ~3 GB | ~7 GB | 128K | `qwen2.5:3b` |
| 7B | 7B | ~5 GB | ~17 GB | 128K | `qwen2.5:7b` |
| 14B | 14B | ~8 GB | ~28 GB | 128K | `qwen2.5:14b` |
| 32B | 32B | ~20 GB | ~64 GB | 128K | `qwen2.5:32b` |
| 72B | 72B | ~42 GB | ~144 GB | 128K | `qwen2.5:72b` |

- **Architecture:** Dense transformer
- **Multilingual:** Chinese, English + 27 languages (Polish included)
- **JSON output:** Native JSON mode support
- **Special:** 1M-token context variants available (7B-1M, 14B-1M)

### Qwen 2.5 Coder

| Size | Parameters | VRAM (Q4_K_M) | Context | Ollama Tag | HumanEval |
|------|-----------|---------------|---------|------------|-----------|
| 0.5B | 0.5B | ~1 GB | 128K | `qwen2.5-coder:0.5b` | — |
| 1.5B | 1.5B | ~2 GB | 128K | `qwen2.5-coder:1.5b` | — |
| 3B | 3B | ~3 GB | 128K | `qwen2.5-coder:3b` | — |
| 7B | 7B | ~5 GB | 128K | `qwen2.5-coder:7b` | 88.4% |
| 14B | 14B | ~8 GB | 128K | `qwen2.5-coder:14b` | — |
| 32B | 32B | ~20 GB | 128K | `qwen2.5-coder:32b` | 92.7% |

- **Text-to-SQL (Spider):** 81.7% EX (7B, SPS-SQL framework), 82.1% EX (test set)
- **Text-to-SQL (BIRD):** 68.51% EX (32B fine-tuned as XiYanSQL)
- **Best coding benchmark:** Qwen2.5-Coder-32B matches GPT-4o on EvalPlus, LiveCodeBench, BigCodeBench

### Qwen 3 (Base/Instruct)

| Size | Total Params | Active Params | Architecture | VRAM (Q4_K_M) | Context | Ollama Tag |
|------|-------------|--------------|-------------|---------------|---------|------------|
| 0.6B | 0.6B | 0.6B | Dense | ~1 GB | 32K | `qwen3:0.6b` |
| 1.7B | 1.7B | 1.7B | Dense | ~2 GB | 32K | `qwen3:1.7b` |
| 4B | 4B | 4B | Dense | ~3 GB | 32K | `qwen3:4b` |
| 8B | 8B | 8B | Dense | ~5 GB | 128K | `qwen3:8b` |
| 14B | 14B | 14B | Dense | ~9 GB | 128K | `qwen3:14b` |
| 30B-A3B | 30B | 3B | MoE (128E/8A) | ~18 GB | 128K | `qwen3:30b-a3b` |
| 32B | 32B | 32B | Dense | ~20 GB | 128K | `qwen3:32b` |
| 235B-A22B | 235B | 22B | MoE | ~112-143 GB | 128K | `qwen3:235b` |

- **Thinking mode:** All Qwen3 models support thinking/non-thinking mode toggle
- **Key advantage:** Qwen3-4B reportedly rivals Qwen2.5-72B on some benchmarks (18x reduction)

### Qwen3-Coder

| Size | Total Params | Active Params | Architecture | VRAM (Q4_K_M) | Context | Ollama Tag |
|------|-------------|--------------|-------------|---------------|---------|------------|
| 30B-A3B | 30.5B | 3.3B | MoE (128E/8A) | ~18 GB | 262K | `qwen3-coder:30b` |
| 480B-A35B | 480B | 35B | MoE | ~250+ GB | 262K | — |

- **Architecture:** MoE with 128 experts, 8 activated per token
- **SWE-bench:** Strong agentic coding performance
- **Inference speed:** ~34 tok/s on RX 7900 XTX (30B-A3B)
- **This is our current BIAI model**

### QwQ (Reasoning)

| Size | Parameters | Architecture | VRAM (Q4_K_M) | Context | Ollama Tag |
|------|-----------|-------------|---------------|---------|------------|
| 32B | 32B | Dense | ~20 GB | 128K | `qwq:32b` |

- **Focus:** Mathematical and logical reasoning (chain-of-thought)
- **Benchmarks:** 65.2% GPQA, 90.6% MATH-500, 50% LiveCodeBench
- **SQL relevance:** Can improve complex analytical query generation through reasoning

---

## 2. DeepSeek Family

**Creator:** DeepSeek AI
**License:** DeepSeek License (open-weight, commercial use allowed)

### DeepSeek-V3 / V3.1 / V3.2

| Model | Total Params | Active Params | VRAM (Q4_K_M) | Context | Ollama |
|-------|-------------|--------------|---------------|---------|--------|
| V3 | 671B | 37B | ~245 GB (2-bit dynamic) | 128K | `deepseek-v3` |
| V3.1 | 671B | 37B | ~245 GB | 128K | Available |
| V3.2 | 685B | 37B | ~250 GB | 128K | Available |

- **Architecture:** MoE with Multi-head Latent Attention (MLA) + DeepSeekMoE
- **V3.1 key feature:** Hybrid thinking/non-thinking (combines V3 + R1 in one model)
- **V3.2:** Added sparse attention, improved coding
- **Consumer GPU:** Requires massive RAM/VRAM; 1-bit dynamic quant (~170 GB) works with 24GB GPU + 256GB RAM offloading
- **Not practical for typical consumer setups**

### DeepSeek-R1

| Variant | Total Params | Active Params | VRAM (Q4_K_M) | Context | Ollama Tag |
|---------|-------------|--------------|---------------|---------|------------|
| Full | 671B | 37B | ~245 GB | 128K | `deepseek-r1:671b` |
| Distill-Qwen-1.5B | 1.5B | 1.5B | ~2 GB | 128K | `deepseek-r1:1.5b` |
| Distill-Qwen-7B | 7B | 7B | ~5 GB | 128K | `deepseek-r1:7b` |
| Distill-Llama-8B | 8B | 8B | ~5 GB | 128K | `deepseek-r1:8b` |
| Distill-Qwen-14B | 14B | 14B | ~9 GB | 128K | `deepseek-r1:14b` |
| Distill-Qwen-32B | 32B | 32B | ~20 GB | 128K | `deepseek-r1:32b` |
| Distill-Llama-70B | 70B | 70B | ~42 GB | 128K | `deepseek-r1:70b` |

- **R1-Distill-Qwen-32B** outperforms OpenAI o1-mini across various benchmarks
- **Reasoning:** Chain-of-thought reasoning trained via reinforcement learning
- **SQL relevance:** Reasoning capabilities help with complex analytical queries

### DeepSeek-Coder-V2

| Variant | Total Params | Active Params | VRAM (Q4_K_M) | Context | Ollama Tag |
|---------|-------------|--------------|---------------|---------|------------|
| Lite | 16B | 2.4B | ~10 GB | 128K | `deepseek-coder-v2:16b` |
| Full | 236B | 21B | ~142 GB | 128K | `deepseek-coder-v2:236b` |

- **Architecture:** DeepSeekMoE
- **Lite variant:** Very efficient — 2.4B active params with 128K context
- **Performance:** Outperforms GPT-4 Turbo, Claude 3 Opus on coding benchmarks
- **VRAM (Lite, Q5_K_L):** ~12 GB — fits on RTX 3090/4090
- **Ollama:** Official support, multiple quant options

### DeepSeek-R2 (Upcoming)

- **Status:** Not yet released as of Feb 2026; rumored mid-Feb 2026
- **Specs:** Rumored 1.2T parameters MoE
- **Delay:** Training issues with Huawei Ascend chips
- **Will likely be open-weight consistent with DeepSeek history**

---

## 3. GLM Family (Zhipu AI / Z.AI)

**Creator:** Zhipu AI (Z.AI)
**License:** MIT (all versions from 4.5+)

### GLM-4 (Legacy)

| Model | Parameters | Context | Note |
|-------|-----------|---------|------|
| GLM-4-9B | 9B | 128K | Older generation |
| ChatGLM3-6B | 6B | 32K | Legacy, still on HuggingFace |

- **Text-to-SQL (Spider):** GLM-4-9B achieved 79.0% EX (SPS-SQL framework)

### GLM-4.5

| Model | Total Params | Architecture | Context | Ollama |
|-------|-------------|-------------|---------|--------|
| GLM-4.5 | ~355B (estimated) | MoE | 128K | Available |

- **Benchmark:** Score of 63.2 (3rd among all models)
- **License:** MIT

### GLM-4.6

| Model | Total Params | Architecture | Context | Ollama Tag |
|-------|-------------|-------------|---------|------------|
| GLM-4.6 | 357B | MoE | 200K | `glm-4.6` |
| GLM-4.6V-Flash | — | MoE + Vision | 200K | — |

- **Improvements over 4.5:** 200K context (up from 128K), better coding, tool-use during inference
- **License:** MIT

### GLM-4.7

| Model | Total Params | Active Params | Architecture | VRAM (Q4_K_M) | Context | Ollama Tag |
|-------|-------------|--------------|-------------|---------------|---------|------------|
| GLM-4.7 | 358B | ~35B | MoE | ~130 GB | 200K | `glm-4.7` |
| GLM-4.7-Flash | 30B | ~3.6B | MoE | ~18 GB | 200K | `glm-4.7-flash` |

- **Release:** December 22, 2025 (full), January 2026 (Flash)
- **SWE-bench Verified:** 73.8% (full), 59.2% (Flash) — highest among 30B-class open-source
- **Tool-use (tau2-Bench):** 79.5% — matches Claude 3.5 Sonnet
- **Terminal Bench 2.0:** 41% (full)
- **Flash on RTX 4090:** 120-220 tok/s at Q4, 4K-8K context
- **Flash VRAM:** ~17-23 GB depending on context length (fits 24GB GPUs)
- **Output capacity:** 128K tokens
- **JSON/structured output:** Yes
- **Multilingual:** Strong Chinese + English, reasonable other languages

**GLM-4.7-Flash is a top recommendation for BIAI — excellent coding + tool-use on 24GB GPU**

---

## 4. Kimi K2 Family (Moonshot AI)

**Creator:** Moonshot AI
**License:** Modified MIT License

### Kimi K2

| Model | Total Params | Active Params | Architecture | VRAM | Context | Ollama |
|-------|-------------|--------------|-------------|------|---------|--------|
| K2-Instruct | 1T+ | 32B | MoE | 200+ GB (quantized) | 128K | `kimi-k2` (community) |
| K2-Thinking | 1T+ | 32B | MoE | 200+ GB | 128K | `kimi-k2-thinking` |

- **Training:** 15.5 trillion tokens
- **Special:** K2-Thinking interleaves chain-of-thought with tool calls
- **Consumer GPU:** NOT practical — even quantized needs 200+ GB total memory
- **Ollama:** Available but requires manual patching (LLAMA_MAX_EXPERTS limit)

### Kimi K2.5

| Model | Total Params | VRAM | Context |
|-------|-------------|------|---------|
| K2.5 | ~630 GB full | 240 GB (1.8-bit dynamic) | 128K+ |

- **Release:** January 2026
- **Features:** Native multimodal, agent swarm paradigm
- **Consumer GPU:** NOT practical — minimum 24GB GPU + 256GB RAM
- **Requires at least 4x H200 for full speed**

**Verdict: Too large for typical consumer hardware. Skip for BIAI unless running on server.**

---

## 5. MiniMax Family

**Creator:** MiniMax
**License:** Custom (open-weight)

### MiniMax-Text-01 / MiniMax-M1

| Model | Total Params | Active Params | Architecture | Context | VRAM |
|-------|-------------|--------------|-------------|---------|------|
| MiniMax-Text-01 | 456B | 45.9B | MoE + Lightning Attention | 4M (inference) | ~300+ GB |
| MiniMax-M1 | 456B | 45.9B | MoE + Lightning Attention | 1M | ~300+ GB |

- **Architecture:** 80 transformer layers, 32 experts, Top-2 routing
- **M1:** First open-weight large-scale hybrid-attention reasoning model
- **Lightning Attention:** Custom attention for efficient long-context processing
- **Benchmarks:** Strong on FullStackBench, SWE-bench, MATH, GPQA, TAU-Bench
- **Often outperforms DeepSeek-R1 and Qwen3-235B on agent tasks**

### MiniMax-M2.1 / M2.5

- **M2.5:** Latest version, SOTA in coding and agent tasks
- **Availability:** HuggingFace, API

**Verdict: Too large for consumer hardware (456B params). Excellent but server-only.**

---

## 6. Yi Family (01.AI)

**Creator:** 01.AI (founded by Kai-Fu Lee)
**License:** Apache 2.0

### Yi-Coder

| Size | Parameters | VRAM (Q4_K_M) | Context | Ollama Tag | HumanEval |
|------|-----------|---------------|---------|------------|-----------|
| 1.5B | 1.5B | ~1.5 GB | 128K | `yi-coder:1.5b` | — |
| 9B | 9B | ~6 GB | 128K | `yi-coder:9b` | 85.4% |

- **MBPP:** 73.8% (9B-Chat)
- **NL2SQL:** 45.23% EX (1.5B), much higher for 9B
- **Languages:** 52 programming languages
- **Special:** Official NL2SQL cookbook provided by 01.AI
- **Strengths:** Excellent for full-stack (Python, JS, HTML, SQL), praised as "zippy" in community

### Yi-1.5

| Size | Parameters | VRAM (Q4_K_M) | Context | Ollama |
|------|-----------|---------------|---------|--------|
| 6B | 6B | ~4 GB | 32K | Available |
| 9B | 9B | ~6 GB | 32K | Available |
| 34B | 34B | ~20 GB | 32K | Available |

- **Bilingual:** Chinese + English optimized
- **Note:** Older generation, Yi-Coder is better for SQL/code tasks

### Yi-Lightning / Yi-Large

- **Status:** API-only, not available for local deployment
- **Skip for BIAI**

---

## 7. ERNIE Family (Baidu)

**Creator:** Baidu
**License:** Apache 2.0

### ERNIE 4.5 (Open-sourced July 2025)

| Model | Total Params | Active Params | Architecture | Context | Ollama |
|-------|-------------|--------------|-------------|---------|--------|
| ERNIE-4.5-0.3B | 0.3B | 0.3B | Dense | — | Community GGUF |
| ERNIE-4.5-VL-28B-A3B | 28-30B | 3B | MoE (64E) | — | — |
| ERNIE-4.5-VL-424B-A47B | 424B | 47B | MoE | — | — |

- **10 model variants** total (text + vision)
- **Multimodal:** All variants support text + vision
- **Development toolkit:** ERNIEKit (SFT, LoRA, DPO, quantization)
- **Deployment:** FastDeploy toolkit for inference
- **Ollama:** Only community 0.3B GGUF available; larger models need PaddlePaddle
- **SQL benchmarks:** Not available in public data
- **Framework:** Runs on PaddlePaddle (not standard PyTorch), limited llama.cpp/GGUF support

**Verdict: Limited Ollama/GGUF support makes integration with BIAI difficult. 0.3B too small for SQL.**

---

## 8. InternLM Family (Shanghai AI Lab)

**Creator:** Shanghai AI Laboratory
**License:** Apache 2.0

### InternLM 2.5

| Size | Parameters | VRAM (Q4_K_M) | Context | Ollama Tag |
|------|-----------|---------------|---------|------------|
| 1.8B | 1.8B | ~2 GB | 32K | `internlm/internlm2.5:1.8b` |
| 7B | 7B | ~5 GB | 32K | `internlm/internlm2.5:7b` |
| 20B | 20B | ~12 GB | 32K | `internlm/internlm2.5:20b` |

- **Strengths:** Structured data extraction, HTML-to-JSON conversion
- **Chat-base variants:** Specialized for data extraction tasks
- **Training cost:** 75% less than comparable models (efficient training)

### InternLM3

| Size | Parameters | VRAM (Q4_K_M) | Context | Ollama |
|------|-----------|---------------|---------|--------|
| 8B | 8B | ~5 GB | 32K | Community |

- **Architecture:** Dense transformer
- **Deep thinking mode:** Long chain-of-thought reasoning for complex tasks
- **Surpasses:** Llama3.1-8B and Qwen2.5-7B on reasoning/knowledge tasks
- **Training:** Only 4T tokens (75% cost savings)
- **Ollama:** Community uploads available, not official library

**Verdict: Good general model but no standout SQL capabilities. InternLM2.5-7B useful for data extraction.**

---

## 9. Hunyuan Family (Tencent)

**Creator:** Tencent
**License:** Tencent Hunyuan Community License (open-weight)

| Model | Total Params | Active Params | Architecture | VRAM | HuggingFace |
|-------|-------------|--------------|-------------|------|-------------|
| Hunyuan-Large (MoE-A52B) | 389B | 52B | MoE | Server-class | Yes |
| Hunyuan-A13B | 80B | 13B | MoE (64E) | ~50 GB (Q4) | Yes |
| Hunyuan-MT-7B | 7B | 7B | Dense | ~5 GB | Yes (translation) |

- **Hunyuan-A13B:** Most practical for consumer use at Q4 (~50 GB, needs 2x 24GB GPUs)
- **Ollama:** No official support; GGUF community conversions may exist
- **SQL benchmarks:** Not publicly available
- **Focus:** General-purpose, not code-specialized

**Verdict: Limited local deployment ecosystem. Hunyuan-A13B possible on dual-GPU setups but not ideal for BIAI.**

---

## 10. TeleChat Family (China Telecom)

**Creator:** China Telecom AI (Tele-AI)
**License:** Apache 2.0

| Size | Parameters | Context | HuggingFace |
|------|-----------|---------|-------------|
| 3B | 3B | 8K | `Tele-AI/TeleChat2-3B` |
| 7B | 7B | 8K/32K | `Tele-AI/TeleChat2-7B` |
| 35B | 35B | 8K | `Tele-AI/TeleChat2-35B` |
| 115B | 115B | 8K | `Tele-AI/TeleChat2-115B` |

- **Training:** 10 trillion tokens
- **Function calling:** Supported in 3B/7B/35B
- **Ollama:** No official support; GGUF conversion needed
- **Unique:** Entirely trained on domestic Chinese hardware
- **SQL benchmarks:** Not available
- **Context:** Only 8K default (32K variant for 7B) — SHORT for SQL tasks

**Verdict: Short context window and no Ollama support make it impractical for BIAI.**

---

## 11. Baichuan Family (Baichuan AI)

**Creator:** Baichuan Intelligence
**License:** Apache 2.0 (7B/13B), Custom (larger)

### Baichuan 2

| Size | Parameters | Context | HuggingFace |
|------|-----------|---------|-------------|
| 7B | 7B | 4K | `baichuan-inc/Baichuan2-7B-Chat` |
| 13B | 13B | 4K | `baichuan-inc/Baichuan2-13B-Chat` |

- **Training:** 2.6 trillion tokens
- **Multilingual:** Chinese + English
- **Context:** Only 4K — **TOO SHORT for SQL tasks with schema**
- **Ollama:** Not in official library

### Baichuan-M2-32B

- **Type:** Medical reasoning model (built on Qwen2.5-32B)
- **Not relevant for SQL/analytics**

**Verdict: Outdated (2023), 4K context is insufficient for text-to-SQL. Skip.**

---

## 12. Skywork Family (Inspur/TianGong)

**Creator:** Inspur / TianGong / SkyworkAI
**License:** Apache 2.0 / Custom

### Skywork-OR1 (Open Reasoner)

| Size | Parameters | Architecture | Focus |
|------|-----------|-------------|-------|
| 7B | 7B | Dense (Qwen-based) | Math + Code reasoning |
| 32B | 32.8B | Dense | Math + Code reasoning |

- **Training method:** Large-scale rule-based reinforcement learning
- **Based on:** Qwen2.5-Coder backbone
- **Ollama:** Community uploads available
- **SQL:** No specific benchmarks, code reasoning focused

### Skywork-o1 Open

| Variant | Base Model | Parameters |
|---------|-----------|-----------|
| Skywork-o1-Open-Llama-3.1-8B | Llama 3.1 8B | 8B |
| Skywork-o1-Open-PRM-Qwen-2.5-7B | Qwen 2.5 7B | 7B |
| Skywork-o1-Open-PRM-Qwen-2.5-1.5B | Qwen 2.5 1.5B | 1.5B |

**Verdict: Niche reasoning models, not specialized for SQL. Underlying Qwen models are better choices.**

---

## 13. Aquila Family (BAAI)

**Creator:** Beijing Academy of Artificial Intelligence (BAAI)
**License:** Custom (BAAI Aquila License)

| Size | Parameters | Context | HuggingFace |
|------|-----------|---------|-------------|
| 7B | 7B | 4K | `BAAI/Aquila2-7B` |
| 34B | 34B | 4K | `BAAI/Aquila2-34B` |
| 70B (Experimental) | 70B | 4K | `BAAI/Aquila2-70B-Expr` |

- **Context:** Only 4K — **TOO SHORT**
- **Ollama:** Not available
- **Last major update:** 2024
- **SQL:** No benchmarks available

**Verdict: Outdated, short context, no Ollama support. Skip.**

---

## 14. XVERSE Family

**Creator:** Shenzhen Yuanxiang Technology
**License:** Apache 2.0

| Size | Parameters | Context | HuggingFace |
|------|-----------|---------|-------------|
| 7B | 7B | 16K | `xverse/XVERSE-7B` |
| 13B | 13B | 16K | `xverse/XVERSE-13B` |
| 65B | 65B | 16K | `xverse/XVERSE-65B` |
| MoE-A4.2B | ~MoE | 16K | — |

- **Architecture:** Decoder-only Transformer
- **Context:** 16K (adequate but not great)
- **Last major release:** November 2023
- **Ollama:** Not in official library
- **SQL:** No benchmarks

**Verdict: Outdated, no Ollama support, surpassed by Qwen/DeepSeek. Skip.**

---

## 15. Specialized Text-to-SQL Models

These are purpose-built models fine-tuned specifically for text-to-SQL tasks:

### XiYanSQL-QwenCoder (Alibaba XGenerationLab)

| Size | Base Model | BIRD EX | HuggingFace |
|------|-----------|---------|-------------|
| 3B | Qwen2.5-Coder-3B | — | `XGenerationLab/XiYanSQL-QwenCoder-3B-2504` |
| 7B | Qwen2.5-Coder-7B | — | `XGenerationLab/XiYanSQL-QwenCoder-7B-2504` |
| 14B | Qwen2.5-Coder-14B | ~66% | `XGenerationLab/XiYanSQL-QwenCoder-14B-2504` |
| 32B | Qwen2.5-Coder-32B | **69.03%** | `XGenerationLab/XiYanSQL-QwenCoder-32B-2412` |

- **SOTA:** 69.03% on BIRD test set (single fine-tuned model record)
- **Multi-dialect:** PostgreSQL, MySQL, SQLite
- **100K+ downloads** on ModelScope
- **Can be used as base for further fine-tuning**
- **HIGHLY RELEVANT for BIAI — purpose-built SQL model**

### OmniSQL (RUC/VLDB 2025)

| Size | Base Model | BIRD EX | Spider EX |
|------|-----------|---------|-----------|
| 7B | Qwen2.5-Coder-7B | ~60% | ~85% |
| 14B | Qwen2.5-Coder-14B | ~63% | ~86% |
| 32B | Qwen2.5-Coder-32B | **67.0%** | ~87% |

- **Training data:** SynSQL-2.5M (first million-scale text-to-SQL dataset)
- **Evaluated on 9 datasets** including Spider, BIRD, EHRSQL, ScienceBenchmark
- **OmniSQL-32B:** Competitive with GPT-4o + Distillery pipeline
- **Open source** on GitHub

### Prem-1B-SQL (Prem AI)

| Size | Base Model | BIRD EX |
|------|-----------|---------|
| 1.3B | DeepSeek-1.3B | ~50% (BIRD test) |

- **Smallest practical text-to-SQL model** (1.3B parameters)
- **Surpasses Claude 2 baseline** on BIRD
- **Runs on CPU** when quantized
- **Ollama:** Community upload available
- **Great for resource-constrained environments**

---

## 16. Text-to-SQL Benchmark Summary

### Spider Dataset (Classic, ~200 DBs)

| Model | Size | EX (Dev) | EX (Test) | Method |
|-------|------|----------|-----------|--------|
| Qwen2.5-Coder-7B | 7B | 81.7% | 82.1% | SPS-SQL |
| Llama 3.1-8B | 8B | 80.5% | — | SPS-SQL |
| GLM-4-9B | 9B | — | 79.0% | SPS-SQL |
| OmniSQL-32B | 32B | ~87% | — | Direct |

### BIRD Dataset (Complex, 95 DBs, 33.4 GB)

| Model | Size | EX (Dev) | EX (Test) | Notes |
|-------|------|----------|-----------|-------|
| XiYanSQL-QwenCoder-32B | 32B | ~68.5% | **69.03%** | SOTA single model |
| OmniSQL-32B | 32B | 67.0% | — | MV@16 |
| Prem-1B-SQL | 1.3B | — | ~50% | Smallest practical |
| DeepSeek-V3 (zero-shot) | 671B | ~49% | — | Zero-shot |
| Qwen2.5-Instruct (zero-shot) | various | ~44% | — | Zero-shot |

### Key Insight for BIAI

- **7B models** achieve ~80-82% on Spider (sufficient for most BI queries)
- **32B models** achieve ~67-69% on BIRD (more realistic/complex)
- **Fine-tuned SQL models** (XiYanSQL, OmniSQL) dramatically outperform base models
- **Zero-shot** performance on BIRD is ~44-49% for best models (what BIAI does via Vanna RAG)

---

## 17. Recommendations for BIAI

### Tier 1: Best for BIAI (Consumer GPU 24GB, Ollama)

| Model | Why | VRAM | Ollama Tag | Priority |
|-------|-----|------|------------|----------|
| **Qwen2.5-Coder-7B** | Best text-to-SQL at 7B, 82% Spider EX | ~5 GB | `qwen2.5-coder:7b` | HIGH |
| **Qwen3-Coder-30B-A3B** | Current model, strong agentic coding | ~18 GB | `qwen3-coder:30b` | CURRENT |
| **GLM-4.7-Flash** | 59.2% SWE-bench, fast, 200K context, MIT license | ~18 GB | `glm-4.7-flash` | HIGH |
| **XiYanSQL-QwenCoder-7B** | Purpose-built SQL model, multi-dialect | ~5 GB | Custom GGUF | HIGH |

### Tier 2: Strong Alternatives (24GB GPU)

| Model | Why | VRAM | Ollama Tag |
|-------|-----|------|------------|
| **Qwen2.5-Coder-14B** | Better quality, still fits 24GB at Q4 | ~8 GB | `qwen2.5-coder:14b` |
| **DeepSeek-Coder-V2-Lite** | 2.4B active, 128K context, efficient | ~10 GB | `deepseek-coder-v2:16b` |
| **DeepSeek-R1-Distill-14B** | Reasoning for complex analytical queries | ~9 GB | `deepseek-r1:14b` |
| **Yi-Coder-9B** | 85.4% HumanEval, 128K context, Apache 2.0 | ~6 GB | `yi-coder:9b` |
| **Qwen3-32B** | Thinking mode, strong general + SQL | ~20 GB | `qwen3:32b` |

### Tier 3: Specialized / Server-Class

| Model | Why | VRAM | Note |
|-------|-----|------|------|
| **XiYanSQL-QwenCoder-32B** | SOTA BIRD 69%, purpose-built SQL | ~20 GB | Needs GGUF conversion |
| **OmniSQL-32B** | 67% BIRD, trained on 2.5M SQL pairs | ~20 GB | Research model |
| **Qwen2.5-Coder-32B** | 92.7% HumanEval, strong all-around | ~20 GB | `qwen2.5-coder:32b` |
| **GLM-4.7** (full) | 73.8% SWE-bench, 200K context | ~130 GB | Server only |
| **Prem-1B-SQL** | Runs on CPU, 50% BIRD | ~1 GB | Edge/mobile |

### Tier 4: Not Recommended for BIAI

| Model | Reason |
|-------|--------|
| Kimi K2 / K2.5 | Too large (1T params), impractical for consumer |
| MiniMax-M1/M2 | 456B params, server-only |
| DeepSeek V3/V3.1/V3.2 | 671B+ params, needs server cluster |
| ERNIE 4.5 | PaddlePaddle framework, limited Ollama/GGUF |
| Baichuan 2 | 4K context too short, outdated |
| Aquila2 | 4K context, no Ollama, outdated |
| XVERSE | No Ollama, outdated, 16K context |
| TeleChat2 | 8K context, no Ollama |
| Hunyuan-Large | Server-only, limited tooling |

### Action Items for BIAI

1. **Test XiYanSQL-QwenCoder-7B** — Convert to GGUF, load in Ollama via Modelfile; this is specifically trained for multi-dialect SQL generation and could dramatically improve accuracy
2. **Test GLM-4.7-Flash** — Direct competitor to Qwen3-Coder-30B at same VRAM tier; MIT license, strong tool-use
3. **Test Qwen2.5-Coder-7B** — If wanting to reduce VRAM usage from 18GB to 5GB with minimal SQL quality loss
4. **Consider hybrid approach** — Use Qwen2.5-Coder-7B for simple queries, Qwen3-Coder-30B for complex ones
5. **Monitor DeepSeek-R2** release — May be a game-changer if it maintains open-weight policy

---

## Appendix: Quick VRAM Reference

Approximate VRAM for Q4_K_M quantization on Ollama:

| Parameters | VRAM (Q4_K_M) | GPU Example |
|-----------|---------------|-------------|
| 0.5-1.5B | 1-2 GB | Any GPU |
| 3B | 3 GB | GTX 1060 6GB |
| 7-9B | 5-6 GB | RTX 3060 8GB |
| 14B | 8-10 GB | RTX 3060 12GB |
| 30B MoE (3B active) | 17-20 GB | RTX 3090/4090 24GB |
| 32B dense | 20 GB | RTX 3090/4090 24GB |
| 70B | 40-45 GB | 2x RTX 3090 |
| 235B MoE | 110-145 GB | Server / 4x A100 |
| 670B+ MoE | 170-250 GB | Server cluster |

---

*Research compiled February 2026. Sources include Ollama library, HuggingFace, GitHub repos, BIRD-bench, Spider benchmarks, Papers with Code, and vendor documentation.*
