'use strict';
let equipmentReady = false, equipmentSequence = 0, equipmentView;
const startingGroupSelections = new Map();
function setEquipmentBusy() {
  document.querySelectorAll('#equipment-panel input, #equipment-panel select, #equipment-panel button').forEach(element => {
    element.disabled = navigationBusy || !equipmentReady;
  });
  const selected = equipmentView?.catalog.find(item => item.id === $('equipment-choice').value);
  $('purchase-equipment').disabled = navigationBusy || !equipmentReady || (selected?.cost_credits == null && !selected?.cost_credits_range);
  $('reload-weapon').disabled = navigationBusy || !equipmentReady || !$('reload-weapon-choice').value || !$('reload-clip-choice').value;
}
async function loadEquipment(character) {
  const sequence = ++equipmentSequence;
  equipmentReady = false; setEquipmentBusy();
  if (character.game !== 'rifts') return;
  const view = await request(`/api/characters/${character.id}/equipment`);
  if (current.id !== character.id || sequence !== equipmentSequence) return;
  equipmentView = view;
  const starting = view.starting_choices;
  $('starting-choices-form').hidden = !starting.supported || starting.generated;
  $('starting-choices-receipt').hidden = !starting.generated;
  $('starting-choices-guidance').textContent = starting.guidance.join(' ');
  for (const [kind,ids] of Object.entries(starting.definitions)) {
    $('starting-choice-' + kind).replaceChildren(...ids.map(id => {
      const option = document.createElement('option'); option.value = id;
      option.textContent = view.catalog.find(item => item.id === id).name; return option;
    }));
  }
  $('starting-choices-grants').replaceChildren(...starting.grants.map(grant => {
    const row = document.createElement('li');
    row.textContent = `${view.catalog.find(item => item.id === grant.item_id).name} × ${grant.quantity}`; return row;
  }));
  $('starting-choices-source').textContent = starting.generated ? `${equipmentSourceCitation(starting.source)}. Original free grant; later inventory edits do not regenerate these items.` : '';
  renderStartingGroups(view.starting_groups, view.catalog, character.id);
  const gear = view.starting_gear;
  $('grant-starting-gear').hidden = !gear.supported || gear.generated;
  $('starting-gear-guidance').textContent = gear.guidance.join(' ');
  $('starting-gear-status').textContent = gear.generated ? `Original personal gear grant recorded (${gear.grants.length} rows). Edited or removed possessions do not regenerate.` : '';
  $('starting-gear-receipt').hidden = !gear.generated;
  $('starting-gear-grants').replaceChildren(...gear.grants.map(grant => {
    const row = document.createElement('li');
    row.textContent = `${view.catalog.find(item => item.id === grant.item_id).name} × ${grant.quantity}`; return row;
  }));
  $('starting-gear-source').textContent = gear.generated ? `${equipmentSourceCitation(gear.source)}. This is the original grant; current possessions are listed below.` : '';
  const funds = view.starting_funds;
  $('generate-starting-funds').hidden = !funds.supported || funds.generated;
  $('starting-funds-guidance').textContent = funds.guidance.join(' ');
  $('starting-funds-record').replaceChildren(...Object.entries(funds.funds).map(([id,record]) => {
    const row = document.createElement('p'); row.className = 'help';
    const definition = funds.definitions.find(entry => entry.id === id);
    row.textContent = `${definition.name}: ${record.value.toLocaleString()} credits = (${[...record.rolls, ...(definition.constant ? [definition.constant] : [])].join(' + ') || '0'}) × ${definition.multiplier}. ${equipmentSourceCitation(record.source)}.`;
    return row;
  }));
  $('equipment-credits').value = view.inventory.credits;
  $('equipment-weight').textContent = `${view.carried_weight_complete ? 'Carried weight' : 'Known carried weight'}: ${view.carried_weight_lbs.toLocaleString()} lb.${view.carried_weight_complete ? '' : ` ${view.unknown_carried_weight_quantity} carried item(s) have unspecified weight.`} Reviewed items only; an encumbrance limit is not yet calculated.`;
  $('equipment-guidance').textContent = view.guidance.join(' ');
  $('equipment-warnings').replaceChildren(...view.warnings.map(message => {
    const row = document.createElement('li'); row.textContent = message; return row;
  }));
  filterEquipmentCatalog();
  const reloadable = view.items.filter(item => item.category === 'weapon' && item.weapon_kind !== 'melee' && item.location === 'carried' && item.quantity === 1);
  $('reload-weapon-choice').replaceChildren(...reloadable.map(item => {
    const option = document.createElement('option'); option.value = item.id; option.textContent = `${item.name} · ${item.shots}/${item.capacity} shots`; return option;
  }));
  filterReloadClips();
  $('equipment-list').replaceChildren(...view.items.map(item => {
    const row = document.createElement('details'), heading = document.createElement('summary');
    heading.textContent = `${item.name} × ${item.quantity} · ${item.location}${item.equipped ? ' · equipped' : ''}`;
    const source = document.createElement('p'); source.className = 'help';
    source.textContent = `${equipmentSourceCitation(item.source)} · ${item.weight_lbs == null ? 'weight unspecified' : item.weight_lbs + ' lb each'}${item.cost_credits_range ? ` · ${item.cost_credits_range.min}–${item.cost_credits_range.max} credits each` : item.cost_credits == null ? ' · purchase price unspecified' : ''}`;
    const form = document.createElement('form');
    const input = (text,type,value) => {
      const label = document.createElement('label'), field = document.createElement('input');
      label.textContent = text; field.type = type;
      if (type === 'checkbox') field.checked = value;
      else { field.value = value; field.required = true; field.step = '1'; }
      label.append(field); form.append(label); return field;
    };
    const quantity = input('Quantity','number',item.quantity); quantity.min = '1'; quantity.max = '1000';
    const label = document.createElement('label'); label.textContent = 'Location';
    const location = document.createElement('select');
    for (const name of ['carried','stored']) {
      const option = document.createElement('option'); option.value = name; option.textContent = name; location.append(option);
    }
    location.value = item.location; label.append(location); form.append(label);
    const equipped = input('Equipped','checkbox',item.equipped);
    const shots = item.shots == null ? null : input('Shots remaining per item','number',item.shots);
    if (shots) { shots.min = '0'; shots.max = String(item.capacity); }
    const save = document.createElement('button'); save.type = 'submit'; save.textContent = 'Save possession';
    const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Remove possession';
    form.append(save,remove);
    if (item.quantity > 1) {
      const split = document.createElement('button'); split.type = 'button'; split.textContent = 'Separate one item into its own row';
      split.onclick = () => characterAction('split-equipment',{possession_id:item.id}).catch(showError);
      form.append(split);
    }
    form.onsubmit = event => {
      event.preventDefault();
      const inventory = structuredClone(equipmentView.inventory);
      Object.assign(inventory.items.find(entry => entry.id === item.id),{
        quantity:Number(quantity.value),location:location.value,equipped:equipped.checked,shots:shots ? Number(shots.value) : null
      });
      characterAction('equipment',{inventory}).catch(showError);
    };
    remove.onclick = () => {
      const inventory = structuredClone(equipmentView.inventory);
      inventory.items = inventory.items.filter(entry => entry.id !== item.id);
      characterAction('equipment',{inventory}).catch(showError);
    };
    row.append(heading,source,form); return row;
  }));
  const explanations = [];
  for (const attack of view.attacks) {
    const row = document.createElement('details'), heading = document.createElement('summary');
    heading.textContent = `${attack.name} · ${attack.damage}`;
    const text = document.createElement('p'); text.className = 'help';
    text.textContent = ['single','aimed'].map(context => {
      const total = attack[context];
      return `${context}: ${total.value == null ? 'unavailable; see guidance' : '+' + total.value} (${Object.entries(total.contributions).map(([name,value]) => name.replaceAll('_',' ') + ' ' + value).join(' + ')}) · ${total.actions} action(s)`;
    }).join(' · ');
    if (attack.guidance) text.textContent += ' · ' + attack.guidance;
    row.append(heading,text); explanations.push(row);
  }
  for (const attack of view.melee_attacks) {
    const row = document.createElement('details'), heading = document.createElement('summary');
    heading.textContent = `${attack.name} · ${attack.damage}`;
    const text = document.createElement('p'); text.className = 'help';
    text.textContent = ['strike','parry'].map(context => {
      const total = attack[context];
      return `${context}: ${total.value == null ? 'pending' : '+' + total.value} (${Object.entries(total.contributions).map(([name,value]) => name.replaceAll('_',' ') + ' ' + value).join(' + ')})`;
    }).join(' · ') + ` · Damage bonus: ${Object.entries(attack.damage_bonus.contributions).map(([name,value]) => name.replaceAll('_',' ') + ' ' + value).join(', ')}. ${attack.damage_bonus.sources.map(source => source.book + ', pp. ' + source.pages.join(', ')).join('; ')}. ` + attack.guidance;
    row.append(heading,text); explanations.push(row);
  }
  for (const armor of view.armor) {
    const row = document.createElement('p'); row.className = 'help';
    row.textContent = `${armor.name}: ${Object.entries(armor.locations).map(([location,value]) => location.replaceAll('_',' ') + ' ' + value + ' M.D.C.').join(' · ')}. Movement skill penalty: ${armor.movement_penalty}%.`;
    const protection = document.createElement('p'); protection.className = 'help';
    protection.textContent = `${armor.environmental == null ? 'Environmental status unspecified by these pinned rules' : armor.environmental ? 'Environmental armor' : 'Non-environmental armor'}. ${armor.protection_notes.join(' ')}`;
    const citation = document.createElement('p'); citation.className = 'help';
    citation.textContent = `${armor.source.book}, p. ${armor.source.pages.join(', ')}; movement: p. ${armor.movement_source.pages.join(', ')}.`;
    explanations.push(row,protection,citation);
  }
  $('equipment-effects').replaceChildren(...explanations);
  equipmentReady = true; setEquipmentBusy();
}
function equipmentSourceCitation(source) {
  return modifierSourceCitation(source) + (source.section ? '; ' + source.section : '');
}
function renderStartingGroups(starting, catalog, characterId) {
  const panel = $('starting-groups'), container = $('starting-groups-list');
  const groups = starting?.supported ? (starting.groups || []).filter(group => group.generated || group.options?.some(id => catalog.some(item => item.id === id))) : [];
  panel.hidden = !groups.length;
  container.replaceChildren(...groups.map(group => {
    const section = document.createElement('section');
    const heading = document.createElement('h4');
    heading.textContent = group.name + (group.training_name ? ' - ' + group.training_name : '');
    section.append(heading);
    const selectionKey = `${characterId}:${group.id}`;
    if (group.generated && group.receipt) {
      const selected = catalog.find(item => item.id === group.receipt.selection);
      const record = document.createElement('p'); record.className = 'help';
      record.textContent = `Original selection: ${selected?.name || group.receipt.selection} × ${group.quantity}. This receipt is independent of current inventory and cannot grant this group again.`;
      section.append(record);
      if (group.receipt.condition) {
        const condition = document.createElement('p'); condition.className = 'help';
        condition.textContent = `${group.condition.name}: ${group.receipt.condition.value}%; recorded dice: ${group.receipt.condition.rolls.join(', ')}.`;
        section.append(condition);
      }
      for (const grant of group.receipt.grants.slice(1)) {
        const item = catalog.find(item => item.id === grant.item_id);
        const detail = document.createElement('p'); detail.className = 'help';
        detail.textContent = `Original additional grant: ${item?.name || grant.item_id} × ${grant.quantity}${grant.rolls ? `; recorded dice: ${grant.rolls.join(', ')}` : ''}.`;
        section.append(detail);
      }
      const receiptSource = document.createElement('p'); receiptSource.className = 'help';
      receiptSource.textContent = `Original receipt source: ${equipmentSourceCitation(group.receipt.source)}`;
      section.append(receiptSource);
    } else {
      const form = document.createElement('form');
      const label = document.createElement('label');
      label.textContent = `${group.category} choice`;
      const select = document.createElement('select');
      const options = group.options.map(id => catalog.find(item => item.id === id)).filter(Boolean);
      select.replaceChildren(...options.map(item => {
        const option = document.createElement('option'); option.value = item.id; option.textContent = item.name; return option;
      }));
      const previous = startingGroupSelections.get(selectionKey);
      if (options.some(item => item.id === previous)) select.value = previous;
      select.onchange = () => startingGroupSelections.set(selectionKey, select.value);
      label.append(select); form.append(label);
      const button = document.createElement('button'); button.type = 'submit'; button.textContent = 'Add selected starting equipment';
      form.append(button);
      form.onsubmit = event => {
        event.preventDefault();
        startingGroupSelections.set(selectionKey, select.value);
        characterAction('starting-group',{group_id:group.id,selection:select.value}).catch(showError);
      };
      section.append(form);
    }
    const source = document.createElement('p'); source.className = 'help';
    source.textContent = `Rule source: ${equipmentSourceCitation(group.source)}`;
    const guidance = document.createElement('p'); guidance.className = 'help';
    guidance.textContent = `${group.quantity} item${group.quantity === 1 ? '' : 's'} · ${group.location}. ${group.guidance.join(' ')}`;
    const requirements = document.createElement('p'); requirements.className = 'help';
    const renderRequirements = option => {
      requirements.textContent = (group.option_requirements?.[option] || []).map(row =>
        `${row.satisfied ? 'Training matched' : 'Training guidance'}: ${row.text}`).join(' ? ');
    };
    if (group.generated) renderRequirements(group.receipt.selection);
    else {
      const select = section.querySelector('select');
      renderRequirements(select.value);
      select.addEventListener('change', () => renderRequirements(select.value));
    }
    section.append(source, guidance, requirements);
    return section;
  }));
}
function filterEquipmentCatalog() {
  if (!equipmentView) return;
  const category = $('equipment-category').value, previous = $('equipment-choice').value;
  const entries = equipmentView.catalog.filter(item => !category || item.category === category);
  $('equipment-choice').replaceChildren(...entries.map(item => {
    const option = document.createElement('option'); option.value = item.id;
    option.textContent = `${item.name} · ${item.cost_credits_range ? item.cost_credits_range.min + '–' + item.cost_credits_range.max + ' credits' : item.cost_credits == null ? 'purchase price unspecified' : item.cost_credits.toLocaleString() + ' credits'}`; return option;
  }));
  if (entries.some(item => item.id === previous)) $('equipment-choice').value = previous;
  const selected = entries.find(item => item.id === $('equipment-choice').value);
  const range = selected?.cost_credits_range, price = $('equipment-unit-cost');
  $('equipment-unit-cost-label').hidden = !range;
  price.required = !!range;
  if (range) { price.min = range.min; price.max = range.max; price.value = ''; }
  $('equipment-price-guidance').textContent = range ? `Choose a price per item within the source range (${range.min}–${range.max} credits).` : selected?.cost_credits == null ? 'This item has no reviewed purchase price. Use its class starting grant to add it without a purchase.' : '';
  setEquipmentBusy();
}
function filterReloadClips() {
  const weapon = equipmentView?.items.find(item => item.id === $('reload-weapon-choice').value);
  const clips = equipmentView?.items.filter(item => item.category === 'ammunition' && item.location === 'carried' && item.quantity === 1 && item.compatible_weapons.includes(weapon?.item_id)) || [];
  $('reload-clip-choice').replaceChildren(...clips.map(item => {
    const option = document.createElement('option'); option.value = item.id; option.textContent = `${item.name} · ${item.shots}/${item.capacity} shots`; return option;
  }));
  setEquipmentBusy();
}
function wireEquipmentEvents() {
  $('starting-choices-form').onsubmit = event => {
    event.preventDefault();
    const choices = Object.fromEntries(['armor','gun','knife','transport'].map(kind => [kind,$('starting-choice-' + kind).value]));
    characterAction('starting-choices',{choices}).catch(showError);
  };
  $('reload-weapon-choice').onchange = filterReloadClips;
  $('equipment-reload-form').onsubmit = event => {
    event.preventDefault();
    characterAction('reload-weapon',{weapon_possession_id:$('reload-weapon-choice').value,clip_possession_id:$('reload-clip-choice').value}).catch(showError);
  };
  $('grant-starting-gear').onclick = () => characterAction('starting-gear',{}).catch(showError);
  $('equipment-choice').onchange = filterEquipmentCatalog;
  $('generate-starting-funds').onclick = () => characterAction('starting-funds',{}).catch(showError);
  $('equipment-category').onchange = filterEquipmentCatalog;
  $('equipment-funds-form').onsubmit = event => {
    event.preventDefault();
    const inventory = structuredClone(equipmentView.inventory); inventory.credits = Number($('equipment-credits').value);
    characterAction('equipment',{inventory}).catch(showError);
  };
  $('equipment-purchase-form').onsubmit = event => {
    event.preventDefault();
    const purchase = {item_id:$('equipment-choice').value,quantity:Number($('equipment-quantity').value)};
    if (equipmentView.catalog.find(item => item.id === purchase.item_id)?.cost_credits_range) purchase.unit_cost = Number($('equipment-unit-cost').value);
    characterAction('purchase-equipment',purchase).catch(showError);
  };
}
