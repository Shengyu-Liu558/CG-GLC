#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize LLM-judge scores by method and paired comparison against CG-GLC."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = PROJECT_ROOT / 'results' / 'llm_eval' / 'llm_judge_results.jsonl'
DEFAULT_KEY = PROJECT_ROOT / 'data' / 'evaluation' / 'llm_judge' / 'llm_eval_key.csv'
DEFAULT_OUT_DIR = PROJECT_ROOT / 'results' / 'llm_eval'

DIMENSIONS = [
    'predicate_completeness',
    'logical_correctness',
    'grouping_correctness',
    'faithfulness',
    'downstream_usability',
    'total_score',
]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(rows, path: Path, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_error_flags(value) -> str:
    if value is None:
        return ''
    if isinstance(value, list):
        return ';'.join(str(item) for item in value)
    return str(value)


def merge_results(results, key_rows):
    key = {row['candidate_id']: row for row in key_rows}
    merged = []
    for row in results:
        candidate_id = row.get('candidate_id')
        if candidate_id not in key:
            continue
        scores = row.get('scores')
        if not isinstance(scores, dict):
            scores = row
        total = scores.get('total_score')
        if total is None:
            total = sum(scores.get(name, 0) for name in DIMENSIONS if name != 'total_score')
        merged.append({
            **key[candidate_id],
            'candidate_id': candidate_id,
            'doc_id': row.get('doc_id') or key[candidate_id].get('doc_id'),
            'case_bucket': row.get('case_bucket') or key[candidate_id].get('case_bucket'),
            **{name: float(scores.get(name, 0)) for name in DIMENSIONS if name != 'total_score'},
            'total_score': float(total),
            'error_flags': normalize_error_flags(scores.get('error_flags')),
            'brief_rationale': scores.get('brief_rationale', ''),
        })
    return merged


def summarize_by_method(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['method_key']].append(row)

    out = []
    for method_key, items in groups.items():
        row = {
            'method_key': method_key,
            'method_label': items[0]['method_label'],
            'n': len(items),
        }
        for dim in DIMENSIONS:
            row[f'{dim}_mean'] = mean(item[dim] for item in items)
        out.append(row)
    return sorted(out, key=lambda r: r['total_score_mean'], reverse=True)


def paired_vs_cgglc(rows):
    by_doc = defaultdict(dict)
    for row in rows:
        by_doc[row['doc_id']][row['method_key']] = row

    methods = sorted({row['method_key'] for row in rows if row['method_key'] != 'cgglc'})
    out = []
    for method in methods:
        diffs = []
        wins = ties = losses = 0
        n = 0
        for doc_id, doc_rows in by_doc.items():
            if 'cgglc' not in doc_rows or method not in doc_rows:
                continue
            n += 1
            ours = doc_rows['cgglc']['total_score']
            other = doc_rows[method]['total_score']
            diffs.append(ours - other)
            if ours > other:
                wins += 1
            elif ours < other:
                losses += 1
            else:
                ties += 1
        if n:
            out.append({
                'comparison': f'CG-GLC vs {method}',
                'n': n,
                'mean_total_score_difference': mean(diffs),
                'cgglc_wins': wins,
                'ties': ties,
                'cgglc_losses': losses,
            })
    return out


def main():
    parser = argparse.ArgumentParser(description='Summarize LLM judge outputs.')
    parser.add_argument('--results', default=str(DEFAULT_RESULTS))
    parser.add_argument('--key', default=str(DEFAULT_KEY))
    parser.add_argument('--out-dir', default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    merged = merge_results(load_jsonl(Path(args.results)), load_csv(Path(args.key)))
    out_dir = Path(args.out_dir)
    write_csv(
        merged,
        out_dir / 'llm_judge_per_item.csv',
        ['candidate_id', 'doc_id', 'method_key', 'method_label', 'case_bucket'] + DIMENSIONS + ['error_flags', 'brief_rationale']
    )
    write_csv(
        summarize_by_method(merged),
        out_dir / 'llm_judge_summary_by_method.csv',
        ['method_key', 'method_label', 'n'] + [f'{name}_mean' for name in DIMENSIONS]
    )
    write_csv(
        paired_vs_cgglc(merged),
        out_dir / 'llm_judge_paired_vs_cgglc.csv',
        ['comparison', 'n', 'mean_total_score_difference', 'cgglc_wins', 'ties', 'cgglc_losses']
    )
    print(str(out_dir))


if __name__ == '__main__':
    main()
