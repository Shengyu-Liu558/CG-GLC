#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare GPT scores with two-reviewer human scores for CG-GLC samples."""

import argparse
import csv
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REVIEWER_FILES = [
    PROJECT_ROOT / 'results' / 'human_eval' / 'cgglc_human_eval_1.csv',
    PROJECT_ROOT / 'results' / 'human_eval' / 'cgglc_human_eval_2.csv',
]
DEFAULT_GPT_PER_ITEM = PROJECT_ROOT / 'results' / 'llm_eval' / 'llm_judge_per_item.csv'
DEFAULT_OUT = PROJECT_ROOT / 'results' / 'llm_eval' / 'gpt_human_agreement_summary.csv'

DIMENSIONS = [
    'predicate_completeness',
    'logical_correctness',
    'grouping_correctness',
    'faithfulness',
    'downstream_usability',
]

KEY_FIELDS = ['sample_id', 'doc_id']


def read_csv(path: Path) -> List[Dict[str, str]]:
    last_error = None
    for encoding in ('utf-8-sig', 'utf-8', 'gb18030', 'cp936'):
        try:
            with path.open('r', encoding=encoding, newline='') as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError as exc:
            last_error = exc
    raise last_error


def write_csv(rows: List[Dict[str, object]], path: Path, fieldnames: List[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def item_key(row: Dict[str, str]) -> Tuple[str, str]:
    return tuple(row.get(field, '') for field in KEY_FIELDS)


def to_score(value) -> Optional[float]:
    text = str(value or '').strip()
    if text == '':
        return None
    score = float(text)
    if score not in (0.0, 1.0, 2.0):
        raise ValueError(f'Scores must be 0, 1, or 2; got {text!r}')
    return score


def to_number(value) -> Optional[float]:
    text = str(value or '').strip()
    if text == '':
        return None
    return float(text)


def mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) < 2:
        return None
    x_mean = mean(xs)
    y_mean = mean(ys)
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


def quadratic_weighted_kappa(xs: List[float], ys: List[float]) -> Optional[float]:
    categories = [0, 1, 2]
    if not xs:
        return None
    if any(x not in categories or y not in categories for x, y in zip(xs, ys)):
        return None

    n = len(xs)
    observed = [[0.0 for _ in categories] for _ in categories]
    left_counts = [0.0 for _ in categories]
    right_counts = [0.0 for _ in categories]
    index = {category: idx for idx, category in enumerate(categories)}

    for x, y in zip(xs, ys):
        i = index[int(x)]
        j = index[int(y)]
        observed[i][j] += 1
        left_counts[i] += 1
        right_counts[j] += 1

    def weight(i: int, j: int) -> float:
        return ((i - j) / (len(categories) - 1)) ** 2

    observed_disagreement = sum(
        weight(i, j) * observed[i][j] / n
        for i in range(len(categories))
        for j in range(len(categories))
    )
    expected_disagreement = sum(
        weight(i, j) * (left_counts[i] / n) * (right_counts[j] / n)
        for i in range(len(categories))
        for j in range(len(categories))
    )
    if expected_disagreement == 0:
        return None
    return 1 - observed_disagreement / expected_disagreement


def rounded(value: Optional[float]):
    if value is None:
        return ''
    return round(value, 6)


def compare_series(left: List[float], right: List[float], include_kappa: bool = False) -> Dict[str, object]:
    diffs = [r - l for l, r in zip(left, right)]
    abs_diffs = [abs(diff) for diff in diffs]
    return {
        'n': len(left),
        'left_mean': rounded(mean(left)),
        'right_mean': rounded(mean(right)),
        'right_minus_left_mean': rounded(mean(diffs)),
        'mean_abs_diff': rounded(mean(abs_diffs)),
        'exact_agreement': rounded(sum(1 for diff in diffs if diff == 0) / len(diffs)) if diffs else '',
        'within_1': rounded(sum(1 for diff in abs_diffs if diff <= 1) / len(abs_diffs)) if abs_diffs else '',
        'within_2': rounded(sum(1 for diff in abs_diffs if diff <= 2) / len(abs_diffs)) if abs_diffs else '',
        'pearson': rounded(pearson(left, right)),
        'spearman': rounded(spearman(left, right)),
        'quadratic_weighted_kappa': rounded(quadratic_weighted_kappa(left, right)) if include_kappa else '',
    }


def load_reviewer_files(paths: List[Path]):
    reviewers = []
    for idx, path in enumerate(paths, 1):
        rows = read_csv(path)
        by_key = {item_key(row): row for row in rows}
        if len(by_key) != len(rows):
            raise ValueError(f'Duplicate sample_id/doc_id keys in {path}')
        reviewers.append({'label': f'r{idx}', 'path': path, 'rows': rows, 'by_key': by_key})
    if len(reviewers) != 2:
        raise ValueError('GPT-human comparison expects exactly two reviewer files.')

    keys = [item_key(row) for row in reviewers[0]['rows']]
    key_set = set(keys)
    for reviewer in reviewers[1:]:
        if set(reviewer['by_key']) != key_set:
            raise ValueError('Reviewer files do not contain the same sample_id/doc_id keys.')
    return reviewers, keys


def load_gpt_cgglc(path: Path) -> Dict[str, Dict[str, str]]:
    rows = read_csv(path)
    return {row['doc_id']: row for row in rows if row.get('method_key') == 'cgglc'}


def build_matched_items(reviewers, keys, gpt_by_doc):
    matched = []
    skipped = []
    for key in keys:
        sample_id, doc_id = key
        gpt_row = gpt_by_doc.get(doc_id)
        if gpt_row is None:
            skipped.append({'sample_id': sample_id, 'doc_id': doc_id, 'reason': 'missing_gpt_cgglc'})
            continue

        r1 = reviewers[0]['by_key'][key]
        r2 = reviewers[1]['by_key'][key]
        item = {
            'sample_id': sample_id,
            'doc_id': doc_id,
            'case_bucket': r1.get('case_bucket', '') or gpt_row.get('case_bucket', ''),
        }
        complete = True
        for dim in DIMENSIONS:
            score_1 = to_score(r1.get(dim, ''))
            score_2 = to_score(r2.get(dim, ''))
            gpt_score = to_number(gpt_row.get(dim, ''))
            if score_1 is None or score_2 is None or gpt_score is None:
                complete = False
                continue
            item[f'{dim}_r1'] = score_1
            item[f'{dim}_r2'] = score_2
            item[f'{dim}_human_mean'] = (score_1 + score_2) / 2
            item[f'{dim}_gpt'] = gpt_score
        if not complete:
            skipped.append({'sample_id': sample_id, 'doc_id': doc_id, 'reason': 'incomplete_scores'})
            continue
        item['total_r1'] = sum(item[f'{dim}_r1'] for dim in DIMENSIONS)
        item['total_r2'] = sum(item[f'{dim}_r2'] for dim in DIMENSIONS)
        item['total_human_mean'] = (item['total_r1'] + item['total_r2']) / 2
        item['total_gpt'] = to_number(gpt_row.get('total_score'))
        if item['total_gpt'] is None:
            item['total_gpt'] = sum(item[f'{dim}_gpt'] for dim in DIMENSIONS)
        matched.append(item)
    return matched, skipped


def add_summary_row(rows, section, target, left_label, right_label, left, right, include_kappa=False):
    row = {
        'section': section,
        'target': target,
        'left_label': left_label,
        'right_label': right_label,
    }
    row.update(compare_series(left, right, include_kappa=include_kappa))
    rows.append(row)


def summarize(matched):
    rows = []
    add_summary_row(
        rows,
        'human_human',
        'total_score',
        'reviewer_1',
        'reviewer_2',
        [item['total_r1'] for item in matched],
        [item['total_r2'] for item in matched],
    )
    for dim in DIMENSIONS:
        add_summary_row(
            rows,
            'human_human',
            dim,
            'reviewer_1',
            'reviewer_2',
            [item[f'{dim}_r1'] for item in matched],
            [item[f'{dim}_r2'] for item in matched],
            include_kappa=True,
        )

    add_summary_row(
        rows,
        'gpt_human',
        'total_score',
        'human_mean',
        'gpt',
        [item['total_human_mean'] for item in matched],
        [item['total_gpt'] for item in matched],
    )
    for dim in DIMENSIONS:
        add_summary_row(
            rows,
            'gpt_human',
            dim,
            'human_mean',
            'gpt',
            [item[f'{dim}_human_mean'] for item in matched],
            [item[f'{dim}_gpt'] for item in matched],
        )

    for bucket in sorted({item['case_bucket'] for item in matched}):
        bucket_items = [item for item in matched if item['case_bucket'] == bucket]
        add_summary_row(
            rows,
            'gpt_human_by_bucket',
            bucket or 'unknown',
            'human_mean_total',
            'gpt_total',
            [item['total_human_mean'] for item in bucket_items],
            [item['total_gpt'] for item in bucket_items],
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description='Compare GPT scores with human scores for CG-GLC samples.')
    parser.add_argument(
        '--reviewer-files',
        nargs=2,
        default=[str(path) for path in DEFAULT_REVIEWER_FILES],
        help='Two filled human reviewer CSV files.'
    )
    parser.add_argument('--gpt-per-item', default=str(DEFAULT_GPT_PER_ITEM))
    parser.add_argument('--out', default=str(DEFAULT_OUT))
    args = parser.parse_args()

    reviewers, keys = load_reviewer_files([Path(path) for path in args.reviewer_files])
    gpt_by_doc = load_gpt_cgglc(Path(args.gpt_per_item))
    matched, skipped = build_matched_items(reviewers, keys, gpt_by_doc)
    if not matched:
        raise ValueError('No complete human/GPT matched items were found.')

    fieldnames = [
        'section',
        'target',
        'left_label',
        'right_label',
        'n',
        'left_mean',
        'right_mean',
        'right_minus_left_mean',
        'mean_abs_diff',
        'exact_agreement',
        'within_1',
        'within_2',
        'pearson',
        'spearman',
        'quadratic_weighted_kappa',
    ]
    out_path = Path(args.out)
    write_csv(summarize(matched), out_path, fieldnames)

    print(f'{out_path} matched={len(matched)} skipped={len(skipped)}')


if __name__ == '__main__':
    main()
