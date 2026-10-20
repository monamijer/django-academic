/* ═══════════════════════════════════════════════════════════
   NAVBAR — comportements UI (ES6+)
   ═══════════════════════════════════════════════════════════ */

/**
 * Marque le lien de navigation correspondant à l'URL courante.
 * Priorité : data-nav-key (explicite côté Django) puis fallback path matching.
 */
const initActiveNavLink = () => {
  const links = document.querySelectorAll('.up-navbar__link');
  if (links.length === 0) return;

  const currentPath = window.location.pathname;

  links.forEach((link) => {
    link.classList.remove('is-active');
    const key = link.dataset.navKey;
    if (key && currentPath.startsWith(key)) {
      link.classList.add('is-active');
    }
  });
};

/**
 * Sur petits écrans, garde le lien actif visible dans la nav scrollable.
 */
const scrollActiveIntoView = () => {
  const active = document.querySelector('.up-navbar__link.is-active');
  if (!active) return;
  active.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
};

document.addEventListener('DOMContentLoaded', () => {
  initActiveNavLink();
  scrollActiveIntoView();
});