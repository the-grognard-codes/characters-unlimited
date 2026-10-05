import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/pdf'
data = json.loads((OUT/'atlantean-juicer-data.json').read_text(encoding='utf-8'))
INK=colors.HexColor('#193039'); TEAL=colors.HexColor('#31676C'); PALE=colors.HexColor('#EDF3F3')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleX',fontName='Helvetica-Bold',fontSize=22,leading=26,textColor=INK,spaceAfter=5))
styles.add(ParagraphStyle(name='SubX',fontSize=10,leading=13,textColor=TEAL,spaceAfter=10))
styles.add(ParagraphStyle(name='HeadX',fontName='Helvetica-Bold',fontSize=11.5,leading=15,textColor=TEAL,spaceBefore=8,spaceAfter=5))
styles.add(ParagraphStyle(name='BodyX',fontSize=9.5,leading=12.5,textColor=INK,spaceAfter=6))
styles.add(ParagraphStyle(name='CellX',fontSize=8.7,leading=11,textColor=INK))
styles.add(ParagraphStyle(name='SmallX',fontSize=8.3,leading=10.7,textColor=INK,spaceAfter=5))
styles.add(ParagraphStyle(name='WhiteX',fontName='Helvetica-Bold',fontSize=8.7,leading=11,textColor=colors.white))
story=[]
def p(text,style='BodyX'):story.append(Paragraph(text,styles[style]))
def h(text):p(text,'HeadX')
def page(title,sub):
    if story:story.append(PageBreak())
    p(title,'TitleX');p(sub,'SubX')
def table(rows,widths):
    cells=[[Paragraph(str(v),styles['WhiteX' if i==0 else 'CellX']) for v in row] for i,row in enumerate(rows)]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
      ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
      ('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#D4DFDF'))]))
    story.append(t)

page(data['name'],'True Atlantean  |  Rogue Scholar 5 / Bio-Wizard Juicer 2  |  Scrupulous')
table([['I.Q.','M.E.','M.A.','P.S.','P.P.','P.E.','P.B.','Spd.'],
       ['22','18','22','32 supernatural','28','25','18','85']],[66]*8)
p('Age 362  |  6 ft 6 in  |  225 lb before living armor  |  Trust/intimidate 70%  |  Speed ~58 mph','SmallX')
h('Resources')
table([['Body M.D.C.','Grafted armor M.D.C.','P.P.E.'],
       ['Current __________ / <b>120</b>','Current __________ / <b>120</b>','Current __________ / <b>22</b>']],[176]*3)
h('Combat')
table([['Actions and initiative','Attacks and defenses','Other bonuses'],
       ['<b>5 actions/melee</b> (15 sec)<br/>Initiative <b>+3</b><br/>Martial Arts level 2',
        'Unarmed strike <b>+9</b><br/>Parry / dodge <b>+10</b><br/>Automatic dodge <b>+7</b>',
        'Roll with impact <b>+6</b><br/>Pull punch <b>+3</b><br/>Perception <b>+5</b>']],[164,182,182])
p('Automatic parry/dodge covers attacks from behind and surprise. Automatic dodge costs no action; '
  'ordinary dodge costs one. Use the automatic dodge bonus separately.','SmallX')
table([['Attack / weapon','Bonus','Damage / range / ammunition'],
       ['Punch','+9','4D6 M.D.'],
       ['Power punch','+9','1D4x10 M.D.; 2 actions'],
       ['Flaming tattoo longsword','+11 strike; +12 parry','2D6 M.D. weapon; 4D6 M.D. full-force blow'],
       ['Grafted forearm blades','+11 strike; +12 parry','Two blades, one/arm; 2D6 M.D. each; 4D6 M.D. full force'],
       ['NG-L5 laser rifle','+2 single; +4 aimed','3D6 M.D.; 1,600 ft; 20 shots/Long E-Clip'],
       ['NG-57 ion pistol','+1 single; +3 aimed','2D4 or 3D6 M.D.; 500 ft; 10 shots/E-Clip'],
       ['Vibro-knife','+10 strike; +11 parry','1D6 M.D. weapon; 4D6 M.D. full force; thrown strike +10']],[174,118,236])
p('Aimed gunshots use 2 actions. Gun bonuses above are complete: do not add P.P. or hand-to-hand bonuses. '
  'For melee, use weapon damage or supernatural-strength damage, whichever is greater; do not add the two. '
  'No simultaneous paired-blade strike.','SmallX')
h('Saving Throws')
table([['Magic','Poison','Disease','Psionic attacks','Possession','Insanity','Horror Factor','Coma/death'],
       ['+11','+9','+4','+4','+2*','+2','+8','+50%']],[66]*8)
p('*Possession is +4 when the effect allows his M.E. bonus. Coma/death adds 50 percentage points to the '
  'applicable survival check.','SmallX')
h('Ammunition')
p('Rifle: loaded Long E-Clip ______ / 20  |  2 spare Long E-Clips<br/>'
  'Pistol: loaded E-Clip ______ / 10  |  1 spare E-Clip')

