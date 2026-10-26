/* A continuous native scroll loop. Only supplied reviews are rendered by the builder. */
(() => {
  'use strict';
  document.querySelectorAll('[data-review-carousel]').forEach(carousel => {
    const viewport = carousel.querySelector('[data-review-viewport]');
    const track = carousel.querySelector('[data-review-track]');
    const group = carousel.querySelector('[data-review-originals]');
    const cards = [...group.children];
    const play = carousel.querySelector('[data-review-play]');
    const toolbar = carousel.querySelector('[data-review-toolbar]');
    const status = carousel.querySelector('[data-review-status]');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (cards.length < 2) return;
    let paused = reduced.matches;
    let requestedPlay = false;
    let hovered = false;
    let inView = false;
    let frame = 0;
    let previousTime = 0;
    let position = 0;
    let period = 0;
    const clones = [];
    const stop = () => { cancelAnimationFrame(frame); frame = 0; previousTime = 0; };
    const allowed = () => !paused && inView && !hovered && !document.hidden && period > 0 &&
      !(carousel.contains(document.activeElement) && !(document.activeElement === play && requestedPlay));
    const tick = time => {
      if (!allowed()) { stop(); return; }
      if (previousTime) {
        // One seven-review circuit takes about a minute, like the original template.
        position = (position + Math.min(time - previousTime, 50) * period / 60000) % period;
        viewport.scrollLeft = position;
      }
      previousTime = time;
      frame = requestAnimationFrame(tick);
    };
    const schedule = () => {
      if (!allowed()) { stop(); return; }
      if (!frame) {
        position = viewport.scrollLeft % period;
        frame = requestAnimationFrame(tick);
      }
    };
    const renderPlay = () => {
      play.setAttribute('aria-pressed', String(paused));
      play.setAttribute('aria-label', paused ? 'Activer le défilement continu des avis' : 'Mettre en pause le défilement des avis');
      play.title = paused ? 'Activer le défilement' : 'Mettre en pause';
    };
    const pause = () => { paused = true; requestedPlay = false; renderPlay(); stop(); };
    const layout = () => {
      stop();
      clones.splice(0).forEach(clone => clone.remove());
      period = group.getBoundingClientRect().width;
      if (!period) return;
      // Include the trailing gap in each group so the loop has no half-gap jump.
      const copies = Math.max(1, Math.ceil(viewport.clientWidth / period));
      for (let i = 0; i < copies; i++) {
        const clone = group.cloneNode(true);
        clone.removeAttribute('data-review-originals');
        clone.setAttribute('data-review-clone', '');
        clone.setAttribute('aria-hidden', 'true');
        clone.setAttribute('inert', '');
        clone.removeAttribute('aria-label');
        track.append(clone);
        clones.push(clone);
      }
      viewport.scrollLeft %= period;
      position = viewport.scrollLeft;
      carousel.dataset.reviewPeriod = String(period);
      schedule();
    };
    const move = index => {
      pause();
      const next = (index + cards.length) % cards.length;
      const target = cards[next].offsetLeft - cards[0].offsetLeft;
      viewport.scrollTo({ left: target, behavior: reduced.matches ? 'instant' : 'smooth' });
      status.textContent = 'Avis ' + (next + 1) + ' sur ' + cards.length + ' : ' + cards[next].dataset.reviewAuthor;
    };
    const current = () => {
      const offset = viewport.scrollLeft % period;
      return cards.reduce((best, card, index) => Math.abs(card.offsetLeft - cards[0].offsetLeft - offset) <
        Math.abs(cards[best].offsetLeft - cards[0].offsetLeft - offset) ? index : best, 0);
    };
    carousel.querySelector('[data-review-prev]').addEventListener('click', () => move(current() - 1));
    carousel.querySelector('[data-review-next]').addEventListener('click', () => move(current() + 1));
    play.addEventListener('click', () => { paused = !paused; requestedPlay = !paused; renderPlay(); schedule(); });
    viewport.addEventListener('mouseenter', () => { hovered = true; schedule(); });
    viewport.addEventListener('mouseleave', () => { hovered = false; schedule(); });
    viewport.addEventListener('pointerdown', pause, { passive: true });
    viewport.addEventListener('wheel', event => { if (Math.abs(event.deltaX) > 0) pause(); }, { passive: true });
    viewport.addEventListener('keydown', event => {
      if (event.target !== viewport) return;
      const targets = { ArrowLeft: current() - 1, ArrowRight: current() + 1, Home: 0, End: cards.length - 1 };
      if (Object.hasOwn(targets, event.key)) { event.preventDefault(); move(targets[event.key]); }
    });
    carousel.addEventListener('focusin', () => { requestedPlay = false; schedule(); });
    carousel.addEventListener('focusout', () => setTimeout(schedule, 0));
    document.addEventListener('visibilitychange', schedule);
    reduced.addEventListener('change', event => { if (event.matches) pause(); schedule(); });
    new IntersectionObserver(entries => { inView = entries[0].isIntersecting; schedule(); }, { threshold: .2 }).observe(carousel);
    new ResizeObserver(layout).observe(viewport);
    toolbar.hidden = false;
    carousel.dataset.reviewReady = '';
    renderPlay();
    layout();
  });
})();
