# vLLM Model Runner V2 Commits Since v0.20.0

> **v0.20.0 released:** 2026-04-27  
> **Range:** `v0.20.0..HEAD` (commit `88d34c6..78743ab`)  
> **Total commits on main since v0.20.0:** ~1,261  
> **MR V2 tagged commits since v0.20.0:** ~40 unique  
> **MR V2 commits total (including before v0.20.0):** ~200+

---

## Table of Contents

1. [Foundation — Before v0.20.0](#foundation--before-v0200)
2. [Core Architecture & Model States (post-v0.20.0)](#core-architecture--model-states-post-v0200)
3. [CUDA Graph & Capture](#cuda-graph--capture)
4. [Speculative Decoding](#speculative-decode)
5. [Sampling & Logprobs](#sampling--logprobs)
6. [Model Support & Enablement](#model-support--enablement)
7. [Bug Fixes](#bug-fixes)
8. [Performance & Optimization](#performance--optimization)
9. [Distributed (DP/PP/EP/KV-Connector)](#distributed-dpppepkv-connector)
10. [Multi-modal & Encoder](#multi-modal--encoder)
11. [Platform Support](#platform-support)
12. [CI & Testing](#ci--testing)
13. [Key Files](#key-files)

---

## Foundation — Before v0.20.0

These commits created the MR V2 infrastructure before v0.20.0 was tagged. They are listed for context — the v0.20.0 tag includes all of these.

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2025-10-10 | `30b44a159` | #25266 | **GPU Model Runner V2 (initial creation)** |
| 2025-10-16 | `e9056056f` | #29221 | Limit cudagraph size to max decode batch size |
| 2025-10-20 | `e9af6ba62` | #29210 | Optimize Gumbel Sampling Kernel |
| 2025-10-21 | `11ea5ec1f` | #29583 | Refactor CudaGraphManager |
| 2025-10-22 | `0aeb698b7` | #29570 | Minor code cleanup |
| 2025-10-23 | `ee80aee1c` | #29576 | Minor cleanup for build_attn_metadata |
| 2025-10-24 | `7f12c82fa` | #29194 | Change bookkeeping logic in preparation for spec decoding |
| 2025-10-25 | `b004c0041` | #29274 | **Support spec decoding [1/N]** |
| 2025-10-28 | `da3222f37` | #29559 | Implement multi-step Eagle with CUDA graph |
| 2025-10-30 | `cc313cb73` | #29300 | Implement Single-step Eagle 1 |
| 2025-10-30 | `97588c4d1` | #29332 | Add minor clarification comments for Eagle |
| 2025-10-31 | `f32c7d6f5` | #29347 | Simplify Eagle bookkeeping with num_rejected |
| 2025-11-01 | `ae0ce1be2` | #29623 | [BugFix] Keep reference to GPU tensors in AsyncOutput |
| 2025-11-04 | `1dcafb3de` | #29703 | Support penalties using bin counts |
| 2025-11-04 | `6afc0ffaf` | #29719 | **Add sample/ directory and reorganize files** |
| 2025-11-04 | `f223ed418` | #29720 | Fuse penalties and temperature into single kernel |
| 2025-11-05 | `ca1b1e729` | #29712 | Refactor prefill token preparation |
| 2025-11-05 | `ec38a7368` | #29756 | Use packed mask for prompt bin counts |
| 2025-11-06 | `cc050558f` | #30029 | Implement get_num_sampled_and_rejected kernel |
| 2025-11-07 | `a238cbd89` | #30171 | Support min-p sampling |
| 2025-11-07 | `d471b2aff` | #30187 | Support num NaNs in logits |
| 2025-11-10 | `3e1ad4065` | #29276 | Add apply_temperature option to gumbel_sample |
| 2025-11-10 | `62d54ba46` | #29275 | Optimize CUDA graph capture time |
| 2025-11-10 | `9e6562a3f` | #30355 | Fix Triton warning on tl.where |
| 2025-11-13 | `6218034dd` | #32348 | Support FlashInfer backend & Fix CUDA Graph bug [1/2] |
| 2025-11-14 | `90c083690` | #32245 | **Refactor Sampler** |
| 2025-11-15 | `19504ac07` | #32132 | Skip building deprecated fields in attn metadata |
| 2025-11-16 | `0a7dd2375` | #32143 | Add support for M-RoPE |
| 2025-11-18 | `ca81811bf` | #32163 | Support logit_bias, allowed_token_ids, min_tokens |
| 2025-11-19 | `dec28688c` | #32209 | Minor refactor for logit_bias |
| 2025-11-20 | `bb1848cd6` | #32546 | Support VLM |
| 2025-11-21 | `43fada536` | #32533 | Refactor `dummy_run` |
| 2025-11-21 | `963dc0b86` | #32535 | Minor optimization for eagle input processing |
| 2025-11-21 | `9a1f16da1` | #32562 | Refactor `update_states` |
| 2025-11-22 | `4147910f1` | #32532 | Move mrope_positions buffer to MRopeState |
| 2025-11-24 | `025a32f9e` | #32083 | Remove async barrier |
| 2025-11-24 | `6c01ffb89` | #32629 | Decouple temperature from penalties |
| 2025-11-25 | `05dc4bfab` | #32624 | Initialized communication buffer for DP |
| 2025-11-25 | `7b7cdce96` | #32625 | Refactor get_cudagraph_and_dp_padding |
| 2025-11-26 | `5e00b561c` | #32820 | Do not error on attention backends |
| 2025-11-28 | `8518b3044` | #32742 | **Add KV Connector support** |
| 2025-11-29 | `46ec6d71c` | #33059 | Use a different stream for grammar bitmask h2d copy |
| 2025-11-29 | `6d86fde09` | #33055 | Remove UvaBufferPool for cpu->gpu copy |
| 2025-11-29 | `a9b53dd43` | #33062 | Add LoRAState to consolidate lora logic |
| 2025-11-30 | `e1da249c9` | #32794 | Minor refactor for `compute_slot_mappings` |
| 2025-12-01 | `edf927bc9` | #33046 | Fix slot_mapping after upstream change |
| 2025-12-02 | `750824324` | #31965 | Simplify BlockTables with UVA |
| 2025-12-02 | `8f121f787` | #32936 | Support auto resolve cudagraph mode/sizes based on attn backend |
| 2025-12-03 | `2f0d3ba74` | #33048 | Minor simplification for finish_requests |
| 2025-12-03 | `387a1898d` | #33433 | Support bad_words sampling param |
| 2025-12-04 | `408195ec5` | #32811 | Refactor Prompt Logprobs |
| 2025-12-05 | `11d3976b8` | #32771 | Support piecewise & mixed cudagraph |
| 2025-12-05 | `ffb3d553c` | #33217 | Init cuda graph pool when necessary |
| 2025-12-06 | `9ab4388cd` | #32709 | Support FLASHINFER_MLA backend |
| 2025-12-08 | `3d66502e1` | #35383 | **Prepare attn metadata in ModelState [2/N]** |
| 2025-12-08 | `c66aa48e9` | #35350 | **Add model states [1/N]** |
| 2025-12-09 | `1a014a0a9` | #35564 | **Move MM encoder to Model States [3/N]** |
| 2025-12-09 | `e3eb146f7` | #35621 | **Add ModelStateInterface [4/N]** |
| 2025-12-09 | `a0a5178ab` | #35774 | **Use ModelState.prepare_attn() for CUDA graph capture [5/N]** |
| 2025-12-10 | `16786da73` | #33251 | Support apply penalty for spec decode |
| 2025-12-10 | `55eed6b7a` | #35790 | **Add WhisperModelState [6/N]** |
| 2025-12-10 | `da543d1ab` | #35628 | Minor refactoring for EncoderRunner |
| 2025-12-11 | `10a5f4d53` | #35930 | Use NamedTuple for `execute_model_state` |
| 2025-12-11 | `72f4d1626` | #35671 | Use block table apis for capture inputs |
| 2025-12-11 | `a3299c3d1` | #35941 | Misc code simplification |
| 2025-12-12 | `4f85bae9d` | #35819 | **Add Design Docs** |
| 2025-12-12 | `467886a0c` | #35917 | Fix inputs_embeds=None bug for MM models |
| 2025-12-13 | `417fd28fb` | #36019 | Fix pooling |
| 2025-12-14 | `483463f73` | #35959 | Extensible CG dispatch rework |
| 2025-12-15 | `2a194ddd7` | #36544 | Add model_state inputs to CUDA graph capture |
| 2025-12-15 | `8d983d7cd` | #36041 | Add initial CI tests |
| 2025-12-16 | `c77181e53` | #35461 | Add probabilistic rejection sampling for spec decoding |
| 2025-12-17 | `86ac7bcf8` | #35120 | Support pooling models |
| 2025-12-17 | `944ffb596` | #35039 | [Minor] Remove redundant `do_spec_decode` field |
| 2025-12-17 | `b1d9f5372` | #35172 | Warmup kernels |
| 2025-12-17 | `b71fbd06e` | #35036 | Support attention group |
| 2025-12-18 | `2cbf9656c` | #35040 | Enable CUDA graph for Eagle3 |
| 2025-12-18 | `a4047d4ea` | #35029 | Support Eagle3 (no CUDA graph) |
| 2025-12-18 | `c645e9a21` | #35070 | Remove propose_draft method |
| 2025-12-19 | `043ac17fc` | #36588 | Fix mm input embeddings lookup |
| 2025-12-19 | `3ed46f374` | #36817 | Add Support for XD-RoPE |
| 2025-12-19 | `b6d5a1729` | #35063 | Fix error-handling |
| 2025-12-20 | `63f49b8bd` | #35162 | Enable piecewise CUDA graphs for pipeline parallelism |
| 2025-12-20 | `a49ea5a58` | #34766 | A bit more PP simplification |
| 2025-12-20 | `be3af2d29` | #34724 | Further simplification for PP |
| 2025-12-21 | `04925b220` | #34666 | Minor cleanup for PP |
| 2025-12-21 | `96efb9148` | #37144 | Fix processed logits in sample() |
| 2025-12-21 | `d00df624f` | #34662 | Minor refactoring for penalties |
| 2025-12-21 | `d74278fb6` | #34667 | Fix unintended CPU-GPU sync in make_dummy |
| 2025-12-21 | `9752da9d9` | #34669 | Minor simplification for BadWordsState |
| 2025-12-22 | `8ccbcda5c` | #36817 | Remove unused warmup_for_prefill method |
| 2025-12-22 | `9ca768c74` | #34563 | Minor cleanup for Sampler |
| 2025-12-22 | `cd32d6f58` | #36929 | Some code simplification |
| 2025-12-23 | `0aeb698b7` | #29570 | Minor code cleanup |
| 2025-12-23 | `2f8b4ce0c` | #36824 | Do not initialize sampler for non-last PP ranks |
| 2025-12-23 | `4e824d1c8` | #38031 | [Minor] Simplify PP logic |
| 2025-12-23 | `95be2a7f2` | #34786 | Minor simplification for DCP |
| 2025-12-24 | `40b2f1c3d` | #34856 | Minor CPU optimizations |
| 2025-12-24 | `c50e105a8` | #34780 | Avoid prepare prefill kernel launch overhead |
| 2025-12-24 | `c878b43b6` | #34849 | Remove unnecessary copies in PW CUDA graph capture |
| 2025-12-26 | `5fcb0cdd6` | #34854 | Use FP32 for Gumbel Noise |
| 2025-12-26 | `b35468652` | #36280 | Fix warmup for pipeline parallel |
| 2025-12-28 | `05dc4bfab` | #32624 | Initialized communication buffer for DP |
| 2025-12-28 | `a73af584f` | #36176 | Fix warmup for very small kvcache and/or blocksizes |
| 2025-12-28 | `ab33d2a62` | #34179 | **Decode Context Parallel (DCP) support** |
| 2025-12-29 | `13025e71e` | #35325 | Add coding style guide |
| 2025-12-29 | `168ee03e1` | #35376 | [Perf] align dummy_run tokens to uniform decode for dp cudagraph |
| 2025-12-29 | `b3e846017` | #36097 | Support multi-modal embeddings for spec decode model |
| 2025-12-30 | `5daf62271` | #38496 | Fuse probabilistic rejection sample kernels |
| 2025-12-30 | `6e956d9ec` | #36520 | Add dummy profile_cudagraph_memory API |
| 2025-12-30 | `85f671b8e` | #37028 | Support Streaming Inputs |
| 2025-12-30 | `a2443de5f` | #34222 | Use pinned memory for write_contents |
| 2025-12-30 | `f088a831d` | #36626 | Use unpadded num_tokens for PW CUDA graph attn metadata |
| 2025-12-31 | `384e4d5f4` | #38311 | Rebuild attention metadata before eagle decode full graph |
| 2026-01-01 | `9efc3bdcd` | #36580 | Fix `_compute_slot_mappings_kernel` for chunked prefill |
| 2026-01-01 | `ce9b1d76c` | #37818 | [MRV2] Skip hidden states allocation for PW CUDA graphs |
| 2026-01-01 | `e80cfe575` | #37645 | [MRV2] Avoid recompilation of `_gather_block_tables_kernel` |
| 2026-01-02 | `a5e9d511d` | #37798 | [MRV2] Use FP64 for Gumbel noise |
| 2026-01-02 | `ccf90ba78` | #37588 | Add full cuda graph support for eagle prefill |
| 2026-01-03 | `40b8363b4` | #37526 | [MRV2] Use fp32 for draft logits |
| 2026-01-03 | `43877a620` | #37830 | [MRV2] Enable PP CUDA graph test |
| 2026-01-03 | `dcee9be95` | #37639 | Fix draft logits not populated during cudagraph replay |
| 2026-01-04 | `04244fd0e` | #37238 | Spec decode rejection sampler greedy support |
| 2026-01-04 | `053f3b630` | #37237 | Spec decode rejection sampler logprobs support |
| 2026-01-04 | `ffb5b32b5` | #37812 | [MRV2] Consider spec decoding in warmup |
| 2026-01-05 | `8f4824b66` | #37932 | Gather multimodal embeddings before draft model postprocess |
| 2026-01-06 | `62095e82c` | #39115 | [BugFix] Fix cuda event reuse race |
| 2026-01-07 | `39474513f` | #37364 | Fix draft attention metadata generation |
| 2026-01-07 | `d7e93e13f` | #37488 | **EPLB Support** |
| 2026-01-08 | `4b53740d7` | #38030 | [MRV2] Fix for DS v3.2 |
| 2026-01-08 | `f186cfe75` | #39098 | [MRV2] Fix hanging issue with DeepSeek V3.2 |
| 2026-01-09 | `5f1de2b14` | #38758 | Add config validation for not-yet-supported features |
| 2026-01-09 | `c32e97602` | #38045 | Enable forcing a specific acceptance rate during rejection sampling |
| 2026-01-10 | `a505cf807` | #42538 | Share identical MTP weights |
| 2026-01-10 | `e9f331d72` | #40746 | [MRV2] Ensure warmup covers prefill path |
| 2026-01-11 | `311c98164` | #38698 | [MRV2][KVConnector] Fix missing build_connector_worker_meta |
| 2026-01-11 | `56e19d7ee` | #39353 | Fix flex attention kv blocks calculation issue |
| 2026-01-12 | `343f65234` | #39951 | [BugFix] fix num_sampled dtype for probabilistic rejection |
| 2026-01-12 | `3bfe55a03` | #39773 | Disable piecewise cudagraph mode fallback for eagle draft decodes |
| 2026-01-12 | `66cc3fa55` | #39937 | Multiple prompt logprobs support |
| 2026-01-13 | `9a6a66f3b` | #39833 | Fix model accuracy regression caused by stale last_sampled_tokens |
| 2026-01-14 | `58b0c78a4` | — | [MRV2] Support expert index capture |

---

## Core Architecture & Model States (post-v0.20.0)

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-04-29 | `51fda1ba4` | #40648 | Fix block table IMA issue |
| 2026-04-30 | `526927be9` | #41285 | Fix v2 compile counter `num_gpu_runner_capture_triggers` and `num_cudagraph_captured` |
| 2026-05-01 | `51295793a` | #40559 | Add `logprob_token_ids` support |
| 2026-05-02 | `e6ff3e9c8` | #41297 | Add `shutdown()` method |
| 2026-05-08 | `7a08b34fb` | #35520 | Support qwen35 / mamba hybrid model |
| 2026-05-14 | `ae4f59f0e` | #39337 | **Oracle for model runner v2 - qwen3 dense model by default [1/N]** |
| 2026-05-15 | `d0921bafe` | #42706 | Unwrap VLM wrappers for EPLB on Model Runner V2 |
| 2026-05-15 | `6147c7022` | #42673 | Support reload weights (sleep mode) |
| 2026-05-17 | `ff712f644` | #42710 | [MRV2][XPU] add Model Runner V2 log |
| 2026-05-19 | `f5d3dc711` | #42783 | Support update_config |
| 2026-05-18 | `69c91d010` | #42955 | Default to MRv1 when a connector is present |
| 2026-05-22 | `47d4407d7` | #35045 | Support sharing kv cache layers |
| 2026-05-23 | `33d7cbe02` | #43233 | Force v1 runner for tests |
| 2026-05-27 | `626fa9bba` | #43808 | Fix blocked reasoning parsing with MRV2 |
| 2026-05-28 | `7e53283b1` | #43732 | Cleanup KVConnector handling with PP + fix MRV2 |
| 2026-05-30 | `27fa5aa3b` | #44050 | Support breakable CUDA graph |
| 2026-06-01 | `4721bb3aa` | #44078 | Remove Eagle's dedicated CUDA graph pool |
| 2026-06-02 | `1edfd09ff` | #43991 | Use actual batch max_seq_len for attn metadata |
| 2026-06-02 | `8a9eb4080` | #43990 | Support zeroing freshly allocated KV blocks for hybrid + fp8 KVCache |
| 2026-06-02 | `da107a59e` | #43458 | Also enable MRV2 for Llama and Mistral dense models |
| 2026-06-02 | `e4a2e584e` | #44338 | Remove assignment of graph_pool in cudagraph_utils |
| 2026-06-03 | `ec8d60bea` | #42472 | Use FlashInfer sampler |
| 2026-06-03 | `91945b6e4` | #44253 | [Spec Decode] Warmup & capture with different attention states for speculator prefill |
| 2026-06-03 | `ceb0111a9` | #43241 | Add Gemma4 MTP support |
| 2026-06-03 | `ffce72c04` | #44568 | Fix v2 `AttributeError: 'CohereASRDecoder' has no embed_input_ids` |
| 2026-06-04 | `0bae1d384` | #44586 | [MRV2][Spec Decode] DFlash |
| 2026-06-04 | `2c27c294c` | #44450 | Fix mrv2 mm lora issue |

---

## CUDA Graph & Capture

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-04-27 | `4c7c69b4e` | #40410 | Skip attention metadata rebuild before draft prefill |
| 2026-05-04 | `e1e4646b0` | #41162 | Rebuild attn metadata between draft decode steps |
| 2026-05-11 | `9af6a5ed7` | #42202 | Fix `seq_lens_cpu_upper_bound` |
| 2026-05-12 | `fe5b4e0fe` | #41035 | Apply synthetic mode to probabilistic rejection sampler |
| 2026-05-14 | `3b6a20478` | #42444 | [DSV4] Ensure lazy attention state initializations happen during cudagraph capture |
| 2026-05-19 | `39bba710b` | #43160 | [BugFix] Fix default-stream CG capture in P/W LoRA case |
| 2026-05-22 | `e15f20258` | #42187 | Avoid pipeline parallel bubbles |
| 2026-05-30 | `27fa5aa3b` | #44050 | Support breakable CUDA graph |
| 2026-06-01 | `4721bb3aa` | #44078 | Remove Eagle's dedicated CUDA graph pool |
| 2026-06-03 | `91945b6e4` | #44253 | Warmup & capture with different attention states for speculator prefill |

---

## Speculative Decode

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-04-26 | `f5f987851` | #40651 | Fix rejection sampling acceptance rate gap vs MRV1 |
| 2026-04-27 | `4c7c69b4e` | #40410 | Skip attention metadata rebuild before draft prefill |
| 2026-05-04 | `e1e4646b0` | #41162 | Rebuild attn metadata between draft decode steps |
| 2026-05-12 | `fe5b4e0fe` | #41035 | Apply synthetic mode to probabilistic rejection sampler |
| 2026-05-26 | `8c94938cf` | #43719 | Fix KV connector handling in spec decode case |
| 2026-06-03 | `ceb0111a9` | #43241 | Add Gemma4 MTP support |
| 2026-06-03 | `91945b6e4` | #44253 | Warmup & capture with different attention states for speculator prefill |
| 2026-06-04 | `0bae1d384` | #44586 | DFlash |

---

## Sampling & Logprobs

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-05-01 | `51295793a` | #40559 | Add `logprob_token_ids` support |
| 2026-05-11 | `d7af6b34d` | #41761 | Bug fix: logprob dtype int64/int32 issue |
| 2026-05-16 | `016259660` | #41775 | FP32 gumbel sampling |
| 2026-05-18 | `e26736973` | #42778 | Fix prompt logprobs calculation `Sizes of tensors must match` error |
| 2026-06-03 | `ec8d60bea` | #42472 | Use FlashInfer sampler |

---

## Bug Fixes

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-04-26 | `f5f987851` | #40651 | Fix rejection sampling acceptance rate gap vs MRV1 |
| 2026-04-29 | `51fda1ba4` | #40648 | Fix block table IMA issue |
| 2026-04-30 | `526927be9` | #41285 | Fix v2 compile counter |
| 2026-05-11 | `9af6a5ed7` | #42202 | Fix `seq_lens_cpu_upper_bound` |
| 2026-05-11 | `d7af6b34d` | #41761 | Bug fix: logprob dtype int64/int32 issue |
| 2026-05-14 | `3b6a20478` | #42444 | [DSV4] Ensure lazy attention state initializations during cudagraph capture |
| 2026-05-15 | `af9616d84` | #42676 | Fix kv_connector `pre_forward` order |
| 2026-05-18 | `e26736973` | #42778 | Fix prompt logprobs calculation error |
| 2026-05-19 | `39bba710b` | #43160 | Fix default-stream CG capture in P/W LoRA case |
| 2026-05-19 | `fba010dd7` | #42766 | Fix KVCache tensor explicit `kernel_block_size` dim |
| 2026-05-20 | `9640970de` | #43139 | Fix lora `Triton Error [CUDA]: device-side assert triggered` |
| 2026-05-26 | `8c94938cf` | #43719 | Fix KV connector handling in spec decode case |
| 2026-05-27 | `626fa9bba` | #43808 | Fix blocked reasoning parsing with MRV2 |
| 2026-06-03 | `ffce72c04` | #44568 | Fix v2 CohereASRDecoder embed_input_ids AttributeError |
| 2026-06-04 | `2c27c294c` | #44450 | Fix mrv2 mm lora issue |

---

## Performance & Optimization

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-05-12 | `422dd0259` | #41411 | Fix prompt logprobs on request eviction during chunked prefill |
| 2026-05-12 | `989c176c0` | #41434 | [Perf][3/n] Eliminate GPU<->CPU syncs in attention impls |
| 2026-05-12 | `bbee53298` | #41429 | [Perf][1/n] Eliminate various GPU<->CPU syncs |
| 2026-05-14 | `4e498b5e5` | #40657 | Improve penalties triton kernel performance |
| 2026-06-03 | `ec8d60bea` | #42472 | Use FlashInfer sampler (performance) |

---

## Distributed (DP/PP/EP/KV-Connector)

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-05-15 | `af9616d84` | #42676 | Fix kv_connector `pre_forward` order |
| 2026-05-18 | `69c91d010` | #42955 | Default to MRv1 when a connector is present |
| 2026-05-22 | `e15f20258` | #42187 | Avoid pipeline parallel bubbles |
| 2026-05-26 | `8c94938cf` | #43719 | Fix KV connector handling in spec decode case |
| 2026-05-28 | `7e53283b1` | #43732 | Cleanup KVConnector handling with PP + fix MRV2 |
| 2026-05-22 | `47d4407d7` | #35045 | Support sharing kv cache layers |
| 2026-05-14 | `3b6a20478` | #42444 | [DSV4] Lazy attention state init during cudagraph capture |
| 2026-05-22 | `0b0ed55302` | — | Add UCX one-shot AllReduce for DP metadata sync |
| 2026-06-03 | `32f34d393` | #44420 | Add index share feature for DSA MTP |
| 2026-06-04 | `e2f7fffab` | — | Enable all dense models for MRV2 |
| 2026-06-04 | `51dda9829` | — | MRV2 migration MOE |
| 2026-06-05 | `700f2490c` | — | MRV2 quantized model |

---

## Multi-modal & Encoder

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-05-08 | `7a08b34fb` | #35520 | Support qwen35 / mamba hybrid model |
| 2026-05-22 | `1223732dd` | #38831 | Support kernel block size in hybrid model |
| 2026-06-02 | `8a9eb4080` | #43990 | Support zeroing freshly allocated KV blocks for hybrid + fp8 KVCache |
| 2026-06-04 | `2c27c294c` | #44450 | Fix mrv2 mm lora issue |

---

## Platform Support

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-05-17 | `ff712f644` | #42710 | [MRV2][XPU] add Model Runner V2 log |
| 2026-05-22 | `65b7a812a` | #43225 | [CPU] Experimentally enable Triton and MRV2 |

---

## CI & Testing

| Date | Commit | PR | Description |
|------|--------|----|-------------|
| 2026-05-22 | `33d7cbe02` | #43233 | Force v1 runner for tests |
| 2026-05-23 | `5ea76fa89` | #43314 | Fix test_lora_with_spec_decode on V2 model runner |

---

## Key Files

The MR V2 architecture lives primarily in these files (relative to `/rebase/vllm`):

```
vllm/v1/worker/gpu/
├── model_runner.py         # Main GPUModelRunner (~3,400 lines)
├── input_batch.py          # InputBatch with Triton kernels
├── states.py               # RequestState slot management
├── attn_utils.py           # Attention metadata construction
├── block_table.py          # Block table management
├── dp_utils.py             # Data-parallel utilities
├── kv_connector.py         # KV cache connector
├── lora/                   # LoRA state management
├── sample/                 # Sampling (GPUModelRunnerSampler, rejection, etc.)
│   ├── __init__.py
│   ├── gpu_model_runner_sampler.py
│   ├── rejection_sample.py
│   └── ...
├── model_states/           # ModelState abstraction layer
│   ├── __init__.py         # init_model_state() factory
│   ├── default.py          # DefaultModelState (~800 lines)
│   ├── whisper.py          # WhisperModelState (reference impl)
│   ├── eagle.py            # Eagle spec-decode state
│   └── ...
├── cudagraph_utils.py      # CUDA graph manager
├── spec_decode/            # Speculative decode
│   ├── eagle.py
│   ├── eagle3.py
│   └── ...
└── ...
```

---

## Summary

- **Total MR V2 commits before v0.20.0:** ~160+ (foundational infrastructure)
- **Total MR V2 tagged commits since v0.20.0:** ~40 unique
- **Total related commits (including file-level changes):** ~70+
- **Key themes since v0.20.0:**
  1. **Stabilization** — fixing V1/V2 acceptance rate gaps, logprob dtype issues, KV connector ordering
  2. **Model coverage expansion** — enabling MRV2 for Llama, Mistral, hybrid models, Qwen3.5, Gemma4 MTP
  3. **Performance** — eliminating GPU↔CPU syncs, FlashInfer sampler, breakable CUDA graph
  4. **Distributed** — PP bubble elimination, KV cache layer sharing, UCX one-shot AllReduce
  5. **CX** — adding `shutdown()`, `update_config`, sleep mode support, config validation
