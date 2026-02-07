# Super Factory - OpenAI: Reusable ComfyUI Master Workflow (Z-Image)

This template is a **single reusable production workflow** for generating lifelike influencer-style model content with:
- high consistency,
- high photoreal quality,
- balanced speed/quality on a **24 GB RunPod GPU**,
- and scalable batch automation for 20 characters.

---

## 1) Production Target

Per character:
- 4 lanes: `SFW`, `Suggestive`, `Spicy`, `NSFW`
- Per lane output target:
  - `80` one-offs
  - `10 bundles x 3 = 30`
  - `10 bundles x 5 = 50`
  - `4 bundles x 10 = 40`
- Total per lane: `200`
- Total per character: `800`

Phase 1 target:
- `20` characters x `800` = **16,000 final images**.

---

## 2) Folder Standard (Reusable Template)

```text
project_root/
  personas/
    model_001/
      persona.md
      refs/
        ref_01.png
        ref_02.png
        ref_03.png
    model_002/
      ...
  prompts/
    lane_taxonomy.yaml
    shot_catalog.yaml
    negative_global.txt
  workflows/
    super_factory_openai_zimage_master.json
  outputs/
    model_001/
      sfw/
      suggestive/
      spicy/
      nsfw/
  logs/
    generation_log.csv
```

---

## 3) ComfyUI Node Graph (Single Master Flow)

Use one graph with a lane switch and style/pose sampler branch. Keep all character identity settings upstream.

### 3.1 Inputs
1. **Persona text input** (from `persona.md`)
2. **3 core references** (`ref_01/02/03`)
3. **Lane selector** (`sfw|suggestive|spicy|nsfw`)
4. **Shot recipe selector** (`one_off`, `bundle3`, `bundle5`, `bundle10`)
5. **Seed policy** (`fixed_id_seed + varied_scene_seed`)

### 3.2 Core identity branch (consistency-first)
1. `Load Checkpoint` -> `z-image-base`
2. `CLIP Text Encode` (identity prompt from persona parser)
3. `IPAdapter FaceID / InstantID` with 3 references (weighted blend)
4. Optional `PuLID` or `ReActor` identity lock (if available)
5. `KSampler` (identity pass)

### 3.3 Quality-speed branch
- **Default**: `z-image-base` for keyframes + identity-sensitive shots.
- **Fast branch**: `z-image-turbo` for volume shots where pose/context variation is high and micro-detail is less critical.
- Use a Boolean/routing node to choose branch by shot type.

### 3.4 Detail refinement
1. Latent upscale x1.5~x2 (or tiled diffusion upscale)
2. Refiner/detail pass (same model family for coherence)
3. Face restore (subtle; avoid plastic skin)
4. Final upscaler (4x-UltraSharp or ESRGAN variant)
5. Output resize to delivery format (e.g., 1440x2160 or 2048x3072)

### 3.5 Safety/lane conditioning
- Lane-specific prompt injector node:
  - SFW: conservative wardrobe/poses
  - Suggestive: mild sensuality, no explicit nudity
  - Spicy: elevated sensual cues, controlled explicitness
  - NSFW: explicit lane only if policy/legal constraints are met
- Lane-specific negative prompts to prevent artifacts and “AI plastic” look.

---

## 4) Recommended Parameter Baselines (24 GB VRAM)

### 4.1 Identity Keyframe (z-image-base)
- Resolution: `832x1216` or `1024x1536`
- Steps: `28-36`
- CFG: `4.5-6.0`
- Sampler: `DPM++ 2M Karras` (or best local benchmark)
- Denoise for img2img passes: `0.25-0.45`

### 4.2 Volume Pass (z-image-turbo)
- Resolution: `768x1152` or `832x1216`
- Steps: `8-16`
- CFG: `2.0-4.0`
- Seed strategy: fixed identity seed block + per-shot seed offset

### 4.3 Upscale/Refine
- Latent upscale factor: `1.5-2.0`
- Refine steps: `12-20`
- Final sharpen: mild only (avoid overprocessed skin)

---

