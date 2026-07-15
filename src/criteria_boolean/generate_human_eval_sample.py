#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a random expert-review template for CG-GLC outputs."""

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_JSONL = PROJECT_ROOT / 'data' / 'processed' / 'source_criteria.jsonl'
DEFAULT_CGGLC_JSONL = PROJECT_ROOT / 'data' / 'processed' / 'boolean_outputs' / 'cgglc.jsonl'
DEFAULT_OUT_DIR = PROJECT_ROOT / 'results' / 'human_eval'
DEFAULT_OUT_PREFIX = 'cgglc_human_eval'

DIMENSIONS = [
    'predicate_completeness',
    'logical_correctness',
    'grouping_correctness',
    'faithfulness',
    'downstream_usability',
]

EMPTY_TEXT_VALUES = {'', 'NA', 'N/A', 'NONE', 'NULL'}
EMPTY_EXPRESSIONS = {'', '(EMPTY)', 'EMPTY'}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def has_or(record: Dict[str, Any]) -> bool:
    return any(ev.get('type') == 'OR' and len(ev.get('args', [])) >= 2 for ev in record.get('events', []))


def has_scope(record: Dict[str, Any]) -> bool:
    return any(rel.get('type') == 'Has_scope' for rel in record.get('relations', []))


def bucket_name(record: Dict[str, Any]) -> str:
    if has_or(record):
        return 'or'
    if has_scope(record):
        return 'scope'
    return 'other'


def normalized_text(value: Any) -> str:
    return ' '.join(str(value or '').split())


def is_reviewable(record: Dict[str, Any], output: Dict[str, Any]) -> bool:
    source_text = normalized_text(record.get('text', ''))
    expression = normalized_text(output.get('boolean_expression', ''))
    if source_text.upper() in EMPTY_TEXT_VALUES:
        return False
    if expression.upper() in EMPTY_EXPRESSIONS:
        return False
    return True


def sample_records(records, sample_size, seed):
    rng = random.Random(seed)
    if sample_size >= len(records):
        selected = list(records)
        rng.shuffle(selected)
        return selected
    buckets = {'or': [], 'scope': [], 'other': []}
    for row in records:
        buckets[bucket_name(row)].append(row)
    targets = {'or': int(sample_size * 0.5), 'scope': int(sample_size * 0.3)}
    targets['other'] = sample_size - targets['or'] - targets['scope']
    selected = []
    for name, target in targets.items():
        selected.extend(rng.sample(buckets[name], min(target, len(buckets[name]))))
    selected_ids = {row['doc_id'] for row in selected}
    remaining = [row for row in records if row['doc_id'] not in selected_ids]
    if len(selected) < sample_size:
        selected.extend(rng.sample(remaining, min(sample_size - len(selected), len(remaining))))
    rng.shuffle(selected)
    return selected[:sample_size]


def main():
    parser = argparse.ArgumentParser(description='Create CG-GLC human evaluation templates.')
    parser.add_argument('--source-jsonl', default=str(DEFAULT_SOURCE_JSONL))
    parser.add_argument('--cgglc-jsonl', default=str(DEFAULT_CGGLC_JSONL))
    parser.add_argument('--out-dir', default=str(DEFAULT_OUT_DIR))
    parser.add_argument('--out-prefix', default=DEFAULT_OUT_PREFIX)
    parser.add_argument('--reviewer-count', type=int, default=2)
    parser.add_argument('--sample-size', type=int, default=50)
    parser.add_argument('--seed', type=int, default=2026)
    args = parser.parse_args()
    if args.reviewer_count < 1:
        raise ValueError('--reviewer-count must be at least 1')

    outputs = {row['doc_id']: row for row in load_jsonl(Path(args.cgglc_jsonl))}
    records = [
        row for row in load_jsonl(Path(args.source_jsonl))
        if row.get('doc_id') in outputs and is_reviewable(row, outputs[row['doc_id']])
    ]
    selected = sample_records(records, args.sample_size, args.seed)

    fieldnames = [
        'sample_id', 'doc_id', 'case_bucket', 'source_criterion', 'candidate_expression',
    ]
    fieldnames.extend(DIMENSIONS)
    fieldnames.append('reviewer_notes')

    rows = []
    for idx, record in enumerate(selected, 1):
        pred = outputs.get(record['doc_id'])
        if pred is None:
            continue
        row = {
            'sample_id': f'H{idx:03d}',
            'doc_id': record['doc_id'],
            'case_bucket': bucket_name(record),
            'source_criterion': normalized_text(record.get('text', '')),
            'candidate_expression': pred.get('boolean_expression', ''),
        }
        for dim in DIMENSIONS:
            row[dim] = ''
        row['reviewer_notes'] = ''
        rows.append(row)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_paths = []
    for reviewer_idx in range(1, args.reviewer_count + 1):
        out_path = out_dir / f'{args.out_prefix}_{reviewer_idx}.csv'
        with out_path.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        out_paths.append(out_path)
    print(json.dumps([str(path) for path in out_paths], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
