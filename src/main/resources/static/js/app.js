// js/app.js
// Vanilla JS, no build step — fetch() against the same-origin Spring Boot API.

const API = "/api";

const IMAGE_PLACEHOLDER =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='300'%3E" +
  "%3Crect width='200' height='300' fill='%23ddd'/%3E" +
  "%3Ctext x='50%25' y='50%25' font-size='16' fill='%23888' text-anchor='middle' dy='.3em'%3EPas d'image%3C/text%3E" +
  "%3C/svg%3E";

// --- Auth / session storage ---

function getToken() { return localStorage.getItem("token"); }
function getUtilisateurId() { return localStorage.getItem("utilisateurId"); }
function getPseudo() { return localStorage.getItem("pseudo"); }

function setSession(token, utilisateurId, pseudo, role, statut) {
  localStorage.setItem("token", token);
  localStorage.setItem("utilisateurId", utilisateurId);
  localStorage.setItem("pseudo", pseudo);
  localStorage.setItem("role", role);
  localStorage.setItem("statut", statut);
}

function getRole() { return localStorage.getItem("role"); }
function getStatut() { return localStorage.getItem("statut"); }

function deconnexion() {
  localStorage.removeItem("token");
  localStorage.removeItem("utilisateurId");
  localStorage.removeItem("pseudo");
  localStorage.removeItem("role");
  localStorage.removeItem("statut");
  location.reload();
}

// --- Auth tabs ---

document.querySelectorAll(".auth-tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    // 1. Désactive tous les onglets
    document.querySelectorAll(".auth-tab").forEach((b) => {
      b.classList.remove("active");
      b.setAttribute("aria-selected", "false");
    });
    // 2. Cache tous les panels (via classe + attribut, ceinture + bretelles)
    document.querySelectorAll(".auth-panel").forEach((p) => {
      p.classList.remove("active");
      p.setAttribute("hidden", "");
    });
    // 3. Active le bon
    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    const panel = document.getElementById(`form-${btn.dataset.auth}`);
    panel.classList.add("active");
    panel.removeAttribute("hidden");
    // 4. Reset du message d'erreur
    document.getElementById("login-erreur").textContent = "";
  });
});

// --- Generic API wrapper ---

async function appelApi(url, options = {}) {
  const token = getToken();
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const reponse = await fetch(url, { headers, ...options });

  if (reponse.status === 401 || reponse.status === 403) {
    if (!url.includes("/auth/")) deconnexion();
    throw new Error("Non authentifié");
  }

  if (!reponse.ok) {
    const erreur = await reponse.json().catch(() => ({ message: reponse.statusText }));
    throw new Error(erreur.message || "Erreur API");
  }
  return reponse.status === 204 ? null : reponse.json();
}

function creerElement(html) {
  const conteneur = document.createElement("div");
  conteneur.innerHTML = html.trim();
  return conteneur.firstElementChild;
}

function attacherPlaceholder(img) {
  if (!img) return;
  img.addEventListener("error", () => { img.src = IMAGE_PLACEHOLDER; }, { once: true });
}

function messageVide(texte) {
  return `<p class="aucun-resultat" role="status">${texte}</p>`;
}
function messageChargement(texte = "Chargement...") {
  return `<p class="chargement" role="status">${texte}</p>`;
}
function messageErreur(texte) {
  return `<p class="erreur-api" role="alert">Erreur : ${texte}</p>`;
}

// --- Login / Inscription ---

function afficherLogin() {
  document.getElementById("app").classList.add("hidden");
  document.getElementById("login").classList.remove("hidden");
}

function afficherApp(pseudo) {
  document.getElementById("login").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
  if (pseudo) document.getElementById("nom-utilisateur").textContent = `👤 ${pseudo}`;
  afficherOngletAdminSiBesoin();
  chargerMesSeries();
  chargerGenres();
}

document.getElementById("form-connexion").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const motDePasse = document.getElementById("login-motdepasse").value;
  try {
    const data = await appelApi(`${API}/auth/connexion`, {
      method: "POST",
      body: JSON.stringify({ email, motDePasse }),
    });
    setSession(data.token, data.utilisateurId, data.pseudo, data.role, data.statut);
    afficherApp(data.pseudo);
  } catch (err) {
    document.getElementById("login-erreur").textContent = "Identifiants invalides";
  }
});

