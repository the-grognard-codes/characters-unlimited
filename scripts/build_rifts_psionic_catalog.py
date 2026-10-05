"""Produce a reviewable ordinary-psionic proposal; never activate an archive."""

import argparse
import html
import json
from pathlib import Path
import re


BOOK = 'Rifts Ultimate Edition'
ALIASES = {'Bio-Regenerate (self)': 'Bio-Regeneration',
           'Impervious to Poison': 'Impervious to Poison/Toxin',
           'Speed Reading': 'Speed Reading Speed Reading'}
SUMMARIES = {
    'Restore P.P.E': 'Convert 2 ISP into 1 PPE and transfer it to another person, plus 4 ISP to initiate the transfer. For example, transferring 5 PPE costs 14 ISP. Mind Block prevents transfer; PPE cannot be converted into ISP.',
    'Stop Bleeding': 'Temporarily stop bleeding without healing the injury; medical treatment is still required. Unconsciousness ends the protection. New wounds require renewed concentration and another 2 ISP. While concentrating, attacks per melee and combat bonuses are halved; normal skills remain unaffected.',
    'Nightvision': 'Amplify existing light to see up to about600 feet; total darkness still prevents sight. Sudden exposure to light brighter than one candle blinds the psychic for3D4 melee rounds. May instead provide polarized sight to reduce glare.',
    'Resist Hunger': 'Suppress hunger and remain functional without food, but starvation continues: lose3 pounds per day. Continuous use permits60 days without food; on day61 the psychic enters a coma with-20% to save versus coma/death.',
    'Exorcism': 'Expel a supernatural possessing spirit from a living person or animal; excludes symbiotes and psychic possession. After preparation, roll28% +7% per additional level to expel it, then21% +7% per additional level to send it home. Expulsion without banishment leaves the spirit free to seek another host; it must leave the area and cannot repossess the same victim for six months. Nega-Psychics and some powerful possessors halve these chances. The possessing force retains its powers but has half its attacks during the rite; assistants can defend the healer, and the attempt may be repeated.',
    'Telekinetic Push': 'Push with effective P.S.16 +1 per level, inflicting1D4 SDC/HP. Ordinary humans move about2 yards with60% knockdown chance; a fallen target loses initiative and one action. Targets over200 pounds or with Robotic/Supernatural P.S. move only1-2 feet with12% knockdown chance. Inanimate objects under50 pounds slide about4 yards.',
    'Telekinetic Punch': 'Enhance a physical punch to3D6 SDC/HP or kick to4D6 SDC, adding the P.S. bonus. Roll strike normally; opponents may parry or dodge. ISP is spent even on a miss. Each use requires a save of14 or higher to avoid1D6 self-damage from muscular or joint strain.',
    'Mask I.S.P. & Psionics': 'Hide psychic energy and potential from psychic detection and aura readers. While masking, the psychic blocks incoming emanations and cannot use other psionic powers until the mask is released.',
    'Speed Reading': 'Read30 pages per minute with normal retention. Highly technical material reduces the rate to15 pages per minute and may require two readings for detailed recall.',
    'Detect Psionics': 'Detect nearby psychic energy without pinpointing its location; estimate only weak, medium or strong potential. Directed at an individual, detect psychic potential, Group Mind Block or psionic possession without identifying specific powers.',
    'Clairvoyance': 'Seek brief, uncertain glimpses of a possible future, at most twice daily. Concentrate2D4 melee rounds; no other activity is possible during the vision. Base chance58% +2% per level, plus5% for a friend or loved one. Failure gives no insight but still spends4 ISP; the future may be changed.',
    'Telepathy': 'Read one person\'s surface thoughts at a time; no deep memory probe or simultaneous reading. Send brief directed messages to one recipient; two-way conversation requires both participants to have telepathy. A suspected probe permits a standard save, and Mind Block prevents probes or communication.',
    'Ectoplasm': 'Create vapor or a solid limb. Vapor handles objects under9 ounces and passes through cracks, but not solid walls; a solid limb carries up to40 pounds and needs at least a quarter-sized opening. Directed actions consume the creator\'s actions; automatic dodge is separate. Bright light halves range. Destruction of the appendage causes1 HP and10 SDC damage to its creator.',
    'Levitation': 'Raise and suspend objects vertically; sideways movement is impossible. Maximum height for up to2 pounds is8 feet +1 per level;3-20 pounds,6 feet +1 per level; heavier targets,4 feet +1 per level. Self-levitation reaches10 feet +2 per level. Heavy targets cost6 ISP plus1 for each10 pounds beyond20.',
    'Telekinesis': 'Move one visible object at a time by concentration; each feat consumes one physical attack/action. Up to2 pounds may travel60 feet;3-20 pounds,30 feet; over20 pounds,15 feet. Heavy targets cost8 ISP for the first20 pounds plus1 per additional10. May manipulate or throw objects, but cannot crush with force alone, levitate oneself or stop projectiles. Telekinetic combat uses its own+3 strike/+4 parry rather than physical/skill bonuses.',
    'Ectoplasmic Disguise': 'Shape ectoplasm into altered facial/body features. Impersonation chance50% +3% per level, plus16% with Disguise. Close scrutiny reveals its dull, pasty appearance; damage visibly tears and reforms it. Concentration causes-4 initiative and halves combat bonuses, attacks and normal skill performance; loss of concentration or unconsciousness dissolves the disguise.',
    'Astral Projection': 'After4D4 minutes of concentration, project an Astral Self connected by a silver cord while the body lies helpless. Observe the material world as a flying, intangible spirit; communication requires psychic means. Astral/psychic/magical threats can harm the spirit or cord. A severed cord risks death; locating the body without it has30% chance, best two of three. Astral Plane time differs, and returning requires finding the way back; a lost or captured spirit endangers the body.',
    'Intuitive Combat': 'Concentrate one melee round before gaining+3 initiative,+1 strike/parry,+4 dodge/pull punch,+2 roll with impact/disarm, immunity to surprise and+10% Acrobatics/Gymnastics/Climb/Swim abilities. Other psionic powers, including Mind Block, cannot be used during this state. Cancel with a thought.',
    'Machine Ghost': 'Read electronic information at ten times normal speed, including disks or damaged machines; cannot edit data or enter sentient self-aware machines. The trance leaves the body oblivious and undefended; Telepathy can communicate. Virtual defenders and viruses threaten the projection: virtual death or failure to find the exit before duration ends requires coma/death checks. Breaking ordinary file contact causes one melee at half actions/combat bonuses.',
    'Object Read': 'Hold an object to seek impressions and images of its history and last owner; roll separately for each. Each psychic may read a given object only once, even after failure. A successful impression or image permits a present-time glimpse for an additional4 ISP, with its own success check. Reading a possessed object exposes the psychic to psychic attacks without saving bonuses.',
    'Presence Sense': 'Sense supernatural or magical presences without exact location, estimating proximity, number and power. Human and D-Bee presence may register weakly, without reliable distance or count.',
    'Remote Viewing': 'Use a photo/video image to glimpse a person or small place as it is now for2D6+6 seconds, even if already familiar. Cannot survey a whole building or revisit the same subject for24 hours. Psychic targets may resist by concentrating, spending1 ISP and making a standard psychic save.',
    'Sense Evil': 'Feel supernatural evil automatically without ISP; activate the power for approximate number, strength, location and tracking. Human evil registers only with immediate evil intent plus psychic powers or psychosis, and Mind Block may mask it.',
    'Commune with Spirits': 'Feel nearby spirits and ask questions aloud. Only the psychic hears replies unless using a group trance. Spirits may refuse, lie, break contact or attack; communion does not reveal alignment or magic energy and prevents other psionic powers. Breaking contact ends awareness of the spirit.',
    'Total Recall': 'Recall written and visual information in detail; the source also includes spoken words. This utility follows the prose cost of3 ISP per precisely recalled block; the printed header instead says2 ISP. With no ISP, roll percentile:01-50 full detail,51-80 ideas without details,81-100 basic concepts only.',
    'Alter Aura': 'Temporarily disguise the information revealed by your aura, such as alignment, psychic potential and magical energy.',
    'Summon Inner Strength': 'Draw on inner reserves to ward off pain and fatigue. While active, gain10 S.D.C., +2 against poison/toxins and +5% against coma/death.',
    'Telekinetic Leap': 'Add2 feet per level to vertical leaps or3 feet per level to lengthwise leaps. An optional Leap Kick deals6D6+6 plus P.S. bonus but causes2D6 SDC self-damage; a roll with impact may be needed for a safe landing.',
    'See Aura': 'Read an aura to estimate experience, psychic potential, magic, health and supernatural influences, but not alignment. Mind Block hides psychic ability, PPE level and possession.',
    'Sense Magic': 'Sense nearby magic and follow emanations toward the source; identify enchantment or active spellcasting. Invisible magical or supernatural targets locate only to a general area. Psionic effects are excluded.',
    'Sixth Sense': 'An automatic precognitive warning of imminent, unexpected life-threatening danger. The initial danger round grants+6 initiative, +2 parry and +3 dodge; it does not reveal the danger or operate when ISP is exhausted.',
    'Read Dimensional Portal': 'Read information about an active dimensional portal, its destination and, where applicable, how to operate the gateway.',
}

