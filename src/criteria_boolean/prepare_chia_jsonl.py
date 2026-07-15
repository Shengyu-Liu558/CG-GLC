#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare CHIA brat annotations as one full JSONL dataset."""

import argparse
import json
import os
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / 'data' / 'raw' / 'chia_with_scope.zip'
DEFAULT_OUT_DIR = PROJECT_ROOT / 'data' / 'processed'

ENTITY_RE = re.compile(r'^(T\d+)\t(\S+)\s+(.+?)\t(.*)$')
REL_RE = re.compile(r'^(R\d+)\t(\S+)\s+Arg1:(T\d+)\s+Arg2:(T\d+).*')
ATTR_RE = re.compile(r'^(A\d+)\t(\S+)\s+(T\d+)\s*$')


def parse_spans(span_str: str) -> List[Dict[str, int]]:
    spans = []
    for part in span_str.split(';'):
        part = part.strip()
        if not part:
            continue
        start, end = part.split()
        spans.append({'start': int(start), 'end': int(end)})
    return spans


def parse_brat_ann(ann_text: str):
    entities = []
    relations = []
    events = []
    attributes = []
    event_id = 0

    for line in ann_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith('T'):
            match = ENTITY_RE.match(line)
            if not match:
                continue
            tid, entity_type, span_str, mention = match.groups()
            entities.append({
                'id': tid,
                'type': entity_type,
                'spans': parse_spans(span_str),
                'text': mention
            })
            continue

        if line.startswith('R'):
            match = REL_RE.match(line)
            if not match:
                continue
            rid, relation_type, arg1, arg2 = match.groups()
            relations.append({
                'id': rid,
                'type': relation_type,
                'arg1': arg1,
                'arg2': arg2
            })
            continue

        if line.startswith('*'):
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            items = parts[1].split()
            if len(items) < 2:
                continue
            event_id += 1
            events.append({
                'id': f'E{event_id}',
                'type': items[0],
                'args': items[1:]
            })
            continue

        if line.startswith('A'):
            match = ATTR_RE.match(line)
            if not match:
                continue
            aid, attribute_type, target = match.groups()
            attributes.append({
                'id': aid,
                'type': attribute_type,
                'target': target
            })

    return entities, relations, events, attributes


def build_trial_index(names: Iterable[str]):
    index = defaultdict(lambda: {'inc': {}, 'exc': {}})
    for name in names:
        base = os.path.basename(name)
        if base in {'annotation.conf', 'kb_shortcuts.conf'}:
            continue
        match = re.match(r'^(NCT\d+)_(inc|exc)\.(txt|ann)$', base)
        if not match:
            continue
        trial_id, section, ext = match.groups()
        index[trial_id][section][ext] = name
    return index


def _directory_reader(input_path: Path) -> Tuple[List[str], Callable[[str], str]]:
    files = [str(path) for path in input_path.rglob('*') if path.is_file()]

    def read_text(name: str) -> str:
        return Path(name).read_text(encoding='utf-8', errors='replace')

    return files, read_text


def _write_records(trial_list, trial_index, read_text, out_dir, counters):
    out_path = out_dir / 'source_criteria.jsonl'
    with out_path.open('w', encoding='utf-8') as out_f:
        for trial_id in trial_list:
            for section in ('inc', 'exc'):
                txt_name = trial_index[trial_id][section].get('txt')
                ann_name = trial_index[trial_id][section].get('ann')
                if not txt_name or not ann_name:
                    continue

                text = read_text(txt_name)
                ann_text = read_text(ann_name)
                entities, relations, events, attributes = parse_brat_ann(ann_text)

                for entity in entities:
                    counters['entities'][entity['type']] += 1
                for relation in relations:
                    counters['relations'][relation['type']] += 1
                for event in events:
                    counters['events'][event['type']] += 1
                for attribute in attributes:
                    counters['attributes'][attribute['type']] += 1

                record = {
                    'doc_id': f'{trial_id}_{section}',
                    'trial_id': trial_id,
                    'section': section,
                    'text': text,
                    'entities': entities,
                    'relations': relations,
                    'events': events,
                    'attributes': attributes,
                    'source': {'txt': os.path.basename(txt_name), 'ann': os.path.basename(ann_name)}
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return out_path


def prepare_chia_jsonl(input_path: Path, out_dir: Path):
    input_path = input_path.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    def run(names, read_text):
        trial_index = build_trial_index(names)
        missing = []
        for trial_id, sections in trial_index.items():
            for section in ('inc', 'exc'):
                if 'txt' not in sections[section] or 'ann' not in sections[section]:
                    missing.append((trial_id, section))
        if missing:
            raise RuntimeError(f'Missing txt/ann pairs: {missing[:10]}')

        trial_ids = sorted(trial_index.keys())
        counters = {
            'entities': Counter(),
            'relations': Counter(),
            'events': Counter(),
            'attributes': Counter()
        }
        out_path = _write_records(trial_ids, trial_index, read_text, out_dir, counters)

        stats = {
            'num_trials': len(trial_ids),
            'num_criteria_units': len(trial_ids) * 2,
            'entity_types': dict(counters['entities']),
            'relation_types': dict(counters['relations']),
            'event_types': dict(counters['events']),
            'attribute_types': dict(counters['attributes']),
            'files': {'source_criteria': str(out_path.relative_to(PROJECT_ROOT))}
        }
        (out_dir / 'source_stats.json').write_text(
            json.dumps(stats, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        return stats

    if input_path.is_file() and input_path.suffix.lower() == '.zip':
        with zipfile.ZipFile(input_path) as archive:
            names = archive.namelist()

            def read_from_zip(name: str) -> str:
                return archive.read(name).decode('utf-8', errors='replace')

            return run(names, read_from_zip)

    if input_path.is_dir():
        names, read_from_directory = _directory_reader(input_path)
        return run(names, read_from_directory)

    raise FileNotFoundError(f'Input path not found or unsupported: {input_path}')


def main():
    parser = argparse.ArgumentParser(description='Convert CHIA brat .txt/.ann files into one full JSONL dataset.')
    parser.add_argument('--input', default=str(DEFAULT_INPUT), help='Raw CHIA zip file or directory.')
    parser.add_argument('--out-dir', default=str(DEFAULT_OUT_DIR), help='Output directory for source_criteria.jsonl and source_stats.json.')
    args = parser.parse_args()

    stats = prepare_chia_jsonl(
        Path(args.input),
        Path(args.out_dir)
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
