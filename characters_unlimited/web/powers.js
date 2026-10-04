'use strict';
let heroPowersReady = false, heroPowersSequence = 0, heroPowersView = null;

function setHeroPowersBusy() {
  document.querySelectorAll('#hero-powers-panel button').forEach(button => {
    button.disabled = navigationBusy || !heroPowersReady;
  });
}

function heroPowerLine(text) {
  const item = document.createElement('li'); item.textContent = text; return item;
}

function heroPowerSource(source) {
  return `${source.book}, printed p. ${source.printed_page} (PDF p. ${source.pdf_page})`;
}

function heroPowerNames(identifiers, catalog) {
  return identifiers.map(id => catalog.find(power => power.id === id)?.name || id).join(', ') || 'No powers selected';
}

async function loadHeroPowers(character) {
  const sequence = ++heroPowersSequence;
  heroPowersReady = false; heroPowersView = null; setHeroPowersBusy();
  $('hero-powers-status').textContent = 'Loading reviewed powers…';
  $('hero-powers-list').replaceChildren(); $('hero-powers-history').replaceChildren(); $('hero-powers-receipts').replaceChildren();
  $('hero-powers-warnings').replaceChildren(); $('hero-powers-guidance').replaceChildren();
  if (character.game !== 'heroes-unlimited' || character.character_class !== 'mutant') return;
  const view = await request(`/api/characters/${character.id}/hero-powers`);
  if (current.id !== character.id || sequence !== heroPowersSequence) return;
  heroPowersView = view;
  const budget = view.minor;
  $('hero-powers-status').textContent = `${budget.used} Minor selection${budget.used === 1 ? '' : 's'} used · ${budget.allowance} starting allowance · ${budget.remaining} remaining. Selections exceeding the allowance stay saved and appear as warnings.`;
  const mentalAffinity = current.attributes.MA.value;
  $('hero-powers-trust').textContent = view.trust_intimidate == null
    ? `Trust/intimidate at effective M.A. ${mentalAffinity}: no exceptional chart percentage.`
    : `Trust/intimidate at effective M.A. ${mentalAffinity}: ${view.trust_intimidate}%`;
  const selected = new Set(view.selections);
  const acquired = new Map(view.powers.map(power => [power.id, power]));
  $('hero-powers-list').replaceChildren(...view.catalog.map(definition => {
    const card = document.createElement('section');
    const heading = document.createElement('h3'); heading.textContent = `${definition.name} · ${definition.category}`;
    const details = document.createElement('p'); details.className = 'help';
    const formula = definition.attribute_floor;
    const attribute = formula.attribute === 'MA' ? 'M.A.' : formula.attribute;
    details.textContent = `${attribute} target: ${formula.constant} + ${formula.count}D${formula.sides}. ${definition.guidance.join(' ')}`;
    const source = document.createElement('p'); source.className = 'help';
    source.textContent = heroPowerSource(definition.source);
    card.append(heading, details, source);
    const acquisition = acquired.get(definition.id);
    if (acquisition) {
      const retained = document.createElement('p'); retained.className = 'help';
      retained.textContent = `Recorded D6 rolls: ${acquisition.rolls.join(', ')}. ${attribute} target floor: ${acquisition.target}; it raises calculated M.A. only when higher.`;
      card.append(retained);
    } else {
      const retained = document.createElement('p'); retained.className = 'help';
      retained.textContent = 'Removing and reselecting this power reuses its recorded dice.';
      card.append(retained);
    }
    const toggle = document.createElement('button'); toggle.type = 'button';
    toggle.textContent = selected.has(definition.id) ? 'Remove power' : 'Add power';
    toggle.onclick = () => {
      if (navigationBusy || !heroPowersReady) return;
      const selections = selected.has(definition.id)
        ? view.selections.filter(id => id !== definition.id)
        : [...view.selections, definition.id];
      characterAction('hero-powers',{selections}).catch(showError);
    };
    card.append(toggle);
    return card;
  }));
  $('hero-powers-warnings').replaceChildren(...view.warnings.map(heroPowerLine));
  const receipts = view.receipts || [];
  $('hero-powers-receipts').replaceChildren(...(receipts.length ? receipts.map(receipt => {
    const formula = receipt.attribute_floor;
    const attribute = formula.attribute === 'MA' ? 'M.A.' : formula.attribute;
    return heroPowerLine(`${receipt.name} · ${receipt.active ? 'active' : 'inactive'} · ${attribute} target floor ${receipt.target} · recorded D6 rolls ${receipt.rolls.join(', ')} · ${heroPowerSource(receipt.source)}`);
  }) : [heroPowerLine('No power acquisitions recorded.') ]));
  $('hero-powers-history').replaceChildren(...view.history.map((entry, index) =>
    heroPowerLine(`${index + 1}. ${heroPowerNames(entry.selections, view.catalog)}`)));
  $('hero-powers-guidance').replaceChildren(...[
    ...view.guidance,
    `Trust/intimidate chart: ${heroPowerSource(view.trust_source)}.`,
    `Power rules: ${view.rules.id} ${view.rules.version}.`,
    `Power source: ${heroPowerSource(view.source)}.`
  ].map(heroPowerLine));
  heroPowersReady = true; setHeroPowersBusy();
}