document.getElementById("form-inscription").addEventListener("submit", async (e) => {
  e.preventDefault();
  const pseudo = document.getElementById("inscription-pseudo").value;
  const email = document.getElementById("inscription-email").value;
  const motDePasse = document.getElementById("inscription-motdepasse").value;
  const confirmation = document.getElementById("inscription-motdepasse-confirmation").value;

  const erreurEl = document.getElementById("login-erreur");
  const succesEl = document.getElementById("login-succes");
  erreurEl.textContent = "";
  succesEl.classList.add("hidden");
  succesEl.textContent = "";

  // Vérification côté client
  if (motDePasse !== confirmation) {
    erreurEl.textContent = "Les mots de passe ne correspondent pas.";
    return;
  }
  if (motDePasse.length < 8) {
    erreurEl.textContent = "Le mot de passe doit contenir au moins 8 caractères.";
    return;
  }

  try {
    const data = await appelApi(`${API}/auth/inscription`, {
      method: "POST",
      body: JSON.stringify({ pseudo, email, motDePasse }),
    });

    // Le backend renvoie token=null + statut=EN_ATTENTE
    // → on affiche le message d'attente et on NE connecte PAS
    succesEl.textContent = data.message || "Compte créé. En attente d'approbation par un administrateur.";
    succesEl.classList.remove("hidden");

    // Reset du formulaire
    e.target.reset();

    // Bascule automatiquement sur Connexion après 3 secondes
    setTimeout(() => {
      document.getElementById("tab-connexion").click();
    }, 3000);

  } catch (err) {
    erreurEl.textContent = err.message;
  }
});

document.getElementById("btn-deconnexion")?.addEventListener("click", deconnexion);

// --- Main tabs ---

let ongletDecouvrirCharge = false;

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.remove("active");
      b.setAttribute("aria-selected", "false");
    });
    document.querySelectorAll(".tab-panel").forEach((p) => {
      p.classList.remove("active");
      p.setAttribute("hidden", "");
    });
    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    const panneau = document.getElementById(btn.dataset.tab);
    panneau.classList.add("active");
    panneau.removeAttribute("hidden");

    if (btn.dataset.tab === "decouvrir" && !ongletDecouvrirCharge) {
      ongletDecouvrirCharge = true;
      chargerCategorieTmdb("populaires", document.querySelector(".souscat-btn[data-cat='populaires']"));
    }
        if (btn.dataset.tab === "admin") {
      chargerStatsAdmin();
      chargerListeAdmin();
    }
  });
});

// --- My series ---

let seriesEnMemoire = [];

async function chargerMesSeries() {
  const conteneur = document.getElementById("liste-series");
  conteneur.innerHTML = messageChargement();

  let series;
  try {
    series = await appelApi(`${API}/utilisateurs/${getUtilisateurId()}/series`);
  } catch (err) {
    conteneur.innerHTML = messageErreur(err.message);
    return;
  }

  if (!Array.isArray(series) || series.length === 0) {
    conteneur.innerHTML = messageVide(
      "Aucune série dans votre liste pour l'instant. Ajoutez-en une ci-dessus ou explorez l'onglet Découvrir."
    );
    seriesEnMemoire = [];
    return;
  }

  seriesEnMemoire = [];
  for (const serie of series) {
    let progression = null;
    try {
      progression = await appelApi(`${API}/utilisateurs/${getUtilisateurId()}/progression/${serie.id}`);
      // Si la réponse est neutre (0 épisodes), on n'affiche pas de barre
      if (!progression || progression.episodesTotal === 0) progression = null;
    } catch { /* pas de progression → pas grave */ }
    seriesEnMemoire.push({ serie, progression });
  }

  rendreMesSeries();
}

function trierEtFiltrerSeries() {
  const tri = document.getElementById("select-tri").value;
  const filtreGenre = document.getElementById("input-filtre-genre").value.trim().toLowerCase();

  let liste = [...seriesEnMemoire];
  if (filtreGenre) {
    liste = liste.filter((item) => (item.serie.genre || "").toLowerCase().includes(filtreGenre));
  }

  const comparateurs = {
    "titre-asc": (a, b) => a.serie.titre.localeCompare(b.serie.titre),
    "titre-desc": (a, b) => b.serie.titre.localeCompare(a.serie.titre),
    "annee-desc": (a, b) => (b.serie.anneeSortie || 0) - (a.serie.anneeSortie || 0),
    "annee-asc": (a, b) => (a.serie.anneeSortie || 0) - (b.serie.anneeSortie || 0),
    "note-desc": (a, b) => (b.serie.note || 0) - (a.serie.note || 0),
    "progression-desc": (a, b) => (b.progression?.pourcentage || 0) - (a.progression?.pourcentage || 0),
  };
  liste.sort(comparateurs[tri] || comparateurs["titre-asc"]);
  return liste;
}

