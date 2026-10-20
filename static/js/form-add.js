/* ═══════════════════════════════════════════════════════════
   FORM ADD — boutons "+ Ajouter" à côté des selects
   ============================================================
   Tout <select data-add-url="..."> reçoit un lien cliquable
   qui ouvre le formulaire cible dans un nouvel onglet, en
   transmettant l'URL de retour pour que "Annuler" ramène ici.
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
    if (select.dataset.addInitialized === '1') return;
    const widget = buildAddLink(select);
    if (!widget) return;
    select.dataset.addInitialized = '1';
    select.insertAdjacentElement('afterend', widget);
  });
};

/**
 * Sur les formulaires ouverts avec ?return=, le lien "Annuler" ramène
 * à la page d'origine au lieu d'un historique vide.
 */
const initReturnUrl = () => {
  const params = new URLSearchParams(window.location.search);
  const returnUrl = params.get('return');
  if (!returnUrl) return;

  const cancel = document.querySelector('form a.btn-outline-secondary');
  if (cancel) cancel.href = returnUrl;
};

document.addEventListener('DOMContentLoaded', () => {
  initAddButtons();
  initReturnUrl();
});