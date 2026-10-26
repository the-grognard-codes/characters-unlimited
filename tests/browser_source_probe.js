'use strict';
// Execute the actual renderers with minimal-source API output and a small DOM surface.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = process.argv[2];
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));

class Element {
  constructor() {
    this.children = []; this.textContent = ''; this.value = ''; this.dataset = {};
    this.classList = {add() {}, remove() {}, toggle() {}};
  }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children = [...items]; }
  addEventListener() {}
  querySelectorAll() { return []; }
  querySelector() { return new Element(); }
  setAttribute() {}
}

async function render(data) {
  const nodes = new Map();
  const context = vm.createContext({
    console, current: data.character, navigationBusy: false, skillsReady: true,
    $: id => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); },
    document: {createElement: () => new Element(), querySelectorAll: () => []},
    request: async () => data.equipment,
  });
  const app = fs.readFileSync(path.join(root, 'characters_unlimited/web/app.js'), 'utf8');
  const helpers = app.slice(app.indexOf('function modifierSourceCitation('), app.indexOf('function skillEffectEvidence('));
  vm.runInContext(helpers, context);
  for (const name of ['combat.js', 'equipment.js']) {
    vm.runInContext(fs.readFileSync(path.join(root, 'characters_unlimited/web', name), 'utf8'), context);
  }
  context.data = data;
  vm.runInContext('renderCombat(data.combat)', context);
  await vm.runInContext('loadEquipment(data.character)', context);
  function text(item) {
    return typeof item === 'string' ? item : String(item.textContent) + ' ' + item.children.map(text).join(' ');
  }
  return [...nodes.values()].map(text).join(' ');
}

(async () => {
  const control = JSON.parse(JSON.stringify(payload));
  function addPages(value) {
    if (!value || typeof value !== 'object') return;
    if (typeof value.book === 'string' && !('pages' in value)) value.pages = [1];
    for (const child of Object.values(value)) addPages(child);
  }
  addPages(control);
  await render(control); // The harness must handle an ordinary page-based rendering first.
  const result = await render(payload);
  const section = payload.combat.strength.source.section;
  if (!result.includes(section)) throw new Error('Minimum-source section is absent from actual rendered text');
  console.log('Browser source rendering passed: ' + section);
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