function rendreMesSeries() {
  const conteneur = document.getElementById("liste-series");
  const liste = trierEtFiltrerSeries();

  if (liste.length === 0) {
    conteneur.innerHTML = messageVide("Aucune série ne correspond à ce filtre.");
    return;
  }

  conteneur.innerHTML = "";
  for (const { serie, progression } of liste) {
    const carte = creerElement(`
      <div class="serie-card" data-id="${serie.id}">
        <img src="${serie.imageUrl || IMAGE_PLACEHOLDER}" alt="Affiche de ${serie.titre}">
        <div class="contenu">
          <h3>${serie.titre}</h3>
          <span class="meta">${serie.genre || ''} ${serie.anneeSortie ? '· ' + serie.anneeSortie : ''}</span>
          ${progression ? `
            <div class="barre-progression">
              <div class="remplissage" style="width:${progression.pourcentage}%"></div>
            </div>
            <span class="meta">${progression.episodesVus}/${progression.episodesTotal} épisodes</span>
          ` : ''}
          <div class="actions-carte">
            <button class="btn-editer" data-id="${serie.id}" data-action="editer">Éditer</button>
            <button class="btn-supprimer" data-id="${serie.id}" data-action="supprimer">Supprimer</button>
          </div>
        </div>
      </div>
    `);

    attacherPlaceholder(carte.querySelector("img"));

    carte.querySelector('[data-action="supprimer"]').addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm(`Supprimer "${serie.titre}" ?`)) return;
      try {
        await appelApi(`${API}/utilisateurs/${getUtilisateurId()}/series/${serie.id}`, { method: "DELETE" });
        chargerMesSeries();
      } catch (err) { alert(err.message); }
    });

    carte.querySelector('[data-action="editer"]').addEventListener("click", (e) => {
      e.stopPropagation();
      ouvrirEditionSerie(serie);
    });

    carte.addEventListener("click", () => ouvrirDetailSerie(serie));
    conteneur.appendChild(carte);
  }
}

document.getElementById("select-tri").addEventListener("change", rendreMesSeries);
document.getElementById("input-filtre-genre").addEventListener("input", rendreMesSeries);

document.getElementById("form-ajout-serie").addEventListener("submit", async (e) => {
  e.preventDefault();
  const titre = document.getElementById("input-titre").value;
  const genre = document.getElementById("input-genre").value;
  try {
    await appelApi(`${API}/utilisateurs/${getUtilisateurId()}/series`, {
      method: "POST",
      body: JSON.stringify({ titre, genre }),
    });
    e.target.reset();
    chargerMesSeries();
  } catch (err) { alert(err.message); }
});

// --- Edition modal ---

function ouvrirEditionSerie(serie) {
  const contenu = document.getElementById("detail-contenu");
  contenu.innerHTML = `
    <h2 id="titre-detail">Éditer « ${serie.titre} »</h2>
    <form id="form-edition-serie" class="form-inline">
      <label for="edit-titre" class="sr-only">Titre</label>
      <input id="edit-titre" type="text" value="${serie.titre || ''}" required>

      <label for="edit-genre" class="sr-only">Genre</label>
      <input id="edit-genre" type="text" value="${serie.genre || ''}" placeholder="Genre">

      <label for="edit-annee" class="sr-only">Année</label>
      <input id="edit-annee" type="number" value="${serie.anneeSortie || ''}" placeholder="Année" min="1900" max="2100">

      <label for="edit-note" class="sr-only">Note</label>
      <input id="edit-note" type="number" value="${serie.note ?? ''}" placeholder="Note" min="0" max="10" step="0.1">

      <label for="edit-image" class="sr-only">URL de l'image</label>
      <input id="edit-image" type="url" value="${serie.imageUrl || ''}" placeholder="URL de l'affiche">

      <button type="submit">Enregistrer</button>
    </form>
  `;
  ouvrirModale();

  document.getElementById("form-edition-serie").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      titre: document.getElementById("edit-titre").value,
      genre: document.getElementById("edit-genre").value || null,
      anneeSortie: document.getElementById("edit-annee").value || null,
      note: document.getElementById("edit-note").value || null,
      imageUrl: document.getElementById("edit-image").value || null,
    };
    try {
      await appelApi(`${API}/utilisateurs/${getUtilisateurId()}/series/${serie.id}`, {
        method: "PUT",
        body: JSON.stringify(body),
      });
      fermerModale();
      chargerMesSeries();
    } catch (err) { alert(err.message); }
  });
}

