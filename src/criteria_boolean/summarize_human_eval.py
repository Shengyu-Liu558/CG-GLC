#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize filled CG-GLC human evaluation scores from reviewer files."""

import argparse
import csv
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REVIEWER_FILES = [
    PROJECT_ROOT / 'results' / 'human_eval' / 'cgglc_human_eval_1.csv',
    PROJECT_ROOT / 'results' / 'human_eval' / 'cgglc_human_eval_2.csv',
]
DEFAULT_OUT = PROJECT_ROOT / 'results' / 'human_eval' / 'cgglc_human_eval_summary.csv'

DIMENSIONS = [
    'predicate_completeness',
    'logical_correctness',
    'grouping_correctness',
    'faithfulness',
    'downstream_usability',
]

KEY_FIELDS = ['sample_id', 'doc_id']


def to_score(value) -> Optional[float]:
    value = str(value).strip()
    if value == '':
        return None
    score = float(value)
    if score not in (0.0, 1.0, 2.0):
        raise ValueError(f'Human evaluation scores must be 0, 1, or 2; got {value!r}')
    return score


def load_csv(path: Path) -> List[Dict[str, str]]:
    last_error = None
    for encoding in ('utf-8-sig', 'utf-8', 'gb18030', 'cp936'):
        try:
            with path.open('r', encoding=encoding, newline='') as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError as exc:
            last_error = exc
    raise last_error


def item_key(row: Dict[str, str]) -> Tuple[str, str]:
    return tuple(row.get(field, '') for field in KEY_FIELDS)


def load_reviewer_files(paths: List[Path]):
    reviewers = []
    for idx, path in enumerate(paths, 1):
        rows = load_csv(path)
        by_key = {item_key(row): row for row in rows}
        if len(by_key) != len(rows):
            raise ValueError(f'Duplicate sample_id/doc_id keys in {path}')
        reviewers.append({
            'label': f'r{idx}',
            'path': path,
            'rows': rows,
            'by_key': by_key,
        })
    return reviewers


def aligned_keys(reviewers) -> List[Tuple[str, str]]:
    first_keys = [item_key(row) for row in reviewers[0]['rows']]
    first_set = set(first_keys)
    for reviewer in reviewers[1:]:
        keys = set(reviewer['by_key'])
        if keys != first_set:
            missing = sorted(first_set - keys)[:5]
            extra = sorted(keys - first_set)[:5]
            raise ValueError(
                f'Reviewer files do not contain the same sample_id/doc_id keys. '
                f'Missing examples: {missing}; extra examples: {extra}'
            )
    return first_keys


def row_total(row: Dict[str, str]) -> Optional[float]:
    values = [to_score(row.get(dim, '')) for dim in DIMENSIONS]
    if any(value is None for value in values):
        return None
    return sum(value for value in values if value is not None)


def write_csv(rows: List[Dict[str, object]], path: Path, fieldnames: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(reviewers, keys):
    summary = {
        'n_items': len(keys),
        'n_reviewers': len(reviewers),
    }

    for dim in DIMENSIONS:
        all_values = []
        paired = []
        for key in keys:
            values = []
            for reviewer in reviewers:
                value = to_score(reviewer['by_key'][key].get(dim, ''))
                if value is not None:
                    values.append(value)
                    all_values.append(value)
            if len(values) == len(reviewers):
                paired.append(values)
        summary[f'{dim}_mean'] = mean(all_values) if all_values else ''
        if len(reviewers) == 2 and paired:
            summary[f'{dim}_exact_agreement'] = sum(1 for values in paired if values[0] == values[1]) / len(paired)
            summary[f'{dim}_mean_abs_diff'] = mean(abs(values[0] - values[1]) for values in paired)
        else:
            summary[f'{dim}_exact_agreement'] = ''
            summary[f'{dim}_mean_abs_diff'] = ''

    totals_by_reviewer = {reviewer['label']: [] for reviewer in reviewers}
    paired_totals = []
    for key in keys:
        item_totals = []
        complete = True
        for reviewer in reviewers:
            label = reviewer['label']
            row = reviewer['by_key'][key]
            total = row_total(row)
            if total is None:
                complete = False
            else:
                totals_by_reviewer[label].append(total)
                item_totals.append(total)
        if complete:
            paired_totals.append(item_totals)

    for reviewer in reviewers:
        label = reviewer['label']
        values = totals_by_reviewer[label]
        summary[f'total_score_mean_{label}'] = mean(values) if values else ''

    all_totals = [value for values in totals_by_reviewer.values() for value in values]
    summary['total_score_mean'] = mean(all_totals) if all_totals else ''
    summary['n_items_scored_by_all_reviewers'] = len(paired_totals)
    if len(reviewers) == 2 and paired_totals:
        summary['total_score_exact_agreement'] = sum(1 for values in paired_totals if values[0] == values[1]) / len(paired_totals)
        summary['total_score_mean_abs_diff'] = mean(abs(values[0] - values[1]) for values in paired_totals)
    else:
        summary['total_score_exact_agreement'] = ''
        summary['total_score_mean_abs_diff'] = ''

    return summary


def main():
    parser = argparse.ArgumentParser(description='Summarize filled human evaluation reviewer files.')
    parser.add_argument(
        '--reviewer-files',
        nargs='+',
        default=[str(path) for path in DEFAULT_REVIEWER_FILES],
        help='Filled reviewer CSV files to summarize.'
    )
    parser.add_argument('--out', default=str(DEFAULT_OUT))
    args = parser.parse_args()

    reviewers = load_reviewer_files([Path(path) for path in args.reviewer_files])
    if not reviewers:
        raise ValueError('At least one reviewer file is required.')
    keys = aligned_keys(reviewers)
    summary = summarize(reviewers, keys)

    summary_path = Path(args.out)
    write_csv([summary], summary_path, list(summary.keys()))

    print(str(summary_path))


if __name__ == '__main__':
    main()
