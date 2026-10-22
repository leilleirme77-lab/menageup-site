/* Native scrolling remains available when JavaScript or automatic motion is off. */
(() => {
  'use strict';
  document.querySelectorAll('[data-partner-carousel]').forEach(carousel => {
    const track = carousel.querySelector('[data-partner-track]');
    const toolbar = carousel.querySelector('[data-partner-toolbar]');
    const pagination = carousel.querySelector('[data-partner-pagination]');
    const status = carousel.querySelector('[data-partner-status]');
    const play = carousel.querySelector('[data-partner-play]');
    const slides = [...track.children];
    if (slides.length < 2) return;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let paused = reducedMotion.matches;
    let inView = false;
    let hovered = false;
    let requestedPlay = false;
    let timer;
    let scrollTimer;
    let positions = [];
    let dots = [];
    const stop = () => { clearTimeout(timer); timer = undefined; };
    const current = () => positions.reduce((best, position, index) => Math.abs(position - track.scrollLeft) < Math.abs(positions[best] - track.scrollLeft) ? index : best, 0);
    const update = (announce = false) => {
      const index = current();
      dots.forEach((dot, i) => dot.setAttribute('aria-current', String(i === index)));
      if (announce) {
        const shown = slides.filter(slide => {
          const item = slide.getBoundingClientRect();
          const frame = track.getBoundingClientRect();
          return item.left >= frame.left - 3 && item.right <= frame.right + 3;
        }).map(slide => slide.dataset.partnerName);
        status.textContent = shown.length ? shown.join(', ') : slides[index].dataset.partnerName;
      }
    };
    const schedule = () => {
      stop();
      const readingFocus = carousel.contains(document.activeElement) && !(document.activeElement === play && requestedPlay);
      if (paused || !inView || hovered || document.hidden || readingFocus || positions.length < 2) return;
      timer = setTimeout(() => { move(current() + 1, false); }, 6000);
    };
    const renderPlay = () => {
      play.setAttribute('aria-pressed', String(paused));
      play.setAttribute('aria-label', paused ? 'Activer le défilement automatique des partenaires' : 'Mettre en pause le défilement automatique des partenaires');
      play.title = paused ? 'Activer le défilement' : 'Mettre en pause';
    };
    const move = (index, manual = true) => {
      if (manual) { paused = true; renderPlay(); }
      stop();
      const target = (index + positions.length) % positions.length;
      track.scrollTo({ left: positions[target], behavior: reducedMotion.matches ? 'instant' : 'smooth' });
      if (manual) setTimeout(() => update(true), reducedMotion.matches ? 0 : 450);
      schedule();
    };
    const layout = () => {
      const max = Math.max(0, track.scrollWidth - track.clientWidth);
      const origin = slides[0].offsetLeft;
      positions = [...new Set(slides.map(slide => Math.round(Math.min(max, slide.offsetLeft - origin))))];
      pagination.replaceChildren();
      dots = positions.map((position, index) => {
        const dot = document.createElement('button');
        dot.type = 'button';
        dot.className = 'partner-dot';
        dot.setAttribute('aria-label', 'Afficher le groupe de partenaires ' + (index + 1));
        dot.setAttribute('aria-controls', track.id);
        dot.addEventListener('click', () => move(index));
        pagination.append(dot);
        return dot;
      });
      toolbar.hidden = positions.length < 2;
      update();
      schedule();
    };
    carousel.querySelector('[data-partner-prev]').addEventListener('click', () => move(current() - 1));
    carousel.querySelector('[data-partner-next]').addEventListener('click', () => move(current() + 1));
    play.addEventListener('click', () => { paused = !paused; requestedPlay = !paused; renderPlay(); schedule(); });
    track.addEventListener('keydown', event => {
      if (event.target !== track) return;
      const targets = { ArrowLeft: current() - 1, ArrowRight: current() + 1, Home: 0, End: positions.length - 1 };
      if (Object.hasOwn(targets, event.key)) { event.preventDefault(); move(targets[event.key]); }
    });
    track.addEventListener('pointerdown', () => { paused = true; renderPlay(); stop(); }, { passive: true });
    track.addEventListener('scroll', () => {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(update, 90);
    }, { passive: true });
    carousel.addEventListener('mouseenter', () => { hovered = true; stop(); });
    carousel.addEventListener('mouseleave', () => { hovered = false; schedule(); });
    carousel.addEventListener('focusin', () => { requestedPlay = false; stop(); });
    carousel.addEventListener('focusout', () => setTimeout(schedule, 0));
    document.addEventListener('visibilitychange', schedule);
    reducedMotion.addEventListener('change', event => { if (event.matches) paused = true; renderPlay(); schedule(); });
    new IntersectionObserver(entries => { inView = entries[0].isIntersecting; schedule(); }, { threshold: .3 }).observe(carousel);
    new ResizeObserver(layout).observe(track);
    renderPlay();
    layout();
  });
})();