// --- Detail panel (accessible modal) ---

let elementDeclencheur = null;

function ouvrirModale() {
  const panneau = document.getElementById("panneau-detail");
  elementDeclencheur = document.activeElement;
  panneau.classList.remove("hidden");
  panneau.removeAttribute("inert");
  document.body.style.overflow = "hidden";
  const premierFocusable = panneau.querySelector("button, [href], input, select, textarea, [tabindex]");
  premierFocusable?.focus();
  document.addEventListener("keydown", gererClavierModale);
}

function fermerModale() {
  const panneau = document.getElementById("panneau-detail");
  panneau.classList.add("hidden");
  panneau.setAttribute("inert", "");
  document.body.style.overflow = "";
  document.removeEventListener("keydown", gererClavierModale);
  elementDeclencheur?.focus();
}

function gererClavierModale(e) {
  const panneau = document.getElementById("panneau-detail");
  if (e.key === "Escape") { fermerModale(); return; }
  if (e.key === "Tab") {
    const focusables = panneau.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusables.length === 0) return;
    const premier = focusables[0];
    const dernier = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === premier) { e.preventDefault(); dernier.focus(); }
    else if (!e.shiftKey && document.activeElement === dernier) { e.preventDefault(); premier.focus(); }
  }
}

document.getElementById("panneau-detail").addEventListener("click", (e) => {
  if (e.target.id === "panneau-detail") fermerModale();
});

async function chargerFournisseurs(serie, tmdbId) {
  const conteneur = document.getElementById("fournisseurs-detail");
  if (!conteneur) return;

  // Si la série n'a pas de tmdbId (créée manuellement), on affiche un message
  if (!tmdbId) {
    conteneur.innerHTML = messageVide(
      "Aucune plateforme connue pour cette série (ajoutée manuellement)."
    );
    return;
  }

  conteneur.innerHTML = messageChargement("Recherche des plateformes...");

  let parPays;
  try {
    parPays = await appelApi(`${API}/tmdb/serie/${tmdbId}/fournisseurs`);
  } catch (err) {
    conteneur.innerHTML = messageErreur(err.message);
    return;
  }

  // Priorité au pays FR, sinon premier pays dispo
  const pays = parPays.FR ? "FR" : Object.keys(parPays)[0];
  const fournisseurs = pays ? parPays[pays] : null;

  if (!fournisseurs || fournisseurs.length === 0) {
    conteneur.innerHTML = messageVide(
      "Aucune plateforme de streaming référencée pour cette série."
    );
    return;
  }

  const libelles = { FLATRATE: "Abonnement", RENT: "Location", BUY: "Achat" };

  conteneur.innerHTML = `
    <div class="fournisseurs-liste">
      ${fournisseurs.map((f) => `
        <a class="fournisseur" href="${f.lien}" target="_blank" rel="noopener noreferrer"
           title="${f.nom} — ${libelles[f.type] || f.type}">
          ${f.logoUrl
            ? `<img src="${f.logoUrl}" alt="${f.nom}">`
            : `<span class="fournisseur-nom">${f.nom}</span>`}
          <span class="fournisseur-type">${libelles[f.type] || f.type}</span>
        </a>
      `).join("")}
    </div>
    <p class="fournisseurs-source">Données TMDB · <a href="https://www.themoviedb.org" target="_blank" rel="noopener">themoviedb.org</a></p>
  `;
}

