import json
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf'
rolls = json.loads((OUT/'nikandros-roll-record.json').read_text(encoding='utf-8'))
NAME = rolls.get('character_name', 'Nikandros Veyr')
first = NAME.split()[0]
INK = colors.HexColor('#193039')
TEAL = colors.HexColor('#31676C')
PALE = colors.HexColor('#EDF3F3')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleX', fontName='Helvetica-Bold', fontSize=23, leading=26, textColor=INK, spaceAfter=5))
styles.add(ParagraphStyle(name='SubX', fontSize=10.2, leading=14, textColor=TEAL, spaceAfter=11))
styles.add(ParagraphStyle(name='HeadX', fontName='Helvetica-Bold', fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=8, spaceAfter=5))
styles.add(ParagraphStyle(name='BodyX', fontSize=9.3, leading=12.5, textColor=INK, spaceAfter=5))
styles.add(ParagraphStyle(name='SmallX', fontSize=8, leading=9.7, textColor=INK, spaceAfter=4))
styles.add(ParagraphStyle(name='CellX', fontSize=8.4, leading=10.3, textColor=INK))
styles.add(ParagraphStyle(name='WhiteX', fontName='Helvetica-Bold', fontSize=8.3, leading=10.3, textColor=colors.white))
story=[]

def p(text, style='BodyX'):
    story.append(Paragraph(text, styles[style]))

def h(text): p(text,'HeadX')

def table(rows, widths, header=True, size='CellX'):
    cells=[]
    for i,row in enumerate(rows):
        cells.append([Paragraph(str(v),styles['WhiteX' if header and i==0 else size]) for v in row])
    t=Table(cells,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
    commands=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),
              ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),3),
              ('BOTTOMPADDING',(0,0),(-1,-1),3),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#D4DFDF'))]
    if header:
        commands += [('BACKGROUND',(0,0),(-1,0),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE])]
    t.setStyle(TableStyle(commands));story.append(t)

def newpage(title, subtitle):
    if story: story.append(PageBreak())
    p(title,'TitleX');p(subtitle,'SubX')

IQ_BONUS=8
def percent(base,inc,level,bonus=0,synergy=0):
    vals=base if isinstance(base,tuple) else (base,)
    return '/'.join(str(min(98,b+inc*(level-1)+bonus+synergy+IQ_BONUS)) for b in vals)+'%'

scholar=[]
def skill(name,base,inc,level=5,bonus=0,synergy=0,slot='Required',note=''):
    scholar.append([name,percent(base,inc,level,bonus,synergy),slot,note])

skill('Literacy: Greek',40,5,bonus=50,note='Native; 98% cap')
for lang in ('Dragonese/Elven','American','Techno-Can'):
    skill('Literacy: '+lang,40,5,bonus=30,note='Techno-Can is written only' if lang=='Techno-Can' else '')
scholar += [['Speak: Greek / Dragonese / American','98% each','Required','Greek native; others raised by Juicer grant']]
skill('Appraise Goods',30,5,bonus=20)
skill('Mathematics: Basic',45,5,bonus=25)
skill('Computer Operation',40,5,bonus=20)
skill('Computer Programming',30,5,bonus=15)
skill('Creative Writing',25,5,bonus=15)
skill('Find Contraband',26,4,bonus=15,note='85% for books / historic artifacts')
skill('History: Pre-Rifts', (32,24),4,bonus=22,synergy=20,note='General / ancient Atlantean specialty')
skill('History: Post-Apocalypse',(35,30),5,bonus=20,synergy=15,note='General / Splugorth Atlantis specialty')
skill('Public Speaking',30,5,bonus=20)
skill('Research',40,5,bonus=30)
skill('Pilot: Hover Craft (ground)',50,5,bonus=10)
for name,base,inc,synergy,note in [
    ('Lore: Magic',25,5,12,'Symbols 70%; enchantment 65%'),
    ('Lore: Demons & Monsters',25,5,12,'Atlantean encounters; local adaptation'),
    ('Lore: Faeries & Creatures of Magic',25,5,7,''),
    ('Mythology',30,5,0,'Greek / Atlantean tradition'),
    ('Philosophy',30,5,0,'Ethics, argument, cultural context')]:
    skill(name,base,inc,bonus=15,synergy=synergy,slot='Related 1',note=note)
