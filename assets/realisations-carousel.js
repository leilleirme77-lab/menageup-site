/* Continuous photo strip, with native scrolling and pauses for interaction. */
(() => {
  'use strict';
  document.querySelectorAll('[data-realisation-carousel]').forEach(carousel => {
    const viewport = carousel.querySelector('[data-realisation-viewport]');
    const originals = [...viewport.children];
    if (originals.length < 2) return;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
    const copies = originals.map(card => {
      const copy = card.cloneNode(true);
      copy.dataset.carouselCopy = '';
      copy.setAttribute('aria-hidden', 'true');
      copy.querySelectorAll('[id]').forEach(el => { el.id += '-loop'; });
      copy.querySelectorAll('[aria-controls]').forEach(el => { el.setAttribute('aria-controls', el.getAttribute('aria-controls') + '-loop'); });
      copy.querySelectorAll('a,button').forEach(el => { el.tabIndex = -1; });
      viewport.append(copy);
      return copy;
    });
    let inView = false, hovered = false, focused = false, held = false;
    let keyboardMode = true, touching = false, manualScroll = false, drag = null, touchOrigin = null;
    let resumeUnderMouse = false, releasePoint = null, blockClickUntil = 0;
    let frame = 0, last = 0, position = 0, distance = 0, holdUntil = 0, resumeTimer;
    const RESUME_DELAY = 2500;
    function normalise(value) {
      return distance > 0 && !reduced.matches ? ((value % distance) + distance) % distance : value;
    }
    function tick(now) {
      if (last) position = normalise(position + Math.min(now - last, 50) * .027);
      viewport.scrollLeft = position;
      last = now;
      frame = requestAnimationFrame(tick);
    }
    function refresh() {
      const running = distance > 0 && inView && (!hovered || resumeUnderMouse) && !focused && !held && !reduced.matches && !document.hidden && performance.now() >= holdUntil;
      carousel.dataset.running = String(running);
      if (running && !frame) {
        position = normalise(viewport.scrollLeft);
        manualScroll = false;
        last = 0;
        frame = requestAnimationFrame(tick);
      } else if (!running && frame) {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    }
    function hold(ms = RESUME_DELAY) {
      holdUntil = performance.now() + ms;
      clearTimeout(resumeTimer);
      resumeTimer = setTimeout(refresh, ms + 20);
      refresh();
    }
    function layout() {
      const previous = distance;
      distance = reduced.matches ? 0 : copies[0].getBoundingClientRect().left - originals[0].getBoundingClientRect().left;
      if (previous && distance) viewport.scrollLeft = normalise(viewport.scrollLeft / previous * distance);
      position = normalise(viewport.scrollLeft);
      refresh();
    }
    carousel.addEventListener('pointerenter', event => {
      if (finePointer.matches && event.pointerType === 'mouse') { hovered = true; refresh(); }
    });
    carousel.addEventListener('pointerleave', () => { hovered = false; resumeUnderMouse = false; refresh(); });
    document.addEventListener('keydown', () => {
      keyboardMode = true;
      focused = viewport.contains(document.activeElement);
      refresh();
    });
    document.addEventListener('pointerdown', () => {
      keyboardMode = false;
      focused = false;
      refresh();
    }, {capture:true, passive:true});
    carousel.addEventListener('focusin', () => { focused = keyboardMode && viewport.contains(document.activeElement); refresh(); });
    carousel.addEventListener('focusout', () => {
      queueMicrotask(() => { focused = keyboardMode && viewport.contains(document.activeElement); refresh(); });
    });

    // Wait for a real drag before capturing the mouse: an ordinary click still opens the card.
    viewport.addEventListener('pointerdown', event => {
      blockClickUntil = 0;
      if (event.pointerType !== 'mouse' || event.button !== 0 || !event.isPrimary || event.target.closest('button')) return;
      held = true;
      resumeUnderMouse = false;
      drag = {id:event.pointerId, x:event.clientX, origin:viewport.scrollLeft, moved:false};
      refresh();
    });
    window.addEventListener('pointermove', event => {
      if (!drag || event.pointerId !== drag.id) {
        if (event.pointerType === 'mouse' && resumeUnderMouse && releasePoint && Math.hypot(event.clientX - releasePoint.x, event.clientY - releasePoint.y) > 4) {
          resumeUnderMouse = false;
          refresh();
        }
        return;
      }
      const delta = event.clientX - drag.x;
      if (!drag.moved && Math.abs(delta) < 6) return;
      if (!drag.moved) {
        drag.moved = true;
        manualScroll = true;
        viewport.setPointerCapture(event.pointerId);
        carousel.classList.add('is-dragging');
      }
      event.preventDefault();
      const next = normalise(drag.origin - delta);
      drag.origin = next + delta;
      viewport.scrollLeft = next;
    }, {passive:false});
    function releaseMouse(event) {
      if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.id)) return;
      const finished = drag;
      drag = null;
      held = touching;
      carousel.classList.remove('is-dragging');
      if (finished.moved) {
        blockClickUntil = performance.now() + 600;
        resumeUnderMouse = Number.isFinite(event.clientX);
        releasePoint = resumeUnderMouse ? {x:event.clientX, y:event.clientY} : null;
      }
      if (viewport.hasPointerCapture(finished.id)) viewport.releasePointerCapture(finished.id);
      hold();
    }
    window.addEventListener('pointerup', releaseMouse, {passive:true});
    window.addEventListener('pointercancel', releaseMouse, {passive:true});
    viewport.addEventListener('lostpointercapture', releaseMouse);
    viewport.addEventListener('dragstart', event => event.preventDefault());
    viewport.addEventListener('click', event => {
      if (event.detail && performance.now() < blockClickUntil) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }
    }, true);

    // Native touch scrolling keeps vertical page scrolling and momentum intact.
    // Touch events remain active after pointercancel, which the browser fires when it starts panning.
    viewport.addEventListener('touchstart', event => {
      touching = true;
      held = true;
      manualScroll = true;
      touchOrigin = {x:event.touches[0].clientX, y:event.touches[0].clientY, checked:false};
      refresh();
    }, {passive:true});
    viewport.addEventListener('touchmove', event => {
      if (!touchOrigin || touchOrigin.checked || event.touches.length !== 1) return;
      const dx = event.touches[0].clientX - touchOrigin.x;
      const dy = event.touches[0].clientY - touchOrigin.y;
      if (Math.max(Math.abs(dx), Math.abs(dy)) < 8) return;
      touchOrigin.checked = true;
      if (distance && dx > Math.abs(dy) && viewport.scrollLeft < viewport.clientWidth) viewport.scrollLeft += distance;
    }, {passive:true});
    function releaseTouch(event) {
      if (!touching || event.touches.length) return;
      touching = false;
      touchOrigin = null;
      held = !!drag;
      hold();
    }
    window.addEventListener('touchend', releaseTouch, {passive:true});
    window.addEventListener('touchcancel', releaseTouch, {passive:true});
    viewport.addEventListener('wheel', () => { manualScroll = true; hold(); }, {passive:true});
    viewport.addEventListener('scroll', () => {
      if (!frame && !held && manualScroll) hold();
    }, {passive:true});
    window.addEventListener('blur', () => {
      if (drag) releaseMouse({});
      touching = false;
      held = false;
      hold();
    });
    document.addEventListener('visibilitychange', refresh);
    reduced.addEventListener('change', layout);
    new IntersectionObserver(entries => { inView = entries[0].isIntersecting; refresh(); }, {threshold:.1}).observe(carousel);
    new ResizeObserver(layout).observe(viewport);
    layout();
  });
})();