async function ouvrirDetailSerie(serie) {
  const contenu = document.getElementById("detail-contenu");
  contenu.innerHTML = `<h2 id="titre-detail">${serie.titre}</h2>` + messageChargement();
  ouvrirModale();

  let saisons;
  try {
    saisons = await appelApi(`${API}/utilisateurs/${getUtilisateurId()}/series/${serie.id}/saisons`);
  } catch (err) {
    contenu.innerHTML = `<h2 id="titre-detail">${serie.titre}</h2>` + messageErreur(err.message);
    return;
  }

  if (!Array.isArray(saisons) || saisons.length === 0) {
    contenu.innerHTML = `<h2 id="titre-detail">${serie.titre}</h2>`
      + messageVide("Aucune saison enregistrée pour cette série.");
    return;
  }

    let html = `<h2 id="titre-detail">${serie.titre}</h2>
    <section class="bloc-fournisseurs">
      <h3>Où regarder ?</h3>
      <div id="fournisseurs-detail" aria-live="polite"></div>
    </section>`;
  for (const saison of saisons) {
    let episodes = [];
    try {
      episodes = await appelApi(`${API}/saisons/${saison.id}/episodes`);
    } catch { /* leave empty */ }

    html += `<h3>Saison ${saison.numero}</h3>`;
    if (!Array.isArray(episodes) || episodes.length === 0) {
      html += messageVide("Aucun épisode enregistré pour cette saison.");
      continue;
    }
    for (const ep of episodes) {
      html += `
        <div class="episode-ligne" data-episode-id="${ep.id}">
          <span>Épisode ${ep.numero} — ${ep.titre || ''}</span>
          <input type="checkbox" class="check-vu" data-episode-id="${ep.id}" id="ep-${ep.id}">
          <label for="ep-${ep.id}" class="sr-only">Marquer l'épisode ${ep.numero} comme vu</label>
        </div>
      `;
    }
  }
  contenu.innerHTML = html;

   chargerFournisseurs(serie, serie.tmdbId);
   
  contenu.querySelectorAll(".check-vu").forEach((checkbox) => {
    checkbox.addEventListener("change", async (e) => {
      const episodeId = e.target.dataset.episodeId;
      const ligne = e.target.closest(".episode-ligne");
      try {
        if (e.target.checked) {
          await appelApi(`${API}/utilisateurs/${getUtilisateurId()}/visionnages/${episodeId}`, { method: "POST" });
          ligne.classList.add("vu");
        } else {
          await appelApi(`${API}/utilisateurs/${getUtilisateurId()}/visionnages/${episodeId}`, { method: "DELETE" });
          ligne.classList.remove("vu");
        }
      } catch (err) {
        alert(err.message);
        e.target.checked = !e.target.checked;
      }
    });
  });
}

document.getElementById("btn-fermer-panneau").addEventListener("click", () => {
  fermerModale();
  chargerMesSeries();
});

// --- TMDB discovery (avec pagination) ---

let requeteTmdbCourante = null;

function afficherPagination(page, totalPages) {
  const nav = document.getElementById("pagination-tmdb");
  if (!totalPages || totalPages <= 1) {
    nav.classList.add("hidden");
    return;
  }
  nav.classList.remove("hidden");
  document.getElementById("info-page").textContent = `Page ${page} / ${totalPages}`;
  document.getElementById("btn-page-prec").disabled = page <= 1;
  document.getElementById("btn-page-suiv").disabled = page >= totalPages;
}

function cacherPagination() {
  document.getElementById("pagination-tmdb").classList.add("hidden");
}

function afficherResultatsTmdb(series, conteneurId = "resultats-tmdb", options = {}) {
  const conteneur = document.getElementById(conteneurId);
  const { avecImport = true } = options;

  if (!Array.isArray(series) || series.length === 0) {
    conteneur.innerHTML = messageVide("Aucun résultat pour cette recherche.");
    return;
  }

  conteneur.innerHTML = "";
  for (const serie of series) {
    const boutonImport = avecImport
      ? `<button class="btn-importer" data-tmdb-id="${serie.tmdbId}">Importer</button>`
      : "";
    const carte = creerElement(`
      <div class="serie-card">
        <img src="${serie.imageUrl || IMAGE_PLACEHOLDER}" alt="Affiche de ${serie.titre}">
        <div class="contenu">
          <h3>${serie.titre}</h3>
          <span class="meta">${serie.dateDiffusion || 'Date inconnue'} · ⭐ ${serie.note?.toFixed(1) || '?'}</span>
          ${boutonImport}
        </div>
      </div>
    `);
    attacherPlaceholder(carte.querySelector("img"));

    if (avecImport) {
      carte.querySelector(".btn-importer").addEventListener("click", async (e) => {
        e.stopPropagation();
        const btn = e.target;
        btn.disabled = true;
        btn.textContent = "Import...";
        try {
          await appelApi(`${API}/utilisateurs/${getUtilisateurId()}/tmdb/importer/${serie.tmdbId}`, { method: "POST" });
          btn.textContent = "Importé ✓";
        } catch (err) {
          alert(err.message);
          btn.disabled = false;
          btn.textContent = "Importer";
        }
      });
    }

    conteneur.appendChild(carte);
  }
}

