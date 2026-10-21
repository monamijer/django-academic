/* ═══════════════════════════════════════════════════════════
   FORM CASCADE — Faculté → Département (filière déduite serveur)
   Réinjecte aussi les boutons "+ Ajouter" après repeuplement.
   Dépend de form-add.js qui expose window.UNIVPILOT_addButtons().
   ═══════════════════════════════════════════════════════════ */

const API_DEPARTEMENTS = '/academique/api/departements/';

const remplirSelect = (select, items, placeholder) => {
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

  faculteSelect.addEventListener('change', async (event) => {
    const faculteId = event.target.value;
    // Réinitialise immédiatement pour montrer le rechargement
    remplirSelect(departementSelect, [], '— Chargement… —');

    const departements = faculteId
      ? await charger(`${API_DEPARTEMENTS}?faculte=${faculteId}`)
      : [];
    remplirSelect(
      departementSelect,
      departements,
      departements.length
        ? '— Sélectionnez un département —'
        : '— Aucun département dans cette faculté —'
    );
    refreshAddButtons();
  });

  // Si faculte déjà pré-remplie (édition), déclencher le chargement
  if (faculteSelect.value) {
    faculteSelect.dispatchEvent(new Event('change'));
  }
};

document.addEventListener('DOMContentLoaded', initCascade);