for name,base,synergy,note in [
    ('Anthropology',30,0,''),('Archaeology',(30,20),0,'Study / identify artifacts'),
    ('Mathematics: Advanced',45,0,''),('Biology',30,0,''),('Chemistry',30,0,''),
    ('Astronomy & Navigation',30,10,'Includes Advanced Math synergy')]:
    skill(name,base,5,bonus=10,synergy=synergy,slot='Related 1',note=note)
skill('Cryptography',25,5,level=3,bonus=10,slot='Related 3',note='Acquired Scholar 3; proficiency 3')
skill('Forgery',20,5,level=3,synergy=10,slot='Related 3',note='Acquired Scholar 3; restoration synergy')
for name,base,lev,syn,slot in [('Cook',35,5,0,'Secondary 1'),('Sing',35,5,0,'Secondary 1'),
    ('Art',35,5,10,'Secondary 1'),('Sewing',40,4,0,'Secondary 2'),
    ('Whittling & Sculpting',30,1,0,'Secondary 5')]:
    skill(name,base,5,level=lev,synergy=syn,slot=slot)

juicer=[]
def jskill(name,base,inc,bonus=0,slot='Required',note=''):
    juicer.append([name,percent(base,inc,2,bonus),slot,note])
for name,base,inc,bonus,note in [('Radio: Basic',45,5,5,''),('Intelligence',32,4,10,''),
    ('Tracking (people)',25,5,10,''),('Land Navigation',36,4,10,''),
    ('Wilderness Survival',30,5,10,''),('Climbing',(40,30),5,10,'Climb / rappel'),
    ('Swimming',50,5,5,'')]:jskill(name,base,inc,bonus,note=note)
for name,base,bonus in [('Detect Ambush',30,5),('Detect Concealment',25,5),
                       ('Escape Artist',30,5),('Prowl',25,5)]:
    jskill(name,base,5,bonus,slot='Related',note='Prowl uses Physical allowance' if name=='Prowl' else '')
for name,base in [('First Aid',45),('Rope Works',30),('General Repair & Maintenance',35),
                  ('Preserve Food',30),('Fishing',40),('Recognize Weapon Quality',25)]:
    jskill(name,base,5,slot='Secondary')

newpage(NAME, 'True Atlantean  |  Rogue Scholar 5 / Bio-Wizard Juicer 2')
p('<b>Alignment:</b> Scrupulous. <b>Age:</b> 362 lived years; dimensional travel makes calendar age uncertain. '
  '<b>Height:</b> 6 ft 6 in. <b>Weight:</b> 225 lb before the living shell. <b>Home:</b> an off-Earth Atlantean sanctuary. '
  '<b>Affiliation:</b> House of the Open Hand, a small original clan for this campaign.')
table([['I.Q.','M.E.','M.A.','P.S.','P.P.','P.E.','P.B.','Spd.'],
       ['22','18','22','32 supernatural','28','25','18','85']], [66]*8)
p('I.Q. adds <b>+8%</b> to percentile skills. Trust/intimidate <b>70%</b>. P.P. combat bonus <b>+7</b>. '
  'Running speed is about <b>58 mph</b> at full pace. '
  'Supernatural strength carries 1,600 lb and lifts 3,200 lb.','SmallX')
h('Combat at Juicer level 2')
table([['Actions / initiative','Melee / defense','Other combat'],
       ['<b>5 attacks/actions</b> per 15-second melee<br/>Initiative <b>+3</b>',
        'Unarmed strike <b>+9</b><br/>Parry / ordinary dodge <b>+10</b><br/>Automatic dodge <b>+7</b>',
        'Roll with impact <b>+6</b><br/>Pull punch <b>+3</b><br/>Perception <b>+5</b> (retained Scholar)']], [166,184,178])
p('Hand to Hand: Martial Arts 2. Automatic defenses cover surprise and rear attacks. Auto-dodge uses the P.P. bonus, '
  'not ordinary dodge bonuses. A normal dodge consumes an action; an automatic dodge does not.','SmallX')
