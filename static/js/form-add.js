/* ═══════════════════════════════════════════════════════════
   FORM ADD — boutons "+ Ajouter" à côté des selects
   Expose window.UNIVPILOT_addButtons() pour que la cascade
   puisse réinjecter les boutons après repeuplement.
   ═══════════════════════════════════════════════════════════ */

const buildAddLink = (select) => {
  const baseUrl = (select.dataset.addUrl || '').trim();
  const label = select.dataset.addLabel || 'Ajouter';
  if (!baseUrl) return null;

  const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);

  const wrapper = document.createElement('div');
  wrapper.className = 'up-add-hint';

  const link = document.createElement('a');
  link.className = 'btn btn-outline-brand btn-sm';
  link.href = `${baseUrl}?return=${returnUrl}`;
  link.target = '_blank';
  link.rel = 'noopener';
  link.innerHTML = `<i class="bi bi-plus-lg"></i> ${label}`;

  const hint = document.createElement('span');
  hint.textContent = 'Ouvre un nouvel onglet.';

  wrapper.appendChild(link);
  wrapper.appendChild(hint);
  return wrapper;
};

const initAddButtons = () => {
  const selects = document.querySelectorAll('select[data-add-url]');
  selects.forEach((select) => {
    // Si un wrapper existe déjà juste après, on le retire puis on remet
    const next = select.nextElementSibling;
    if (next && next.classList && next.classList.contains('up-add-hint')) {
      next.remove();
    }
    const widget = buildAddLink(select);
    if (!widget) return;
    select.insertAdjacentElement('afterend', widget);
  });
};

const initReturnUrl = () => {
  const params = new URLSearchParams(window.location.search);
  const returnUrl = params.get('return');
  if (!returnUrl) return;
  const cancel = document.querySelector('form a.btn-outline-secondary');
  if (cancel) cancel.href = returnUrl;
};

// Exposé pour que form-cascade.js puisse rappeler après repeuplement
window.UNIVPILOT_addButtons = initAddButtons;

document.addEventListener('DOMContentLoaded', () => {
  initAddButtons();
  initReturnUrl();
});
