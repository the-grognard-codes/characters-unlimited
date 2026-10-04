'use strict';
let resourcesReady = false, resourceLoadSequence = 0;
function setResourcesBusy() {
  document.querySelectorAll('#resources-panel button, #resource-form button').forEach(element => {
    element.disabled = navigationBusy || !resourcesReady;
  });
}
function renderResources(view) {
  resourcesReady = view.supported;
  const game = current.game === 'heroes-unlimited' ? 'HEROES UNLIMITED' : 'RIFTS';
  $('resources-tag').textContent = `${game} · ${(view.path_name || 'Starting resources').toUpperCase()}`;
  $('resources-intro').textContent = current.game === 'heroes-unlimited'
    ? 'Generate after choosing attributes. Starting HP retains effective P.E. at this step. Base Mutant S.D.C. and general P.P.E. are recorded; ' + (view.power_supported ? 'reviewed Physical and Extraordinary Physical Endurance contributions apply when selected. Other skill and power contributions remain unfinished.' : view.physical_supported ? 'reviewed Physical bonuses apply when selected. Other skill and power contributions remain unfinished.' : 'additional skill and power contributions remain unfinished.')
    : 'Generate after choosing attributes. Hit Points retain your effective P.E. at this step; S.D.C. includes active Physical bonuses.';
  $('generate-resources').hidden = !view.supported || view.generated;
  $('resources-guidance').textContent = view.supported
    ? view.guidance.join(' ')
    : 'Review a rule update to add starting Hit Points and physical S.D.C.';
  $('resource-list').replaceChildren(...Object.entries(view.resources).map(([id, result]) => {
    const row = document.createElement('details'), heading = document.createElement('summary');
    heading.textContent = `${result.name}: ${result.value ?? 'not generated'}`;
    const explanation = document.createElement('p'); explanation.className = 'help';
    const terms = Object.entries(result.contributions).map(([name, value]) => {
      const faces = result.rolls[name];
      return `${name.replaceAll('-', ' ')} ${value}${faces.length ? ' (dice: ' + faces.join(' + ') + ')' : ''}`;
    });
    terms.push(...new Set(result.sources.map(source => `${source.book}, pp. ${(source.pages || [source.printed_page]).join(', ')}`)));
    if (result.fixed != null) terms.push(`Fixed total ${result.fixed}; calculated value ${result.calculated_value}.`);
    else if (result.adjustment) terms.push(`Player adjustment ${result.adjustment}.`);
    explanation.textContent = terms.join(' · ');
    row.append(heading, explanation);
    if (view.generated) {
      const edit = document.createElement('button'); edit.type = 'button'; edit.textContent = `Edit ${result.name}`;
      edit.disabled = navigationBusy;
      edit.onclick = () => {
        $('resource-title').textContent = `Edit ${result.name}`;
        $('editing-resource').value = id;
        $('resource-mode').value = result.fixed != null ? 'fixed' : 'adjustment';
        $('resource-value').value = result.fixed ?? result.adjustment;
        $('resource-value').disabled = false;
        $('resource-value').required = true;
        $('resource-error').hidden = true;
        $('resource-dialog').showModal();
      };
      row.append(edit);
    }
    return row;
  }));
  setResourcesBusy();
}
async function loadHeroResources(character) {
  const sequence = ++resourceLoadSequence;
  resourcesReady = false; setResourcesBusy();
  $('resource-list').replaceChildren();
  $('resources-guidance').textContent = 'Loading starting resources…';
  const view = await request(`/api/characters/${character.id}/resources`);
  if (current.id !== character.id || sequence !== resourceLoadSequence) return;
  renderResources(view);
}
function wireResourcesEvents() {
  $('resource-mode').onchange = () => {
    const calculated = $('resource-mode').value === 'calculated';
    $('resource-value').disabled = calculated;
    $('resource-value').required = !calculated;
  };
  $('generate-resources').onclick = () => characterAction('resources',{}).catch(showError);
  $('resource-cancel').onclick = () => $('resource-dialog').close();
  $('resource-form').onsubmit = async event => {
    event.preventDefault();
    if (navigationBusy) return;
    const mode = $('resource-mode').value;
    try {
      await characterAction('resource',{resource:$('editing-resource').value,mode,
        ...(mode === 'calculated' ? {} : {value:Number($('resource-value').value)})});
      $('resource-dialog').close();
    } catch (error) {
      $('resource-error').textContent = error.message;
      $('resource-error').hidden = false;
    }
  };
}

let advancementSupported = false;
let advancementMaximumLevel = 2;
let advancementMaximumXP = 3750;
function setAdvancementBusy() {
  document.querySelectorAll('#advancement-panel input, #advancement-panel select, #advancement-panel button').forEach(element => {
    element.disabled = navigationBusy || !(current?.game === 'heroes-unlimited' ? educationReady : skillsReady) || !advancementSupported;
  });
}
function renderAdvancement(view) {
  advancementSupported = view.supported;
  advancementMaximumLevel = view.max_level;
  advancementMaximumXP = view.max_xp;
  const dice = view.dice.map(roll => `L${roll.level}${roll.power ? " endurance power" : ""}: ${roll.face}${roll.active ? '' : ' (retained for replay)'}`).join(', ');
  $('advancement-status').textContent = `Level ${view.level} · ${view.xp} XP${dice ? ' · HP dice ' + dice : ''}`;
  $('advancement-guidance').textContent = view.guidance;
  $('undo-advancement').hidden = !view.active;
  $('advancement-method').value = 'xp';
  $('advancement-value').min = 0;
  $('advancement-value').max = advancementMaximumXP;
  $('advancement-value').value = view.xp;
  setAdvancementBusy();
}
function wireAdvancementEvents() {
  $('advancement-method').onchange = () => {
    const direct = $('advancement-method').value === 'level';
    $('advancement-value').min = direct ? 2 : 0;
    $('advancement-value').max = direct ? advancementMaximumLevel : advancementMaximumXP;
    $('advancement-value').value = direct ? Math.min(current.level + 1, advancementMaximumLevel) : current.experience ?? 0;
  };
  $('advancement-form').onsubmit = async event => {
    event.preventDefault();
    if (!advancementSupported || navigationBusy || !(current?.game === 'heroes-unlimited' ? educationReady : skillsReady)) return;
    const value = Number($('advancement-value').value);
    if (!Number.isSafeInteger(value)) return showError(new Error('Enter a whole-number XP or level'));
    await characterAction('advance', {method:$('advancement-method').value, value}).catch(showError);
  };
  $('undo-advancement').onclick = () => {
    $('undo-error').hidden = true;
    $('undo-dialog').showModal();
  };
  $('undo-cancel').onclick = () => $('undo-dialog').close();
  $('undo-confirm').onclick = async () => {
    if (navigationBusy || !current) return;
    lockNavigation(true);
    $('undo-confirm').disabled = true;
    try {
      await flushSave();
      const result = await request(`/api/characters/${current.id}/undo-advancement`, {revision:current.revision});
      characters.unshift(result.recovery);
      render(result.character);
      $('undo-dialog').close();
      $('save-status').textContent = 'Restored; later edits kept in a separate library save';
    } catch(error) {
      $('undo-error').textContent = error.message;
      $('undo-error').hidden = false;
    } finally {
      lockNavigation(false);
      $('undo-confirm').disabled = false;
    }
  };

}
