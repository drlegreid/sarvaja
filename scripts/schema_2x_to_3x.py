#!/usr/bin/env python3
"""
TypeDB Schema 2.x to 3.x Converter.

Per GAP-TYPEDB-UPGRADE-001: Automated schema migration.

Syntax changes handled:
1. entity X sub entity → entity X
2. relation X sub relation → relation X
3. attribute X sub attribute, value TYPE → attribute X, value TYPE
4. rule X: when {...} then {...}; → fun X() -> {...} { match ... return ... }

Usage:
    python3 scripts/schema_2x_to_3x.py input.tql output.tql
    python3 scripts/schema_2x_to_3x.py --all  # Convert all schema files
"""

import re
import sys
from pathlib import Path


def convert_entity(line: str) -> str:
    """Convert entity definition from 2.x to 3.x syntax.

    2.x: rule-entity sub entity,
    3.x: entity rule-entity,
    """
    # Pattern: "name sub entity," → "entity name,"
    match = re.match(r'^(\s*)(\w[\w-]*)\s+sub\s+entity,\s*$', line)
    if match:
        indent, name = match.groups()
        return f"{indent}entity {name},\n"

    # Pattern: "name sub entity" (no comma - standalone)
    match = re.match(r'^(\s*)(\w[\w-]*)\s+sub\s+entity\s*;?\s*$', line)
    if match:
        indent, name = match.groups()
        return f"{indent}entity {name};\n"

    return line


def convert_relation(line: str) -> str:
    """Convert relation definition from 2.x to 3.x syntax.

    2.x: rule-dependency sub relation,
    3.x: relation rule-dependency,
    """
    # Pattern: "name sub relation," → "relation name,"
    match = re.match(r'^(\s*)(\w[\w-]*)\s+sub\s+relation,\s*$', line)
    if match:
        indent, name = match.groups()
        return f"{indent}relation {name},\n"

    # Pattern: "name sub relation" (no comma - standalone)
    match = re.match(r'^(\s*)(\w[\w-]*)\s+sub\s+relation\s*;?\s*$', line)
    if match:
        indent, name = match.groups()
        return f"{indent}relation {name};\n"

    return line


def convert_attribute(line: str) -> str:
    """Convert attribute definition from 2.x to 3.x syntax.

    2.x: rule-id sub attribute, value string;
    3.x: attribute rule-id value string;
    """
    # Pattern: "name sub attribute, value TYPE;" → "attribute name value TYPE;"
    match = re.match(r'^(\s*)(\w[\w-]*)\s+sub\s+attribute,\s+value\s+(\w+);', line)
    if match:
        indent, name, value_type = match.groups()
        return f"{indent}attribute {name} value {value_type};\n"

    return line


def convert_inference_rule(content: str) -> str:
    """Convert inference rules to functions (3.x).

    This is complex - rules need manual review.
    We mark them for conversion but don't auto-convert.
    """
    # Pattern: rule name: when {...} then {...};
    pattern = r'rule\s+(\w[\w-]*)\s*:\s*when\s*\{'

    def replace_rule(match):
        name = match.group(1)
        return f"# TODO: Convert to function\n# fun {name}() -> {{ ... }} {{\n#     Original rule:\nrule {name}: when {{"

    return re.sub(pattern, replace_rule, content)


def convert_schema_file(input_path: Path, output_path: Path) -> dict:
    """Convert a single schema file from 2.x to 3.x syntax."""
    with open(input_path, 'r') as f:
        content = f.read()

    stats = {
        'entities': 0,
        'relations': 0,
        'attributes': 0,
        'rules': 0,
        'lines': 0
    }

    lines = content.split('\n')
    converted_lines = []

    for line in lines:
        original = line
        stats['lines'] += 1

        # Convert entity definitions
        if 'sub entity' in line:
            line = convert_entity(line)
            if line != original:
                stats['entities'] += 1

        # Convert relation definitions
        elif 'sub relation' in line:
            line = convert_relation(line)
            if line != original:
                stats['relations'] += 1

        # Convert attribute definitions
        elif 'sub attribute' in line:
            line = convert_attribute(line)
            if line != original:
                stats['attributes'] += 1

        converted_lines.append(line)

    converted = '\n'.join(converted_lines)

    # Mark inference rules for conversion
    if 'rule ' in converted and 'when {' in converted:
        converted = convert_inference_rule(converted)
        stats['rules'] = content.count('rule ') - content.count('# rule')

    # Add 3.x header
    header = "# TypeDB 3.x Schema (Converted from 2.x)\n"
    header += f"# Converted from: {input_path.name}\n"
    header += "# Review cardinality annotations (@card) for owns/plays\n\n"

    if not converted.startswith('#'):
        converted = header + converted

    with open(output_path, 'w') as f:
        f.write(converted)

    return stats


def convert_all_schemas(schema_dir: Path, output_dir: Path) -> dict:
    """Convert all schema files in directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    total_stats = {
        'files': 0,
        'entities': 0,
        'relations': 0,
        'attributes': 0,
        'rules': 0,
        'lines': 0
    }

    for tql_file in sorted(schema_dir.glob('*.tql')):
        output_file = output_dir / f"{tql_file.stem}_3x.tql"
        stats = convert_schema_file(tql_file, output_file)

        print(f"Converted: {tql_file.name} → {output_file.name}")
        print(f"  Entities: {stats['entities']}, Relations: {stats['relations']}, "
              f"Attributes: {stats['attributes']}, Rules: {stats['rules']}")

        total_stats['files'] += 1
        for key in ['entities', 'relations', 'attributes', 'rules', 'lines']:
            total_stats[key] += stats[key]

    return total_stats


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == '--all':
        schema_dir = Path(__file__).parent.parent / 'governance' / 'schema'
        output_dir = Path(__file__).parent.parent / 'governance' / 'schema_3x'

        print(f"Converting all schemas in {schema_dir}")
        print(f"Output directory: {output_dir}\n")

        stats = convert_all_schemas(schema_dir, output_dir)

        print(f"\n{'='*50}")
        print(f"TOTAL: {stats['files']} files, {stats['lines']} lines")
        print(f"Converted: {stats['entities']} entities, {stats['relations']} relations, "
              f"{stats['attributes']} attributes")
        print(f"Rules needing manual conversion: {stats['rules']}")
        print(f"\nOutput: {output_dir}")
        print("\nNOTE: Review converted files for:")
        print("  1. Cardinality annotations (@card) on owns/plays")
        print("  2. Inference rules → functions conversion")
        print("  3. Any complex inheritance patterns")

    elif len(sys.argv) == 3:
        input_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2])

        if not input_path.exists():
            print(f"Error: {input_path} not found")
            sys.exit(1)

        stats = convert_schema_file(input_path, output_path)
        print(f"Converted: {input_path} → {output_path}")
        print(f"Stats: {stats}")

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