table([['Weapon / proficiency','Attack bonus','Damage / range / supply'],
       ['Punch / power punch','+9','4D6 M.D. / 1D4x10 M.D. (power uses 2 actions)'],
       ['Sword / W.P. Sword 5','+11 strike; +12 parry','Flaming tattoo longsword: 2D6 M.D.; see weapon rule below'],
       ['Two grafted forearm blades','+11 / +12 using Sword','2D6 M.D. each; one blade on each arm; no paired strike'],
       ['NG-L5 / W.P. Energy Rifle 5','+2 single; +4 aimed','3D6 M.D.; 1,600 ft; 20 shots/Long E-Clip'],
       ['NG-57 / W.P. Energy Pistol 2','+1 single; +3 aimed','2D4 or 3D6 M.D.; 500 ft; 10 shots/E-Clip'],
       ['Vibro-knife / W.P. Knife 2','+10 strike; +11 parry','1D6 M.D.; thrown strike +10']], [180,121,227])
p('P.P. and hand-to-hand bonuses do not apply to guns. Aimed shots use 2 actions. For melee weapons, RUE allows '
  'weapon damage or supernatural-strength damage, whichever is greater; use <b>4D6 M.D.</b> for his standard full-force '
  'melee blow rather than adding punch damage to blade damage.','SmallX')
h('Durability, recovery and saving throws')
p('<b>Body: 120 M.D.C.</b> (2D4 roll 3+1, x10+60, plus 20 for two Juicer levels). '
  '<b>Living grafted armor: 120 M.D.C.</b>, a separate damage pool. Each normally regenerates <b>1D4x10 M.D.C./hour</b>; '
  'can regrow limbs/organs. No separate mortal H.P./S.D.C. pool is used after conversion.')
p('<b>Save bonuses:</b> magic +11; poison +9; disease +4; psionic attacks +4; possession +2 '
  '(+4 if the effect permits M.E.); insanity +2; Horror Factor +8; coma/death +50%. Bonuses are additions to the '
  'applicable saving roll or percentage, not automatic successes.','SmallX')
p('<b>Critical armor failure:</b> At 0 armor M.D.C., its roots retreat. Body regeneration stops; the symbiote drains '
  '3D6 body M.D.C./hour until it recovers 50 M.D.C. Normal regeneration then resumes; armor fully returns 10 hours '
  'after that threshold. Removing the Maxi-Inducer kills him.','SmallX')

newpage('Scholar Skills', 'O.C.C. skills  |  Scholar level 5')
p('Former skills remain frozen at the proficiency attained when Scholar level 5 ended.','SmallX')
p('Skills include I.Q. +8%; displayed percentages cap at 98%. Related 1 means selected at Scholar level 1, '
  'Related 3 means selected at level 3. Later acquisitions receive fewer advancement increases.','SmallX')
table([['Scholar skill','Current','Selection','Focus / qualification']]+scholar[:16],[182,62,83,201])
h('Professional expertise')
p('<b>Recognize Authenticity 78%</b>; <b>Professional Restoration 78%</b>. Successful restoration can improve '
  'quality/value by 40% at Scholar 5. He can teach mundane Secondary Skills with time and practice. Retention of these '
  'professional abilities and the Scholar perception bonus is an explicit campaign interpretation.','SmallX')
newpage('Scholar Skill Selections', 'Related and Secondary skills  |  Scholar level 5')
table([['Scholar skill','Current','Selection','Focus / qualification']]+scholar[16:],[182,62,83,201])
h('Selection accounting and cross-skill bonuses')
p('<b>11 starting Related selections:</b> 5 Technical + 6 Science. <b>2 level-3 selections:</b> Cryptography and Forgery. '
  '<b>5 Secondary selections:</b> three at level 1, one at level 2, one at level 5. His former required ancient '
  'weapon is Sword and his energy choice is Rifle. No old hand-to-hand selection; Martial Arts came with conversion.','SmallX')
p('<b>Synergies counted:</b> Anthropology +5% Lore/Pre-Rifts History; Archaeology +2% Lore/+10% History; '
  'Research +5% History; Mythology +5% Magic/Demons Lore; Advanced Mathematics +10% Astronomy; '
  'Restoration +10% Art/Forgery. Historical and Lore specialties are adapted to Atlantis rather than North America.','SmallX')

