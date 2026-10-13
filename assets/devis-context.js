/* Contexte de devis : paramètres limités, sans cookie ni stockage navigateur. */
(function () {
  'use strict';

  var services = {
    domicile: 'Ménage à domicile', repassage: 'Repassage et linge',
    vitres: 'Nettoyage de vitres', textile: 'Nettoyage de mobilier',
    edl: 'État des lieux', demenagement: 'Déménagement',
    airbnb: 'Location courte durée', commerce: 'Commerce ou bureau',
    copro: 'Copropriété', evenementiel: 'Événementiel',
    chantier: 'Fin de chantier', basevie: 'Entretien de base vie',
    debarraschantier: 'Débarras de chantier', debarras: 'Débarras de maison / appartement',
    grandnettoyage: 'Grand nettoyage', autre: 'Autre demande'
  };
  var choices = {
    frequence: { ponctuel: 'Ponctuel', quotidien: 'Quotidien', hebdomadaire: 'Hebdomadaire', 'plusieurs-fois-semaine': 'Plusieurs fois par semaine', 'a-definir': 'À définir' },
    vitres: { oui: 'Oui', non: 'Non', 'a-definir': 'À définir' },
    linge: { oui: 'Oui', non: 'Non', 'a-definir': 'À définir' },
    rotation: { ponctuelle: 'Ponctuelle', reguliere: 'Régulière', 'a-definir': 'À définir' },
    etage: { rdc: 'Rez-de-chaussée', 'avec-ascenseur': 'Étage avec ascenseur', 'sans-ascenseur': 'Étage sans ascenseur', 'a-definir': 'À définir' },
    dechets: { gravats: 'Gravats', mobilier: 'Mobilier', mixte: 'Déchets mixtes', 'a-definir': 'À définir' }
  };
  var labels = { surface: 'Surface indicative (m²)', modules: 'Nombre de modules', occupants: 'Nombre de personnes', frequence: 'Fréquence souhaitée', vitres: 'Vitres à inclure', linge: 'Linge à prévoir', rotation: 'Rotation locative', volume: 'Volume indicatif (m³)', etage: 'Accès aux espaces', dechets: 'Nature des déchets' };
  var maxNumbers = { surface: 1000000, modules: 500, occupants: 10000, volume: 10000 };
  var audiences = { part: true, ent: true, copro: true };
  var owns = function (object, key) { return Object.prototype.hasOwnProperty.call(object, key); };

  function validService(value) { return typeof value === 'string' && owns(services, value) ? value : ''; }
  function validAudience(value) { return typeof value === 'string' && owns(audiences, value) ? value : ''; }

  function cleanCity(value) {
    if (typeof value !== 'string') return '';
    var city = value.trim().replace(/\s+/g, ' ');
    return city.length <= 100 && /^[\p{L}\p{M}\d '\u2019().-]+$/u.test(city) ? city : '';
  }

  function cleanSource(value) {
    // Un chemin du site uniquement : ni domaine, ni requête, ni fragment.
    if (typeof value !== 'string' || value.length > 200 || !/^\/(?:[a-z0-9_-]+(?:\/[a-z0-9_-]+)*\/?)?$/i.test(value)) return '';
    return value;
  }

  function cleanDetails(input) {
    var result = {};
    if (!input || typeof input !== 'object' || Array.isArray(input)) return result;
    Object.keys(labels).forEach(function (name) {
      if (!owns(input, name)) return;
      var value = input[name];
      if (typeof value !== 'string' && typeof value !== 'number') return;
      value = String(value).trim();
      if (owns(maxNumbers, name)) {
        if (!/^\d{1,7}(?:[.,]\d{1,2})?$/.test(value)) return;
        var number = Number(value.replace(',', '.'));
        if (number > 0 && number <= maxNumbers[name] && (name === 'surface' || name === 'volume' || Number.isInteger(number))) result[name] = String(number);
      } else if (owns(choices[name], value)) result[name] = value;
    });
    return result;
  }

  function readContext(search) {
    var params = new URLSearchParams(search);
    var rawDetails = params.get('details') || '';
    var details = {};
    if (rawDetails.length <= 1000) {
      try { details = cleanDetails(JSON.parse(rawDetails)); } catch (_) { /* Paramètre facultatif mal formé : ignoré. */ }
    }
    var service = validService(params.get('service'));
    return { service: service, audience: service ? validAudience(params.get('audience')) : '', ville: cleanCity(params.get('ville')), source: cleanSource(params.get('source')), details: details };
  }

  function detailsText(details) {
    return Object.keys(details).map(function (name) {
      var value = owns(choices, name) ? choices[name][details[name]] : details[name];
      return labels[name] + ' : ' + value;
    }).join('\n');
  }

  function buildQuoteURL(context, origin) {
    var service = validService(context.service);
    if (!service) return null;
    var url = new URL('/', origin);
    url.searchParams.set('service', service);
    var audience = validAudience(context.audience);
    if (audience) url.searchParams.set('audience', audience);
    var ville = cleanCity(context.ville);
    var source = cleanSource(context.source);
    var details = cleanDetails(context.details);
    if (ville) url.searchParams.set('ville', ville);
    if (source) url.searchParams.set('source', source);
    if (Object.keys(details).length) url.searchParams.set('details', JSON.stringify(details));
    url.hash = 'devis';
    return url.href;
  }

  function initHome() {
    var form = document.getElementById('lead');
    if (!form) return;
    var context = readContext(window.location.search);
    var boxes = form.querySelectorAll('input[name="prestations"]');
    if (context.service) {
      var audience = context.audience || (context.service === 'copro' ? 'copro' : (['commerce', 'basevie', 'chantier', 'debarraschantier', 'evenementiel', 'airbnb'].indexOf(context.service) !== -1 ? 'ent' : 'part'));
      var tab = document.querySelector('.switch button[data-aud="' + audience + '"]');
      if (tab) tab.click();
      boxes.forEach(function (box) { box.checked = box.value === context.service; });
      if (boxes.length) boxes[0].dispatchEvent(new Event('change', { bubbles: true }));
    } else if (context.source) {
      // Une page multi-prestations conserve son contexte sans supposer le besoin.
      boxes.forEach(function (box) { box.checked = false; });
      if (boxes.length) boxes[0].dispatchEvent(new Event('change', { bubbles: true }));
    }
    if (context.ville) form.elements.cp.value = context.ville;
    if (form.elements.service_page) form.elements.service_page.value = context.service;
    if (form.elements.source_page) form.elements.source_page.value = context.source;
    var precisions = form.elements.precisions;
    if (precisions && Object.keys(context.details).length) precisions.value = detailsText(context.details);
    var summary = document.getElementById('quote-context');
    if (summary && (context.service || context.ville || Object.keys(context.details).length)) {
      summary.hidden = false;
      summary.textContent = 'Votre demande a été préremplie' + (context.service ? ' : ' + services[context.service] : '') + (context.ville ? ' à ' + context.ville : '') + '. Vous pouvez modifier les informations ci-dessous.';
    }
    // Le script historique remet la page en haut : rétablir la destination demandée.
    if (window.location.hash === '#devis') {
      var target = document.getElementById('devis');
      target.classList.remove('rv');
      var loaded = new Promise(function (resolve) {
        if (document.readyState === 'complete') resolve();
        else window.addEventListener('load', resolve, { once: true });
      });
      var fonts = document.fonts ? document.fonts.ready : Promise.resolve();
      Promise.all([loaded, fonts]).then(function () {
        window.requestAnimationFrame(function () { target.scrollIntoView({ block: 'start', behavior: 'instant' }); });
      });
    }
  }

  function initBuilders() {
    document.querySelectorAll('form[data-quote-builder]').forEach(function (form) {
      form.addEventListener('submit', function (event) {
        event.preventDefault();
        if (!form.reportValidity()) return;
        var details = {};
        Object.keys(labels).forEach(function (name) {
          var field = form.elements.namedItem(name);
          if (field) details[name] = field.value;
        });
        var cityField = form.elements.namedItem('ville');
        var target = buildQuoteURL({ service: form.dataset.service, audience: form.dataset.audience, ville: cityField ? cityField.value : form.dataset.ville, source: window.location.pathname, details: details }, window.location.origin);
        if (!target) {
          var error = form.querySelector('[data-quote-error]');
          if (!error) { error = document.createElement('p'); error.setAttribute('data-quote-error', ''); error.setAttribute('role', 'alert'); form.appendChild(error); }
          error.textContent = 'Cette demande ne peut pas être préremplie. Utilisez le lien de devis de cette page.';
          return;
        }
        window.location.assign(target);
      });
    });
  }

  function initServiceMenus() {
    document.querySelectorAll('details.service-mobile-menu').forEach(function (menu) {
      menu.querySelectorAll('nav a').forEach(function (link) {
        link.addEventListener('click', function () { menu.open = false; });
      });
      document.addEventListener('click', function (event) {
        if (menu.open && !menu.contains(event.target)) menu.open = false;
      });
      menu.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && menu.open) {
          menu.open = false;
          menu.querySelector('summary').focus();
        }
      });
    });
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { readContext: readContext, cleanCity: cleanCity, cleanSource: cleanSource, cleanDetails: cleanDetails, buildQuoteURL: buildQuoteURL, detailsText: detailsText };
  } else if (typeof document !== 'undefined') {
    var init = function () { initHome(); initBuilders(); initServiceMenus(); };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
  }
})();
