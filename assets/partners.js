/* Logo strip that advances one whole logo at a time. Native scrolling remains available when JavaScript or automatic motion is off. */
(() => {
  'use strict';
  document.querySelectorAll('[data-partner-carousel]').forEach(carousel => {
    const track = carousel.querySelector('[data-partner-track]');
    const originals = [...track.children];
    if (originals.length < 2) return;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const DELAY = 2600; // pause entre deux logos, en millisecondes
    let inView = false;
    let hovered = false;
    let focused = false;
    let holdUntil = 0;
    let step = 0;
    let index = 0;
    let timer;

    carousel.classList.add('is-marquee');

    // Copies decoratives pour boucler sans saut ; elles restent hors du clavier et des lecteurs d'ecran.
    const addSet = () => originals.forEach(slide => {
      const copy = slide.cloneNode(true);
      copy.setAttribute('aria-hidden', 'true');
      copy.dataset.partnerClone = '';
      copy.querySelectorAll('img').forEach(img => { img.alt = ''; img.loading = 'eager'; });
      track.append(copy);
    });
    addSet();
    addSet();

    // La fenetre prend la largeur exacte d'un nombre entier de logos, pour qu'aucun ne soit coupe.
    const layout = () => {
      track.style.width = '';
      const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      const slide = originals[0].getBoundingClientRect().width;
      step = slide + gap;
      const room = carousel.getBoundingClientRect().width;
      const count = Math.max(1, Math.min(originals.length, Math.floor((room + gap) / step)));
      track.style.width = Math.round(count * step - gap) + 'px';
      track.scrollLeft = index * step;
    };
    const running = () => !reducedMotion.matches && inView && !hovered && !focused && !document.hidden && Date.now() > holdUntil;
    const advance = () => {
      if (running() && step) {
        index += 1;
        track.scrollTo({ left: index * step, behavior: 'smooth' });
        if (index >= originals.length) {
          // Une fois la premiere serie passee, on revient sans animation au meme visuel.
          setTimeout(() => { index -= originals.length; track.scrollTo({ left: index * step, behavior: 'instant' }); }, 700);
        }
      }
      timer = setTimeout(advance, DELAY);
    };

    // Toucher ou glisser : on laisse la main a la personne, puis le defilement reprend sur un logo entier.
    track.addEventListener('pointerdown', () => { holdUntil = Date.now() + 60000; }, { passive: true });
    window.addEventListener('pointerup', () => { if (holdUntil - Date.now() > 3000) holdUntil = Date.now() + 2500; }, { passive: true });
    track.addEventListener('scroll', () => {
      if (!step || running()) return;
      clearTimeout(track._snap);
      track._snap = setTimeout(() => {
        index = Math.round(track.scrollLeft / step) % originals.length;
        track.scrollTo({ left: index * step, behavior: 'smooth' });
      }, 160);
    }, { passive: true });
    carousel.addEventListener('mouseenter', () => { hovered = true; });
    carousel.addEventListener('mouseleave', () => { hovered = false; });
    carousel.addEventListener('focusin', () => { focused = true; });
    carousel.addEventListener('focusout', () => { focused = false; });
    new IntersectionObserver(entries => { inView = entries[0].isIntersecting; }, { threshold: .2 }).observe(carousel);
    new ResizeObserver(layout).observe(carousel);

    layout();
    timer = setTimeout(advance, DELAY);
  });
})();
