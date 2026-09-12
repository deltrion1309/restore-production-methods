#!/usr/bin/env python3
"""
Generate the building-type-specific half of Restore Production Methods.

Why this exists
---------------
Victoria 3 has no `production_method` scope and no way to iterate a building's
production method groups in script, and building scopes cannot store variables
(confirmed in-game: "This scope doesn't support variables. Scope: Building ...").
So anything per-building has to be written as script that names each building
type and each production method explicitly.

Rather than hand-maintaining that, this script reads the game's own definitions
and emits the script. Point it at your whole mod set and the output covers
modded buildings and modded production methods exactly like vanilla ones.

Data model of the generated script
----------------------------------
A state can hold at most one building of each type, so (state, building type) is
a unique key and the snapshot lives in state variables:

    rpm_lvl_<building_type>        the building's level at the snapshot
    rpm_pm<N>_<building_type>      index of the active production method in the
                                   building type's Nth production method group

Usage
-----
    python dev/generate_pm_script.py \
        --source "D:/SteamLibrary/steamapps/common/Victoria 3/game" \
        --source "C:/.../mod/Some Mod" \
        --out common/scripted_effects/rpm_generated_effects.txt

Later --source roots override earlier ones by file name, which is how Paradox
resolves mod load order.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

GENERATED_HEADER = """\
###############################################################################
# GENERATED FILE - DO NOT EDIT BY HAND
#
# Produced by dev/generate_pm_script.py from:
{sources}
#
# {n_buildings} building types, {n_groups} production method groups,
# {n_methods} production methods, deepest building has {max_groups} groups.
#
# Regenerate after a game patch, or after changing your mod set, with:
#     python dev/generate_pm_script.py --source "<game>/game" [--source "<mod>"]
#
# Why generated: Victoria 3 has no production_method scope and no way to
# iterate a building's production method groups, and building scopes cannot
# store variables. Anything per-building therefore has to name each building
# type and each production method explicitly.
#
# Snapshot lives in state variables, because a state holds at most one building
# of each type:
#     rpm_lvl_<building_type>      level at the time of the snapshot
#     rpm_pm<N>_<building_type>    index of the active production method in the
#                                  building type's Nth production method group
###############################################################################
"""


# --------------------------------------------------------------------------- #
# A very small Paradox script reader
# --------------------------------------------------------------------------- #

TOKEN_RE = re.compile(r'"[^"]*"|[{}=]|[^\s{}=]+')


def tokenize(text: str) -> list[str]:
    """Strip comments and split into tokens."""
    lines = []
    for line in text.splitlines():
        hash_pos = line.find("#")
        if hash_pos != -1:
            line = line[:hash_pos]
        lines.append(line)
    return TOKEN_RE.findall("\n".join(lines))


def parse_blocks(tokens: list[str]) -> dict[str, list[str]]:
    """
    Return {top_level_key: [tokens inside its braces]} for a file shaped like

        key = { ... }
        other_key = { ... }

    Nested braces are kept verbatim in the token list.
    """
    out: dict[str, list[str]] = {}
    i = 0
    while i < len(tokens):
        if i + 2 < len(tokens) and tokens[i + 1] == "=" and tokens[i + 2] == "{":
            key = tokens[i].strip('"')
            depth = 0
            j = i + 2
            while j < len(tokens):
                if tokens[j] == "{":
                    depth += 1
                elif tokens[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            out[key] = tokens[i + 3 : j]
            i = j + 1
        else:
            i += 1
    return out


def list_field(tokens: list[str], field: str) -> list[str]:
    """Read `field = { a b c }` out of a token list, ignoring nested blocks."""
    depth = 0
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "{":
            depth += 1
        elif tok == "}":
            depth -= 1
        elif depth == 0 and tok == field and i + 2 < len(tokens) and tokens[i + 1] == "=" and tokens[i + 2] == "{":
            inner_depth = 0
            j = i + 2
            values = []
            while j < len(tokens):
                if tokens[j] == "{":
                    inner_depth += 1
                    if inner_depth > 1:
                        values.append(tokens[j])
                elif tokens[j] == "}":
                    inner_depth -= 1
                    if inner_depth == 0:
                        break
                    values.append(tokens[j])
                else:
                    values.append(tokens[j])
                j += 1
            return [v.strip('"') for v in values if v not in ("=",)]
        i += 1
    return []


def collect(roots: list[Path], subdir: str) -> dict[str, list[str]]:
    """
    Read every .txt in <root>/common/<subdir> for each root in order.
    Later roots override earlier ones per file name, as the game does.
    """
    by_filename: dict[str, Path] = {}
    for root in roots:
        directory = root / "common" / subdir
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.txt")):
            by_filename[path.name] = path

    definitions: dict[str, list[str]] = {}
    for path in by_filename.values():
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        definitions.update(parse_blocks(tokenize(text)))
    return definitions


# --------------------------------------------------------------------------- #
# Script emission
# --------------------------------------------------------------------------- #


def emit(buildings: dict[str, list[str]], groups: dict[str, list[str]]) -> tuple[str, dict]:
    snapshot: list[str] = []
    restore_pms: list[str] = []
    diff: list[str] = []
    clear: list[str] = []

    stats = {"n_buildings": 0, "n_methods": 0, "max_groups": 0}
    methods_seen: set[str] = set()

    for building in sorted(buildings):
        group_names = [g for g in buildings[building] if g in groups]
        if not group_names:
            # A building with no production methods still has a level worth
            # remembering, so it is not skipped - it just gets no pm variables.
            group_names = []

        stats["n_buildings"] += 1
        stats["max_groups"] = max(stats["max_groups"], len(group_names))

        # ---- snapshot ----------------------------------------------------- #
        body = [
            f"\t\tset_variable = {{ name = rpm_lvl_{building} value = b:{building}.level }}",
        ]
        for index, group in enumerate(group_names):
            methods = groups[group]
            methods_seen.update(methods)
            for position, method in enumerate(methods):
                keyword = "if" if position == 0 else "else_if"
                body.append(
                    f"\t\t{keyword} = {{\n"
                    f"\t\t\tlimit = {{ is_production_method_active = {{ building_type = {building} production_method = {method} }} }}\n"
                    f"\t\t\tset_variable = {{ name = rpm_pm{index}_{building} value = {position} }}\n"
                    f"\t\t}}"
                )
        snapshot.append(
            f"\tif = {{\n"
            f"\t\tlimit = {{ has_building = {building} }}\n" + "\n".join(body) + "\n\t}"
        )

        # ---- restore production methods ----------------------------------- #
        if group_names:
            restore_body = []
            for index, group in enumerate(group_names):
                methods = groups[group]
                branches = []
                for position, method in enumerate(methods):
                    keyword = "if" if position == 0 else "else_if"
                    branches.append(
                        f"\t\t\t{keyword} = {{\n"
                        f"\t\t\t\tlimit = {{ var:rpm_pm{index}_{building} = {position} }}\n"
                        f"\t\t\t\tactivate_production_method = {{ building_type = {building} production_method = {method} }}\n"
                        f"\t\t\t}}"
                    )
                restore_body.append(
                    f"\t\tif = {{\n"
                    f"\t\t\tlimit = {{ has_variable = rpm_pm{index}_{building} }}\n"
                    + "\n".join(branches)
                    + "\n\t\t}"
                )
            restore_pms.append(
                f"\tif = {{\n"
                f"\t\tlimit = {{ has_building = {building} }}\n"
                + "\n".join(restore_body)
                + "\n\t}"
            )

        # ---- diff against the snapshot ------------------------------------ #
        diff_body = [
            "\t\tif = {",
            f"\t\t\tlimit = {{ NOT = {{ has_variable = rpm_lvl_{building} }} }}",
            "\t\t\tscope:rpm_player = { change_variable = { name = rpm_sum_buildings_new add = 1 } }",
            "\t\t}",
            "\t\telse = {",
            f"\t\t\tif = {{",
            f"\t\t\t\tlimit = {{ b:{building}.level > var:rpm_lvl_{building} }}",
            "\t\t\t\tsave_temporary_scope_value_as = {",
            "\t\t\t\t\tname = rpm_delta",
            "\t\t\t\t\tvalue = {",
            f"\t\t\t\t\t\tvalue = b:{building}.level",
            f"\t\t\t\t\t\tsubtract = var:rpm_lvl_{building}",
            "\t\t\t\t\t}",
            "\t\t\t\t}",
            "\t\t\t\tscope:rpm_player = {",
            "\t\t\t\t\tchange_variable = { name = rpm_sum_buildings_expanded add = 1 }",
            "\t\t\t\t\tchange_variable = { name = rpm_sum_levels_added add = scope:rpm_delta }",
            "\t\t\t\t}",
            "\t\t\t}",
            f"\t\t\telse_if = {{",
            f"\t\t\t\tlimit = {{ b:{building}.level < var:rpm_lvl_{building} }}",
            "\t\t\t\tscope:rpm_player = { change_variable = { name = rpm_sum_buildings_reduced add = 1 } }",
            "\t\t\t}",
            "\t\t}",
        ]

        if group_names:
            diff_body.append("\t\tset_variable = { name = rpm_tmp_pm_changes value = 0 }")
            for index, group in enumerate(group_names):
                methods = groups[group]
                branches = []
                for position, method in enumerate(methods):
                    keyword = "if" if position == 0 else "else_if"
                    branches.append(
                        f"\t\t\t{keyword} = {{\n"
                        f"\t\t\t\tlimit = {{\n"
                        f"\t\t\t\t\tvar:rpm_pm{index}_{building} = {position}\n"
                        f"\t\t\t\t\tNOT = {{ is_production_method_active = {{ building_type = {building} production_method = {method} }} }}\n"
                        f"\t\t\t\t}}\n"
                        f"\t\t\t\tchange_variable = {{ name = rpm_tmp_pm_changes add = 1 }}\n"
                        f"\t\t\t}}"
                    )
                diff_body.append(
                    f"\t\tif = {{\n"
                    f"\t\t\tlimit = {{ has_variable = rpm_pm{index}_{building} }}\n"
                    + "\n".join(branches)
                    + "\n\t\t}"
                )
            diff_body.extend([
                "\t\tif = {",
                "\t\t\tlimit = { var:rpm_tmp_pm_changes > 0 }",
                "\t\t\tsave_temporary_scope_value_as = { name = rpm_bldg_pm_changes value = var:rpm_tmp_pm_changes }",
                "\t\t\tscope:rpm_player = {",
                "\t\t\t\tchange_variable = { name = rpm_sum_pm_changes add = scope:rpm_bldg_pm_changes }",
                "\t\t\t\tchange_variable = { name = rpm_sum_pm_buildings add = 1 }",
                "\t\t\t}",
                "\t\t}",
                "\t\tremove_variable = rpm_tmp_pm_changes",
            ])

        diff.append(
            f"\tif = {{\n"
            f"\t\tlimit = {{ has_building = {building} }}\n"
            + "\n".join(diff_body)
            + "\n\t}"
        )

        # ---- clear -------------------------------------------------------- #
        clear_body = [f"\tremove_variable = rpm_lvl_{building}"]
        for index in range(len(group_names)):
            clear_body.append(f"\tremove_variable = rpm_pm{index}_{building}")
        clear.extend(clear_body)

    stats["n_methods"] = len(methods_seen)

    parts = [
        "# Scope: state. Record every building's level and active production methods.",
        "rpm_generated_snapshot_state = {",
        "\n".join(snapshot),
        "}",
        "",
        "# Scope: state. Put production methods back to the snapshot.",
        "# Run this AFTER restoring building levels, never before: rebuilding a",
        "# building resets its production methods.",
        "rpm_generated_restore_pms_state = {",
        "\n".join(restore_pms),
        "}",
        "",
        "# Scope: state, with scope:rpm_player set to the country reading the report.",
        "# Count what the rebel AI changed, into country variables.",
        "rpm_generated_diff_state = {",
        "\n".join(diff),
        "}",
        "",
        "# Scope: state. Forget the snapshot.",
        "rpm_generated_clear_state = {",
        "\n".join(clear),
        "}",
        "",
    ]
    return "\n".join(parts), stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--source",
        action="append",
        required=True,
        metavar="DIR",
        help="A folder containing common/buildings and common/production_method_groups "
        "(the game's 'game' folder, then each mod folder). Repeatable; later wins.",
    )
    parser.add_argument(
        "--out",
        default="common/scripted_effects/rpm_generated_effects.txt",
        help="Where to write the generated script (default: %(default)s).",
    )
    args = parser.parse_args()

    roots = [Path(s) for s in args.source]
    for root in roots:
        if not root.is_dir():
            print(f"error: source not found: {root}", file=sys.stderr)
            return 1

    buildings_raw = collect(roots, "buildings")
    groups_raw = collect(roots, "production_method_groups")

    buildings = {
        name: list_field(tokens, "production_method_groups")
        for name, tokens in buildings_raw.items()
    }
    groups = {
        name: list_field(tokens, "production_methods")
        for name, tokens in groups_raw.items()
    }

    body, stats = emit(buildings, groups)
    header = GENERATED_HEADER.format(
        sources="\n".join(f"#   {r}" for r in roots),
        n_buildings=stats["n_buildings"],
        n_groups=len(groups),
        n_methods=stats["n_methods"],
        max_groups=stats["max_groups"],
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Paradox wants UTF-8 with BOM for script files too, not just localization.
    out_path.write_text(header + "\n" + body, encoding="utf-8-sig", newline="\n")

    print(
        f"wrote {out_path} - {stats['n_buildings']} building types, "
        f"{len(groups)} production method groups, {stats['n_methods']} production methods, "
        f"{out_path.stat().st_size / 1024:.0f} KiB"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