function construireUrlTmdb(requete, page) {
  const p = new URLSearchParams(requete.params || {});
  p.set("page", page);

  switch (requete.type) {
    case "categorie": return `${API}/tmdb/${requete.categorie}?${p.toString()}`;
    case "recherche": return `${API}/tmdb/recherche?${p.toString()}`;
    case "decouvrir": return `${API}/tmdb/decouvrir?${p.toString()}`;
  }
  return null;
}

async function chargerTmdb(url, requete) {
  const conteneur = document.getElementById("resultats-tmdb");
  conteneur.innerHTML = messageChargement();
  cacherPagination();

  let reponse;
  try {
    reponse = await appelApi(url);
  } catch (err) {
    conteneur.innerHTML = messageErreur(err.message);
    return;
  }

  // Backend renvoie un tableau simple : pas de pagination
  if (Array.isArray(reponse)) {
    afficherResultatsTmdb(reponse);
    return;
  }

  // Backend renvoie un objet paginé : { resultats, page, totalPages, totalResultats }
  requeteTmdbCourante = { ...requete, page: reponse.page };
  afficherResultatsTmdb(reponse.resultats);
  afficherPagination(reponse.page, reponse.totalPages);
}

const ROUTES_TMDB = {
  populaires: "populaires",
  tendances: "tendances",
  "mieux-notees": "mieux-notees",
  "diffusees-bientot": "diffusees-bientot",
};

async function chargerCategorieTmdb(cat, bouton) {
  document.querySelectorAll(".souscat-btn").forEach((b) => b.classList.remove("active"));
  bouton?.classList.add("active");

  const requete = { type: "categorie", categorie: cat, params: {}, page: 1 };
  await chargerTmdb(construireUrlTmdb(requete, 1), requete);
}

document.querySelectorAll(".souscat-btn").forEach((btn) => {
  btn.addEventListener("click", () => chargerCategorieTmdb(btn.dataset.cat, btn));
});

document.getElementById("form-recherche-tmdb").addEventListener("submit", async (e) => {
  e.preventDefault();
  const titre = document.getElementById("input-recherche").value;
  if (!titre) return;

  const requete = { type: "recherche", params: { titre }, page: 1 };
  await chargerTmdb(construireUrlTmdb(requete, 1), requete);
});

document.getElementById("form-decouvrir").addEventListener("submit", async (e) => {
  e.preventDefault();
  const genre = document.getElementById("select-genre").value;
  const annee = document.getElementById("input-annee").value;
  const noteMin = document.getElementById("input-note-min").value;

  const params = {};
  if (genre) params.genre = genre;
  if (annee) params.annee = annee;
  if (noteMin) params.noteMin = noteMin;

  const requete = { type: "decouvrir", params, page: 1 };
  await chargerTmdb(construireUrlTmdb(requete, 1), requete);
});

document.getElementById("btn-page-prec").addEventListener("click", () => {
  if (!requeteTmdbCourante || requeteTmdbCourante.page <= 1) return;
  const page = requeteTmdbCourante.page - 1;
  chargerTmdb(construireUrlTmdb(requeteTmdbCourante, page), requeteTmdbCourante);
});

document.getElementById("btn-page-suiv").addEventListener("click", () => {
  if (!requeteTmdbCourante) return;
  const page = requeteTmdbCourante.page + 1;
  chargerTmdb(construireUrlTmdb(requeteTmdbCourante, page), requeteTmdbCourante);
});

// --- Genres ---

async function chargerGenres() {
  const select = document.getElementById("select-genre");
  select.innerHTML = '<option value="">Tous les genres</option>';

  try {
    const genres = await appelApi(`${API}/tmdb/genres`);
    if (!Array.isArray(genres)) return;
    for (const genre of genres) {
      const option = document.createElement("option");
      option.value = genre.id;
      option.textContent = genre.nom;
      select.appendChild(option);
    }
  } catch { /* TMDB unreachable */ }
}

// --- Actor search + filmography ---

let acteursEnMemoire = [];