METADATA = {
    'Exorcism': [('Range', 'Touch or within8 feet.'), ('Duration', 'Instant if successful.'), ('Length of Trance', '30 minutes preparation plus6D6 minutes with the living possessed person/animal.'), ('I.S.P.', '10')],
    'Telekinesis': [('Range', 'Up to60 feet; reduced for heavier objects.'), ('Duration', '2 minutes per level.'), ('I.S.P.', 'Up to2 lb:3;3-20 lb:8; over20 lb:8 for first20 lb plus1 per additional10 lb.')],
    'Total Recall': [('Range', 'Self.'), ('Duration', 'Permanent.'), ('I.S.P.', '3 per detailed block; printed header says2. See description.')],
    'Increased Healing': [('Range', 'Touch or within3 feet.'), ('Duration', '2D4 days.'), ('Length of Trance', '1D6 hours.'), ('I.S.P.', '10')],
    'Restore P.P.E': [('Range', 'Touch.'), ('Duration', 'Permanent.'), ('I.S.P.', '4 initiation plus2 per PPE transferred.')],
    'Summon Inner Strength': [('Range', 'Self.'), ('Duration', '10 minutes per level.'), ('I.S.P.', '4')],
    'Ectoplasm': [('Range', '40 feet plus5 feet per level.'), ('Duration', '4 minutes per level.'), ('I.S.P. (Vapor)', '6'), ('I.S.P. (Solid)', '12')],
    'Empathy': [('Range', '100-foot area.'), ('Duration', '2 minutes per level.'), ('I.S.P.', '4'), ('Saving Throw', 'Standard each melee; a successful save obscures the target\'s emotions. Mind Block prevents emanations.')],
    'Sixth Sense': [('Range', '90 feet.'), ('Duration', 'Until danger passes or occurs; bonuses only in its first melee round.'), ('I.S.P.', '2'), ('Saving Throw', 'None.')],
    'Telekinetic Leap': [('Range', 'Self.'), ('Duration', 'One melee attack/action: a leap.'), ('I.S.P.', '8')],
    'Speed Reading': [('Range', 'Self.'), ('Duration', '3 minutes per level.'), ('I.S.P.', '2')],
    'Clairvoyance': [('Range', 'Self; visions may concern distant people or places.'), ('Duration', '6D6 melee rounds.'), ('I.S.P.', '4'), ('Base Skill', '58% plus2% per level.')],
}


