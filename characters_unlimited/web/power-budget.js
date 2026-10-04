'use strict';
let powerBudgetReady = false, powerBudgetSequence = 0, powerBudgetView = null;

function setPowerBudgetBusy() {
  document.querySelectorAll('#power-budget-panel select, #power-budget-panel button').forEach(element => {
    element.disabled = navigationBusy || !powerBudgetReady;
  });
}

function powerBudgetLine(text) {
  const item = document.createElement('li'); item.textContent = text; return item;
}

function powerBudgetSelectionText(selection, catalog) {
  const outcome = catalog.find(entry => entry.id === selection.id);
  const roll = selection.roll == null ? '' : ` · recorded roll ${selection.roll}`;
  const faces = selection.rolls?.length ? ` · D4 faces ${selection.rolls.join(', ')}` : '';
  return `${outcome?.name || selection.id} · ${selection.method === 'roll' ? 'rolled' : 'chosen'}${roll}${faces}`;
}

async function loadPowerBudget(character) {
  const sequence = ++powerBudgetSequence;
  powerBudgetReady = false; powerBudgetView = null; setPowerBudgetBusy();
  $('power-budget-result').textContent = 'Loading power budgets…';
  $('power-budget-counts').replaceChildren(); $('power-budget-history').replaceChildren();
  if (character.game !== 'heroes-unlimited') return;
  const view = await request(`/api/characters/${character.id}/power-budget`);
  if (current.id !== character.id || sequence !== powerBudgetSequence) return;
  powerBudgetView = view;
  $('power-budget-choice').replaceChildren(...view.catalog.map(entry => {
    const option = document.createElement('option'); option.value = entry.id; option.textContent = entry.name; return option;
  }));
  if (view.selection?.id) $('power-budget-choice').value = view.selection.id;
  const selectedOutcome = view.outcome;
  $('power-budget-result').textContent = selectedOutcome
    ? powerBudgetSelectionText(view.selection, view.catalog)
    : 'No power-budget outcome selected yet.';
  $('power-budget-counts').replaceChildren(...view.budgets.map(budget =>
    powerBudgetLine(`${budget.name}: ${budget.count}`)));
  $('power-budget-history').replaceChildren(...view.history.map(selection =>
    powerBudgetLine(powerBudgetSelectionText(selection, view.catalog))));
  $('power-budget-guidance').replaceChildren(...[
    ...view.guidance,
    `${view.source.book}, printed p. ${view.source.printed_page} (PDF p. ${view.source.pdf_page}).`,
    `Rules: ${view.rules.id} ${view.rules.version}.`
  ].map(powerBudgetLine));
  powerBudgetReady = true; setPowerBudgetBusy();
}

function wirePowerBudgetEvents() {
  $('power-budget-roll').onclick = () => {
    if (!powerBudgetReady || navigationBusy) return;
    characterAction('power-budget',{method:'roll'}).catch(showError);
  };
  $('power-budget-choose').onclick = () => {
    if (!powerBudgetReady || navigationBusy) return;
    characterAction('power-budget',{method:'choose',outcome_id:$('power-budget-choice').value}).catch(showError);
  };
}
