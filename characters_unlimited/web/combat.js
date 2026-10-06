"use strict";
let combatView;
function combatValue(result) {
  return result.value == null ? 'pending' : (result.value > 0 ? '+' : '') + result.value + (result.unit || '');
}
function combatExplanation(result) {
  const terms = Object.entries(result.contributions).map(([name,value]) => `${name.replaceAll('_',' ')} ${value > 0 ? '+' : ''}${value}${result.unit || ''}`);
  const references = (result.sources || []).map(source => `${source.book}, pp. ${source.pages.join(', ')}`);
  return [...terms, ...references].join(' · ');
}
function combatRow(name, result) {
  const detail = document.createElement('details'), heading = document.createElement('summary'), explanation = document.createElement('p');
  heading.textContent = `${name}: ${name === 'attacks' ? result.value : combatValue(result)}`;
  explanation.textContent = combatExplanation(result);
  detail.append(heading, explanation); return detail;
}
function renderCombat(view) {
  combatView = view;
  $('combat-controls').hidden = !view.catalog;
  $('combat-learned-label').hidden = current.level === 1;
  $('combat-learned-level').replaceChildren(...Array.from({length:current.level}, (_,index) => {
    const option=document.createElement('option'); option.value=index+1; option.textContent=index+1; return option;
  }));
  $('combat-learned-level').value = current.level;
  $('combat-counts').textContent = view.catalog ? Object.entries(view.remaining).map(([name,count]) => `${name}: ${count} required choices remaining`).join(' · ') + ` · related skills used by training: ${view.related_cost}` : '';
  if (view.catalog) {
    for (const [id, definitions] of [['hand',view.catalog.hand_to_hand],['ancient',view.catalog.ancient],['modern',view.catalog.modern]]) {
      const previous = $('combat-' + id).value;
      $('combat-' + id).replaceChildren(...definitions.map(definition => { const option=document.createElement('option'); option.value=definition.id; option.textContent=definition.name; return option; }));
      if (id !== 'hand' && definitions.some(definition => definition.id === previous)) $('combat-' + id).value = previous;
    }
    $('combat-hand').value = view.choices.hand_to_hand;
  }
  $('combat-list').replaceChildren();
  for (const family of ['ancient','modern']) {
    for (const id of view.fixed_proficiencies?.[family] || []) {
      const definition = view.catalog[family].find(item => item.id === id);
      const row = document.createElement('p');
      row.textContent = `${definition.name} · O.C.C. grant · ${modifierSourceCitation(view.fixed_proficiencies.source)}`;
      $('combat-list').append(row);
    }
  }
  for (const family of ['ancient','modern']) {
    (view.choices?.[family] || []).forEach((id,index) => {
      const row=document.createElement('p'), remove=document.createElement('button');
      row.textContent=view.catalog[family].find(definition => definition.id===id).name + ' ';
      remove.textContent='Remove proficiency'; remove.type='button';
      remove.onclick=() => saveCombat({[family]:combatView.choices[family].filter((value,position)=>position!==index)});
      row.append(remove); $('combat-list').append(row);
    });
  }
  $('combat-totals').replaceChildren(...Object.entries(view.totals).map(([name,result])=>combatRow(name.replaceAll('_',' '),result)));
  $('class-bonuses').replaceChildren(...Object.entries(view.class_bonuses || {}).map(([name,result]) => {
    const row = combatRow(name + ' O.C.C. bonus',result);
    const note = document.createElement('p'); note.className = 'help';
    note.textContent = 'Class contribution only; other Perception modifiers remain separate.';
    row.append(note); return row;
  }));
  $('saving-section').hidden = !Object.keys(view.saving_bonuses || {}).length;
  $('saving-bonuses').replaceChildren(...Object.values(view.saving_bonuses || {}).map(result=>combatRow(result.name,result)));
  $('saving-notes').textContent = (view.saving_notes || []).join(' ');
  const attacks=[];
  for (const [identifier, condition] of Object.entries(view.conditions || {})) {
    const detail=document.createElement('details'), heading=document.createElement('summary'), explanation=document.createElement('p');
    const names={critical:'Critical strike',knockout:'Knockout/stun',death_blow:'Death blow'};
    const range=condition.natural_min===condition.natural_max ? condition.natural_min : `${condition.natural_min}–${condition.natural_max}`;
    heading.textContent=`${names[identifier] || identifier}: natural ${range}`;
    explanation.textContent=`Hand-to-hand condition. Use the natural die, before bonuses. Other attack restrictions and effects follow below. ${condition.source.book}, pp. ${condition.source.pages.join(', ')}.`;
    detail.append(heading,explanation); attacks.push(detail);
  }
  view.unarmed.forEach(item => { const row=document.createElement('p'); row.textContent=`${item.name}: ${item.damage ?? 'No damage'} · ${item.actions} action(s)`; attacks.push(row); });
  view.melee.forEach(item => { attacks.push(combatRow(item.name+' melee strike',item.strike),combatRow(item.name+' melee parry',item.parry)); if (item.thrown) attacks.push(combatRow(item.name+' thrown strike',item.thrown)); });
  view.shooting.forEach(item => {
    const detail=document.createElement('details'), heading=document.createElement('summary');
    heading.textContent=item.name+' shooting ('+(item.trained?'trained':'untrained')+')'; detail.append(heading);
    for (const context of ['single','aimed','burst','wild']) {
      const row=document.createElement('p'), result=item[context];
      row.textContent=`${context}: ${combatValue(result)} · ${result.actions} action(s) · ${combatExplanation(result)}`; detail.append(row);
    }
    attacks.push(detail);
  });
  $('combat-attacks').replaceChildren(...attacks);
  const source=view.sources.map(item=>`${item.book}, pp. ${item.pages.join(', ')}`);
  for (const [id,items] of [['combat-warnings',view.warnings],['combat-gaps',[...view.gaps,...(view.notes || []),...source]]]) {
    $(id).replaceChildren(...items.map(message=>{ const item=document.createElement('li'); item.textContent=message; return item; }));
  }
}
function saveCombat(changes) {
  if (!skillsReady || navigationBusy || !combatView?.catalog) return;
  characterAction('combat',{learned_level:Number($('combat-learned-level').value),choices:{...combatView.choices,...changes}}).catch(showError);
}
function wireCombatEvents() {
  $('combat-hand').onchange=()=>saveCombat({hand_to_hand:$('combat-hand').value});
  for (const family of ['ancient','modern']) $('combat-add-'+family).onclick=()=>saveCombat({[family]:[...combatView.choices[family],$('combat-'+family).value]});
}