newpage('Juicer Skills and Abilities', 'Bio-Wizard Juicer level 2  |  True Atlantean racial abilities')
table([['Juicer skill','Current','Selection','Qualification']]+juicer,[186,65,85,192])
p('<b>Required languages:</b> Dragonese/Elven and American 98%. <b>Required weapons:</b> Energy Rifle and Sword '
  'retain their stronger Scholar-5 proficiency; his two new choices are Energy Pistol and Knife (both level 2). '
  '<b>Related:</b> four choices. <b>Secondary:</b> six choices, with I.Q. but no occupational bonus. '
  'No extra Bio-Wizard implant rewards and no cybernetics. Insanity percentile 24: no class-table insanity.','SmallX')
h('Atlantean heritage and the two tattoos')
p('<b>P.P.E.: 22</b> (base 10 + 12 from the Marks). Rest restores 10/hour, meditation 15/hour. '
  '<b>Operate Dimensional Pyramids: 68%</b> at effective racial level 7: 30 + 6x5 + I.Q. 8. '
  'Sense vampires within 1,000 ft; recognition 70% from the literal 10%-per-level racial rule (78% if GM applies I.Q.). '
  'Racial save bonuses +2 magic and +4 Horror Factor are already counted on page 1. Ordinary magical metamorphosis cannot change him.')
p('<b>Left wrist: flaming longsword.</b> Non-Tattooed-Man activation costs <b>20 P.P.E.</b> (double the listed 10), '
  'leaving 2 P.P.E. Duration 105 minutes at racial level 7; indestructible while active. The hilt carries his clan crest.')
p('<b>Right wrist: heart pierced by a wooden stake.</b> Costs <b>30 P.P.E.</b> (double 15), lasts 7 hours; protects '
  'against vampiric conversion/enslavement and vampire mind control, not physical attacks. He needs at least '
  '<b>8 additional P.P.E.</b> from a permitted external source to activate it.')
p('<b>Ley-line senses and phasing:</b> retains the Atlantis racial references to Ley Line Walker abilities. '
  'Using RUE and racial level 7: sense a ley line within 70 miles, location check 68%; follow it to a nexus at 78%; '
  'sense a Rift opening/closing within 110 miles, or along the connected line while on it. '
  'Same-line phasing needs 1D4 melees of uninterrupted concentration; no combat or conversation. '
  'Maximum four phasings/hour and 18/day at racial level 7. It transports only him and carried possessions; '
  'it does not open a dimensional Rift. No spellcasting or psychic powers are selected.','SmallX')
h('Equipment')
p('NG-L5 with one loaded Long E-Clip and two spare Long E-Clips; NG-57 with one loaded E-Clip and one spare; '
  'vibro-knife; heavy cloak cut to accommodate his living armor; boots, belt and satchel; radio, binoculars, '
  'flashlight, compass, 50 ft rope, canteen, basic first-aid supplies, magnifier, charcoal and waxed paper, '
  'two notebooks and a rugged recorder. No vehicle; no spendable credits. His grafted shell provides armor; '
  'an ordinary fitted body-armor suit is not assumed.')
p('The recorder holds his family message. One notebook is an archive of slave names; the other holds reconstructed '
  'pyramid diagrams and notes on the Maxi-Inducer. Gear is a modest campaign allocation from the rescuers, '
  'not a second free occupational starting package.','SmallX')

newpage('Background', 'Family  |  Captivity  |  Resistance  |  Objectives')
p('<b>Alias:</b> The Last Archivist.')
p(f'For more than two centuries, {first} was content. He and his wife <b>Eirene</b>, a conservator of manuscripts, '
  'made a home in an Atlantean sanctuary beyond Earth. Their children grew up among shelves, family meals and '
  'arguments that were encouraged to end in better questions. <b>Thalia</b>, the eldest, became an architectural '
  'historian; <b>Menandros</b> studied medicine; <b>Althea</b>, the youngest, loved music and travel. They are adults '
  'now. His happiest memories concern ordinary afternoons rather than great discoveries.')
p('When Atlantis returned to Earth, he joined an expedition to examine the ruins of his ancestral civilization '
  'and recover records before they were destroyed or sold. His family stayed home. The expedition was captured. '
  'The Splugorth discovered that a literate, multilingual Atlantean who understood historical artifacts was more '
  'valuable alive. He spent the following decades cataloguing trophies, translating confiscated documents and '
  'maintaining the records through which people were bought and moved.')
