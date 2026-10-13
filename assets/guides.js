/* Progressive enhancements: every guide and navigation link works without JavaScript. */
(() => {
  'use strict';
  const filter = document.getElementById('guide-category');
  if (filter) {
    document.querySelector('.guide-filters').hidden = false;
    filter.addEventListener('change', () => {
      let count = 0;
      document.querySelectorAll('[data-guide-card]').forEach((card) => {
        card.hidden = filter.value !== 'tous' && card.dataset.category !== filter.value;
        if (!card.hidden) count++;
      });
      document.querySelector('[data-filter-status]').textContent = `${count} guide${count > 1 ? 's' : ''} disponible${count > 1 ? 's' : ''}`;
    });
  }
  const button = document.querySelector('[data-copy-template]');
  const template = document.getElementById('quote-template');
  if (button && template) {
    button.hidden = false;
    button.addEventListener('click', async () => {
      const status = document.querySelector('.copy-status');
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(template.value);
        status.textContent = 'Trame copiée. Vous pouvez la compléter dans votre message.';
      } catch (_) {
        template.focus();
        template.select();
        status.textContent = 'Sélectionnez puis copiez la trame avec le menu de votre appareil.';
      }
    });
  }
  const progress = document.querySelector('.reading-progress');
  const article = document.querySelector('.guide-layout');
  if (progress && article && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    let pending = false;
    const update = () => {
      const top = article.offsetTop;
      const length = Math.max(1, article.offsetHeight - window.innerHeight);
      progress.style.transform = `scaleX(${Math.max(0, Math.min(1, (window.scrollY - top) / length))})`;
      pending = false;
    };
    window.addEventListener('scroll', () => { if (!pending) { pending = true; requestAnimationFrame(update); } }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }
})();
