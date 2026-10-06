/* Small progressive enhancements; the server validates every submitted field. */
document.addEventListener('DOMContentLoaded', () => {
  const navButton = document.querySelector('.mobile-toggle');
  navButton?.addEventListener('click', () => {
    const expanded = document.getElementById('main-nav').classList.toggle('open');
    navButton.setAttribute('aria-expanded', String(expanded));
  });
  const adminButton = document.querySelector('.admin-menu');
  adminButton?.addEventListener('click', () => {
    const expanded = document.getElementById('admin-sidebar').classList.toggle('open');
    adminButton.setAttribute('aria-expanded', String(expanded));
  });
  document.addEventListener('click', (event) => {
    const sidebar = document.getElementById('admin-sidebar');
    if (sidebar?.classList.contains('open') && !sidebar.contains(event.target) && !adminButton?.contains(event.target)) {
      sidebar.classList.remove('open');
      adminButton?.setAttribute('aria-expanded', 'false');
    }
  });
  document.querySelector('.password-toggle')?.addEventListener('click', (event) => {
    const password = document.getElementById('password');
    const visible = password.type === 'password';
    password.type = visible ? 'text' : 'password';
    event.currentTarget.textContent = visible ? 'Hide' : 'Show';
    event.currentTarget.setAttribute('aria-label', visible ? 'Hide password' : 'Show password');
  });
  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
  const clearForm = document.getElementById('clear-history-form');
  const clearToggle = document.getElementById('clear-history-toggle');
  clearToggle?.addEventListener('click', () => {
    clearForm.hidden = !clearForm.hidden;
    clearToggle.setAttribute('aria-expanded', String(!clearForm.hidden));
    if (!clearForm.hidden) document.getElementById('confirmation').focus();
  });
  document.getElementById('clear-history-cancel')?.addEventListener('click', () => {
    clearForm.hidden = true;
    clearToggle.setAttribute('aria-expanded', 'false');
  });
  const form = document.getElementById('prediction-form');
  if (!form) return;
  const catalog = JSON.parse(form.dataset.catalog);
  const inputs = Object.fromEntries(['brand', 'model', 'fuel_type', 'transmission', 'year', 'engine', 'power', 'mileage', 'seats'].map((key) => [key, document.getElementById(key)]));
  const setOptions = (select, options, preferred) => {
    select.replaceChildren(...options.map((value) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      option.selected = value === preferred;
      return option;
    }));
  };
  const updatePreview = () => {
    document.getElementById('preview-car').textContent = `${inputs.brand.value} ${inputs.model.value}`;
    document.getElementById('preview-year').textContent = inputs.year.value || '—';
    document.getElementById('preview-fuel').textContent = inputs.fuel_type.value;
    document.getElementById('preview-transmission').textContent = inputs.transmission.value;
    const year = Number(inputs.year.value);
    document.getElementById('car-age').textContent = year >= 2005 && year <= Number(form.dataset.year) ? Number(form.dataset.year) - year : '—';
  };
  const updateSpecs = (fill) => {
    const spec = catalog[inputs.brand.value]?.[inputs.model.value];
    if (!spec) return;
    setOptions(inputs.fuel_type, spec.fuels, inputs.fuel_type.value);
    if (fill) {
      ['engine', 'power', 'mileage', 'seats'].forEach((key) => { inputs[key].value = spec[key]; });
      if (inputs.fuel_type.value === 'Hybrid') inputs.mileage.value = spec.mileage + 6;
      if (inputs.fuel_type.value === 'Diesel') inputs.mileage.value = spec.mileage + 2;
    }
    updatePreview();
  };
  inputs.brand.addEventListener('change', () => {
    setOptions(inputs.model, Object.keys(catalog[inputs.brand.value]), '');
    updateSpecs(true);
  });
  inputs.model.addEventListener('change', () => updateSpecs(true));
  inputs.fuel_type.addEventListener('change', () => updateSpecs(true));
  inputs.year.min = '2005';
  inputs.year.max = form.dataset.year;
  document.getElementById('kilometers_driven').max = '500000';
  inputs.engine.min = '600'; inputs.engine.max = '6500';
  inputs.power.min = '45'; inputs.power.max = '700';
  inputs.mileage.min = '5'; inputs.mileage.max = '40';
  Object.values(inputs).forEach((input) => input.addEventListener('input', updatePreview));
  const initial = Object.fromEntries(Object.entries(inputs).map(([key, input]) => [key, input.value]));
  form.addEventListener('reset', () => {
    window.setTimeout(() => {
      inputs.brand.value = initial.brand;
      setOptions(inputs.model, Object.keys(catalog[initial.brand]), initial.model);
      setOptions(inputs.fuel_type, catalog[initial.brand][initial.model].fuels, initial.fuel_type);
      Object.entries(initial).forEach(([key, value]) => { inputs[key].value = value; });
      updatePreview();
    }, 0);
  });
  form.addEventListener('submit', () => {
    const button = document.getElementById('predict-submit');
    button.disabled = true;
    button.querySelector('.button-label').hidden = true;
    button.querySelector('.button-loading').hidden = false;
    form.setAttribute('aria-busy', 'true');
  });
  window.addEventListener('pageshow', () => {
    const button = document.getElementById('predict-submit');
    button.disabled = false;
    button.querySelector('.button-label').hidden = false;
    button.querySelector('.button-loading').hidden = true;
    form.removeAttribute('aria-busy');
  });
  updateSpecs(false);
});
