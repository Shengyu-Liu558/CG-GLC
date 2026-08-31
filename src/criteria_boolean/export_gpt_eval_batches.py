#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export Markdown batches for manual GPT evaluation."""

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ITEMS = PROJECT_ROOT / 'data' / 'evaluation' / 'llm_judge' / 'llm_eval_items.jsonl'
DEFAULT_GUIDE = PROJECT_ROOT / 'docs' / 'gpt_manual_evaluation_guide.md'
DEFAULT_OUT_DIR = PROJECT_ROOT / 'data' / 'evaluation' / 'gpt_manual_batches'


def load_jsonl(path: Path):
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_batch(batch, batch_id: int, out_dir: Path, guide_text: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'gpt_eval_batch_{batch_id:04d}.md'
    with out_path.open('w', encoding='utf-8') as f:
        f.write('# GPT-5.5 Evaluation Batch\n\n')
        f.write('请先阅读并遵循以下评估指南，然后评价本批候选。只输出 JSONL 评分结果。\n\n')
        f.write('## Evaluation Guide\n\n')
        f.write(guide_text.strip())
        f.write('\n\n## Candidate Items\n\n')
        f.write('```jsonl\n')
        for item in batch:
            payload = {
                'candidate_id': item['candidate_id'],
                'doc_id': item['doc_id'],
                'case_bucket': item.get('case_bucket'),
                'source_criterion': item.get('source_criterion'),
                'candidate_expression': item.get('candidate_expression'),
            }
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')
        f.write('```\n')
    return out_path


def main():
    parser = argparse.ArgumentParser(description='Export manual GPT evaluation batches as Markdown files.')
    parser.add_argument('--items', default=str(DEFAULT_ITEMS))
    parser.add_argument('--guide', default=str(DEFAULT_GUIDE))
    parser.add_argument('--out-dir', default=str(DEFAULT_OUT_DIR))
    parser.add_argument('--batch-size', type=int, default=25)
    args = parser.parse_args()

    items = list(load_jsonl(Path(args.items)))
    guide_text = Path(args.guide).read_text(encoding='utf-8')
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old_batch in out_dir.glob('gpt_eval_batch_*.md'):
        old_batch.unlink()

    written = []
    for i in range(0, len(items), args.batch_size):
        batch_id = i // args.batch_size + 1
        written.append(write_batch(items[i:i + args.batch_size], batch_id, out_dir, guide_text))

    manifest = {
        'source_items': str(Path(args.items).resolve().relative_to(PROJECT_ROOT)),
        'guide': str(Path(args.guide).resolve().relative_to(PROJECT_ROOT)),
        'batch_size': args.batch_size,
        'num_items': len(items),
        'num_batches': len(written),
        'output_dir': str(out_dir.resolve().relative_to(PROJECT_ROOT)),
    }
    manifest_path = out_dir / 'batch_manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
