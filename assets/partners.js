/* Continuous logo strip. Native scrolling remains available when JavaScript or automatic motion is off. */
(() => {
  'use strict';
  document.querySelectorAll('[data-partner-carousel]').forEach(carousel => {
    const track = carousel.querySelector('[data-partner-track]');
    const toolbar = carousel.querySelector('[data-partner-toolbar]');
    const play = carousel.querySelector('[data-partner-play]');
    const originals = [...track.children];
    if (originals.length < 2) return;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const SPEED = 38; // pixels par seconde
    let paused = reducedMotion.matches;
    let inView = false;
    let hovered = false;
    let focused = false;
    let holdUntil = 0;
    let pos = 0;
    let period = 0;
    let last = 0;

    carousel.classList.add('is-marquee');

    // Copies decoratives pour boucler sans saut ; elles restent hors du clavier et des lecteurs d'ecran.
    const addSet = () => originals.forEach(slide => {
      const copy = slide.cloneNode(true);
      copy.setAttribute('aria-hidden', 'true');
      copy.dataset.partnerClone = '';
      copy.querySelectorAll('img').forEach(img => { img.alt = ''; img.loading = 'eager'; });
      track.append(copy);
    });
    const layout = () => {
      if (!track.querySelector('[data-partner-clone]')) addSet();
      const firstCopy = track.children[originals.length];
      period = firstCopy.offsetLeft - originals[0].offsetLeft;
      while (period > 0 && track.scrollWidth < period + track.clientWidth * 2) addSet();
      pos = track.scrollLeft;
    };
    const wrap = () => {
      if (period <= 0) return;
      if (pos >= period) pos -= period;
      if (pos < 0) pos += period;
      track.scrollLeft = pos;
    };
    const running = () => !paused && inView && !hovered && !focused && !document.hidden && performance.now() > holdUntil;
    const tick = now => {
      const dt = last ? Math.min(now - last, 64) / 1000 : 0;
      last = now;
      if (running()) {
        pos += SPEED * dt;
        wrap();
      }
      requestAnimationFrame(tick);
    };
    const hold = ms => { holdUntil = performance.now() + ms; };
    const step = direction => {
      const slide = originals[0].getBoundingClientRect().width + parseFloat(getComputedStyle(track).columnGap || 0);
      if (direction < 0 && track.scrollLeft < slide && period > 0) { pos = track.scrollLeft + period; track.scrollLeft = pos; }
      hold(1600);
      track.scrollBy({ left: direction * slide, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
    };
    const renderPlay = () => {
      play.setAttribute('aria-pressed', String(paused));
      play.setAttribute('aria-label', paused ? 'Activer le défilement automatique des partenaires' : 'Mettre en pause le défilement automatique des partenaires');
      play.title = paused ? 'Activer le défilement' : 'Mettre en pause';
    };

    carousel.querySelector('[data-partner-prev]').addEventListener('click', () => step(-1));
    carousel.querySelector('[data-partner-next]').addEventListener('click', () => step(1));
    play.addEventListener('click', () => { paused = !paused; renderPlay(); });
    track.addEventListener('keydown', event => {
      if (event.target !== track) return;
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); step(event.key === 'ArrowLeft' ? -1 : 1); }
      if (event.key === 'Home') { event.preventDefault(); hold(1600); track.scrollTo({ left: 0 }); }
    });
    // Toucher ou glisser : on laisse la main a la personne, puis le defilement reprend.
    track.addEventListener('pointerdown', () => hold(60000), { passive: true });
    window.addEventListener('pointerup', () => { if (holdUntil - performance.now() > 3000) hold(2500); }, { passive: true });
    track.addEventListener('wheel', () => hold(2500), { passive: true });
    track.addEventListener('scroll', () => {
      if (Math.abs(track.scrollLeft - pos) > 2) pos = track.scrollLeft;
    }, { passive: true });
    carousel.addEventListener('mouseenter', () => { hovered = true; });
    carousel.addEventListener('mouseleave', () => { hovered = false; });
    carousel.addEventListener('focusin', event => { focused = event.target !== play; });
    carousel.addEventListener('focusout', () => { focused = false; });
    reducedMotion.addEventListener('change', event => { if (event.matches) paused = true; renderPlay(); });
    new IntersectionObserver(entries => { inView = entries[0].isIntersecting; }, { threshold: .2 }).observe(carousel);
    new ResizeObserver(layout).observe(track);

    toolbar.hidden = false;
    renderPlay();
    layout();
    requestAnimationFrame(tick);
  });
})();