## 4.4 RTX 5090 Setup Notes (High-VRAM Single GPU)

When running on an RTX 5090, prioritize **stability + throughput** while keeping the workflow identical:
- **Drivers/Runtime**: Use a recent NVIDIA driver and a matching CUDA runtime (ComfyUI + PyTorch nightly if required for the latest architecture support).
- **VRAM headroom**: Prefer higher base resolution (e.g., 1024x1536 for keyframes) and keep refiner/latent upscale in the same graph.
- **Batching**: Increase batch size for volume shots on `z-image-turbo` (e.g., batch=2–4) but keep keyframes at batch=1 to avoid identity drift.
- **Memory optimizations**: Enable xFormers/SDPA as supported, keep VAE in GPU, and use tiled upscalers only if you hit VRAM spikes.
- **Seed determinism**: For reproducibility at scale, lock identity seeds and store per-shot seed offsets.

If you hit instability after driver updates, pin ComfyUI and PyTorch to a known-good version and only upgrade one component at a time.

---

## 5) Prompt Architecture (Template Slots)

Use a structured prompt schema to keep output consistent while supporting automation.

```text
[IDENTITY_CORE]
[FACE_ANCHORS]
[BODY_ANCHORS]
[WARDROBE_BY_LANE]
[SCENE_CONTEXT]
[LIGHTING]
[CAMERA]
[SHOT_INTENT]
[REALISM_QUALIFIERS]
[LANE_RULES]
```

### 5.1 Identity core example
- immutable traits from persona: age band, facial geometry, skin tone, hair, signature markers
- disallow drift: ethnicity swaps, age drift, body-proportion drift

### 5.2 Realism qualifiers
Use terms such as:
- natural skin texture, realistic pores, subtle asymmetry,
- physically plausible lighting,
- lens-consistent depth of field,
- editorial photography look.

Avoid over-tokening with repetitive “ultra realistic” phrases; prioritize concrete camera/lighting cues.

---

## 6) Negative Prompt Stack (Global)

Use global negatives + lane-specific negatives.

Global negative themes:
- waxy skin, plastic texture, CGI look, over-smoothing
- extra fingers/limbs, warped anatomy, duplicate facial features
- blurry iris, melted teeth, asymmetrical eyes, broken hands
- watermark, text artifacts, logo marks, compression blocks

Keep negatives concise; too long negatives can suppress good detail.

---

## 7) Automated Generation Strategy (Balanced Quality + Speed)

### Stage A: Character calibration (first 20-40 images/model)
- Run only `z-image-base` + identity locks.
- Build accepted identity seeds + pose families.
- Save best presets as `model profile`.

### Stage B: Lane production
- One-offs: mixed base/turbo policy (quality gate enabled)
- Bundles of 3/5/10: fixed scene continuity variables:
  - same location,
  - coherent wardrobe progression,
  - controlled pose arc,
  - gradual camera angle shifts.

### Stage C: Quality gate + repair queue
- Reject frames with identity drift/artifacts.
- Auto-send rejected images to repair branch:
  - lower denoise,
  - stronger face-id weight,
  - hand/face inpaint pass.

---

## 8) Bundle Logic (Narrative Micro-Sequences)

For bundle generation:
- **Bundle-3**: intro -> mid -> close detail
- **Bundle-5**: wider emotional arc and varied framing
- **Bundle-10**: mini storyboard with wardrobe/background continuity

Enforce continuity anchors in prompt metadata:
- `scene_id`, `outfit_id`, `lighting_id`, `mood_id`, `camera_family`.

---

## 9) Suggested Throughput Planning

Per character total = 800 finals.
If acceptance rate is 70%, gross generations needed:
- `800 / 0.70 = ~1143`

For 20 characters:
- `~22,860` gross renders.

Batch design suggestion:
- Daywise blocks per character:
  - calibration block,
  - lane block (SFW -> NSFW),
  - QA + repair block.

---

## 10) ComfyUI Implementation Notes

