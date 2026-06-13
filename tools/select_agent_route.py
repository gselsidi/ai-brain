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
SOURCE_CATALOG_PATHS = {
    "marketing_skill_integration": ROOT / "contracts" / "marketing_skill_integration.yaml",
    "rampstack_skill_integration": ROOT / "contracts" / "rampstack_skill_integration.yaml",
}
SOURCE_SKILL_STOP_WORDS = {
    "and",
    "audit",
    "build",
    "design",
    "development",
    "management",
    "optimization",
    "orchestrator",
    "report",
    "strategy",
    "system",
    "the",
    "web",
}
SOURCE_SKILL_GENERIC_TERMS = {
    "brand",
    "content",
    "copy",
    "design",
    "product",
    "seo",
}


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_source_catalog(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_source_catalogs(contract: dict[str, Any]) -> list[dict[str, Any]]:
    names = list(contract.get("routing_defaults", {}).get("source_skill_catalogs", []))
    if not names:
        names = list(SOURCE_CATALOG_PATHS)

    catalogs: list[dict[str, Any]] = []
    for name in names:
        path = SOURCE_CATALOG_PATHS.get(name, ROOT / "contracts" / f"{name}.yaml")
        catalog = load_source_catalog(path)
        if catalog:
            catalogs.append(catalog)
    return catalogs


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


def dedupe_source_skills(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        slug = item["slug"]
        if slug in seen:
            continue
        seen.add(slug)
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


def source_skill_terms(skill: dict[str, Any]) -> list[str]:
    slug = str(skill.get("slug", "")).strip()
    parts = [part for part in slug.split("-") if part]
    terms = [slug.replace("-", " ")]
    terms.extend(
        " ".join(parts[index : index + 2])
        for index in range(len(parts) - 1)
    )
    terms.extend(
        part
        for part in parts
        if len(part) > 2 and part not in SOURCE_SKILL_STOP_WORDS
    )
    terms.extend(str(term) for term in skill.get("trigger_terms", []))
    return dedupe(terms)


def source_skill_score(
    *,
    matches: list[str],
    full_phrase: str,
) -> int:
    score = 0
    for match in matches:
        if match == full_phrase:
            score += 8
        elif " " in match:
            score += 4
        elif match in SOURCE_SKILL_GENERIC_TERMS:
            score += 1
        else:
            score += 3
    return score


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


def source_skill_candidates(
    prompt: str,
    source_catalog: dict[str, Any],
    selected_division_names: list[str],
) -> list[dict[str, Any]]:
    if not source_catalog or not selected_division_names:
        return []

    selected_division_set = set(selected_division_names)
    candidates: list[dict[str, Any]] = []
    for category, mapping in source_catalog.get("category_mappings", {}).items():
        divisions = list(mapping.get("divisions", []))
        if selected_division_set.isdisjoint(divisions):
            continue

        for skill in mapping.get("skills", []):
            slug = str(skill.get("slug", "")).strip()
            if not slug:
                continue
            terms = source_skill_terms(skill)
            matches = matching_terms(prompt, terms)
            if not matches:
                continue

            full_phrase = slug.replace("-", " ")
            action = str(skill.get("integration_action", mapping.get("default_action", "")))
            score = source_skill_score(
                matches=matches,
                full_phrase=full_phrase,
            )
            candidates.append(
                {
                    "slug": slug,
                    "category": category,
                    "integration_action": action,
                    "merge_into": mapping.get("merge_into", ""),
                    "matched_terms": matches,
                    "score": score,
                    "catalog": source_catalog.get("name", ""),
                    "source": source_catalog.get("source", {}).get("repository", ""),
                }
            )

    return sort_source_skill_candidates(candidates)


def sort_source_skill_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda item: (
            -int(item["score"]),
            item["integration_action"] == "tool_dependent_lens",
            item["category"],
            item["slug"],
            item.get("catalog", ""),
        ),
    )


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


def route_prompt(
    prompt: str,
    contract: dict[str, Any] | None = None,
    source_catalog: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if contract is None:
        contract = load_contract()
    if source_catalog is None:
        source_catalogs = load_source_catalogs(contract)
    elif isinstance(source_catalog, dict):
        source_catalogs = [source_catalog]
    else:
        source_catalogs = source_catalog

    defaults = contract.get("routing_defaults", {})
    primary_limit = int(defaults.get("max_primary_specialists", 3))
    adjacent_limit = int(defaults.get("max_adjacent_specialists", 2))
    adjacent_division_limit = int(defaults.get("max_adjacent_divisions", 1))
    source_skill_limit = int(defaults.get("max_source_skills", 4))
    deferred_source_skill_limit = int(defaults.get("max_deferred_source_skills", 8))
    candidates = division_candidates(prompt, contract)

    selected_framework_agents = list(defaults.get("baseline_framework_agents", []))
    verification_gates: list[str] = []
    selected_specialists: list[dict[str, Any]] = []
    deferred_specialists: list[dict[str, Any]] = []
    selected_source_skills: list[dict[str, Any]] = []
    deferred_source_skills: list[dict[str, Any]] = []

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

    selected_division_names = [division["division"] for division in selected_divisions]
    source_candidates = sort_source_skill_candidates(
        [
            item
            for catalog in source_catalogs
            for item in source_skill_candidates(prompt, catalog, selected_division_names)
        ]
    )
    source_candidates = dedupe_source_skills(source_candidates)
    selected_source_skills = source_candidates[:source_skill_limit]
    deferred_source_pool = source_candidates[
        source_skill_limit : source_skill_limit + deferred_source_skill_limit
    ]
    selected_source_slugs = {selected["slug"] for selected in selected_source_skills}
    deferred_source_skills = [
        item for item in deferred_source_pool if item["slug"] not in selected_source_slugs
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
    if deferred_source_skills:
        routing_notes.append(
            "Some matching source-catalog skills were deferred to avoid unnecessary token use."
        )
    tool_dependent = [
        item["slug"]
        for item in selected_source_skills
        if item.get("integration_action") == "tool_dependent_lens"
    ]
    if tool_dependent:
        routing_notes.append(
            "Tool-dependent source skills require adopting-team credentials, MCPs, URLs, accounts, "
            "analytics/ad data, CRM data, market data, or web research before execution: "
            + ", ".join(tool_dependent)
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
        "selected_source_skills": selected_source_skills,
        "deferred_source_skills": deferred_source_skills,
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
