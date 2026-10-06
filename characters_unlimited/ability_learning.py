"""Known grants, retained learning levels and exclusive source award accounting.

Ordinary selection groups intentionally credit overlaps independently. These
awards instead allocate each elective choice once, to an eligible attained
award. Nothing is rejected merely for exceeding an honor-system allowance.
"""

from collections import deque

from .selection_groups import validate_group


def validate_learning_rules(pack, path, allowance):
    options = {row['id']: row for row in pack['catalog']['options']}
    known = path['known_abilities']
    if (not isinstance(known, list) or len(known) > 1000 or
            any(not isinstance(key, str) or key not in options for key in known) or
            len(set(known)) != len(known)):
        raise ValueError('Known ability grants need distinct catalog identities')
    awards = allowance['awards']
    if not isinstance(awards, list) or not 1 <= len(awards) <= 100:
        raise ValueError('Learning awards need a bounded source declaration list')
    seen = set()
    for row in awards:
        if (not isinstance(row, dict) or set(row) != {'id', 'name', 'source', 'level', 'count', 'categories'} or
                any(not isinstance(row[key], str) or not row[key].strip() for key in ('id', 'name')) or
                row['id'] in seen or type(row['level']) is not int or not 1 <= row['level'] <= 1000):
            raise ValueError('Learning awards need exact identities and supported levels')
        seen.add(row['id'])
        source = row['source']
        if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                not source[key].strip() for key in ('book', 'section'))):
            raise ValueError('Learning awards need book and section evidence')
        categories = row['categories']
        if (not isinstance(categories, list) or not categories or
                any(not isinstance(key, str) or key not in pack['categories'] for key in categories) or
                len(set(categories)) != len(categories)):
            raise ValueError('Learning awards need distinct declared categories')
        validate_group({'count': row['count'], 'option_ids': []})
    group = {'count': sum(row['count'] for row in awards),
             'option_ids': [key for key in options if key not in known],
             'costs': allowance.get('costs', {})}
    validate_group(group)
    if any(cost > 1 and len(options[key]['tags']) != 1 for key, cost in group['costs'].items()):
        raise ValueError('Weighted learning choices need exactly one source category')


def validate_learning_levels(state, path, level):
    levels = state['learning_levels']
    acquisitions = state['abilities']['acquisitions']
    if (not isinstance(levels, dict) or set(levels) != set(acquisitions) or
            any(type(level) is not int or not 1 <= level <= 1000 for level in levels.values()) or
            any(levels.get(key) != 1 for key in path['known_abilities']) or
            set(path['known_abilities']) - set(state['abilities']['selections'])):
        raise ValueError('Ability learning must retain every acquisition and automatic grant')
    if any(levels[key] > level for key in state['abilities']['selections']):
        raise ValueError('Selected abilities cannot be learned after the current level')


def validate_learning_history(character, before):
    current = character.get('class_psionics', {})
    prior = before.get('class_psionics', {})
    if 'learning_levels' not in current or 'learning_levels' not in prior:
        return
    if (current['pin'] != prior['pin'] or
            any(current['learning_levels'].get(key) != value
                for key, value in prior['learning_levels'].items()) or
            any(value <= before['level'] for key, value in current['learning_levels'].items()
                if key not in prior['learning_levels'])):
        raise ValueError('Ability learning levels must agree with retained advancement history')


def project_learning(pack, path, allowance, state, level):
    """Maximum exclusive credit avoids greedy failures for overlapping categories."""
    known = set(path['known_abilities'])
    options = {row['id']: row for row in pack['catalog']['options']}
    selections = [key for key in state['abilities']['selections'] if key not in known]
    awards = [row for row in allowance['awards'] if row['level'] <= level]
    costs = allowance.get('costs', {})
    # Source and sink are tuples to keep catalog identities unambiguous.
    start, end = ('terminal', 'source'), ('terminal', 'sink')
    edges: dict[tuple[str, str], dict[tuple[str, str], int]] = {}

    def edge(left, right, capacity):
        edges.setdefault(left, {})[right] = capacity
        edges.setdefault(right, {})[left] = 0

    for key in selections:
        node = ('ability', key)
        edge(start, node, costs.get(key, 1))
        learned = state['learning_levels'][key]
        if learned > level:
            continue
        for award in awards:
            if award['level'] <= learned and set(options[key]['tags']).intersection(award['categories']):
                edge(node, ('award', award['id']), costs.get(key, 1))
    for award in awards:
        edge(('award', award['id']), end, award['count'])
    credited = 0
    while True:
        previous: dict[tuple[str, str], tuple[str, str]] = {start: start}
        pending = deque([start])
        while pending and end not in previous:
            node = pending.popleft()
            for target, capacity in edges.get(node, {}).items():
                if capacity and target not in previous:
                    previous[target] = node
                    pending.append(target)
        if end not in previous:
            break
        amount, node = 1000, end
        while node != start:
            parent = previous[node]
            amount = min(amount, edges[parent][node])
            node = parent
        node = end
        while node != start:
            parent = previous[node]
            edges[parent][node] -= amount
            edges[node][parent] += amount
            node = parent
        credited += amount
    rows = [{**row, 'credited': row['count'] - edges[('award', row['id'])][end],
             'remaining': edges[('award', row['id'])][end]} for row in awards]
    unallocated = {key: edges[start][('ability', key)] for key in selections
                   if edges[start][('ability', key)]}
    return {'awards': rows, 'credited': credited,
            'remaining': sum(row['count'] for row in awards) - credited,
            'unallocated': unallocated}
