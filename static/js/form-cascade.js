/* ═══════════════════════════════════════════════════════════
   FORM CASCADE — Faculté → Département
   - Recharge les départements au chargement si faculte est pré-remplie
   - Ré-applique la valeur initiale du département après repeuplement
   - Réinjecte les boutons "+ Ajouter" après repeuplement
   ═══════════════════════════════════════════════════════════ */

const API_DEPARTEMENTS = '/academique/api/departements/';

const remplirSelect = (select, items, placeholder, valeurInitiale) => {
  if (!select) return;
  select.innerHTML = '';
  const empty = document.createElement('option');
  empty.value = '';
  empty.textContent = placeholder;
  select.appendChild(empty);
  items.forEach((item) => {
    const opt = document.createElement('option');
    opt.value = item.id;
    opt.textContent = item.nom + (item.code ? ` (${item.code})` : '');
    if (valeurInitiale && String(valeurInitiale) === String(item.id)) {
      opt.selected = true;
    }
    select.appendChild(opt);
  });
};

const charger = async (url) => {
  try {
    const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!response.ok) return [];
    const data = await response.json();
    return data.results || [];
  } catch (err) {
    console.error('[cascade] fetch failed', err);
    return [];
  }
};

const refreshAddButtons = () => {
  if (typeof window.UNIVPILOT_addButtons === 'function') {
    window.UNIVPILOT_addButtons();
  }
};

const initCascade = () => {
  const faculteSelect = document.querySelector('select[data-cascade="faculte"]');
  const departementSelect = document.getElementById('id_departement');
  if (!faculteSelect || !departementSelect) return;

  // Mémorise la valeur initiale du département (utile en édition)
  const valeurDepartementInitiale =
    departementSelect.dataset.initial ||
    departementSelect.value ||
    '';

  const rechargerDepartements = async (faculteId, selectionnerId = null) => {
    if (!faculteId) {
      remplirSelect(departementSelect, [], '— Sélectionnez d\'abord une faculté —');
      refreshAddButtons();
      return;
    }
    remplirSelect(departementSelect, [], '— Chargement… —');
    const departements = await charger(`${API_DEPARTEMENTS}?faculte=${faculteId}`);
    remplirSelect(
      departementSelect,
      departements,
      departements.length
        ? '— Sélectionnez un département —'
        : '— Aucun département dans cette faculté —',
      selectionnerId
    );
    refreshAddButtons();
  };

  faculteSelect.addEventListener('change', (event) => {
    rechargerDepartements(event.target.value);
  });

  // Déclencher au chargement si faculte est déjà choisie
  if (faculteSelect.value) {
    rechargerDepartements(faculteSelect.value, valeurDepartementInitiale);
  }
};

document.addEventListener('DOMContentLoaded', initCascade);
