#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a blinded source-conditioned dataset for LLM judging."""

import argparse
import csv
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_JSONL = PROJECT_ROOT / 'data' / 'processed' / 'source_criteria.jsonl'
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / 'data' / 'processed' / 'boolean_outputs'
DEFAULT_OUT_DIR = PROJECT_ROOT / 'data' / 'evaluation' / 'llm_judge'

DEFAULT_METHODS = [
    ('flat', 'Flat'),
    ('or_direct', 'OR-direct'),
    ('constraint', 'Constraint'),
    ('cgglc', 'CG-GLC'),
]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(rows: Iterable[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


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


def sample_records(records: List[Dict[str, Any]], sample_size: int, seed: int, full_dataset: bool):
    if full_dataset or sample_size >= len(records):
        return list(records)

    rng = random.Random(seed)
    buckets = {'or': [], 'scope': [], 'other': []}
    for record in records:
        buckets[bucket_name(record)].append(record)

    targets = {
        'or': int(sample_size * 0.5),
        'scope': int(sample_size * 0.3),
        'other': sample_size,
    }
    targets['other'] = sample_size - targets['or'] - targets['scope']

    chosen = []
    for name in ('or', 'scope', 'other'):
        bucket = buckets[name]
        k = min(targets[name], len(bucket))
        chosen.extend(rng.sample(bucket, k))

    chosen_ids = {row['doc_id'] for row in chosen}
    remaining = [row for row in records if row['doc_id'] not in chosen_ids]
    if len(chosen) < sample_size and remaining:
        chosen.extend(rng.sample(remaining, min(sample_size - len(chosen), len(remaining))))

    rng.shuffle(chosen)
    return chosen[:sample_size]


def load_method_outputs(output_dir: Path, methods):
    outputs = {}
    for method_key, _ in methods:
        path = output_dir / f'{method_key}.jsonl'
        if not path.exists():
            raise FileNotFoundError(f'Missing method output: {path}')
        outputs[method_key] = {row['doc_id']: row for row in load_jsonl(path)}
    return outputs


def parse_methods(values):
    label_by_key = dict(DEFAULT_METHODS)
    methods = []
    for value in values:
        if value not in label_by_key:
            raise ValueError(f'Unknown method: {value}')
        methods.append((value, label_by_key[value]))
    return methods


def build_dataset(args):
    methods = parse_methods(args.methods)
    source_rows = load_jsonl(Path(args.source_jsonl))
    selected = sample_records(source_rows, args.sample_size, args.seed, args.full_dataset)
    outputs = load_method_outputs(Path(args.output_dir), methods)

    items = []
    key_rows = []
    for record in selected:
        doc_id = record['doc_id']
        for method_key, method_label in methods:
            pred = outputs[method_key].get(doc_id)
            if pred is None:
                continue
            items.append({
                'doc_id': doc_id,
                'trial_id': record.get('trial_id'),
                'section': record.get('section'),
                'source_criterion': ' '.join(str(record.get('text', '')).split()),
                'candidate_expression': pred.get('boolean_expression', ''),
                'candidate_ast': pred.get('boolean_ast'),
                'case_bucket': bucket_name(record),
            })
            key_rows.append({
                'doc_id': doc_id,
                'method_key': method_key,
                'method_label': method_label,
                'case_bucket': bucket_name(record),
            })

    rng = random.Random(args.seed + 1009)
    paired = list(zip(items, key_rows))
    rng.shuffle(paired)

    blinded_items = []
    blinded_key = []
    for idx, (item, key) in enumerate(paired, 1):
        candidate_id = f'LLM{idx:05d}'
        item['candidate_id'] = candidate_id
        key['candidate_id'] = candidate_id
        blinded_items.append(item)
        blinded_key.append(key)

    out_dir = Path(args.out_dir)
    write_jsonl(blinded_items, out_dir / 'llm_eval_items.jsonl')
    with (out_dir / 'llm_eval_key.csv').open('w', encoding='utf-8-sig', newline='') as f:
        fieldnames = ['candidate_id', 'doc_id', 'method_key', 'method_label', 'case_bucket']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(blinded_key)

    manifest = {
        'source_jsonl': str(Path(args.source_jsonl).relative_to(PROJECT_ROOT)),
        'sample_size': len(selected),
        'num_eval_items': len(blinded_items),
        'methods': [{'method_key': k, 'method_label': v} for k, v in methods],
        'seed': args.seed,
        'full_dataset': args.full_dataset,
    }
    (out_dir / 'llm_eval_manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description='Prepare blinded LLM-judge evaluation items.')
    parser.add_argument('--source-jsonl', default=str(DEFAULT_SOURCE_JSONL))
    parser.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument('--out-dir', default=str(DEFAULT_OUT_DIR))
    parser.add_argument('--sample-size', type=int, default=100)
    parser.add_argument('--full-dataset', action='store_true')
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--methods', nargs='+', default=[key for key, _ in DEFAULT_METHODS])
    args = parser.parse_args()

    manifest = build_dataset(args)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
