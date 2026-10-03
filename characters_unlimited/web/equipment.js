'use strict';
let equipmentReady = false, equipmentSequence = 0, equipmentView;
function setEquipmentBusy() {
  document.querySelectorAll('#equipment-panel input, #equipment-panel select, #equipment-panel button').forEach(element => {
    element.disabled = navigationBusy || !equipmentReady;
  });
  const selected = equipmentView?.catalog.find(item => item.id === $('equipment-choice').value);
  $('purchase-equipment').disabled = navigationBusy || !equipmentReady || selected?.cost_credits == null;
}
async function loadEquipment(character) {
  const sequence = ++equipmentSequence;
  equipmentReady = false; setEquipmentBusy();
  if (character.game !== 'rifts') return;
  const view = await request(`/api/characters/${character.id}/equipment`);
  if (current.id !== character.id || sequence !== equipmentSequence) return;
  equipmentView = view;
  const gear = view.starting_gear;
  $('grant-starting-gear').hidden = !gear.supported || gear.generated;
  $('starting-gear-guidance').textContent = gear.guidance.join(' ');
  $('starting-gear-status').textContent = gear.generated ? `Original personal gear grant recorded (${gear.grants.length} rows). Edited or removed possessions do not regenerate.` : '';
  $('starting-gear-receipt').hidden = !gear.generated;
  $('starting-gear-grants').replaceChildren(...gear.grants.map(grant => {
    const row = document.createElement('li');
    row.textContent = `${view.catalog.find(item => item.id === grant.item_id).name} × ${grant.quantity}`; return row;
  }));
  $('starting-gear-source').textContent = gear.generated ? `${gear.source.book}, p. ${gear.source.pages.join(', ')}. This is the original grant; current possessions are listed below.` : '';
  const funds = view.starting_funds;
  $('generate-starting-funds').hidden = !funds.supported || funds.generated;
  $('starting-funds-guidance').textContent = funds.guidance.join(' ');
  $('starting-funds-record').replaceChildren(...Object.entries(funds.funds).map(([id,record]) => {
    const row = document.createElement('p'); row.className = 'help';
    const definition = funds.definitions.find(entry => entry.id === id);
    row.textContent = `${definition.name}: ${record.value.toLocaleString()} credits = (${record.rolls.join(' + ')}) × ${definition.multiplier}. ${record.source.book}, p. ${record.source.pages.join(', ')}.`;
    return row;
  }));
  $('equipment-credits').value = view.inventory.credits;
  $('equipment-weight').textContent = `${view.carried_weight_complete ? 'Carried weight' : 'Known carried weight'}: ${view.carried_weight_lbs.toLocaleString()} lb.${view.carried_weight_complete ? '' : ` ${view.unknown_carried_weight_quantity} carried item(s) have unspecified weight.`} Reviewed items only; an encumbrance limit is not yet calculated.`;
  $('equipment-guidance').textContent = view.guidance.join(' ');
  $('equipment-warnings').replaceChildren(...view.warnings.map(message => {
    const row = document.createElement('li'); row.textContent = message; return row;
  }));
  filterEquipmentCatalog();
  $('equipment-list').replaceChildren(...view.items.map(item => {
    const row = document.createElement('details'), heading = document.createElement('summary');
    heading.textContent = `${item.name} × ${item.quantity} · ${item.location}${item.equipped ? ' · equipped' : ''}`;
    const source = document.createElement('p'); source.className = 'help';
    source.textContent = `${item.source.book}, pp. ${item.source.pages.join(', ')} · ${item.weight_lbs == null ? 'weight unspecified' : item.weight_lbs + ' lb each'}${item.cost_credits == null ? ' · purchase price unspecified' : ''}`;
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
  for (const armor of view.armor) {
    const row = document.createElement('p'); row.className = 'help';
    row.textContent = `${armor.name}: ${Object.entries(armor.locations).map(([location,value]) => location.replaceAll('_',' ') + ' ' + value + ' M.D.C.').join(' · ')}. Movement skill penalty: ${armor.movement_penalty}%.`;
    explanations.push(row);
  }
  $('equipment-effects').replaceChildren(...explanations);
  equipmentReady = true; setEquipmentBusy();
}
function filterEquipmentCatalog() {
  if (!equipmentView) return;
  const category = $('equipment-category').value, previous = $('equipment-choice').value;
  const entries = equipmentView.catalog.filter(item => !category || item.category === category);
  $('equipment-choice').replaceChildren(...entries.map(item => {
    const option = document.createElement('option'); option.value = item.id;
    option.textContent = `${item.name} · ${item.cost_credits == null ? 'purchase price unspecified' : item.cost_credits.toLocaleString() + ' credits'}`; return option;
  }));
  if (entries.some(item => item.id === previous)) $('equipment-choice').value = previous;
  const selected = entries.find(item => item.id === $('equipment-choice').value);
  $('equipment-price-guidance').textContent = selected?.cost_credits == null ? 'This item has no reviewed purchase price. Use its class starting grant to add it without a purchase.' : '';
  setEquipmentBusy();
}
function wireEquipmentEvents() {
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
    characterAction('purchase-equipment',{item_id:$('equipment-choice').value,quantity:Number($('equipment-quantity').value)}).catch(showError);
  };
}
