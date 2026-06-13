from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "domain_agent_routing.yaml"


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def dedupe_specialists(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        name = item["name"]
        if name in seen:
            continue
        seen.add(name)
        result.append(item)
    return result


def matching_terms(prompt: str, trigger_terms: list[str]) -> list[str]:
    lowered = prompt.casefold()
    matches = []
    for term in trigger_terms:
        normalized = term.casefold()
        pattern = r"(?<!\w)" + r"\s+".join(re.escape(part) for part in normalized.split()) + r"(?!\w)"
        if re.search(pattern, lowered):
            matches.append(term)
    return matches


def add_specialist(
    candidates: dict[str, dict[str, Any]],
    name: str,
    *,
    reason: str,
    explicit: bool,
) -> None:
    current = candidates.setdefault(name, {"name": name, "reasons": [], "explicit": False})
    current["reasons"].append(reason)
    current["explicit"] = bool(current["explicit"] or explicit)


def division_candidates(prompt: str, contract: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for division_name, division in contract.get("divisions", {}).items():
        matched_terms = matching_terms(prompt, list(division.get("trigger_terms", [])))
        specialist_candidates: dict[str, dict[str, Any]] = {}
        explicit_specialist_count = 0

        for specialist in division.get("specialists", []):
            terms = matching_terms(prompt, list(specialist.get("trigger_terms", [])))
            if not terms:
                continue
            explicit_specialist_count += 1
            add_specialist(
                specialist_candidates,
                specialist["name"],
                reason=f"explicit terms: {', '.join(terms)}",
                explicit=True,
            )

        for expansion in division.get("expansion_sets", []):
            terms = matching_terms(prompt, list(expansion.get("trigger_terms", [])))
            if not terms:
                continue
            for specialist_name in expansion.get("specialists", []):
                add_specialist(
                    specialist_candidates,
                    specialist_name,
                    reason=f"expansion set {expansion['name']}: {', '.join(terms)}",
                    explicit=False,
                )

        if not specialist_candidates and matched_terms:
            for specialist_name in division.get("default_specialists", []):
                add_specialist(
                    specialist_candidates,
                    specialist_name,
                    reason=f"default for {division_name}",
                    explicit=False,
                )

        score = (len(matched_terms) * 3) + (explicit_specialist_count * 2) + len(
            specialist_candidates
        )
        if score == 0:
            continue

        candidates.append(
            {
                "division": division_name,
                "score": score,
                "matched_terms": matched_terms,
                "required_framework_agents": division.get("required_framework_agents", []),
                "verification_gates": division.get("verification_gates", []),
                "specialist_candidates": list(specialist_candidates.values()),
            }
        )

    return sorted(candidates, key=lambda item: (-item["score"], item["division"]))


def split_specialists(
    candidates: list[dict[str, Any]],
    *,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    explicit = [item for item in candidates if item["explicit"]]
    inferred = [item for item in candidates if not item["explicit"]]
    ordered = explicit + inferred
    selected = ordered[:limit]
    deferred = ordered[limit:]
    return selected, deferred


def route_prompt(prompt: str, contract: dict[str, Any] | None = None) -> dict[str, Any]:
    if contract is None:
        contract = load_contract()

    defaults = contract.get("routing_defaults", {})
    primary_limit = int(defaults.get("max_primary_specialists", 3))
    adjacent_limit = int(defaults.get("max_adjacent_specialists", 2))
    adjacent_division_limit = int(defaults.get("max_adjacent_divisions", 1))
    candidates = division_candidates(prompt, contract)

    selected_framework_agents = list(defaults.get("baseline_framework_agents", []))
    verification_gates: list[str] = []
    selected_specialists: list[dict[str, Any]] = []
    deferred_specialists: list[dict[str, Any]] = []

    primary = candidates[0] if candidates else None
    adjacent = candidates[1 : 1 + adjacent_division_limit] if primary else []
    selected_divisions = [item for item in [primary, *adjacent] if item]

    for division in selected_divisions:
        selected_framework_agents.extend(division.get("required_framework_agents", []))
        verification_gates.extend(division.get("verification_gates", []))

    if primary:
        primary_pool = [
            {**specialist, "division": primary["division"]}
            for specialist in primary.get("specialist_candidates", [])
        ]
        primary_selected, primary_deferred = split_specialists(
            primary_pool,
            limit=primary_limit,
        )
        selected_specialists.extend(primary_selected)
        deferred_specialists.extend(primary_deferred)

    adjacent_pool: list[dict[str, Any]] = []
    for division in adjacent:
        for specialist in division.get("specialist_candidates", []):
            adjacent_pool.append({**specialist, "division": division["division"]})

    adjacent_selected, adjacent_deferred = split_specialists(
        adjacent_pool,
        limit=adjacent_limit,
    )
    selected_specialists.extend(adjacent_selected)
    deferred_specialists.extend(adjacent_deferred)
    selected_specialists = dedupe_specialists(selected_specialists)
    deferred_specialists = [
        item
        for item in dedupe_specialists(deferred_specialists)
        if item["name"] not in {selected["name"] for selected in selected_specialists}
    ]

    routing_notes = [
        defaults.get("escalation_rule", "Start with the smallest useful set.").strip(),
    ]
    if not primary:
        routing_notes.append(
            "No division matched; use baseline SDLC roles and record the routing assumption."
        )
    elif deferred_specialists:
        routing_notes.append(
            "Some plausible specialists were deferred to avoid unnecessary token use."
        )

    return {
        "status": "PASS",
        "contract": str(CONTRACT_PATH.relative_to(ROOT)),
        "primary_division": primary["division"] if primary else None,
        "adjacent_divisions": [item["division"] for item in adjacent],
        "matched_divisions": [
            {
                "division": item["division"],
                "score": item["score"],
                "matched_terms": item["matched_terms"],
            }
            for item in candidates
        ],
        "selected_framework_agents": dedupe(selected_framework_agents),
        "selected_specialists": selected_specialists,
        "deferred_specialists": deferred_specialists,
        "verification_gates": dedupe(verification_gates),
        "routing_notes": routing_notes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select AI Brain divisions, framework agents, and specialist lenses from a prompt.",
    )
    parser.add_argument("--prompt", help="User prompt text. Reads stdin when omitted.")
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    prompt = args.prompt if args.prompt is not None else sys.stdin.read()
    result = route_prompt(prompt)
    payload = json.dumps(result, indent=2, sort_keys=True)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
