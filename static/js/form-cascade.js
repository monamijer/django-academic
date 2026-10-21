/* ═══════════════════════════════════════════════════════════
   FORM CASCADE — remplissage en cascade Faculté → Département → Filière
   Tout <select data-cascade="X" data-target="id_Y"> déclenche un fetch
   sur une URL fournie par data-source, puis repeuple #id_Y.
   ═══════════════════════════════════════════════════════════ */

const API_DEPARTEMENTS = '/academique/api/departements/';
const API_FILIERES = '/academique/api/filieres/';

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

const initCascade = () => {
  const faculteSelect = document.querySelector('select[data-cascade="faculte"]');
  const departementSelect = document.querySelector('select[data-cascade="departement"]');
  const filiereSelect = document.getElementById('id_filiere');

  if (!faculteSelect) return;

  faculteSelect.addEventListener('change', async (e) => {
    const faculteId = e.target.value;
    const departements = faculteId
      ? await charger(`${API_DEPARTEMENTS}?faculte=${faculteId}`)
      : [];
    remplirSelect(departementSelect, departements, '— Sélectionnez un département —');
    remplirSelect(filiereSelect, [], '— Sélectionnez une filière —');
  });

  departementSelect.addEventListener('change', async (e) => {
    const departementId = e.target.value;
    const filieres = departementId
      ? await charger(`${API_FILIERES}?departement=${departementId}`)
      : [];
    remplirSelect(filiereSelect, filieres, '— Sélectionnez une filière —');
  });

  // Au chargement : si faculte est déjà choisie (édition), charger les départements
  if (faculteSelect.value) {
    faculteSelect.dispatchEvent(new Event('change'));
  }
};

document.addEventListener('DOMContentLoaded', initCascade);