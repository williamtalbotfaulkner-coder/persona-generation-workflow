"""Super Factory agent runner skeleton for ComfyUI automation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import time
from typing import Any, Dict, Iterable, List
import urllib.request


@dataclass
class PromptRow:
    character_id: str
    lane: str
    shot_type: str
    bundle_id: str
    frame_index: str
    positive_prompt: str
    negative_prompt: str
    seed: int
    steps: int
    cfg: float
    sampler: str
    checkpoint: str
    resolution: str
    ref_images: List[str]
    face_id_weight: float


def load_prompt_table(path: Path) -> List[PromptRow]:
    rows: List[PromptRow] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                PromptRow(
                    character_id=row["character_id"],
                    lane=row["lane"],
                    shot_type=row["shot_type"],
                    bundle_id=row.get("bundle_id", ""),
                    frame_index=row.get("frame_index", "0"),
                    positive_prompt=row["positive_prompt"],
                    negative_prompt=row["negative_prompt"],
                    seed=int(row["seed"]),
                    steps=int(row["steps"]),
                    cfg=float(row["cfg"]),
                    sampler=row["sampler"],
                    checkpoint=row["checkpoint"],
                    resolution=row["resolution"],
                    ref_images=[row["ref_01"], row["ref_02"], row["ref_03"]],
                    face_id_weight=float(row["face_id_weight"]),
                )
            )
    return rows


def patch_workflow(workflow: Dict[str, Any], row: PromptRow) -> Dict[str, Any]:
    """Patch nodes in the workflow JSON.

    NOTE: Replace node IDs/keys with the IDs in your exported workflow.
    """
    workflow = dict(workflow)
    workflow["positive_prompt"] = row.positive_prompt
    workflow["negative_prompt"] = row.negative_prompt
    workflow["seed"] = row.seed
    workflow["steps"] = row.steps
    workflow["cfg"] = row.cfg
    workflow["sampler"] = row.sampler
    workflow["checkpoint"] = row.checkpoint
    workflow["resolution"] = row.resolution
    workflow["ref_images"] = row.ref_images
    workflow["face_id_weight"] = row.face_id_weight
    return workflow


def post_prompt(server_url: str, workflow: Dict[str, Any]) -> Dict[str, Any]:
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    request = urllib.request.Request(
        f"{server_url}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def queue_empty(server_url: str) -> bool:
    request = urllib.request.Request(f"{server_url}/queue")
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode("utf-8"))
    return not data.get("queue")


def wait_for_queue(server_url: str, poll_s: float = 2.0) -> None:
    while True:
        if queue_empty(server_url):
            return
        time.sleep(poll_s)


def save_manifest(path: Path, row: PromptRow, output_paths: Iterable[str]) -> None:
    entry = {
        "character_id": row.character_id,
        "lane": row.lane,
        "shot_type": row.shot_type,
        "bundle_id": row.bundle_id,
        "frame_index": row.frame_index,
        "seed": row.seed,
        "steps": row.steps,
        "cfg": row.cfg,
        "sampler": row.sampler,
        "checkpoint": row.checkpoint,
        "resolution": row.resolution,
        "ref_images": row.ref_images,
        "face_id_weight": row.face_id_weight,
        "outputs": list(output_paths),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def run_agent(server_url: str, workflow_path: Path, prompt_table_path: Path, manifest_path: Path) -> None:
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    prompt_rows = load_prompt_table(prompt_table_path)

    for row in prompt_rows:
        patched = patch_workflow(workflow, row)
        post_prompt(server_url, patched)
        wait_for_queue(server_url)
        save_manifest(manifest_path, row, output_paths=[])


if __name__ == "__main__":
    run_agent(
        server_url="http://127.0.0.1:8188",
        workflow_path=Path("workflows/super_factory_openai_zimage_master.json"),
        prompt_table_path=Path("prompts/prompt_table.csv"),
        manifest_path=Path("logs/manifest.jsonl"),
    )
