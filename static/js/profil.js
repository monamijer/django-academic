/* Mon profil — garde des boutons d'envoi.

   « Enregistrer » et « Changer le mot de passe » restent désactivés tant que le
   formulaire ne respecte pas les règles qu'un navigateur peut vérifier seul, et
   une ligne d'aide dit ce qui manque.

   Ce n'est qu'un confort : le serveur revalide tout, et applique en plus les
   règles qu'il est seul à connaître (mots de passe trop courants, ressemblance
   avec le nom, etc.). Sans JavaScript, les boutons restent actifs et c'est le
   serveur qui décide. */
(function () {
  'use strict';

  // Mêmes règles que comptes/forms.py (valider_telephone).
  var FORMAT_TELEPHONE = /^\+?[0-9][0-9 .\-]*$/;

  function chercher(form, repere) {
    return form.querySelector('[data-garde-champ="' + repere + '"]');
  }

  function problemeTelephone(form) {
    var champ = chercher(form, 'telephone');
    var valeur = champ.value.trim();
    var min = Number(champ.getAttribute('data-min-chiffres'));
    var max = Number(champ.getAttribute('data-max-chiffres'));

    if (valeur === '') { return 'Saisissez votre numéro de téléphone.'; }
    if (!FORMAT_TELEPHONE.test(valeur)) {
      return 'Chiffres, espaces, points ou tirets uniquement, avec un « + » optionnel au début.';
    }
    var nbChiffres = valeur.replace(/[^0-9]/g, '').length;
    if (nbChiffres < min || nbChiffres > max) {
      return 'Le numéro doit contenir entre ' + min + ' et ' + max + ' chiffres.';
    }
    return '';
  }

  function problemeMotDePasse(form) {
    var ancien = chercher(form, 'ancien').value;
    var nouveau = chercher(form, 'nouveau');
    var confirmation = chercher(form, 'confirmation').value;
    var min = Number(nouveau.getAttribute('data-min-longueur'));

    if (ancien === '') { return 'Saisissez votre mot de passe actuel.'; }
    if (nouveau.value.length < min) {
      return 'Le nouveau mot de passe doit contenir au moins ' + min + ' caractères.';
    }
    if (/^[0-9]+$/.test(nouveau.value)) {
      return 'Le nouveau mot de passe ne peut pas être composé uniquement de chiffres.';
    }
    if (confirmation === '') { return 'Confirmez le nouveau mot de passe.'; }
    if (confirmation !== nouveau.value) { return 'Les deux mots de passe ne correspondent pas.'; }
    return '';
  }

  var REGLES = {
    'telephone': problemeTelephone,
    'mot-de-passe': problemeMotDePasse
  };

  document.querySelectorAll('form[data-garde]').forEach(function (form) {
    var verifier = REGLES[form.getAttribute('data-garde')];
    var bouton = form.querySelector('[data-garde-submit]');
    var aide = form.querySelector('[data-garde-aide]');
    if (!verifier || !bouton) { return; }

    function actualiser() {
      var probleme = verifier(form);
      bouton.disabled = probleme !== '';
      // On ne réécrit le texte que s'il change : un lecteur d'écran ne doit pas
      // ré-annoncer la même phrase à chaque frappe.
      if (aide && aide.textContent !== probleme) { aide.textContent = probleme; }
    }

    form.addEventListener('input', actualiser);
    form.addEventListener('change', actualiser);
    // Dernier filet : un envoi programmatique ne doit pas contourner la garde.
    form.addEventListener('submit', function (evenement) {
      if (verifier(form) !== '') { evenement.preventDefault(); }
    });
    // Retour arrière du navigateur : le champ peut être restauré sans événement.
    window.addEventListener('pageshow', actualiser);

    actualiser();
  });
})();