document.getElementById("form-recherche-acteur").addEventListener("submit", async (e) => {
  e.preventDefault();
  const nom = document.getElementById("input-acteur").value;
  if (!nom) return;

  const conteneur = document.getElementById("resultats-acteurs");
  conteneur.innerHTML = messageChargement();

  let acteurs;
  try {
    acteurs = await appelApi(`${API}/tmdb/recherche-acteur?nom=${encodeURIComponent(nom)}`);
  } catch (err) {
    conteneur.innerHTML = messageErreur(err.message);
    return;
  }

  acteursEnMemoire = Array.isArray(acteurs) ? acteurs : [];

  if (acteursEnMemoire.length === 0) {
    conteneur.innerHTML = messageVide("Aucun acteur trouvé pour cette recherche.");
    return;
  }

  rendreActeurs();
});

function rendreActeurs() {
  const conteneur = document.getElementById("resultats-acteurs");
  conteneur.classList.add("grid");
  conteneur.innerHTML = "";

  for (const acteur of acteursEnMemoire) {
    const carte = creerElement(`
      <div class="serie-card acteur-card" data-acteur-id="${acteur.id}">
        <img src="${acteur.photoUrl || IMAGE_PLACEHOLDER}" alt="Photo de ${acteur.nom}">
        <div class="contenu"><h3>${acteur.nom}</h3></div>
      </div>
    `);
    attacherPlaceholder(carte.querySelector("img"));
    carte.addEventListener("click", () => afficherFilmographie(acteur));
    conteneur.appendChild(carte);
  }
}

async function afficherFilmographie(acteur) {
  const conteneur = document.getElementById("resultats-acteurs");
  conteneur.innerHTML = messageChargement(`Chargement de la filmographie de ${acteur.nom}...`);

  let series;
  try {
    series = await appelApi(`${API}/tmdb/acteur/${acteur.id}/series`);
  } catch (err) {
    conteneur.innerHTML = messageErreur(err.message);
    return;
  }

  conteneur.classList.remove("grid");
  conteneur.innerHTML = `
    <button type="button" class="btn-retour" id="btn-retour-acteurs">← Retour aux acteurs</button>
    <h3 class="titre-section">Séries avec ${acteur.nom}</h3>
    <div class="grid" id="resultats-filmographie"></div>
  `;
  document.getElementById("btn-retour-acteurs").addEventListener("click", () => {
    conteneur.classList.add("grid");
    rendreActeurs();
  });

  afficherResultatsTmdb(series, "resultats-filmographie", { avecImport: true });
}

// --- ADMIN ---

function afficherOngletAdminSiBesoin() {
  const badge = document.getElementById("badge-role");
  const ongletAdmin = document.getElementById("onglet-admin");
  if (getRole() === "ADMIN") {
    badge.textContent = "ADMIN";
    badge.classList.add("badge-admin");
    ongletAdmin.classList.remove("hidden");
  } else {
    badge.textContent = "";
    badge.classList.remove("badge-admin");
    ongletAdmin.classList.add("hidden");
  }
}

async function chargerStatsAdmin() {
  const conteneur = document.getElementById("admin-stats");
  conteneur.innerHTML = messageChargement();
  try {
    const s = await appelApi(`${API}/admin/utilisateurs/statistiques`);
    conteneur.innerHTML = `
      <div class="stat-card"><span class="stat-valeur">${s.totalUtilisateurs}</span><span class="stat-label">Total</span></div>
      <div class="stat-card stat-attente"><span class="stat-valeur">${s.enAttente}</span><span class="stat-label">En attente</span></div>
      <div class="stat-card stat-approuve"><span class="stat-valeur">${s.approuves}</span><span class="stat-label">Approuvés</span></div>
      <div class="stat-card stat-refuse"><span class="stat-valeur">${s.refuses}</span><span class="stat-label">Refusés</span></div>
      <div class="stat-card stat-admin"><span class="stat-valeur">${s.admins}</span><span class="stat-label">Admins</span></div>
    `;
  } catch (err) {
    conteneur.innerHTML = messageErreur(err.message);
  }
}