p('He complied visibly because survival might eventually bring him home. In secret, he recorded prisoners\' true '
  'names, concealed messages in restoration notes, and altered transport paperwork. His resistance work saved lives '
  'one clerical discrepancy at a time. He never told himself that service made him innocent. When a copied transport '
  'ledger exposed the network, the interrogators traced the work to him.')
p('A few years ago, his captors converted him into a Maxi-Killer as punishment and an experiment: could an old '
  'Atlantean dissident be made into a useful combat slave? The symbiote was forced beyond safe operating tolerances. '
  'They kept his mind intact because they wanted him to understand what his new body was doing. His combat '
  'training included forced sparring and escort duty. He survived by remembering every guard rotation and '
  'refusing to surrender the belief that his body was not the whole of him.')
p('Resistance allies eventually intercepted a transfer he had helped plan. He sabotaged the escort from inside '
  'while they freed the other prisoners. They released his restraints and returned his stolen notebooks. '
  'He escaped through their work and his own, and owes them loyalty rather than ownership. One of these rescuers '
  'can be a member of tonight\'s party or a shared contact.')
h('Family and Return Route')
p('A trusted dimensional courier brought a recent recording from Eirene. Each child contributed a message; '
  'Eirene authenticated it with the private family story of a broken blue bowl that only the five of them knew. '
  'They are together, safe in a relocated sanctuary and protected by their clan. The recording is genuine. '
  'Its arrival was possible through a rare courier passage that cannot simply carry him back.')
p('The sanctuary\'s former transit coordinates are obsolete. The resistance has a destination identifier, but '
  'the current return-route record sits in a secured Splugorth archive in Splynn, catalogued among confiscated '
  'Atlantean navigation records. He must recover it, secure a usable dimensional pyramid and enough support to '
  'make the journey, and escape pursuit without exposing his family\'s location. These are campaign objectives, '
  'not new automatic requirements imposed on all pyramids. His scholarship can distinguish the genuine record '
  'from obsolete or deliberately false entries.')
h('Roleplaying')
p('Patient voice, precise questions, and a habit of asking everyone their name. He hums an old household tune '
  'while repairing things and still sets aside food for someone absent. He chooses reunion over revenge, protects '
  'slaves and bystanders, and targets overseers, traffickers and the infrastructure of enslavement. He stays '
  'with the party because their cause is just and he cannot reach home alone. <b>His line:</b> '
  '&quot;Tell me your name. Whatever they called you here, tell me your name.&quot;')
h('Visible Decline')
p('The armor has pale seams that heal unevenly; dark capillaries surround its roots. He experiences brief '
  'hand tremors, involuntary spasms, palpitations, and moments when movement stops after a burst of speed. '
  'He hides them until he needs help. Sustained effort may trigger an episode.')

newpage('Generation and Rules', 'Attribute rolls  |  Campaign interpretations  |  Sources')
rows=[['Attribute','A','B','C','B + one swap','Final']]
for s in ('IQ','ME','MA','PS','PP','PE','PB','Spd'):
    rows.append([s,*[c['attributes'][s]['total'] for c in rolls['columns']],
                 rolls['final_pre_occupation'][s],rolls['final_attributes'][s]])
table(rows,[98,66,66,66,140,92])
p('<b>Column selection:</b> weighted total = sum of all eight racial attributes + twice P.P. + I.Q.; '
  'scores A 189, B 235, C 220. B wins. One allowed cross-column swap exchanges B\'s I.Q. 17 with A\'s I.Q. 21. '
  'The original columns remain in the roll log; no other attribute is exchanged.','SmallX')
rawrows=[['Attribute / racial pool','Selected dice history','Drop / bonus','Racial result']]
chosen=rolls['columns'][1]
for s,a in chosen['attributes'].items():
    if s=='IQ':a=rolls['columns'][0]['attributes']['IQ']
    histories=', '.join('>'.join(map(str,h)) for h in a['histories'])
    dropped=a['histories'][a['dropped_index']][-1]
    pool=(4 if s in ('ME','PS','Spd') else 3)
    bonus='; exceptional '+ '+'.join(str(h[-1]) for h in a['exceptional']) if a['exceptional'] else ''
    rawrows.append([s+f': {pool}D6'+(f"+{a['racial_add']}" if a['racial_add'] else ''),histories,
                    f'Drop {dropped}'+bonus,a['total']])
