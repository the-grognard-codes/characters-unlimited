import json
import secrets
from pathlib import Path

rng = secrets.SystemRandom()
spec = {'IQ': (3, 4), 'ME': (4, 6), 'MA': (3, 4), 'PS': (4, 4),
        'PP': (3, 0), 'PE': (3, 6), 'PB': (3, 6), 'Spd': (4, 6)}

def die(sides=6, reroll_ones=False):
    history = [rng.randint(1, sides)]
    while reroll_ones and history[-1] == 1:
        history.append(rng.randint(1, sides))
    return history

columns = []
for name in ['A', 'B', 'C']:
    attributes = {}
    for stat, (count, racial_add) in spec.items():
        histories = [die(reroll_ones=True) for _ in range(count + 1)]
        faces = [h[-1] for h in histories]
        dropped_index = min(range(len(faces)), key=faces.__getitem__)
        kept_sum = sum(faces) - faces[dropped_index]
        exceptional = []
        # Preserve RUE exceptional dice only on an unmodified racial 3D6
        # attribute (P.P.). House reroll-ones applies to these d6s too.
        if count == 3 and racial_add == 0 and kept_sum >= 16:
            exceptional.append(die(reroll_ones=True))
            if exceptional[-1][-1] == 6:
                exceptional.append(die(reroll_ones=True))
        attributes[stat] = dict(histories=histories, dropped_index=dropped_index,
            kept_sum=kept_sum, racial_add=racial_add, exceptional=exceptional,
            total=kept_sum + racial_add + sum(h[-1] for h in exceptional))
    values = {s: a['total'] for s, a in attributes.items()}
    # Whole columns remain intact. PP has triple weight, IQ double weight.
    score = sum(values.values()) + 2 * values['PP'] + values['IQ']
    columns.append(dict(name=name, attributes=attributes, score=score))
winner = max(columns, key=lambda c: (c['score'], c['attributes']['PP']['total'],
                                    c['attributes']['IQ']['total']))
extras = {'PE_augmentation': die(4), 'PP_augmentation': die(4),
          'speed_augmentation': die(6, reroll_ones=True), 'body_MDC': [die(4), die(4)],
          'scholar_SDC': [die(6), die(6)], 'height_inches': die(4),
          'insanity_percentile': rng.randint(1, 100)}
result = dict(method='Add one d6 to racial dice pool, reroll all 1s, drop lowest;'
              ' keep whole column; preserve RUE exceptional dice on plain 3D6 P.P.',
              ranking='sum(attributes) + 2*PP + IQ; ties PP, then IQ',
              columns=columns, selected=winner['name'], extras=extras)
out = Path('output/pdf/nikandros-roll-record.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
for c in columns:
    print(c['name'], {s:a['total'] for s,a in c['attributes'].items()}, 'score', c['score'])
print('Selected', result['selected'])
print('Extras', extras)
