
# Boolean compiler for CHIA graph annotations.

import os
import json
import argparse
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEFAULT_SOURCE_JSONL = os.path.join(PROJECT_ROOT, 'data', 'processed', 'source_criteria.jsonl')
DEFAULT_OUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed', 'boolean_outputs')
FINAL_METHODS = {
    'flat': {'file_stem': 'flat', 'label': 'Flat'},
    'or_direct': {'file_stem': 'or_direct', 'label': 'OR-direct'},
    'constraint': {'file_stem': 'constraint', 'label': 'Constraint'},
    'cgglc': {'file_stem': 'cgglc', 'label': 'CG-GLC'},
}

MODE_ALIASES = {
    'baseline': 'flat',
    'scope': 'cgglc',
}

MODIFIER_REL_TYPES = {
    'Has_value', 'Has_temporal', 'Has_qualifier', 'Has_negation',
    'Has_multiplier', 'Has_mood', 'Has_context', 'Has_index'
}

IGNORE_ENTITY_TYPES = {'Scope', 'Line'}
EXCLUDE_ENTITY_TYPES = {
    'Not_a_criteria', 'Context_Error', 'Grammar_Error', 'Parsing_Error',
    'Undefined_semantics', 'Non-representable', 'Non-query-able'
}

WEAK_STANDALONE_TYPES = {
    'Temporal', 'Reference_point', 'Qualifier', 'Value', 'Mood', 'Multiplier'
}

ANCHOR_TYPES = {'Condition', 'Observation', 'Procedure', 'Measurement', 'Drug', 'Device', 'Visit', 'Person'}
PERSON_TYPES = {'Person'}
PROCEDURE_LIKE_TYPES = {'Procedure', 'Observation'}
MEASUREMENT_TYPES = {'Measurement'}