- Keep all lane logic in one JSON workflow and pass runtime variables from a prompt table.
- Use queue prompts via API script (Python) for unattended generation.
- Persist metadata per image:
  - character ID, lane, shot type, seed, model checkpoint, CFG, steps.
- Save every successful config as reusable preset for future characters.

---

## 10.1 Automation: Running at Scale (Unattended)

**Goal:** enqueue thousands of renders per character with minimal manual input.

### A) Workflow + prompt table approach (recommended)
1. Export your **single master workflow** as JSON from ComfyUI.
2. Create a **prompt table** (CSV/YAML) with one row per output:
   - character_id, lane, shot_type, bundle_id, frame_index
   - positive prompt, negative prompt
   - seed, steps, cfg, sampler, checkpoint, resolution
3. Use the ComfyUI API to enqueue jobs in batches.

**Typical control flow:**
- Load a row from the prompt table.
- Patch the workflow JSON (swap prompt/seed/params).
- POST to `/prompt` on the ComfyUI server.
- Poll `/queue` until done, then move to next batch.

### B) Batch strategy
- **Keyframes first**: run the high-quality keyframes to lock identity/seed.
- **Volume second**: switch to `z-image-turbo` batch mode for speed.
- **Repair queue**: route failed outputs to a lower denoise + stronger FaceID pass.

### C) Metadata + reproducibility
Store a manifest per image:
- character_id, lane, shot_type, bundle_id, frame_index
- seed, steps, cfg, sampler, checkpoint
- face-id weight, ref images used
- prompt hash (to detect drift)

### D) Minimal automation skeleton (pseudocode)
```python
for row in prompt_table:
    workflow = load_json("super_factory_openai_zimage_master.json")
    workflow = patch_workflow(workflow, row)  # prompts, seed, cfg, steps, model, res
    post("/prompt", workflow)
    wait_for_queue_empty()
    save_metadata(row, output_paths)
```

---

## 11) Master Checklist (Per New Character)

1. Ingest `persona.md` and 3 references.
2. Run identity calibration and lock seed/profile.
3. Validate 10-image pilot in each lane.
4. Generate one-offs.
5. Generate bundles (3/5/10).
6. Run QA and repair queue.
7. Export finals and metadata manifest.

---

## 12) Minimal Prompt Generator Node Design (Elegant Option)

If you prefer a ComfyUI-native prompt generator node:
- Input: persona JSON + lane + shot recipe + continuity keys
- Output: positive prompt, negative prompt, control weights

This avoids manual prompt duplication and keeps outputs consistent across all 20 characters.

Recommended fields in persona JSON:
- `identity_core`
- `appearance_constraints`
- `voice_and_mood`
- `lane_limits`
- `wardrobe_matrix`
- `camera_preferences`

---

## 13) Reference Image Creation & Identity Strategy (LoRA vs. Multi-Ref)

**Goal:** Create three high-quality, identity-locked references per character before bulk generation.

### 13.1 Reference creation workflow (recommended)
1. **Persona-based prompt** (identity + neutral lighting + clean background).
2. Generate 12–20 candidates with `z-image-base`.
3. Select **3 diverse yet consistent** references:
   - front portrait, 3/4 portrait, half-body
   - same hair/skin tone/face geometry across all three
4. Run a light cleanup pass if needed (tiny denoise, no heavy style shifts).
5. Freeze these three as the canonical references used by IPAdapter FaceID/InstantID.

This is fastest and avoids the overhead of training, while still yielding strong consistency for large batches.

### 13.2 When to train a LoRA
Train a LoRA **only if** you see frequent identity drift in volume generation or need extreme pose/scene diversity:
- **Pros**: stronger identity lock across wide pose ranges, better style/wardrobe control.
- **Cons**: additional training time, dataset prep, and maintenance.

If you do train a LoRA:
- Use 20–50 curated images (clean, consistent, varied angles).
- Keep weights low (start 0.4–0.7) and combine with FaceID/InstantID for best control.
- Store LoRA per character and version it with a short changelog.

**Suggested default:** start with 3 reference images + FaceID, and only train a LoRA after the first QA cycle indicates drift.
