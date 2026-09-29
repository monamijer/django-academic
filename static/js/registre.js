/* REGISTRE — micro-interactions. Vanilla JS, aucune dépendance.
   Odomètre : chaque chiffre de [data-odometer] roule jusqu'à sa valeur.
   Sans JS, ou avec prefers-reduced-motion, le nombre reste du texte simple. */
(function () {
  'use strict';

  var reduit = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduit) { return; }

  var TOURS = 2; // nombre de dizaines parcourues avant de s'arrêter

  function bande() {
    var b = document.createElement('span');
    b.className = 'od__bande';
    for (var i = 0; i < 10 * TOURS; i++) {
      var s = document.createElement('span');
      s.textContent = String(i % 10);
      b.appendChild(s);
    }
    return b;
  }

  function monter(el) {
    var texte = el.getAttribute('data-odometer');
    if (!texte) { return; }

    var rouleau = document.createElement('span');
    rouleau.className = 'od';
    rouleau.setAttribute('aria-hidden', 'true');

    var bandes = [];
    texte.split('').forEach(function (car) {
      if (/\d/.test(car)) {
        var boite = document.createElement('span');
        boite.className = 'od__chiffre';
        var b = bande();
        boite.appendChild(b);
        rouleau.appendChild(boite);
        bandes.push({ b: b, cible: 10 * (TOURS - 1) + Number(car) });
      } else {
        var sep = document.createElement('span');
        sep.className = 'od__sep';
        sep.textContent = car;
        rouleau.appendChild(sep);
      }
    });

    el.setAttribute('role', 'img');
    el.setAttribute('aria-label', texte);
    el.textContent = '';
    el.appendChild(rouleau);

    // Deux frames : le navigateur doit peindre l'état initial avant la transition.
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        bandes.forEach(function (o, i) {
          o.b.style.transitionDelay = (i * 110) + 'ms';
          o.b.style.transform = 'translateY(-' + o.cible + 'em)';
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-odometer]').forEach(monter);
  });
})();