ATTACHABLE_SHORT_TEXT = {
    'childbearing age', 'surgical treatment', 'follow-up program',
    'rehabilitation protocol', 'conservative treatment',
    'elective surgery', 'general anesthesia', 'stable 3'
}

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def save_jsonl(rows: List[Dict[str, Any]], path: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

def normalize_space(text: str) -> str:
    return ' '.join(str(text).split())

def get_entity_start(ent: Dict[str, Any]) -> int:
    spans = ent.get('spans', [])
    if spans:
        return min(s['start'] for s in spans)
    return 10**12

def get_entity_end(ent: Dict[str, Any]) -> int:
    spans = ent.get('spans', [])
    if spans:
        return max(s['end'] for s in spans)
    return -1

def sort_entity_ids(entity_ids: List[str], ents: Dict[str, Dict[str, Any]]) -> List[str]:
    return sorted(entity_ids, key=lambda x: (get_entity_start(ents[x]), get_entity_end(ents[x]), x))

def make_atom(text: str, entity_id: Optional[str] = None, entity_type: str = 'ATOM') -> Dict[str, Any]:
    return {
        'node_type': 'ATOM',
        'entity_id': entity_id,
        'entity_type': entity_type,
        'text': normalize_space(text)
    }

def ast_to_json_ready(ast: Dict[str, Any]) -> Dict[str, Any]:
    t = ast['node_type']
    if t == 'ATOM':
        return {
            'type': 'ATOM',
            'entity_id': ast.get('entity_id'),
            'entity_type': ast.get('entity_type'),
            'text': ast.get('text')
        }
    if t == 'NOT':
        return {'NOT': [ast_to_json_ready(c) for c in ast.get('children', [])]}
    if t in ('AND', 'OR'):
        out = {t: [ast_to_json_ready(c) for c in ast.get('children', [])]}
        if ast.get('preserve_group'):
            out['_preserve_group'] = True
        if ast.get('group_source') is not None:
            out['_group_source'] = ast.get('group_source')
        return out
    return {'UNKNOWN': ast}

def ast_signature(node: Dict[str, Any]):
    t = node.get('node_type')
    if t == 'ATOM':
        return ('ATOM', normalize_space(node.get('text', '')))
    if t == 'NOT':
        ch = node.get('children', [])
        return ('NOT', ast_signature(ch[0])) if ch else ('NOT', None)
    return (
        t,
        tuple(ast_signature(c) for c in node.get('children', [])),
        bool(node.get('preserve_group', False)),
        node.get('group_source')
    )

def ast_to_string(ast: Dict[str, Any]) -> str:
    t = ast['node_type']
    if t == 'ATOM':
        return f"({normalize_space(ast['text'])})"
    if t == 'NOT':
        return f"NOT {ast_to_string(ast['children'][0])}"
    if t in ('AND', 'OR'):
        parts = [ast_to_string(c) for c in ast.get('children', [])]
        if len(parts) == 0:
            return '(EMPTY)'
        if len(parts) == 1 and not ast.get('preserve_group', False):
            return parts[0]
        return '(' + f' {t} '.join(parts) + ')'
    return '(UNKNOWN)'

def normalize_ast(node: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if node is None:
        return None
    t = node.get('node_type')

    if t == 'ATOM':
        txt = normalize_space(node.get('text', ''))
        if not txt or txt == 'EMPTY':
            return None
        out = dict(node)
        out['text'] = txt
        return out

    preserve_group = node.get('preserve_group', False)
    group_source = node.get('group_source')

    children = []
    for c in node.get('children', []):
        nc = normalize_ast(c)
        if nc is not None:
            children.append(nc)

    if t in {'AND', 'OR'}:
        flat = []
        for c in children:
            same_type = c.get('node_type') == t
            child_preserve = c.get('preserve_group', False)
            if same_type and not child_preserve:
                flat.extend(c.get('children', []))
            else:
                flat.append(c)
        children = flat

    seen = set()
    dedup = []
    for c in children:
        sig = ast_signature(c)
        if sig not in seen:
            seen.add(sig)
            dedup.append(c)
    children = dedup

    if t == 'NOT':
        if len(children) == 0:
            return None
        out = {'node_type': 'NOT', 'children': [children[0]]}
        if preserve_group:
            out['preserve_group'] = True
        if group_source is not None:
            out['group_source'] = group_source
        return out

    if t in {'AND', 'OR'}:
        if len(children) == 0:
            return None
        if len(children) == 1 and not preserve_group:
            return children[0]
        def srt(c):
            if c.get('node_type') == 'ATOM':
                return (0, normalize_space(c.get('text', '')))
            return (1, json.dumps(ast_to_json_ready(c), ensure_ascii=False, sort_keys=True))
        children = sorted(children, key=srt)
        out = {'node_type': t, 'children': children}
        if preserve_group:
            out['preserve_group'] = True
        if group_source is not None:
            out['group_source'] = group_source
        return out

    return None

def build_modifier_map(record: Dict[str, Any]) -> Tuple[Dict[str, List[Tuple[str, str]]], set]:
    modifier_map = defaultdict(list)
    consumed_nodes = set()
    for r in record.get('relations', []):
        rtype = r.get('type')
        a1 = r.get('arg1')
        a2 = r.get('arg2')
        if rtype in MODIFIER_REL_TYPES and a1 and a2:
            modifier_map[a1].append((rtype, a2))
            consumed_nodes.add(a2)
    return modifier_map, consumed_nodes

def build_scope_groups(record: Dict[str, Any]) -> Dict[str, List[str]]:
    scope_groups = defaultdict(list)
    for r in record.get('relations', []):
        if r.get('type') == 'Has_scope':
            scope_groups[r['arg2']].append(r['arg1'])
    return scope_groups

def build_or_groups(record: Dict[str, Any], candidate_ids: List[str]) -> List[List[str]]:
    ids = set(candidate_ids)
    groups = []
    for ev in record.get('events', []):
        if ev.get('type') == 'OR':
            args = [a for a in ev.get('args', []) if a in ids]
            if len(args) >= 2:
                groups.append(args)
    seen = set()
    uniq = []
    for g in groups:
        sig = tuple(sorted(g))
        if sig not in seen:
            seen.add(sig)
            uniq.append(g)
    return uniq

def build_atomic(eid: str, ents: Dict[str, Dict[str, Any]], modifier_map: Dict[str, List[Tuple[str, str]]],
                 use_modifier_consumption: bool = True) -> Dict[str, Any]:
    ent = ents[eid]
    base_text = normalize_space(ent.get('text', '')) or eid
    negated = False
    extra = []
    if use_modifier_consumption:
        for rel_type, mid in modifier_map.get(eid, []):
            if mid not in ents:
                continue
            mod_text = normalize_space(ents[mid].get('text', ''))
            if not mod_text:
                continue
            if rel_type == 'Has_negation':
                negated = True
            else:
                extra.append((get_entity_start(ents[mid]), mod_text))
    parts = [base_text] + [x[1] for x in sorted(extra, key=lambda z: z[0])]
    atom = {
        'node_type': 'ATOM',
        'entity_id': eid,
        'entity_type': ent['type'],
        'text': normalize_space(' '.join(parts))
    }
    if negated:
        return {'node_type': 'NOT', 'children': [atom]}
    return atom

def can_attach(weak_id: str, anchor_id: str, ents: Dict[str, Dict[str, Any]]) -> bool:
    weak = ents[weak_id]
    anchor = ents[anchor_id]
    weak_text = normalize_space(weak.get('text', '')).lower()
    weak_type = weak['type']
    anchor_type = anchor['type']

    if weak_text in {'childbearing age', 'pregnancy', 'pregnant', 'women', 'woman', 'female', 'male'}:
        return anchor_type in PERSON_TYPES
    if weak_text in {'surgical treatment', 'follow-up program', 'rehabilitation protocol', 'conservative treatment'}:
        return anchor_type in PROCEDURE_LIKE_TYPES
    if weak_type in WEAK_STANDALONE_TYPES:
        return anchor_type in ANCHOR_TYPES
    if weak_type == 'Qualifier' and weak_text in ATTACHABLE_SHORT_TEXT:
        return anchor_type in ANCHOR_TYPES
    if anchor_type in MEASUREMENT_TYPES and weak_type in {'Qualifier', 'Value', 'Temporal'}:
        return True
    return False

def semantic_attachment_pass(candidate_ids: List[str], ents: Dict[str, Dict[str, Any]], distance_threshold: int = 80):
    attached_to = {}
    reverse_attached = defaultdict(list)
    anchors = [eid for eid in candidate_ids if ents[eid]['type'] in ANCHOR_TYPES]
    weak_nodes = [eid for eid in candidate_ids if ents[eid]['type'] in WEAK_STANDALONE_TYPES]
    for wid in weak_nodes:
        ws = get_entity_start(ents[wid])
        best = None
        best_dist = 10**12
        for aid in anchors:
            if aid == wid:
                continue
            if not can_attach(wid, aid, ents):
                continue
            dist = abs(ws - get_entity_end(ents[aid]))
            if dist <= distance_threshold and dist < best_dist:
                best_dist = dist
                best = aid
        if best is not None:
            attached_to[wid] = best
            reverse_attached[best].append(wid)
    return attached_to, reverse_attached

def enrich_atom_with_attached(node: Dict[str, Any], reverse_attached, ents) -> Dict[str, Any]:
    if node.get('node_type') == 'NOT':
        child = enrich_atom_with_attached(node['children'][0], reverse_attached, ents)
        return {'node_type': 'NOT', 'children': [child]}
    if node.get('node_type') != 'ATOM':
        return node
    eid = node.get('entity_id')
    if eid is None:
        return node
    extras = []
    for wid in reverse_attached.get(eid, []):
        if wid in ents:
            extras.append((get_entity_start(ents[wid]), normalize_space(ents[wid].get('text', ''))))
    base_text = node['text']
    extra_texts = [x[1] for x in sorted(extras, key=lambda z: z[0]) if x[1]]
    if extra_texts:
        lb = base_text.lower()
        le = [t.lower() for t in extra_texts]
        if ('women' in lb or 'woman' in lb or 'female' in lb) and 'childbearing age' in le:
            extra_texts = [t for t in extra_texts if t.lower() != 'childbearing age']
            if 'of childbearing age' not in lb:
                base_text = normalize_space(base_text + ' of childbearing age')
    text = normalize_space(' '.join([base_text] + extra_texts))
    out = dict(node)
    out['text'] = text
    return out

def _build_candidate_ids(record, ents, consumed_nodes, use_modifier_consumption: bool):
    candidate_ids = []
    for eid, ent in ents.items():
        et = ent['type']
        if et in IGNORE_ENTITY_TYPES:
            continue
        if et in EXCLUDE_ENTITY_TYPES:
            continue
        if not normalize_space(ent.get('text', '')):
            continue
        if use_modifier_consumption and eid in consumed_nodes:
            continue
        candidate_ids.append(eid)
    return sort_entity_ids(candidate_ids, ents)

def _make_group_node(connective: str, members: List[str], atoms, ents,
                     preserve_group: bool = False, group_source: Optional[str] = None):
    children = [atoms[cid] for cid in sort_entity_ids(members, ents) if cid in atoms]
    if len(children) == 0:
        return None
    if len(children) == 1 and not preserve_group:
        return children[0]
    node = {'node_type': connective, 'children': children}
    if preserve_group:
        node['preserve_group'] = True
    if group_source is not None:
        node['group_source'] = group_source
    return node

MODE_CONFIGS = {
    'flat':                     dict(use_modifier_consumption=False, use_semantic_attachment=False, use_or_groups=False, use_scope_groups=False, use_normalization=True),
    'or_direct':                dict(use_modifier_consumption=False, use_semantic_attachment=False, use_or_groups=True,  use_scope_groups=False, use_normalization=True),
    'constraint':               dict(use_modifier_consumption=True,  use_semantic_attachment=True,  use_or_groups=False, use_scope_groups=False, use_normalization=True),
    'cgglc':                    dict(use_modifier_consumption=True,  use_semantic_attachment=True,  use_or_groups=True,  use_scope_groups=True,  use_normalization=True),
}

def compile_record(
    record: Dict[str, Any],
    mode: str = 'cgglc',
    distance_threshold: int = 80
) -> Dict[str, Any]:
    mode = MODE_ALIASES.get(mode, mode)
    if mode not in MODE_CONFIGS:
        raise ValueError(f'Unknown mode: {mode}')
    cfg = MODE_CONFIGS[mode]

    ents = {e['id']: e for e in record.get('entities', [])}
    modifier_map, consumed_nodes = build_modifier_map(record)
    scope_groups = build_scope_groups(record)
    candidate_ids = _build_candidate_ids(record, ents, consumed_nodes, cfg['use_modifier_consumption'])

    atoms = {
        eid: build_atomic(eid, ents, modifier_map, use_modifier_consumption=cfg['use_modifier_consumption'])
        for eid in candidate_ids
    }

    used = set()
    grouped_nodes = []
    or_groups = build_or_groups(record, list(atoms.keys())) if cfg['use_or_groups'] else []

    num_scope_groups_total = len(scope_groups) if cfg['use_scope_groups'] else 0
    num_scope_groups_built = 0
    num_scope_groups_skipped_small = 0

    member_to_group = {}
    group_node_consumed = set()

    if cfg['use_or_groups']:
        for group in or_groups:
            valid_members = [x for x in group if x in atoms]
            node = _make_group_node('OR', valid_members, atoms, ents, preserve_group=True, group_source='or')
            if node is not None and len(valid_members) >= 2:
                grouped_nodes.append(node)
                used.update(valid_members)
                for mid in valid_members:
                    member_to_group[mid] = node

    if cfg['use_scope_groups']:
        for scope_id, child_ids in scope_groups.items():
            scope_units = []
            seen_group_nodes = set()
            available_atom_ids = []
            for cid in child_ids:
                if cid in atoms and cid not in used:
                    scope_units.append(atoms[cid])
                    available_atom_ids.append(cid)
                elif cid in member_to_group:
                    gnode = member_to_group[cid]
                    gid = id(gnode)
                    if gid not in seen_group_nodes:
                        scope_units.append(gnode)
                        seen_group_nodes.add(gid)
            if len(scope_units) < 2:
                num_scope_groups_skipped_small += 1
                continue
            node = {
                'node_type': 'AND',
                'children': scope_units,
                'preserve_group': True,
                'group_source': 'scope'
            }
            grouped_nodes.append(node)
            used.update(available_atom_ids)
            for unit in scope_units:
                if isinstance(unit, dict) and unit.get('group_source') == 'or':
                    group_node_consumed.add(id(unit))
            num_scope_groups_built += 1

    if cfg['use_semantic_attachment']:
        remaining_candidate_ids = [eid for eid in candidate_ids if eid not in used]
        attached_to, reverse_attached = semantic_attachment_pass(
            remaining_candidate_ids, ents, distance_threshold=distance_threshold
        )
    else:
        attached_to, reverse_attached = {}, defaultdict(list)

    top_level_remaining = [eid for eid in candidate_ids if eid not in used and eid not in attached_to]
    remaining_nodes = [enrich_atom_with_attached(atoms[eid], reverse_attached, ents) for eid in top_level_remaining]

    surviving_grouped_nodes = []
    for node in grouped_nodes:
        if node.get('group_source') == 'or' and id(node) in group_node_consumed:
            continue
        surviving_grouped_nodes.append(node)

    all_children = surviving_grouped_nodes + remaining_nodes
    if len(all_children) == 0:
        ast = make_atom('EMPTY', entity_type='EMPTY')
    elif len(all_children) == 1:
        ast = all_children[0]
    else:
        ast = {'node_type': 'AND', 'children': all_children}

    ast = normalize_ast(ast) if cfg['use_normalization'] else ast
    if ast is None:
        ast = make_atom('EMPTY', entity_type='EMPTY')

    return {
        'doc_id': record.get('doc_id'),
        'trial_id': record.get('trial_id'),
        'section': record.get('section'),
        'text': record.get('text'),
        'mode': mode,
        'boolean_expression': ast_to_string(ast),
        'boolean_ast': ast_to_json_ready(ast),
        'num_entities': len(record.get('entities', [])),
        'num_relations': len(record.get('relations', [])),
        'num_events': len(record.get('events', [])),
        'num_attributes': len(record.get('attributes', [])),
        'num_scope_groups': len(scope_groups),
        'num_scope_groups_total': num_scope_groups_total,
        'num_scope_groups_built': num_scope_groups_built,
        'num_scope_groups_skipped_small': num_scope_groups_skipped_small,
        'num_or_events': len(or_groups),
        'num_attached_weak_nodes': len(attached_to),
        'num_top_level_atoms': len(top_level_remaining)
    }

def compile_dataset(rows: List[Dict[str, Any]], mode: str, out_path: str, **kwargs):
    compiled = []
    stats = Counter()
    for row in rows:
        rec = compile_record(row, mode=mode, **kwargs)
        compiled.append(rec)
        expr = rec['boolean_expression']
        if expr and expr != '(EMPTY)':
            stats['compiled_nonempty'] += 1
        else:
            stats['compiled_empty'] += 1
        if ' OR ' in expr:
            stats['has_or_expression'] += 1
        if 'NOT ' in expr:
            stats['has_not_expression'] += 1
        if rec['num_scope_groups'] > 0:
            stats['has_scope_annotation'] += 1
        if rec['num_or_events'] > 0:
            stats['has_or_event'] += 1
        if rec['num_attached_weak_nodes'] > 0:
            stats['has_semantic_attachment'] += 1
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    save_jsonl(compiled, out_path)
    return compiled, dict(stats), out_path

def run_all_modes(source_jsonl: str, out_dir: str, modes: Optional[List[str]] = None):
    if modes is None:
        modes = list(FINAL_METHODS.keys())
    modes = [MODE_ALIASES.get(mode, mode) for mode in modes]
    unsupported = [mode for mode in modes if mode not in FINAL_METHODS]
    if unsupported:
        raise ValueError(f'Unsupported final methods: {unsupported}')
    rows = load_jsonl(source_jsonl)

    def project_relative(path: str) -> str:
        return os.path.relpath(os.path.abspath(path), PROJECT_ROOT)

    all_summaries = {}
    for mode in modes:
        meta = FINAL_METHODS[mode]
        out_path = os.path.join(out_dir, f"{meta['file_stem']}.jsonl")
        _, stats, data_out = compile_dataset(rows, mode, out_path)
        summary = {
            'mode': mode,
            'method_label': meta['label'],
            'num_records': len(rows),
            'stats': stats,
            'file': project_relative(data_out)
        }
        all_summaries[mode] = summary
    with open(os.path.join(out_dir, 'generation_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(all_summaries, f, ensure_ascii=False, indent=2)
    return all_summaries

def main():
    ap = argparse.ArgumentParser(
        description='Compile the full CHIA-derived dataset into Boolean AST/expression outputs.'
    )
    ap.add_argument('--source-jsonl', default=DEFAULT_SOURCE_JSONL, help='Full source_criteria.jsonl file.')
    ap.add_argument('--out-dir', default=DEFAULT_OUT_DIR, help='Directory for generated Boolean outputs.')
    ap.add_argument('--modes', nargs='*', default=None, choices=sorted(set(FINAL_METHODS) | set(MODE_ALIASES)), help='Optional subset of final methods to run.')
    args = ap.parse_args()

    summaries = run_all_modes(args.source_jsonl, args.out_dir, args.modes)
    print(json.dumps(summaries, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
