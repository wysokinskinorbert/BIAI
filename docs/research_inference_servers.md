# Research: Local LLM Inference Servers & Runtime Platforms (February 2026)

> **Context:** BIAI currently uses Ollama for local LLM inference. This document evaluates ALL major local inference servers and platforms to determine if BIAI should support alternative backends for better performance, broader model compatibility, or specialized features.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Platform Comparison Matrix](#platform-comparison-matrix)
3. [Detailed Platform Profiles](#detailed-platform-profiles)
4. [Model Format Comparison](#model-format-comparison)
5. [Quantization Level Comparison](#quantization-level-comparison)
6. [Performance Benchmarks](#performance-benchmarks)
7. [OpenAI-Compatible API Standard](#openai-compatible-api-standard)
8. [Multi-Server Architecture for BIAI](#multi-server-architecture-for-biai)
9. [Recommendations for BIAI](#recommendations-for-biai)

---

## Executive Summary

The local LLM inference landscape in early 2026 has matured significantly. Key findings:

- **Ollama remains the best choice for BIAI's primary use case** (single-user, simple setup, Windows native), but has 10-30% overhead vs raw llama.cpp
- **vLLM and SGLang** lead in high-throughput production scenarios (up to 24x-44x more throughput than llama.cpp under concurrency) but lack native Windows support
- **llama.cpp** is the foundational engine (Ollama wraps it) with the broadest hardware support (CUDA, Vulkan, Metal, CPU)
- **LM Studio** offers the best GUI experience with OpenAI-compatible API
- **LocalAI** is the most complete OpenAI drop-in replacement with multi-backend support
- **Xinference** is the best choice for distributed/multi-model serving
- **ExLlamaV3** provides the fastest consumer GPU inference with EXL3 quantization
- **All major servers now support OpenAI-compatible APIs**, making BIAI's potential multi-backend architecture feasible

### Quick Recommendation for BIAI

| Scenario | Recommended Server | Why |
|----------|-------------------|-----|
| Current setup (single user, Windows) | **Ollama** | Simplest, works great, native Windows |
| Need faster inference | **llama-cpp-python** or **LM Studio** | 10-30% faster than Ollama |
| Production/multi-user | **vLLM** (via WSL/Docker) | Best throughput at scale |
| Maximum model compatibility | **LocalAI** | Supports GGUF, GPTQ, AWQ, SafeTensors |
| Best quality at low VRAM | **ExLlamaV3 + TabbyAPI** | EXL3 preserves 98% accuracy at 4-bit |

---

## Platform Comparison Matrix

| Platform | Formats | GPU Support | API Type | Windows | Setup (1-5) | Stars | Last Release | Spec. Decoding | Multi-GPU |
|----------|---------|-------------|----------|---------|-------------|-------|--------------|----------------|-----------|
| **Ollama** | GGUF | CUDA, ROCm, Metal | OpenAI-compat | Native | 1 | 163k | Feb 2026 | Via llama.cpp | Yes |
| **vLLM** | SafeTensors, GPTQ, AWQ, FP8 | CUDA, ROCm | OpenAI-compat | WSL/Docker | 3 | 70k | Feb 2026 | Yes (EAGLE, Medusa, n-gram) | Yes (TP/PP) |
| **llama.cpp** | GGUF | CUDA, Vulkan, Metal, ROCm, SYCL, CPU | Custom REST | Native | 2 | 85k+ | Feb 2026 | Yes | Yes (split) |
| **LM Studio** | GGUF, MLX | CUDA, Metal, Vulkan | OpenAI-compat | Native | 1 | N/A | 2025 (v0.4) | Via llama.cpp | Limited |
| **Jan.ai** | GGUF | CUDA, Vulkan, Metal | OpenAI-compat | Native | 1 | 30k+ | Jan 2026 | Via llama.cpp | No |
| **GPT4All** | GGUF | CPU primary, GPU optional | Custom REST | Native | 1 | 72k+ | 2025 | No | No |
| **LocalAI** | GGUF, GPTQ, AWQ, SafeTensors | CUDA, ROCm, Vulkan, SYCL, Metal | OpenAI-compat (full) | Docker/Binary | 2 | 30k+ | Jan 2026 (v3.10) | Via backends | Yes |
| **koboldcpp** | GGUF | CUDA, Vulkan, ROCm | KoboldAI + OpenAI | Native (.exe) | 1 | 10k+ | 2025 | Via llama.cpp | Limited |
| **TGI** | SafeTensors, GPTQ | CUDA, ROCm, Gaudi | OpenAI-compat | Docker only | 3 | 10k+ | **MAINTENANCE MODE** | Yes | Yes |
| **SGLang** | SafeTensors, GPTQ, AWQ, FP8 | CUDA | OpenAI-compat | WSL/Docker | 3 | 20k+ | Feb 2026 | Yes | Yes (TP/EP/DP) |
| **ExLlamaV2** | EXL2 | CUDA | OpenAI (via TabbyAPI) | Yes (fork) | 3 | 5k+ | 2025 (v0.3.2) | No | Yes (TP) |
| **ExLlamaV3** | EXL3 | CUDA | OpenAI (via TabbyAPI) | Partial | 3 | 3k+ | 2025 | No | Yes |
| **TabbyAPI** | EXL2, EXL3 | CUDA | OpenAI-compat | Via ExLlama | 3 | 2k+ | 2025 | No | Yes (TP) |
| **Aphrodite** | GPTQ, AWQ, GGUF, EXL2, FP8+ | CUDA | OpenAI-compat | WSL only | 3 | 4k+ | 2025 | Yes | Yes |
| **TensorRT-LLM** | Custom TRT engines | CUDA (NVIDIA only) | Custom + OpenAI | WSL/Native (beta) | 5 | 10k+ | 2025 | Yes | Yes (TP/PP) |
| **ONNX Runtime GenAI** | ONNX | CUDA, DirectML, CPU | Custom | Native | 3 | 3k+ | 2025 | No | No |
| **MLC LLM** | MLC compiled | CUDA, Vulkan, Metal, WebGPU | OpenAI-compat | Native (Vulkan) | 3 | 20k+ | 2025 | Yes | Limited |
| **Candle** | SafeTensors | CUDA, CPU | Custom | Yes (Rust) | 4 | 16k+ | 2025 | No | Yes (NCCL) |
| **Xinference** | All (via backends) | CUDA, ROCm, Metal | OpenAI-compat | Native | 2 | 8k+ | 2025 | Via backends | Yes |
| **OpenLLM** | SafeTensors | CUDA | OpenAI-compat | Likely yes | 3 | 10k+ | 2025 | Via vLLM | Yes |
| **llama-cpp-python** | GGUF | CUDA, Vulkan, Metal, CPU | OpenAI-compat | Native | 2 | 8k+ | 2025 | Via llama.cpp | Yes |
| **PowerInfer** | Custom sparse | CUDA + CPU hybrid | Custom | Unclear | 4 | 8k+ | 2025 | No | CPU-GPU hybrid |
| **ctransformers** | GGML (legacy) | CUDA, CPU | Custom | Native | 2 | 2k+ | 2025 | No | No |
| **AutoGPTQ** | GPTQ | CUDA | Python lib | Yes | 3 | 5k+ | 2025 | No | No |
| **AutoAWQ** | AWQ | CUDA | Python lib | Yes | 3 | 3k+ | 2025 | No | No |
| **RayLLM** | SafeTensors (via vLLM/SGLang) | CUDA, ROCm | OpenAI-compat | Docker | 4 | N/A | 2025 | Via backends | Yes (multi-node) |

---

## Detailed Platform Profiles

### 1. Ollama (Current BIAI Backend)

**Overview:** The most popular local LLM runner. Wraps llama.cpp in a user-friendly CLI with automatic model downloading, GPU detection, and an OpenAI-compatible API.

**Key Strengths:**
- One-command install and model download (`ollama run llama3.1`)
- Native Windows, macOS, Linux support
- Automatic GPU detection and memory management
- 163k GitHub stars, very active community
- Supports 100+ models including Llama 3.x, DeepSeek R1, Qwen 3, Gemma, Phi, etc.
- Concurrent request handling (OLLAMA_NUM_PARALLEL up to 4 by default)
- New model scheduler (Sep 2025): exact memory allocation, 70% fewer OOM crashes

**Limitations:**
- 10-30% overhead vs raw llama.cpp (abstraction layer cost)
- Only supports GGUF format (no GPTQ, AWQ, EXL2)
- Max 4 parallel requests by default (single-user focused)
- Limited advanced features (no speculative decoding config, no tensor parallelism control)
- Cannot use models not in Ollama registry without Modelfile creation

**API:** OpenAI-compatible (`/v1/chat/completions`, `/v1/embeddings`, `/v1/models`) + native API (`/api/generate`, `/api/chat`)

**Python SDK:** `ollama` package, also works with `openai` Python client

**Performance (RTX 4090, 7B model):** ~40-70 tok/s generation, ~200-400 tok/s prompt processing

**Setup Difficulty:** 1/5 (install binary, run command)

---

### 2. vLLM

**Overview:** High-performance production-grade inference engine. Uses PagedAttention for optimal KV cache management. Best for high-concurrency deployments.

**Key Strengths:**
- PagedAttention: 19-27% less memory usage, up to 24x higher throughput vs TGI
- Continuous batching for multi-user workloads
- Speculative decoding (EAGLE, Medusa, n-gram)
- Extensive quantization: GPTQ, AWQ, INT4/8, FP8, AutoRound
- Tensor parallelism and pipeline parallelism for multi-GPU
- 70k GitHub stars, backed by UC Berkeley / PyTorch Foundation
- Bi-weekly release cadence

**Limitations:**
- **No native Windows support** -- requires WSL2 or Docker
- Requires NVIDIA CUDA GPU (no Vulkan/Metal)
- Higher setup complexity (pip install, model paths, config)
- Overkill for single-user scenarios
- Large memory footprint for the engine itself

**API:** Full OpenAI-compatible server (`/v1/chat/completions`, `/v1/completions`, embeddings, tool calling)

**Python SDK:** `vllm` package, `openai` client compatible

**Performance (H100, 8B model):** ~16,000 tok/s (batch), ~75 tok/s single-user; 35x more RPS than llama.cpp at peak load

**Setup Difficulty:** 3/5 (WSL required on Windows, CUDA toolkit, pip install)

---

### 3. llama.cpp

**Overview:** The foundational C/C++ LLM inference engine. Ollama, LM Studio, Jan, koboldcpp all wrap it. Direct use gives maximum performance and control.

**Key Strengths:**
- Broadest hardware support: CUDA, Vulkan, Metal, ROCm, SYCL, CPU (AVX2/AVX512/ARM)
- 10-30% faster than Ollama (no abstraction overhead)
- GGUF format creator -- first to support new quantization methods
- Speculative decoding support
- Multi-GPU via graph splitting
- 85k+ GitHub stars, extremely active (weekly releases)
- Tiny binary, no Python dependency
- Built-in HTTP server (`llama-server`) with OpenAI-compatible endpoints

**Limitations:**
- No auto-download of models (manual HuggingFace download)
- CLI-focused, no GUI
- Only supports GGUF format
- Configuration via command-line flags (many options)
- Less polished concurrent request handling vs vLLM

**API:** Built-in HTTP server with OpenAI-compatible endpoints + native endpoints

**Python SDK:** `llama-cpp-python` (high-quality bindings with OpenAI server)

**Performance (RTX 4090, 7B Q4_K_M):** ~56 tok/s generation, larger context windows than Ollama

**Setup Difficulty:** 2/5 (build from source or use prebuilt binary, download model manually)

---

### 4. LM Studio

**Overview:** Desktop GUI application for running local LLMs. Beautiful interface with built-in model browser, chat UI, and OpenAI-compatible API server.

**Key Strengths:**
- Best GUI experience for local LLMs
- 1000+ models available in built-in browser
- OpenAI-compatible API at `localhost:1234`
- Python, TypeScript, REST SDKs
- Continuous batching and parallel requests (v0.4.0+)
- Native Windows, macOS, Linux

**Limitations:**
- API only runs while GUI is open (not a background service/daemon)
- Not ideal for production/automated pipelines
- Closed-source (free for personal use)
- Limited programmatic control compared to CLI tools
- No speculative decoding config

**API:** OpenAI-compatible (Chat Completions, Embeddings, Models, Responses) + Anthropic-compatible

**Python SDK:** `lmstudio-python`, also `openai` client compatible

**Performance:** Comparable to llama.cpp (same backend)

**Setup Difficulty:** 1/5 (download installer, click run)

---

### 5. Jan.ai

**Overview:** Open-source ChatGPT alternative that runs 100% offline. Desktop app with chat UI, model management, and API server.

**Key Strengths:**
- Open-source (Apache 2.0)
- Clean chat UI, model browser
- MCP (Model Context Protocol) integration for agentic capabilities
- Can connect to cloud APIs (OpenAI, Anthropic, Groq) alongside local models
- OpenAI-compatible API at `localhost:1337`
- Native Windows support

**Limitations:**
- No function calling in API (requires prompt engineering workaround)
- Smaller model library than Ollama/LM Studio
- Less mature than Ollama
- Performance tied to llama.cpp backend

**API:** OpenAI-compatible (basic, no function calling)

**Python SDK:** `openai` client compatible

**Setup Difficulty:** 1/5 (download, install, run)

---

### 6. GPT4All

**Overview:** Nomic AI's local LLM runner. Focus on privacy and accessibility. Runs on CPU without GPU requirement.

**Key Strengths:**
- Runs on CPU (no GPU required, min 8GB RAM)
- Built-in embedding support (Nomic Embed)
- LocalDocs: chat with your documents locally
- Python SDK with C/C++ backend
- Native Windows, macOS, Linux
- 72k+ GitHub stars

**Limitations:**
- Primarily CPU-focused (GPU acceleration limited)
- Smaller model selection
- Slower than GPU-accelerated alternatives
- Limited API features
- Not ideal for high-performance inference

**API:** Local HTTP API, basic OpenAI compatibility

**Python SDK:** `gpt4all` package

**Setup Difficulty:** 1/5

---

### 7. LocalAI

**Overview:** The most complete OpenAI API drop-in replacement. Supports multiple backends (llama.cpp, vLLM, Transformers, ExLlama) and model formats.

**Key Strengths:**
- **Full OpenAI API compatibility** (all endpoints: chat, completions, embeddings, images, audio, TTS, vision)
- Multiple backends: llama.cpp, vLLM, Transformers, ExLlama, ExLlama2
- Supports GGUF, GPTQ, AWQ, SafeTensors, PyTorch formats
- GPU acceleration: CUDA 12/13, ROCm, Vulkan, Metal, SYCL
- Built-in: function calling, Whisper, Stable Diffusion, TTS
- MCP integration, Anthropic API support (v3.10)
- 30k+ GitHub stars

**Limitations:**
- Primarily Docker-based deployment (binary available but less tested)
- Higher resource usage (multiple backends)
- More complex configuration than Ollama
- Windows support mainly through Docker

**API:** Full OpenAI-compatible + Anthropic-compatible (v3.10)

**Python SDK:** `openai` client compatible

**Setup Difficulty:** 2/5 (Docker) or 3/5 (binary)

---

### 8. koboldcpp

**Overview:** Single-file llama.cpp wrapper with KoboldAI API, web UI, and extras like Stable Diffusion integration.

**Key Strengths:**
- Single .exe file (zero install on Windows)
- Built-in web UI with story/chat features
- CUDA and Vulkan GPU support
- KoboldAI API + OpenAI-compatible endpoints
- Stable Diffusion image generation built-in
- Speech-to-text built-in

**Limitations:**
- Focused on creative/RP use cases
- Smaller community than Ollama
- Limited concurrent request handling
- Performance close to but sometimes slightly below llama.cpp

**API:** KoboldAI API + basic OpenAI compatibility

**Setup Difficulty:** 1/5 (download exe, run)

---

### 9. TGI (Text Generation Inference) -- HuggingFace

**Overview:** HuggingFace's production inference server. High-performance with optimized kernels.

**IMPORTANT: In maintenance mode since December 2025.** Only accepting minor bug fixes.

**Key Strengths:**
- Flash Attention, Paged Attention, custom CUDA kernels
- Continuous batching + streaming (SSE)
- Quantization: bitsandbytes, GPTQ
- Prometheus metrics, OpenTelemetry tracing
- 3x more tokens on long prompts than vLLM (single user)

**Limitations:**
- **MAINTENANCE MODE** -- no new features
- Linux only (Docker for Windows)
- Lower throughput than vLLM under high concurrency
- Being superseded by vLLM in HuggingFace ecosystem

**API:** OpenAI-compatible (`/v1/chat/completions`, `/v1/completions`)

**Setup Difficulty:** 3/5 (Docker required)

---

### 10. SGLang

**Overview:** Fastest structured generation runtime. RadixAttention provides 85-95% prefix cache hit rate vs 15-25% for PagedAttention.

**Key Strengths:**
- **Fastest throughput**: up to 6.4x higher than other systems
- RadixAttention: 85-95% cache hit rate for repeated prompts
- Zero-overhead CPU scheduler (<2% CPU overhead)
- Compressed finite state machine for structured outputs
- Speculative decoding, continuous batching, paged attention
- FP4/FP8/INT4/AWQ/GPTQ quantization
- Multi-LoRA batching
- 20k+ GitHub stars, backed by LMSYS (Chatbot Arena creators)

**Limitations:**
- **No native Windows** -- requires WSL2 or Docker (Linux CUDA kernels required)
- SGLang Model Gateway does run on Windows (gateway component only)
- Primarily NVIDIA CUDA only
- Higher setup complexity
- Less mature model compatibility than vLLM

**API:** OpenAI-compatible

**Performance (H100, 8B model):** ~16,215 tok/s (batch); 158,596 tok/s with shared prefix caching

**Setup Difficulty:** 3/5

---

### 11. ExLlamaV2 / ExLlamaV3

**Overview:** Optimized inference library for consumer GPUs. EXL2/EXL3 quantization provides the best quality-per-bit on NVIDIA GPUs.

**Key Strengths:**
- **Fastest consumer GPU inference**: 56+ tok/s on T4 GPU
- EXL2: mixed-precision (2-8 bit per weight), any average bitrate
- EXL3: improved quantization (QTIP-based), slashes VRAM by 50%
- ExLlamaV3 preserves 98% zero-shot accuracy at 4-bit
- Tensor parallelism for multi-GPU
- TabbyAPI provides OpenAI-compatible server

**Limitations:**
- NVIDIA CUDA only (no AMD, no CPU fallback)
- Windows support via dedicated fork (ExLlamaV2-for-windows)
- Smaller model ecosystem (need EXL2/EXL3 quantized models)
- No speculative decoding
- Requires PyTorch + CUDA toolkit

**API:** Via TabbyAPI (OpenAI-compatible, HF model download, embeddings, chat templates)

**Setup Difficulty:** 3/5

---

### 12. TabbyAPI

**Overview:** Official API server for ExLlamaV2/V3. Provides OpenAI-compatible endpoints.

**Key Strengths:**
- Official ExLlama backend server
- OpenAI-compatible API
- HuggingFace model downloading
- Embedding model support
- Jinja2 chat template support
- Handles multi-user requests

**Limitations:**
- Depends on ExLlamaV2/V3
- NVIDIA CUDA only
- Smaller community

**Setup Difficulty:** 3/5 (requires ExLlama setup first)

---

### 13. Aphrodite Engine

**Overview:** vLLM fork by PygmalionAI. Supports the widest range of quantization formats.

**Key Strengths:**
- **Most quantization formats**: AQLM, AutoRound, AWQ, BitNet, Bitsandbytes, EETQ, GGUF, GPTQ, QuIP#, SqueezeLLM, Marlin, FP2-FP12, VPTQ, MXFP4
- Paged Attention (from vLLM)
- Continuous batching
- Speculative decoding
- Multi-LoRA support (Punica)
- OpenAI-compatible API

**Limitations:**
- Linux only (WSL on Windows)
- Based on older vLLM version (may lag behind vLLM updates)
- Focused on creative/RP use cases
- Smaller community than vLLM

**Setup Difficulty:** 3/5 (WSL required on Windows)

---

### 14. TensorRT-LLM (NVIDIA)

**Overview:** NVIDIA's optimized inference library. Maximum performance on NVIDIA GPUs.

**Key Strengths:**
- **Best NVIDIA GPU performance**: up to 8x vs unoptimized, 62.57% faster than llama.cpp
- FP8, FP4, INT4 AWQ, INT8 SmoothQuant
- Custom attention kernels, in-flight batching
- Speculative decoding (up to 3.6x boost)
- Multi-GPU (tensor parallelism, pipeline parallelism)
- 10,000 tok/s on H100
- Native Windows support (beta) for RTX GPUs

**Limitations:**
- **NVIDIA only** (no AMD, no Intel, no CPU)
- Complex setup (model conversion to TRT engines required)
- Windows native is beta quality
- WSL recommended for full functionality
- Not open-source friendly (NVIDIA ecosystem lock-in)

**API:** Custom Python API + OpenAI-compatible via Triton

**Setup Difficulty:** 5/5 (model conversion, CUDA toolkit, complex config)

---

### 15. ONNX Runtime GenAI (Microsoft)

**Overview:** Microsoft's cross-platform inference runtime with DirectML support for any Windows GPU.

**Key Strengths:**
- **DirectML**: works with ANY DirectX 12 GPU (NVIDIA, AMD, Intel)
- Native Windows support (first-class citizen)
- Powers Windows ML, VS Code AI Toolkit, Foundry Local
- ONNX format for cross-platform deployment
- Grammar specification for tool calling
- KV cache management built-in

**Limitations:**
- Requires ONNX model format (conversion needed)
- Fewer models available in ONNX format
- Lower performance than CUDA-native solutions
- Less community support for LLM use cases
- Primarily .NET/C# focused (Python bindings available)

**API:** Custom API (not OpenAI-compatible natively)

**Setup Difficulty:** 3/5 (model conversion, ONNX format)

---

### 16. MLC LLM

**Overview:** Universal deployment engine using ML compilation (Apache TVM). Runs on virtually any hardware.

**Key Strengths:**
- **Truly universal**: Windows, Linux, macOS, iOS, Android, Web (WebGPU)
- Vulkan backend for Windows (works with any GPU)
- OpenAI-compatible API
- Continuous batching, speculative decoding, paged KV
- Compiler optimizations for each target platform
- Python, JavaScript, mobile SDKs

**Limitations:**
- Requires model compilation step for each target
- Smaller model library
- Less community adoption than Ollama/vLLM
- Performance depends on compilation quality
- Vulkan performance lower than native CUDA

**API:** OpenAI-compatible

**Setup Difficulty:** 3/5 (compilation step required)

---

### 17. Xinference

**Overview:** Distributed inference platform supporting multiple backends. Best for multi-model, multi-machine setups.

**Key Strengths:**
- **Native Windows, macOS, Linux**
- Multiple backends: vLLM, SGLang, Transformers, MLX
- 100+ built-in models (DeepSeek, Qwen3, InternVL, etc.)
- OpenAI-compatible API + WebUI
- Distributed inference across multiple machines
- Heterogeneous hardware support (NVIDIA, AMD, Intel, Apple)
- Automatic load balancing

**Limitations:**
- Higher complexity for simple single-model use
- Depends on underlying backends for performance
- Less polished than Ollama for simple use cases

**API:** OpenAI-compatible + RPC + CLI + WebUI

**Setup Difficulty:** 2/5 (pip install, simple start)

---

### 18. OpenLLM (BentoML)

**Overview:** BentoML's LLM serving framework. Run any open-source LLM as OpenAI-compatible API.

**Key Strengths:**
- One-command LLM serving
- 3-5x throughput vs raw HuggingFace
- Continuous batching, prefix caching
- BentoCloud integration for cloud deployment
- OpenAI-compatible API
- Built-in chat UI

**Limitations:**
- Primarily cloud/production focused
- Smaller model selection
- Depends on BentoML ecosystem
- Windows support unclear

**API:** OpenAI-compatible

**Setup Difficulty:** 3/5

---

### 19. llama-cpp-python

**Overview:** High-quality Python bindings for llama.cpp with OpenAI-compatible API server.

**Key Strengths:**
- **Direct llama.cpp performance** (no Ollama overhead)
- Drop-in OpenAI API replacement
- Function calling support
- Constrained output (JSON schema, grammar)
- Multi-model routing via config
- HuggingFace Hub integration (from_pretrained)
- Native Windows support

**Limitations:**
- Requires manual model downloading
- Python dependency (vs standalone binary)
- Less user-friendly than Ollama
- GGUF only

**API:** Full OpenAI-compatible (`/v1/chat/completions`, function calling, JSON mode)

**Setup Difficulty:** 2/5 (pip install, download model)

---

### 20. PowerInfer

**Overview:** Research project for sparse LLM inference. Exploits neuron activation locality for CPU-GPU hybrid execution.

**Key Strengths:**
- Run 175B models on single RTX 4090 (13-29 tok/s)
- 6x faster than llama.cpp for small batch sizes
- Only 18% slower than A100 server GPU
- Innovative sparse activation approach

**Limitations:**
- Research prototype (not production-ready)
- Requires pre-profiled models (neuron activation maps)
- Limited model support
- Windows support unclear
- Development pace slowed

**Setup Difficulty:** 4/5

---

### 21. ctransformers (Legacy)

**Overview:** Python bindings for GGML models. Being deprecated in favor of llama-cpp-python.

**Status:** Effectively deprecated. LangChain deprecated its integration in October 2025. Use llama-cpp-python instead.

---

### 22. AutoGPTQ / AutoAWQ

**Overview:** Quantization libraries for GPTQ and AWQ formats. Primarily used for model preparation, not serving.

**AutoGPTQ:**
- GPTQ one-shot weight quantization
- 2/3/4/8-bit support
- Integrated with HuggingFace Transformers
- Best for GPU inference flexibility

**AutoAWQ:**
- Activation-aware weight quantization
- Protects salient weights (~1% of weights)
- Near full-precision accuracy at 4-bit
- Faster than GPTQ with similar or better quality
- Limited newer architecture support (no Gemma, DeciLM)

**Note:** These are quantization tools, not inference servers. Models quantized with them are served via vLLM, Aphrodite, ExLlama, etc.

---

### 23. RayLLM / Ray Serve LLM

**Overview:** Distributed LLM serving on Ray framework. Best for multi-node, enterprise-scale deployments.

**Key Strengths:**
- Multi-node inference (pipeline + tensor + expert + data parallelism)
- Prefix caching with cache-aware routing
- Autoscaling based on request load
- Supports vLLM and SGLang as backends

**Limitations:**
- Enterprise/cloud focused (overkill for local)
- Complex setup (Ray cluster required)
- Docker/Linux preferred
- High resource overhead

**Setup Difficulty:** 4/5

---

### 24. Candle (HuggingFace)

**Overview:** Minimalist ML framework in Rust. Provides fast, safe inference with low memory footprint.

**Key Strengths:**
- Rust-based: memory safety, no GC overhead
- WASM support (run in browser)
- CUDA + CPU backends
- Supports LLaMA, Falcon, Mistral, Phi, etc.
- LoRA support
- Foundation for candle-vllm (Rust vLLM)

**Limitations:**
- Rust expertise required for customization
- Smaller ecosystem
- No built-in API server (need candle-vllm)
- Fewer pre-quantized models

**Setup Difficulty:** 4/5 (Rust toolchain required)

---

## Model Format Comparison

| Format | Type | Created By | Best For | Quality (vs FP16) | Speed | VRAM | Servers |
|--------|------|------------|----------|-------------------|-------|------|---------|
| **GGUF** | File format + quant | llama.cpp | Universal, CPU+GPU | 92% (Q4_K_M) | Medium | Low | Ollama, llama.cpp, LM Studio, Jan, LocalAI, koboldcpp |
| **GPTQ** | Quant method | Frantar et al. | GPU inference | 90% (4-bit) | Fast (GPU) | Medium | vLLM, Aphrodite, ExLlama, LocalAI, TGI |
| **AWQ** | Quant method | MIT/Song | Max quality 4-bit | 95% (4-bit) | Fastest (Marlin) | Medium | vLLM, Aphrodite, LocalAI, SGLang |
| **EXL2** | Quant method | turboderp | Consumer GPU | 94% (4-bit avg) | Very Fast | Low | ExLlamaV2, TabbyAPI, Aphrodite |
| **EXL3** | Quant method | turboderp | Consumer GPU (new) | 98% (4-bit avg) | Fastest (CUDA) | Very Low | ExLlamaV3, TabbyAPI |
| **SafeTensors** | File format | HuggingFace | Full precision | 100% (FP16/BF16) | Baseline | High | vLLM, TGI, SGLang, Transformers |
| **FP8** | Quant level | NVIDIA | Datacenter GPU | 99% | Very Fast | Medium | vLLM, TensorRT-LLM, SGLang |
| **ONNX** | Model format | Microsoft | Cross-platform | Varies | Fast (DirectML) | Varies | ONNX Runtime GenAI |
| **MLC** | Compiled format | MLC.ai | Universal deployment | Varies | Fast | Varies | MLC LLM |

### Key Takeaways:
- **GGUF** is the most universal format (works everywhere), but not the fastest on GPU
- **AWQ** provides the best quality at 4-bit quantization (95% vs 90% GPTQ)
- **EXL3** is the newest format with 98% accuracy at 4-bit (but NVIDIA only)
- **SafeTensors** is required for vLLM/SGLang (full precision, highest VRAM)
- **FP8** is the sweet spot for datacenter GPUs (99% quality, fast)

---

## Quantization Level Comparison (GGUF)

| Quant Level | Bits/Weight | Size (7B model) | Perplexity vs FP16 | Quality Assessment | RAM/VRAM | Recommended Use |
|-------------|-------------|------------------|---------------------|-------------------|----------|-----------------|
| **Q2_K** | ~2.5 | ~2.7 GB | +1.5-2.0 ppl | Significant degradation | Very Low | Extreme constraints only |
| **Q3_K_S** | ~3.0 | ~3.0 GB | +0.55 ppl (8.96 for Llama-3.1-8B) | Noticeable quality loss | Very Low | When VRAM is critical |
| **Q3_K_M** | ~3.4 | ~3.3 GB | +0.24 ppl | High quality loss but usable | Low | Tight VRAM budget |
| **Q4_K_S** | ~4.0 | ~3.9 GB | +0.08 ppl | Good quality | Low | Good balance |
| **Q4_K_M** | ~4.5 | ~4.1 GB | +0.05 ppl | **Recommended** balance | Medium-Low | **Best general-purpose** |
| **Q5_K_S** | ~5.0 | ~4.8 GB | +0.04 ppl | Very good quality | Medium | Quality-conscious |
| **Q5_K_M** | ~5.3 | ~5.1 GB | +0.03 ppl | **Recommended** for quality | Medium | **Best quality/size ratio** |
| **Q6_K** | ~6.0 | ~5.5 GB | +0.01 ppl | Near-original quality | Medium-High | Quality priority |
| **Q8_0** | ~8.0 | ~7.2 GB | ~0 ppl | Indistinguishable from FP16 | High | When VRAM allows |
| **FP16** | 16.0 | ~14 GB | Baseline (7.32 for Llama-3.1-8B) | Original quality | Very High | Reference/fine-tuning |

### Recommendations:
- **Q4_K_M**: Best general-purpose quant. 92% quality, fits most GPUs. This is what Ollama uses by default.
- **Q5_K_M**: Best quality/size ratio. Use when you have 1-2 GB extra VRAM.
- **Q6_K**: Near-original quality. Use for critical tasks (SQL generation, code).
- **Q8_0**: Use when VRAM is not a constraint. Practically identical to FP16.
- **Q3_K_M and below**: Only when absolutely necessary. Noticeable quality degradation.

**Important caveat:** Perplexity is not a complete predictor of downstream behavior. Different quants with similar perplexity can exhibit different performance on instruction-following, reasoning, and safety tasks.

---

## Performance Benchmarks

### Single-User Throughput (Tokens/sec generation, ~7B model, RTX 4090)

| Server | tok/s | Notes |
|--------|-------|-------|
| ExLlamaV3 (EXL3 4-bit) | ~70-80 | Fastest consumer GPU |
| ExLlamaV2 (EXL2 4-bit) | ~56 | Very fast on NVIDIA |
| llama.cpp (Q4_K_M) | ~50-60 | Baseline performance |
| Ollama (Q4_K_M) | ~40-50 | 10-30% overhead vs llama.cpp |
| vLLM (FP16) | ~45-55 | Optimized for batch, not single-user |

### High-Concurrency Throughput (H100 GPU, 8B model, many concurrent users)

| Server | tok/s (total) | Relative |
|--------|---------------|----------|
| SGLang | 16,215 | **1.29x vLLM** |
| vLLM | 12,553 | 1.0x baseline |
| TGI | ~5,000 | 0.4x vLLM |
| llama.cpp | ~350 | 0.03x vLLM |
| Ollama | ~300 | 0.02x vLLM |

### Shared Prefix Caching (SGLang specialty)

| Server | Cache Hit Rate | tok/s |
|--------|---------------|-------|
| SGLang (RadixAttention) | 85-95% | 158,596 |
| vLLM (PagedAttention) | 15-25% | ~50,000 |

### Multi-GPU Scaling (vLLM, 2x GPU)

vLLM delivers 35x more RPS and 44x more total output tokens than llama.cpp at peak load with multi-GPU tensor parallelism.

---

## OpenAI-Compatible API Standard

The OpenAI API has become the de facto standard for LLM inference APIs. Most local servers now implement at least the core endpoints:

### Core Endpoints (widely supported)

| Endpoint | Description | Supported By |
|----------|-------------|-------------|
| `POST /v1/chat/completions` | Chat with model | ALL major servers |
| `POST /v1/completions` | Text completion | Most servers |
| `POST /v1/embeddings` | Generate embeddings | Ollama, vLLM, LocalAI, LM Studio |
| `GET /v1/models` | List available models | ALL major servers |

### Advanced Features (partial support)

| Feature | Description | Supported By |
|---------|-------------|-------------|
| Streaming (SSE) | Token-by-token output | ALL major servers |
| Function/Tool Calling | Structured tool use | vLLM, Ollama, LocalAI, LM Studio, SGLang |
| JSON Mode | Constrained JSON output | vLLM, Ollama, llama-cpp-python, SGLang |
| Vision (multimodal) | Image input | Ollama, vLLM, LocalAI, SGLang |
| Audio (Whisper) | Speech-to-text | LocalAI |
| TTS | Text-to-speech | LocalAI |
| Image Generation | Stable Diffusion | LocalAI, koboldcpp |

### Compatibility Matrix for BIAI

Since BIAI uses the Ollama Python client, switching to any OpenAI-compatible server requires minimal code changes:

```python
# Current BIAI (Ollama native)
import ollama
response = ollama.chat(model="qwen2.5-coder:7b", messages=[...])

# Alternative: Any OpenAI-compatible server
from openai import OpenAI
client = OpenAI(base_url="http://localhost:PORT/v1", api_key="not-needed")
response = client.chat.completions.create(model="model-name", messages=[...])
```

**BIAI already uses Vanna.ai which uses the Ollama class internally.** To support other backends, BIAI would need to modify `vanna_client.py` to use the OpenAI client instead of the Ollama-specific client when a non-Ollama backend is configured.

---

## Multi-Server Architecture for BIAI

### Can BIAI use multiple inference servers?

**Yes, absolutely.** Several approaches:

### Approach 1: Router/Proxy Pattern
Use a lightweight proxy (like Llama-Swap) to route requests to different backends based on model or task type:

```
BIAI App
  |
  v
Llama-Swap Proxy (localhost:8080)
  |--- Ollama (localhost:11434) -- simple queries, embeddings
  |--- vLLM (localhost:8000)   -- complex SQL generation (via WSL)
  |--- TabbyAPI (localhost:5000) -- high-quality code models (EXL3)
```

### Approach 2: Backend Abstraction in BIAI
Add a configuration option to BIAI that selects the inference backend:

```python
# settings.py
INFERENCE_BACKEND = "ollama"  # or "openai_compat"
INFERENCE_URL = "http://localhost:11434"  # Ollama default
# INFERENCE_URL = "http://localhost:8000/v1"  # vLLM
# INFERENCE_URL = "http://localhost:1234/v1"  # LM Studio
```

### Approach 3: Xinference as Unified Platform
Deploy Xinference which manages multiple backends internally:

```
BIAI App
  |
  v
Xinference (localhost:9997)
  |--- vLLM backend (for SQL models)
  |--- llama.cpp backend (for embeddings)
  |--- Transformers backend (for specialized models)
```

### Recommended Architecture for BIAI

**Phase 1 (Current):** Keep Ollama as primary backend. It works well for single-user.

**Phase 2 (Enhancement):** Add OpenAI-compatible backend support in `vanna_client.py`. This allows users to point BIAI at any compatible server. Minimal code change, maximum flexibility.

**Phase 3 (Advanced):** For multi-user deployment, consider vLLM (via Docker/WSL) or Xinference for managed multi-backend serving.

---

## Recommendations for BIAI

### Immediate (No code changes)
1. **Stay with Ollama** for development and single-user use
2. **Use Q5_K_M or Q6_K quantization** for SQL generation models (quality matters more than speed for SQL)
3. Consider **LM Studio** as a user-friendly alternative for non-technical users

### Short-term (Minor code changes)
4. **Add OpenAI-compatible backend support** in `vanna_client.py` -- this is a ~20 line change that unlocks ALL compatible servers
5. **Test llama-cpp-python** as a direct replacement for Ollama (10-30% faster, same GGUF models)
6. **Evaluate EXL3 models via TabbyAPI** if users have NVIDIA GPUs and want maximum quality

### Long-term (Significant changes)
7. **Consider vLLM for multi-user deployments** (Docker on Windows via WSL2)
8. **Evaluate Xinference** for enterprise deployments requiring multiple models
9. **Monitor SGLang** -- if/when Windows support improves, it could be the fastest option for structured SQL output generation (compressed FSM for constrained decoding)

### Models Not Available on Ollama
Some high-quality models may only be available in GPTQ/AWQ/EXL2 formats on HuggingFace. With OpenAI-compatible backend support, BIAI users could use:
- **vLLM** to serve GPTQ/AWQ models
- **TabbyAPI** to serve EXL2/EXL3 models
- **LocalAI** to serve any format
- **Xinference** to manage multiple model formats

This gives BIAI access to the entire HuggingFace model ecosystem, not just Ollama's curated library.

---

## Key Platforms to Watch in 2026

1. **SGLang** -- Fastest growing, best for structured outputs (perfect for SQL)
2. **ExLlamaV3** -- Best quality-per-bit on consumer GPUs
3. **vLLM V2** -- Major rewrite in progress, even faster
4. **LocalAI** -- Most complete OpenAI replacement, adding Anthropic support
5. **Xinference** -- Best multi-model management platform

---

*Document generated: February 2026*
*Research by: BIAI Infrastructure Research Team*
