#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate human-evaluation templates for Boolean expression outputs.

The script can either draw a new stratified sample from source criteria or reuse
an existing human-evaluation CSV as the reference sample. Reusing the CG-GLC
sample is the preferred workflow for paired human comparison across methods.
"""

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_JSONL = PROJECT_ROOT / 'data' / 'processed' / 'source_criteria.jsonl'
DEFAULT_BOOLEAN_DIR = PROJECT_ROOT / 'data' / 'processed' / 'boolean_outputs'
DEFAULT_OUT_DIR = PROJECT_ROOT / 'results' / 'human_eval'
DEFAULT_REFERENCE_CSV = DEFAULT_OUT_DIR / 'cgglc_human_eval_1.csv'

METHOD_LABELS = {
    'flat': 'Flat',
    'or_direct': 'OR-direct',
    'constraint': 'Constraint',
    'cgglc': 'CG-GLC',
}

DIMENSIONS = [
    'predicate_completeness',
    'logical_correctness',
    'grouping_correctness',
    'faithfulness',
    'downstream_usability',
]

BASE_FIELDNAMES = [
    'sample_id',
    'doc_id',
    'case_bucket',
    'source_criterion',
    'candidate_expression',
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


def load_csv(path: Path) -> List[Dict[str, str]]:
    last_error = None
    for encoding in ('utf-8-sig', 'utf-8', 'gb18030', 'cp936'):
        try:
            with path.open('r', encoding=encoding, newline='') as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError as exc:
            last_error = exc
    raise last_error


def write_csv(rows: List[Dict[str, Any]], path: Path, fieldnames: List[str], overwrite: bool, skip_existing: bool) -> bool:
    if path.exists() and not overwrite:
        if skip_existing:
            return False
        raise FileExistsError(f'{path} already exists. Use --overwrite to replace it.')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return True


def normalized_text(value: Any) -> str:
    return ' '.join(str(value or '').split())


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


def is_reviewable(record: Dict[str, Any], output: Dict[str, Any]) -> bool:
    source_text = normalized_text(record.get('text', ''))
    expression = normalized_text(output.get('boolean_expression', ''))
    if source_text.upper() in EMPTY_TEXT_VALUES:
        return False
    if expression.upper() in EMPTY_EXPRESSIONS:
        return False
    return True


def sample_records(records: List[Dict[str, Any]], sample_size: int, seed: int) -> List[Dict[str, Any]]:
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


def reference_rows_from_csv(path: Path) -> List[Dict[str, str]]:
    rows = load_csv(path)
    required = set(BASE_FIELDNAMES)
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f'{path} is missing required columns: {sorted(missing)}')

    out = []
    seen_doc_ids = set()
    for row in rows:
        doc_id = normalized_text(row.get('doc_id', ''))
        if not doc_id:
            continue
        if doc_id in seen_doc_ids:
            raise ValueError(f'Duplicate doc_id in reference CSV: {doc_id}')
        seen_doc_ids.add(doc_id)
        out.append({
            'sample_id': normalized_text(row.get('sample_id', '')),
            'doc_id': doc_id,
            'case_bucket': normalized_text(row.get('case_bucket', '')),
            'source_criterion': normalized_text(row.get('source_criterion', '')),
        })
    return out


def reference_rows_from_sample(source_path: Path, cgglc_path: Path, sample_size: int, seed: int) -> List[Dict[str, str]]:
    cgglc_outputs = {row['doc_id']: row for row in load_jsonl(cgglc_path)}
    records = [
        row for row in load_jsonl(source_path)
        if row.get('doc_id') in cgglc_outputs and is_reviewable(row, cgglc_outputs[row['doc_id']])
    ]
    selected = sample_records(records, sample_size, seed)
    return [
        {
            'sample_id': f'H{idx:03d}',
            'doc_id': record['doc_id'],
            'case_bucket': bucket_name(record),
            'source_criterion': normalized_text(record.get('text', '')),
        }
        for idx, record in enumerate(selected, 1)
    ]


def load_method_outputs(boolean_dir: Path, method: str) -> Dict[str, Dict[str, Any]]:
    path = boolean_dir / f'{method}.jsonl'
    if not path.exists():
        raise FileNotFoundError(f'Missing Boolean output file for {method}: {path}')
    return {row['doc_id']: row for row in load_jsonl(path)}


def build_rows(reference_rows: List[Dict[str, str]], method_outputs: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    missing_doc_ids = []
    for ref in reference_rows:
        doc_id = ref['doc_id']
        pred = method_outputs.get(doc_id)
        if pred is None:
            missing_doc_ids.append(doc_id)
            continue
        row = {
            'sample_id': ref['sample_id'],
            'doc_id': doc_id,
            'case_bucket': ref.get('case_bucket', ''),
            'source_criterion': ref.get('source_criterion', ''),
            'candidate_expression': pred.get('boolean_expression', ''),
        }
        for dim in DIMENSIONS:
            row[dim] = ''
        row['reviewer_notes'] = ''
        rows.append(row)

    if missing_doc_ids:
        raise ValueError(f'Missing method outputs for doc_ids: {missing_doc_ids[:10]}')
    return rows


def output_prefix_for_method(method: str, out_prefix: str) -> str:
    if out_prefix:
        return out_prefix
    return f'{method}_human_eval'


def main():
    parser = argparse.ArgumentParser(description='Create human-evaluation CSV templates.')
    parser.add_argument('--source-jsonl', default=str(DEFAULT_SOURCE_JSONL))
    parser.add_argument('--boolean-dir', default=str(DEFAULT_BOOLEAN_DIR))
    parser.add_argument('--out-dir', default=str(DEFAULT_OUT_DIR))
    parser.add_argument('--methods', nargs='+', default=['cgglc'], choices=sorted(METHOD_LABELS))
    parser.add_argument('--reference-csv', default='', help='Reuse sample_id/doc_id/source text from an existing human-eval CSV.')
    parser.add_argument('--out-prefix', default='', help='Optional output prefix; only use with a single method.')
    parser.add_argument('--reviewer-count', type=int, default=2)
    parser.add_argument('--sample-size', type=int, default=50)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--skip-existing', action='store_true', help='Leave existing reviewer CSV files unchanged.')
    args = parser.parse_args()

    if args.reviewer_count < 1:
        raise ValueError('--reviewer-count must be at least 1')
    if args.out_prefix and len(args.methods) != 1:
        raise ValueError('--out-prefix can only be used when exactly one method is requested.')

    if args.reference_csv:
        reference_rows = reference_rows_from_csv(Path(args.reference_csv))
    else:
        reference_rows = reference_rows_from_sample(
            Path(args.source_jsonl),
            Path(args.boolean_dir) / 'cgglc.jsonl',
            args.sample_size,
            args.seed,
        )

    fieldnames = BASE_FIELDNAMES + DIMENSIONS + ['reviewer_notes']
    out_dir = Path(args.out_dir)
    out_paths = []
    for method in args.methods:
        method_outputs = load_method_outputs(Path(args.boolean_dir), method)
        rows = build_rows(reference_rows, method_outputs)
        prefix = output_prefix_for_method(method, args.out_prefix)
        for reviewer_idx in range(1, args.reviewer_count + 1):
            out_path = out_dir / f'{prefix}_{reviewer_idx}.csv'
            if write_csv(rows, out_path, fieldnames, overwrite=args.overwrite, skip_existing=args.skip_existing):
                out_paths.append(out_path)

    print(json.dumps([str(path) for path in out_paths], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