def normalize(value):
    return re.sub(r'[^a-z0-9]', '', html.unescape(value).lower())


def build(text):
    index = text.split('## Psionic Powers', 1)[1].split('## Super-Psionics', 1)[0]
    memberships = {}
    for category, expected in [('Healing', 15), ('Physical', 21), ('Sensitive', 24)]:
        part = index.split('## ' + category + '\n', 1)[1].split('\n## ', 1)[0]
        entries = [line.strip() for line in part.splitlines() if line.strip()]
        if len(entries) != expected:
            raise ValueError('Source checklist changed: ' + category)
        for entry in entries:
            name = html.unescape(re.sub(r'\s*\([^()]*\)\s*$', '', entry))
            memberships.setdefault(name, []).append(category)
    if len(memberships) != 56:
        raise ValueError('Expected56 unique ordinary powers')
    headings = {normalize(ALIASES.get(name, name)): name for name in memberships}
    chapter = text.split('## Healing Psionics', 1)[1].split('## Super-Psionics', 1)[0]
    blocks, current = {}, None
    for line in chapter.splitlines():
        if line.startswith('## '):
            title = normalize(line[3:])
            if title in headings:
                current = headings[title]
                # Shared powers have one identity and the first full definition.
                if current in blocks and any(line.strip() for line in blocks[current]):
                    current = None
                else:
                    blocks[current] = []
                continue
            if line[3:] in ('Physical Psionics', 'Sensitive Psionics'):
                current = None
        if current:
            blocks[current].append(line.removeprefix('## '))
    if set(blocks) != set(memberships):
        raise ValueError('Source powers missing descriptions')
    options = []
    prefix = re.compile(r'^(Range|Duration|(?:I|L)[.:]S\.P\.[^:]*|Saving Throw|Length of Trance|Preparation|Base Skill|Limitations):', re.I)
    for name, categories in memberships.items():
        source = {'book': BOOK, 'section': 'Psionic Powers: ' + ALIASES.get(name, name)}
        paragraphs = [html.unescape(' '.join(part.split())) for part in '\n'.join(blocks[name]).split('\n\n')
                      if part.strip() and not part.strip().startswith('<!--')]
        metadata = []
        for part in paragraphs:
            if not prefix.match(part):
                break
            metadata.append(part)
        if name in METADATA:
            metadata = [label + ': ' + value for label, value in METADATA[name]]
        narrative = [part for part in paragraphs if not prefix.match(part)]
        if not narrative:
            raise ValueError('No narrative for ' + name)
        options.append({'id': re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
            'name': name, 'category': categories[0], 'tags': categories, 'source': source,
            'description': re.sub(r'(?<=[a-z])(?=[0-9])', ' ', SUMMARIES.get(name, narrative[0])).replace('fadea', 'fades').replace('damiage', 'damage'), 'parameters': [
                {'id': 'metadata-' + str(number), 'name': part.split(':', 1)[0],
                 'text': part.split(':', 1)[1].strip(), 'source': source}
                for number, part in enumerate(metadata) if part.split(':', 1)[1].strip()]})
    source = {'book': BOOK, 'section': 'Step4: Determine Psionics; Psionic Saving Throws'}
    def path(identifier, name, count, bonus):
        psychic = count is not None
        return {'id': identifier, 'name': name, 'source': source,
            'save_target': 12 if psychic else 15,
            'allowances': {'single': {'count': 8 if identifier == 'major' else 2 if psychic else 0,
                 'minimum_categories': 1 if psychic else 0, 'maximum_categories': 1 if psychic else 0},
                **({'mixed': {'count': 6, 'minimum_categories': 2, 'maximum_categories': 3}} if identifier == 'major' else {})},
            'resources': {'definitions': [{'id': 'ISP', 'name': 'Inner Strength Points', 'contributions': [
                {'id': 'starting-ME', 'attribute': 'ME', 'source': source},
                {'id': 'starting-dice', 'formula': {'count': count, 'sides': 6, 'bonus': 0}, 'source': source}]}],
                'guidance': ['Starting M.E. is recorded when ISP is first generated.']} if psychic else None,
            'growth': {'ISP': {'formula': {'count': 1, 'sides': 6, 'constant': bonus}, 'source': source}} if psychic else {}}
    return {'id': 'rifts-natural-psionics', 'version': '1.0.0', 'name': 'Natural psionics',
        'game': 'rifts', 'source': source, 'format': 'ability-paths-v1',
        'categories': ['Healing', 'Physical', 'Sensitive'], 'skip_path': 'none',
        'catalog': {'id': 'rifts-ordinary-psionic-powers', 'version': '1.0.0', 'game': 'rifts',
                    'format': 'abilities-v1', 'options': options, 'groups': []},
        'chance_table': [{'maximum': 10, 'path': 'major'}, {'maximum': 25, 'path': 'minor'},
                         {'maximum': 100, 'path': 'none'}],
        'paths': [path('none', 'Not psychic', None, 0), path('minor', 'Minor psychic', 2, 0),
                  path('major', 'Major psychic', 4, 1)]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(args.source.read_text(encoding='utf-8')), indent=2,
                                     ensure_ascii=False) + '\n', encoding='utf-8')
