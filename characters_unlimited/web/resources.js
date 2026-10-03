'use strict';
function setResourcesBusy() {
  document.querySelectorAll('#resources-panel button, #resource-form button').forEach(element => {
    element.disabled = navigationBusy || !skillsReady;
  });
}
function renderResources(view) {
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
    terms.push(...new Set(result.sources.map(source => `${source.book}, pp. ${source.pages.join(', ')}`)));
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