page('Skills','Current percentages')
skills=[(s[0],s[1]) for s in data['scholar_skills']+data['juicer_skills']]
skills += [('Recognize Authenticity','78%'),('Professional Restoration','78%'),('Operate Dimensional Pyramids','68%')]
skills.sort(key=lambda s:s[0].lower())
mid=(len(skills)+1)//2
left,right=skills[:mid],skills[mid:]
rows=[['Skill','%','Skill','%']]
for i in range(mid):
    a=left[i];b=right[i] if i<len(right) else ('','')
    rows.append([*a,*b])
table(rows,[204,60,204,60])
h('Specialized Checks')
p('<b>History: Pre-Rifts 98% / 90%:</b> general / ancient Atlantean specialty.<br/>'
  '<b>History: Post-Apocalypse 98% / 93%:</b> general / Splugorth Atlantis specialty.<br/>'
  '<b>Archaeology 68% / 58%:</b> historical study / artifact identification.<br/>'
  '<b>Climbing 63% / 53%:</b> climbing / rappelling.<br/>'
  '<b>Lore: Magic:</b> symbols, runes and circles 70%; recognize enchantment 65%; '
  'identify unknown or alien magic artifacts 65%.<br/>'
  '<b>Find Contraband:</b> books and historical artifacts 85%.<br/>'
  '<b>Literacy: Techno-Can:</b> written language only.','SmallX')

page('Abilities and Equipment','Racial abilities  |  Symbiotes  |  Inventory')
h('Healing and Grafted Armor')
p('Body and grafted armor each normally regenerate <b>1D4x10 M.D.C. per hour</b>. '
  'Severed limbs and lost organs can regrow; virtually impervious to pain.')
p('<b>Armor at 0 M.D.C.:</b> the shell retreats; body regeneration stops. The symbiote drains '
  '<b>3D6 body M.D.C. per hour</b>, restoring the same amount to itself. At <b>50 M.D.C.</b>, '
  'normal regeneration resumes; the armor fully returns 10 hours later. If Lysandros dies, both die. '
  '<b>Removing the Maxi-Inducer kills him.</b>')
h('Atlantean Abilities')
p('<b>Strength:</b> carry 1,600 lb; lift 3,200 lb.<br/>'
  '<b>Vampires:</b> sense within 1,000 ft; recognize by appearance 70%.<br/>'
  '<b>Ley lines:</b> sense within 70 miles; locate 68%; follow to a nexus 78%.<br/>'
  '<b>Rifts:</b> sense opening/closing within 110 miles; while on a ley line, sense along it or a connected line.<br/>'
  '<b>Phasing:</b> teleport himself and carried possessions along the same ley line; no P.P.E. cost. '
  'Concentrate for 1D4 melees without combat or conversation. Limit 4/hour and 18/day.<br/>'
  '<b>Protection:</b> cannot be changed by ordinary magical metamorphosis.<br/>'
  '<b>P.P.E. recovery:</b> 10/hour resting; 15/hour meditating. No spellcasting or psionics.')
h('Magic Tattoos')
table([['Tattoo','Activation','Effect'],
       ['Flaming longsword<br/>(left wrist)','20 P.P.E.<br/>105 minutes','Indestructible summoned longsword; 2D6 M.D. weapon damage.'],
       ['Heart pierced by stake<br/>(right wrist)','30 P.P.E.<br/>7 hours','Protects from vampire conversion/enslavement and mind control; not physical damage.']],[162,97,269])
p('The protection mark needs at least <b>8 P.P.E. beyond his personal reserve</b>, from a permitted outside source.','SmallX')
h('Inventory')
p('NG-L5 rifle; NG-57 pistol; vibro-knife; 3 Long E-Clips total; 2 standard E-Clips total. '
  'Cloak fitted around living armor; boots, belt and satchel; radio, binoculars, flashlight, compass, '
  '50 ft rope, canteen, first-aid supplies, magnifier, charcoal, waxed paper, two notebooks and rugged recorder. '
  '<b>Credits: 0. No vehicle.</b>')
p('Recorder: authenticated family message. Notebooks: slave names, pyramid diagrams and symbiote observations.','SmallX')
h('Roleplaying and Objective')
p('Wife <b>Eirene</b>; children <b>Thalia, Menandros and Althea</b>. All are safe in an off-Earth sanctuary. '
  'Recover their return-route record from the secured archive in Splynn and secure dimensional pyramid passage. '
  'Reunion comes before revenge; protect slaves and bystanders. Patient voice; asks people their true names.')
p('<b>Decline:</b> pale armor seams, dark capillaries, tremors, spasms, palpitations and brief movement failures. '
  'Episodes are story driven; no fixed countdown or standing statistical penalty.','SmallX')

def footer(c,doc):
    c.saveState();c.setStrokeColor(TEAL);c.line(42,38,570,38)
    c.setFillColor(INK);c.setFont('Helvetica',8)
    c.drawString(42,25,'Lysandros Melanthos | Play sheet')
    c.drawRightString(570,25,str(doc.page));c.restoreState()

pdf=OUT/'lysandros-melanthos-play-sheet.pdf'
SimpleDocTemplate(str(pdf),pagesize=letter,leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=48,
                  title='Lysandros Melanthos - Play Sheet',author='Character workshop').build(
                  story,onFirstPage=footer,onLaterPages=footer)
print(pdf)
