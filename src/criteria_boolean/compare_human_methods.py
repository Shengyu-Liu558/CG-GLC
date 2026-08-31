#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize paired human scores and GPT-human agreement for all methods."""

import argparse
import csv
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HUMAN_DIR = PROJECT_ROOT / 'results' / 'human_eval'
DEFAULT_GPT_PER_ITEM = PROJECT_ROOT / 'results' / 'llm_eval' / 'llm_judge_per_item.csv'
DEFAULT_METHODS = ['flat', 'or_direct', 'constraint', 'cgglc']
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

BASE_FIELDS = [
    'sample_id',
    'doc_id',
    'method_key',
    'method_label',
    'case_bucket',
    'source_criterion',
    'candidate_expression',
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    last_error = None
    for encoding in ('utf-8-sig', 'utf-8', 'gb18030', 'cp936'):
        try:
            with path.open('r', encoding=encoding, newline='') as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError as exc:
            last_error = exc
    raise last_error


def write_csv(rows: List[Dict[str, object]], path: Path, fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def score_or_none(value) -> Optional[float]:
    text = str(value or '').strip()
    if text == '':
        return None
    score = float(text)
    if score not in (0.0, 1.0, 2.0):
        raise ValueError(f'Human evaluation scores must be 0, 1, or 2; got {text!r}')
    return score


def number_or_none(value) -> Optional[float]:
    text = str(value or '').strip()
    if text == '':
        return None
    return float(text)


def avg(values: Iterable[float]) -> Optional[float]:
    values = list(values)
    return sum(values) / len(values) if values else None


def rounded(value: Optional[float]) -> object:
    if value is None:
        return ''
    return round(value, 6)


def pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) < 2:
        return None
    x_mean = avg(xs)
    y_mean = avg(ys)
    if x_mean is None or y_mean is None:
        return None
    x_var = sum((x - x_mean) ** 2 for x in xs)
    y_var = sum((y - y_mean) ** 2 for y in ys)
    if x_var == 0 or y_var == 0:
        return None
    cov = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    return cov / math.sqrt(x_var * y_var)


def ranks(values: List[float]) -> List[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    out = [0.0] * len(values)
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][1] == ordered[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            out[ordered[k][0]] = avg_rank
        i = j
    return out


def spearman(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) < 2:
        return None
    return pearson(ranks(xs), ranks(ys))


def compare_series(left: List[float], right: List[float]) -> Dict[str, object]:
    diffs = [r - l for l, r in zip(left, right)]
    abs_diffs = [abs(diff) for diff in diffs]
    return {
        'n': len(left),
        'left_mean': rounded(avg(left)),
        'right_mean': rounded(avg(right)),
        'right_minus_left_mean': rounded(avg(diffs)),
        'mean_abs_diff': rounded(avg(abs_diffs)),
        'exact_agreement': rounded(sum(1 for diff in diffs if diff == 0) / len(diffs)) if diffs else '',
        'within_1': rounded(sum(1 for diff in abs_diffs if diff <= 1) / len(abs_diffs)) if abs_diffs else '',
        'within_2': rounded(sum(1 for diff in abs_diffs if diff <= 2) / len(abs_diffs)) if abs_diffs else '',
        'pearson': rounded(pearson(left, right)),
        'spearman': rounded(spearman(left, right)),
    }


def one_sided_sign_test_p(wins: int, losses: int) -> object:
    """Exact sign test for H1: CG-GLC is more often higher than the baseline."""
    n = wins + losses
    if n == 0:
        return ''
    probability = sum(math.comb(n, k) for k in range(wins, n + 1)) / (2 ** n)
    return f'{probability:.12g}'


def item_key(row: Dict[str, object]) -> Tuple[str, str]:
    return str(row.get('sample_id', '')), str(row.get('doc_id', ''))


def load_method_reviewers(human_dir: Path, method: str) -> List[Dict[str, object]]:
    files = [human_dir / f'{method}_human_eval_1.csv', human_dir / f'{method}_human_eval_2.csv']
    missing = [path for path in files if not path.exists()]
    if missing:
        raise FileNotFoundError(f'Missing reviewer files for {method}: {missing}')

    rows_1 = read_csv(files[0])
    rows_2 = read_csv(files[1])
    by_key_2 = {item_key(row): row for row in rows_2}
    if len(by_key_2) != len(rows_2):
        raise ValueError(f'Duplicate sample_id/doc_id keys in {files[1]}')

    out: List[Dict[str, object]] = []
    for row_1 in rows_1:
        key = item_key(row_1)
        row_2 = by_key_2.get(key)
        if row_2 is None:
            raise ValueError(f'Missing matching reviewer-2 row for {method}: {key}')

        item: Dict[str, object] = {
            'sample_id': row_1.get('sample_id', ''),
            'doc_id': row_1.get('doc_id', ''),
            'method_key': method,
            'method_label': METHOD_LABELS.get(method, method),
            'case_bucket': row_1.get('case_bucket', ''),
            'source_criterion': row_1.get('source_criterion', ''),
            'candidate_expression': row_1.get('candidate_expression', ''),
            'reviewer_1_notes': row_1.get('reviewer_notes', ''),
            'reviewer_2_notes': row_2.get('reviewer_notes', ''),
        }

        complete = True
        for dim in DIMENSIONS:
            score_1 = score_or_none(row_1.get(dim, ''))
            score_2 = score_or_none(row_2.get(dim, ''))
            if score_1 is None or score_2 is None:
                complete = False
                continue
            item[f'{dim}_r1'] = score_1
            item[f'{dim}_r2'] = score_2
            item[f'{dim}_human_mean'] = (score_1 + score_2) / 2.0

        item['complete'] = complete
        if complete:
            item['total_r1'] = sum(float(item[f'{dim}_r1']) for dim in DIMENSIONS)
            item['total_r2'] = sum(float(item[f'{dim}_r2']) for dim in DIMENSIONS)
            item['total_human_mean'] = (float(item['total_r1']) + float(item['total_r2'])) / 2.0
        out.append(item)
    return out


def load_all_human(human_dir: Path, methods: List[str]) -> Dict[str, List[Dict[str, object]]]:
    return {method: load_method_reviewers(human_dir, method) for method in methods}


def complete_items(method_items: Dict[str, List[Dict[str, object]]], methods: List[str]) -> List[Dict[str, object]]:
    return [
        item
        for method in methods
        for item in method_items.get(method, [])
        if item.get('complete')
    ]


def summarize_methods(method_items: Dict[str, List[Dict[str, object]]], methods: List[str]) -> List[Dict[str, object]]:
    rows = []
    for method in methods:
        items = [item for item in method_items.get(method, []) if item.get('complete')]
        row: Dict[str, object] = {
            'method_key': method,
            'method_label': METHOD_LABELS.get(method, method),
            'n_complete': len(items),
        }
        for dim in DIMENSIONS:
            row[f'{dim}_mean'] = rounded(avg(float(item[f'{dim}_human_mean']) for item in items))
        row['reviewer_1_total_mean'] = rounded(avg(float(item['total_r1']) for item in items))
        row['reviewer_2_total_mean'] = rounded(avg(float(item['total_r2']) for item in items))
        row['total_score_mean'] = rounded(avg(float(item['total_human_mean']) for item in items))
        rows.append(row)
    return rows


def paired_vs_cgglc(method_items: Dict[str, List[Dict[str, object]]], methods: List[str]) -> List[Dict[str, object]]:
    cgglc_items = {
        item_key(item): item
        for item in method_items.get('cgglc', [])
        if item.get('complete')
    }
    out = []
    for method in methods:
        if method == 'cgglc':
            continue
        diffs: List[float] = []
        cgglc_scores: List[float] = []
        baseline_scores: List[float] = []
        wins = ties = losses = 0
        for item in method_items.get(method, []):
            if not item.get('complete'):
                continue
            key = item_key(item)
            cgglc_item = cgglc_items.get(key)
            if cgglc_item is None:
                continue
            cgglc_score = float(cgglc_item['total_human_mean'])
            baseline_score = float(item['total_human_mean'])
            diff = cgglc_score - baseline_score
            cgglc_scores.append(cgglc_score)
            baseline_scores.append(baseline_score)
            diffs.append(diff)
            if diff > 0:
                wins += 1
            elif diff < 0:
                losses += 1
            else:
                ties += 1

        non_tie = wins + losses
        out.append({
            'comparison': f'CG-GLC vs {METHOD_LABELS.get(method, method)}',
            'baseline_method_key': method,
            'baseline_method_label': METHOD_LABELS.get(method, method),
            'n_paired_complete': len(diffs),
            'cgglc_total_score_mean': rounded(avg(cgglc_scores)),
            'baseline_total_score_mean': rounded(avg(baseline_scores)),
            'mean_total_score_difference': rounded(avg(diffs)),
            'cgglc_wins': wins,
            'ties': ties,
            'cgglc_losses': losses,
            'non_tie_n': non_tie,
            'cgglc_win_rate_non_tie': rounded(wins / non_tie) if non_tie else '',
            'sign_test_alternative': 'CG-GLC > baseline',
            'sign_test_p_one_sided': one_sided_sign_test_p(wins, losses),
        })
    return out


def human_per_item_rows(items: List[Dict[str, object]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for item in items:
        row = {field: item.get(field, '') for field in BASE_FIELDS}
        for dim in DIMENSIONS:
            row[f'{dim}_r1'] = item.get(f'{dim}_r1', '')
            row[f'{dim}_r2'] = item.get(f'{dim}_r2', '')
            row[f'{dim}_human_mean'] = item.get(f'{dim}_human_mean', '')
        row['total_r1'] = item.get('total_r1', '')
        row['total_r2'] = item.get('total_r2', '')
        row['total_human_mean'] = item.get('total_human_mean', '')
        row['reviewer_1_notes'] = item.get('reviewer_1_notes', '')
        row['reviewer_2_notes'] = item.get('reviewer_2_notes', '')
        rows.append(row)
    return rows


def reviewer_agreement(items: List[Dict[str, object]], methods: List[str]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    groups: List[Tuple[str, str, str, List[Dict[str, object]]]] = [('overall', 'all', 'All methods', items)]
    for method in methods:
        groups.append((
            'by_method',
            method,
            METHOD_LABELS.get(method, method),
            [item for item in items if item.get('method_key') == method],
        ))

    for group, method_key, method_label, group_items in groups:
        targets = [('total_score', 'total_r1', 'total_r2')]
        targets.extend((dim, f'{dim}_r1', f'{dim}_r2') for dim in DIMENSIONS)
        for target, left_field, right_field in targets:
            left = [float(item[left_field]) for item in group_items if left_field in item and right_field in item]
            right = [float(item[right_field]) for item in group_items if left_field in item and right_field in item]
            metrics = compare_series(left, right)
            rows.append({
                'group': group,
                'method_key': method_key,
                'method_label': method_label,
                'target': target,
                'n': metrics['n'],
                'reviewer_1_mean': metrics['left_mean'],
                'reviewer_2_mean': metrics['right_mean'],
                'reviewer_2_minus_reviewer_1_mean': metrics['right_minus_left_mean'],
                'mean_abs_diff': metrics['mean_abs_diff'],
                'exact_agreement': metrics['exact_agreement'],
                'within_1': metrics['within_1'],
                'within_2': metrics['within_2'],
                'pearson': metrics['pearson'],
                'spearman': metrics['spearman'],
            })
    return rows


def load_gpt_scores(path: Path) -> Dict[Tuple[str, str], Dict[str, str]]:
    rows = read_csv(path)
    out: Dict[Tuple[str, str], Dict[str, str]] = {}
    for row in rows:
        key = (row.get('doc_id', ''), row.get('method_key', ''))
        if key in out:
            raise ValueError(f'Duplicate GPT row for doc/method key: {key}')
        out[key] = row
    return out


def add_gpt_scores(items: List[Dict[str, object]], gpt_by_key: Dict[Tuple[str, str], Dict[str, str]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for item in items:
        gpt = gpt_by_key.get((str(item.get('doc_id', '')), str(item.get('method_key', ''))))
        if gpt is None:
            continue
        row = {field: item.get(field, '') for field in BASE_FIELDS}
        row['candidate_id'] = gpt.get('candidate_id', '')
        for dim in DIMENSIONS:
            human_score = float(item[f'{dim}_human_mean'])
            gpt_score = number_or_none(gpt.get(dim, ''))
            row[f'{dim}_human_mean'] = human_score
            row[f'{dim}_gpt'] = gpt_score if gpt_score is not None else ''
            row[f'{dim}_gpt_minus_human'] = (gpt_score - human_score) if gpt_score is not None else ''
        human_total = float(item['total_human_mean'])
        gpt_total = number_or_none(gpt.get('total_score', ''))
        if gpt_total is None:
            dim_scores = [number_or_none(gpt.get(dim, '')) for dim in DIMENSIONS]
            if all(score is not None for score in dim_scores):
                gpt_total = sum(float(score) for score in dim_scores)
        row['total_human_mean'] = human_total
        row['total_gpt'] = gpt_total if gpt_total is not None else ''
        row['total_gpt_minus_human'] = (gpt_total - human_total) if gpt_total is not None else ''
        row['error_flags'] = gpt.get('error_flags', '')
        row['brief_rationale'] = gpt.get('brief_rationale', '')
        rows.append(row)
    return rows


def gpt_human_agreement(rows: List[Dict[str, object]], methods: List[str]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    groups: List[Tuple[str, str, str, List[Dict[str, object]]]] = [('overall', 'all', 'All methods', rows)]
    for method in methods:
        groups.append((
            'by_method',
            method,
            METHOD_LABELS.get(method, method),
            [row for row in rows if row.get('method_key') == method],
        ))

    for group, method_key, method_label, group_rows in groups:
        targets = [('total_score', 'total_human_mean', 'total_gpt')]
        targets.extend((dim, f'{dim}_human_mean', f'{dim}_gpt') for dim in DIMENSIONS)
        for target, left_field, right_field in targets:
            pairs = [
                (float(row[left_field]), float(row[right_field]))
                for row in group_rows
                if row.get(left_field, '') != '' and row.get(right_field, '') != ''
            ]
            left = [pair[0] for pair in pairs]
            right = [pair[1] for pair in pairs]
            metrics = compare_series(left, right)
            out.append({
                'group': group,
                'method_key': method_key,
                'method_label': method_label,
                'target': target,
                'n': metrics['n'],
                'human_mean': metrics['left_mean'],
                'gpt_mean': metrics['right_mean'],
                'gpt_minus_human_mean': metrics['right_minus_left_mean'],
                'mean_abs_diff': metrics['mean_abs_diff'],
                'exact_agreement': metrics['exact_agreement'],
                'within_1': metrics['within_1'],
                'within_2': metrics['within_2'],
                'pearson': metrics['pearson'],
                'spearman': metrics['spearman'],
            })
    return out


def main():
    parser = argparse.ArgumentParser(description='Compare paired human scores across Boolean compilation methods.')
    parser.add_argument('--human-dir', default=str(DEFAULT_HUMAN_DIR))
    parser.add_argument('--gpt-per-item', default=str(DEFAULT_GPT_PER_ITEM))
    parser.add_argument('--methods', nargs='+', default=DEFAULT_METHODS, choices=sorted(METHOD_LABELS))
    parser.add_argument('--human-per-item-out', default=str(DEFAULT_HUMAN_DIR / 'human_eval_per_item_200.csv'))
    parser.add_argument('--summary-out', default=str(DEFAULT_HUMAN_DIR / 'human_eval_summary_by_method.csv'))
    parser.add_argument('--paired-out', default=str(DEFAULT_HUMAN_DIR / 'human_eval_paired_vs_cgglc.csv'))
    parser.add_argument('--reviewer-agreement-out', default=str(DEFAULT_HUMAN_DIR / 'human_eval_reviewer_agreement.csv'))
    parser.add_argument('--gpt-human-items-out', default=str(DEFAULT_HUMAN_DIR / 'gpt_human_eval_200.csv'))
    parser.add_argument('--gpt-human-summary-out', default=str(DEFAULT_HUMAN_DIR / 'gpt_human_agreement_200.csv'))
    args = parser.parse_args()

    human_dir = Path(args.human_dir)
    methods = list(args.methods)
    method_items = load_all_human(human_dir, methods)
    items = complete_items(method_items, methods)

    summary_rows = summarize_methods(method_items, methods)
    paired_rows = paired_vs_cgglc(method_items, methods)
    human_rows = human_per_item_rows(items)
    agreement_rows = reviewer_agreement(items, methods)

    gpt_by_key = load_gpt_scores(Path(args.gpt_per_item))
    gpt_human_rows = add_gpt_scores(items, gpt_by_key)
    gpt_human_summary_rows = gpt_human_agreement(gpt_human_rows, methods)

    score_triplets = [f'{dim}_{suffix}' for dim in DIMENSIONS for suffix in ('r1', 'r2', 'human_mean')]
    write_csv(
        human_rows,
        Path(args.human_per_item_out),
        BASE_FIELDS + score_triplets + ['total_r1', 'total_r2', 'total_human_mean', 'reviewer_1_notes', 'reviewer_2_notes'],
    )
    write_csv(
        summary_rows,
        Path(args.summary_out),
        ['method_key', 'method_label', 'n_complete']
        + [f'{dim}_mean' for dim in DIMENSIONS]
        + ['reviewer_1_total_mean', 'reviewer_2_total_mean', 'total_score_mean'],
    )
    write_csv(
        paired_rows,
        Path(args.paired_out),
        [
            'comparison',
            'baseline_method_key',
            'baseline_method_label',
            'n_paired_complete',
            'cgglc_total_score_mean',
            'baseline_total_score_mean',
            'mean_total_score_difference',
            'cgglc_wins',
            'ties',
            'cgglc_losses',
            'non_tie_n',
            'cgglc_win_rate_non_tie',
            'sign_test_alternative',
            'sign_test_p_one_sided',
        ],
    )
    write_csv(
        agreement_rows,
        Path(args.reviewer_agreement_out),
        [
            'group',
            'method_key',
            'method_label',
            'target',
            'n',
            'reviewer_1_mean',
            'reviewer_2_mean',
            'reviewer_2_minus_reviewer_1_mean',
            'mean_abs_diff',
            'exact_agreement',
            'within_1',
            'within_2',
            'pearson',
            'spearman',
        ],
    )

    gpt_fields = [f'{dim}_{suffix}' for dim in DIMENSIONS for suffix in ('human_mean', 'gpt', 'gpt_minus_human')]
    write_csv(
        gpt_human_rows,
        Path(args.gpt_human_items_out),
        BASE_FIELDS
        + ['candidate_id']
        + gpt_fields
        + ['total_human_mean', 'total_gpt', 'total_gpt_minus_human', 'error_flags', 'brief_rationale'],
    )
    write_csv(
        gpt_human_summary_rows,
        Path(args.gpt_human_summary_out),
        [
            'group',
            'method_key',
            'method_label',
            'target',
            'n',
            'human_mean',
            'gpt_mean',
            'gpt_minus_human_mean',
            'mean_abs_diff',
            'exact_agreement',
            'within_1',
            'within_2',
            'pearson',
            'spearman',
        ],
    )

    print(args.human_per_item_out)
    print(args.summary_out)
    print(args.paired_out)
    print(args.reviewer_agreement_out)
    print(args.gpt_human_items_out)
    print(args.gpt_human_summary_out)
    print(f'complete_human_items={len(items)} matched_gpt_items={len(gpt_human_rows)}')


if __name__ == '__main__':
    main()