table(rawrows,[138,174,151,65])
p('A &gt; B in a die history means a reroll, not addition. Roll one extra d6 per racial pool, reroll every 1, '
  'drop the lowest die, then add racial constants. P.P. kept 6+4+6 = 16, with RUE exceptional dice 6+3 = 9. '
  'Exceptional rolls apply here only to the plain racial 3D6 attribute P.P.','SmallX')
p('<b>Occupational additions:</b> Scholar I.Q. +1 and M.A. +2; Juicer P.S. +8, P.E. +4 '
  '(1D4 roll 4), P.P. +3 (1D4 roll 2, then +1), Speed +60 (1D6 history 1&gt;6). '
  'Resource dice use ordinary rolls: body 2D4 = 3+1; old Scholar S.D.C. roll 1+6 is superseded by the M.D.C. body. '
  'Height roll 3 plus three century inches produces 6 ft 6 in.','SmallX')
h('Decline Rules')
p('The damaged experimental conversion is an agreed story exception to the normal Atlantean Maxi-Killer '
  'lifespan of 25 years plus 4D6 months. No death date or remaining-life roll is assigned.')
p('The GM can introduce episodes after sustained strain or at meaningful moments, with warning and a chance '
  'to respond. There is no blanket statistical penalty, automatic loss of an action, or random mid-fight death '
  'written into this sheet. Serious worsening, a final reunion and death are story decisions. Ordinary damage '
  'regeneration does not cure the failing host-symbiote relationship.','SmallX')
h('Campaign interpretations and sources')
p('The approved 5/2 career split is not one level-7 Juicer: new Juicer skills, combat and grafted blades use level 2. '
  'Old Scholar skills stay frozen; duplicate weapon grants use the stronger prior proficiency without stacking. '
  'Permanent Scholar attribute gains and professional abilities are retained. Racial pyramid/tattoo progression '
  'uses combined experience 7. Body M.D.C. uses the literal +10 per Juicer level (120); counting only post-first-level '
  'increases would give 110. Equipment, the minor clan and the family transit problem are original campaign choices.','SmallX')
p('<b>Primary references:</b> Rifts Ultimate Edition, Rogue Scholar (pp. 93-94), skill descriptions, '
  'Martial Arts and attribute/supernatural-strength rules; World Book 2: Atlantis, True Atlanteans and tattoo magic; '
  'World Book 10: Juicer Uprising, printed pp. 53-55 / PDF pp. 54-56. '
  'Energy-weapon schedules also checked against the '
  '<link href="https://d1vzi28wh99zvq.cloudfront.net/pdf_previews/96335-sample.pdf" color="#31676C">publisher\'s GM Support Kit sample</link>. '
  'The supplied Juicer edition grants no separate Perception bonus or level-based auto-dodge bonus; '
  'ordinary human Juicer bonuses have not been stacked. General career-retention guidance: '
  '<link href="https://palladiumbooks.com/dual-occs/" color="#31676C">palladiumbooks.com/dual-occs/</link>.','SmallX')

def footer(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(TEAL);canvas.setLineWidth(.5);canvas.line(42,38,570,38)
    canvas.setFont('Helvetica',8);canvas.setFillColor(INK)
    canvas.drawString(42,25,NAME+' | RIFTS Atlantis | Personal campaign character')
    canvas.drawRightString(570,25,str(doc.page))
    canvas.restoreState()

pdf=OUT/'atlantean-juicer-character.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=letter,leftMargin=42,rightMargin=42,
                      topMargin=40,bottomMargin=48,title=NAME+' - RIFTS Atlantis',author='Character workshop')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
data={'name':NAME,'attributes':rolls['final_attributes'],'scholar_skills':scholar,'juicer_skills':juicer,
      'body_MDC':120,'grafted_armor_MDC':120,'PPE':22,'attacks':5,'IQ_skill_bonus':8}
(OUT/'atlantean-juicer-data.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(pdf)
