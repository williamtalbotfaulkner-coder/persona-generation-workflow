# Super Factory Agent Runner (Automation Blueprint)

This is a minimal **agent-style orchestration** pattern for running the full workflow end-to-end:
- load personas and reference images,
- build prompts per lane and shot recipe,
- enqueue ComfyUI jobs via API,
- record metadata and outputs,
- route failures to a repair queue.

Use this blueprint to wire your own runner on RunPod/RTX 5090.

---

## 1) Responsibilities (Agent Loop)

1. **Ingest** persona + references for a character.
2. **Generate prompt rows** for all lanes + bundle recipes.
3. **Enqueue jobs** to ComfyUI `/prompt`.
4. **Monitor queue** and collect outputs.
5. **Validate** identity drift/artifacts (basic checks or human QA).
6. **Repair** failed outputs with a lower-denoise, stronger FaceID pass.
7. **Persist** metadata manifest and output file mapping.

---

## 2) Data Contracts

### 2.1 Prompt table (CSV/YAML)
Each row represents one output image.

Required fields:
- character_id, lane, shot_type, bundle_id, frame_index
- positive_prompt, negative_prompt
- seed, steps, cfg, sampler, checkpoint, resolution
- ref_images (3 paths)
- face_id_weight

### 2.2 Output manifest (JSON/CSV)
Persist for every successful image:
- output_path
- all prompt table fields
- timestamps
- workflow_hash

---

## 3) Runtime Topology

- **ComfyUI** running with the master JSON workflow.
- **Agent runner** (Python) controlling job queue.
- **Shared storage** for outputs + manifests.

---

## 4) Failure & Repair Policy

- Reject if: face mismatch, anatomy break, strong artifacting, blurred eyes.
- Repair pass:
  - reduce denoise (0.20–0.35)
  - increase FaceID weight (e.g., +0.05–0.10)
  - optional inpaint for hands/face

---

## 5) Minimal Agent Skeleton

See `tools/agent_runner.py` for a starter implementation.
