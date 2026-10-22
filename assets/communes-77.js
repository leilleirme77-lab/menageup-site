/* Official commune directory: local filtering only, no tracking or network request. */
(function () {
  'use strict';
  var container = document.querySelector('[data-commune-search]');
  var source = document.getElementById('communes-77-data');
  if (!container || !source) return;
  var data;
  try { data = JSON.parse(source.textContent); } catch (_) { return; }
  if (!Array.isArray(data) || !data.length || data.length > 1000) return;
  var input = document.getElementById('commune-search');
  var result = container.querySelector('[data-commune-results]');
  var status = container.querySelector('[data-commune-status]');
  function normalize(value) { return String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[’'-]/g, ' ').replace(/\s+/g, ' ').trim(); }
  var communes = data.filter(function (c) { return c && typeof c.nom === 'string' && /^77\d{3}$/.test(c.code) && Array.isArray(c.codesPostaux) && c.codesPostaux.every(function (p) { return /^77\d{3}$/.test(p); }); });
  if (communes.length !== data.length) return;
  function update() {
    var query = normalize(input.value);
    result.replaceChildren();
    if (query.length < 2) { status.textContent = ''; return; }
    var found = communes.filter(function (c) { return normalize(c.nom).includes(query) || c.codesPostaux.some(function (p) { return p.indexOf(query) === 0; }); });
    if (!found.length) { status.textContent = 'Aucune commune trouvée dans ce répertoire du 77. Vérifiez le nom ou indiquez votre commune dans le formulaire de devis.'; return; }
    status.textContent = found.length + (found.length === 1 ? ' commune trouvée.' : ' communes trouvées.') + (found.length > 12 ? ' Les 12 premières sont affichées ; précisez votre recherche.' : '');
    found.slice(0, 12).forEach(function (c) {
      var item = document.createElement('li');
      var link = document.createElement('a');
      var label = document.createElement('strong');
      var detail = document.createElement('span');
      var params = new URLSearchParams({ service: 'autre', audience: 'part', ville: c.nom, source: '/zones-intervention-seine-et-marne-77/' });
      link.href = '/?' + params.toString() + '#devis';
      link.setAttribute('aria-label', 'Préparer une demande à ' + c.nom + ', ' + c.codesPostaux.join(', '));
      label.textContent = c.nom;
      detail.textContent = c.codesPostaux.join(' · ') + ' — Préparer ma demande';
      link.append(label, detail); item.append(link); result.append(item);
    });
  }
  input.addEventListener('input', update);
  container.hidden = false;
  update();
})();