async function chargerListeAdmin() {
  const conteneur = document.getElementById("admin-liste");
  const statut = document.getElementById("select-statut-admin").value;
  conteneur.innerHTML = messageChargement();

  const url = statut
    ? `${API}/admin/utilisateurs?statut=${statut}`
    : `${API}/admin/utilisateurs`;

  let utilisateurs;
  try {
    utilisateurs = await appelApi(url);
  } catch (err) {
    conteneur.innerHTML = messageErreur(err.message);
    return;
  }

  if (!Array.isArray(utilisateurs) || utilisateurs.length === 0) {
    conteneur.innerHTML = messageVide("Aucun utilisateur à afficher.");
    return;
  }

  const libellesStatut = { EN_ATTENTE: "En attente", APPROUVE: "Approuvé", REFUSE: "Refusé" };

  conteneur.innerHTML = "";
  for (const u of utilisateurs) {
    const carte = creerElement(`
      <div class="admin-carte">
        <div class="admin-info">
          <h3>${u.pseudo} <span class="badge-role-inline badge-${u.role.toLowerCase()}">${u.role}</span></h3>
          <p class="meta">${u.email}</p>
          <p class="meta">Statut : <strong class="statut-${u.statut.toLowerCase()}">${libellesStatut[u.statut] || u.statut}</strong></p>
          <p class="meta">Inscrit le : ${u.dateInscription ? new Date(u.dateInscription).toLocaleDateString("fr-FR") : "—"}</p>
        </div>
               ${(() => {
          const dernierAdmin = u.role === "ADMIN" && utilisateurs.filter(x => x.role === "ADMIN" && x.statut === "APPROUVE").length <= 1;
          return `
          <div class="admin-actions">
            ${u.statut !== "APPROUVE" ? `<button class="btn-approuver" data-id="${u.id}" data-action="approuver">Approuver</button>` : ""}
            ${u.statut !== "REFUSE" ? `<button class="btn-refuser" data-id="${u.id}" data-action="refuser" ${dernierAdmin ? "disabled" : ""}>Refuser</button>` : ""}
            ${u.role !== "ADMIN" ? `<button class="btn-promouvoir" data-id="${u.id}" data-action="promouvoir">Promouvoir</button>` : ""}
            ${u.role === "ADMIN" ? `<button class="btn-retrograder" data-id="${u.id}" data-action="retrograder" ${dernierAdmin ? "disabled" : ""}>Rétrograder</button>` : ""}
            <button class="btn-motdepasse" data-id="${u.id}" data-action="motdepasse">Changer MDP</button>
            <button class="btn-supprimer" data-id="${u.id}" data-action="supprimer" ${dernierAdmin ? "disabled" : ""}>Supprimer</button>
          </div>
          `;
        })()}
      </div>
    `);

    carte.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => actionAdmin(btn.dataset.action, u));
    });

    conteneur.appendChild(carte);
  }
}

async function actionAdmin(action, u) {
  try {
    switch (action) {
      case "approuver":
        await appelApi(`${API}/admin/utilisateurs/${u.id}/approuver`, { method: "PATCH" });
        break;
      case "refuser":
        if (!confirm(`Refuser le compte de ${u.pseudo} ?`)) return;
        await appelApi(`${API}/admin/utilisateurs/${u.id}/refuser`, { method: "PATCH" });
        break;
      case "promouvoir":
        await appelApi(`${API}/admin/utilisateurs/${u.id}/promouvoir`, { method: "PATCH" });
        break;
      case "retrograder":
        if (!confirm(`Rétrograder ${u.pseudo} en USER ?`)) return;
        await appelApi(`${API}/admin/utilisateurs/${u.id}/retrograder`, { method: "PATCH" });
        break;
      case "supprimer":
        if (!confirm(`Supprimer DÉFINITIVEMENT ${u.pseudo} ? Toutes ses séries seront perdues.`)) return;
        await appelApi(`${API}/admin/utilisateurs/${u.id}`, { method: "DELETE" });
        break;
      case "motdepasse": {
        const nouveau = prompt(`Nouveau mot de passe pour ${u.pseudo} (min. 8 caractères) :`);
        if (!nouveau || nouveau.length < 8) {
          if (nouveau) alert("Le mot de passe doit faire au moins 8 caractères.");
          return;
        }
        await appelApi(`${API}/admin/utilisateurs/${u.id}/mot-de-passe`, {
          method: "PATCH",
          body: JSON.stringify({ nouveauMotDePasse: nouveau }),
        });
        alert(`Mot de passe de ${u.pseudo} changé avec succès.`);
        break;
      }
    }
    chargerListeAdmin();
    chargerStatsAdmin();
  } catch (err) {
    alert(err.message);
  }
}

document.getElementById("select-statut-admin").addEventListener("change", chargerListeAdmin);
document.getElementById("btn-rafraichir-admin").addEventListener("click", () => {
  chargerStatsAdmin();
  chargerListeAdmin();
});


// --- Startup ---

if (getToken()) {
  afficherApp(getPseudo());
} else {
  afficherLogin();
}