(() => {
  'use strict';
  const cards = [...document.querySelectorAll('[data-comparison]')];
  if (!cards.length) return;
  const hover = window.matchMedia('(hover: hover) and (pointer: fine)');
  let dialog;
  let opener;
  let previousOverflow;
  function show(card, side) {
    card.dataset.view = side;
    card.querySelector('[data-state]').textContent = side === 'avant' ? 'Avant' : 'Après';
    card.querySelector('[data-hint]').textContent = side === 'avant' ? 'Avant l’intervention' : 'Survolez pour voir l’avant';
    card.querySelector('.mu-before').setAttribute('aria-hidden', String(side !== 'avant'));
    card.querySelector('.mu-after').setAttribute('aria-hidden', String(side !== 'apres'));
    card.querySelectorAll('[data-side]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.side === side));
    });
  }
  function enlarge(card, button) {
    if (!dialog) {
      dialog = document.createElement('dialog');
      dialog.className = 'mu-lightbox';
      dialog.setAttribute('aria-labelledby', 'mu-lightbox-title');
      dialog.innerHTML = '<div class="mu-lightbox-head"><h2 id="mu-lightbox-title"></h2><button class="mu-lightbox-close" type="button" aria-label="Fermer les photos">×</button></div><div class="mu-lightbox-pair"><figure><img alt=""><figcaption>Avant</figcaption></figure><figure><img alt=""><figcaption>Après</figcaption></figure></div><p>Les prises de vue peuvent avoir des angles différents.</p>';
      document.body.append(dialog);
      dialog.querySelector('button').addEventListener('click', () => dialog.close());
      dialog.addEventListener('click', event => {
        const rect = dialog.getBoundingClientRect();
        if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
      });
      dialog.addEventListener('close', () => {
        document.body.style.overflow = previousOverflow;
        opener?.focus({preventScroll:true});
      });
    }
    opener = button;
    dialog.querySelector('h2').textContent = card.dataset.title;
    dialog.querySelector('p').textContent = 'Photographies complètes. Les prises de vue peuvent avoir des angles différents.';
    const imgs = dialog.querySelectorAll('img');
    ['avant', 'apres'].forEach((side, i) => {
      imgs[i].src = card.dataset[side];
      imgs[i].alt = `${card.dataset.title} — ${side === 'avant' ? 'avant' : 'après'}`;
    });
    previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    dialog.showModal();
  }
  cards.forEach(card => {
    let selected = 'apres';
    const stage = card.querySelector('.mu-comparison-stage');
    card.querySelector('.mu-comparison-controls').hidden = false;
    stage.addEventListener('pointerenter', event => {
      if (hover.matches && event.pointerType === 'mouse') show(card, 'avant');
    });
    stage.addEventListener('pointerleave', () => show(card, selected));
    card.querySelectorAll('[data-side]').forEach(button => {
      button.addEventListener('click', () => { selected = button.dataset.side; show(card, selected); });
    });
    card.querySelector('[data-enlarge]')?.addEventListener('click', event => { event.preventDefault(); enlarge(card, event.currentTarget); });
    show(card, selected);
  });
  const filters = [...document.querySelectorAll('[data-gallery-filter]')];
  const sections = [...document.querySelectorAll('[data-realisation-section]')];
  function filter(value) {
    sections.forEach(section => { section.hidden = value !== 'all' && section.dataset.realisationSection !== value; });
    filters.forEach(link => link.setAttribute('aria-current', String(link.dataset.galleryFilter === value)));
  }
  filters.forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    filter(link.dataset.galleryFilter);
    history.replaceState(null, '', link.getAttribute('href'));
  }));
  if(filters.length) {
    function syncFilterFromHash() {
      const match = filters.find(link => link.getAttribute('href') === location.hash);
      filter(match?.dataset.galleryFilter || 'all');
    }
    window.addEventListener('hashchange', syncFilterFromHash);
    syncFilterFromHash();
  }
})();
