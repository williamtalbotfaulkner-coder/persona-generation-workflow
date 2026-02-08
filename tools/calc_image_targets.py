"""Quick planner for Super Factory OpenAI image production targets."""

from dataclasses import dataclass


@dataclass
class LanePlan:
    one_off: int = 80
    bundle3_count: int = 10
    bundle5_count: int = 10
    bundle10_count: int = 4

    @property
    def total(self) -> int:
        return self.one_off + self.bundle3_count * 3 + self.bundle5_count * 5 + self.bundle10_count * 10


def estimate_total(characters: int = 20, lanes: int = 4, acceptance_rate: float = 0.70) -> dict:
    lane = LanePlan()
    per_character = lane.total * lanes
    final_total = per_character * characters
    gross_required = int(round(final_total / acceptance_rate))
    return {
        "per_lane": lane.total,
        "per_character": per_character,
        "final_total": final_total,
        "gross_required": gross_required,
    }


if __name__ == "__main__":
    data = estimate_total()
    for key, value in data.items():
        print(f"{key}: {value}")
