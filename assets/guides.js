/* Progressive enhancements: every guide and navigation link works without JavaScript. */
(() => {
  'use strict';
  const filter = document.getElementById('guide-category');
  if (filter) {
    const control = filter.closest('.guide-filter-control');
    const list = document.getElementById(filter.getAttribute('aria-controls'));
    const options = [...list.querySelectorAll('[role="option"]')];
    const valueLabel = document.getElementById('guide-category-value');
    let selectedIndex = options.findIndex(option => option.getAttribute('aria-selected') === 'true');
    let activeIndex = selectedIndex;
    let search = '';
    let searchTimer;
    document.querySelector('.guide-filters').hidden = false;
    const activate = (index) => {
      activeIndex = Math.max(0, Math.min(options.length - 1, index));
      options.forEach((option, i) => option.classList.toggle('is-active', i === activeIndex));
      filter.setAttribute('aria-activedescendant', options[activeIndex].id);
      options[activeIndex].scrollIntoView({ block: 'nearest' });
    };
    const open = (index = selectedIndex) => {
      list.hidden = false;
      filter.setAttribute('aria-expanded', 'true');
      control.classList.add('is-open');
      activate(index);
    };
    const close = () => {
      list.hidden = true;
      filter.setAttribute('aria-expanded', 'false');
      filter.removeAttribute('aria-activedescendant');
      control.classList.remove('is-open');
    };
    const select = (index) => {
      selectedIndex = index;
      const option = options[index];
      filter.dataset.value = option.dataset.value;
      valueLabel.textContent = option.textContent.trim();
      options.forEach((item, i) => item.setAttribute('aria-selected', String(i === index)));
      let count = 0;
      document.querySelectorAll('[data-guide-card]').forEach((card) => {
        card.hidden = option.dataset.value !== 'tous' && card.dataset.category !== option.dataset.value;
        if (!card.hidden) count++;
      });
      document.querySelector('[data-filter-status]').textContent = `${count} guide${count !== 1 ? 's' : ''} disponible${count !== 1 ? 's' : ''}`;
      close();
    };
    filter.addEventListener('click', () => {
      if (list.hidden) open(); else close();
    });
    options.forEach((option, index) => {
      option.addEventListener('pointerdown', event => event.preventDefault());
      option.addEventListener('click', () => { select(index); filter.focus({ preventScroll: true }); });
      option.addEventListener('pointermove', () => {
        if (!list.hidden && activeIndex !== index) activate(index);
      });
    });
    filter.addEventListener('keydown', event => {
      const expanded = !list.hidden;
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        if (!expanded) open();
        else activate(activeIndex + (event.key === 'ArrowDown' ? 1 : -1));
      } else if (event.key === 'Home' || event.key === 'End') {
        event.preventDefault();
        if (!expanded) open();
        activate(event.key === 'Home' ? 0 : options.length - 1);
      } else if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        if (expanded) select(activeIndex); else open();
      } else if (event.key === 'Escape' && expanded) {
        event.preventDefault();
        event.stopPropagation();
        close();
      } else if (event.key === 'Tab' && expanded) {
        select(activeIndex);
      } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
        event.preventDefault();
        clearTimeout(searchTimer);
        search += event.key.toLocaleLowerCase('fr');
        const start = expanded ? activeIndex : selectedIndex;
        const order = options.map((_, i) => (start + i + 1) % options.length);
        const index = order.find(i => options[i].textContent.trim().toLocaleLowerCase('fr').startsWith(search));
        if (index !== undefined) { if (!expanded) open(index); else activate(index); }
        searchTimer = setTimeout(() => { search = ''; }, 700);
      }
    });
    document.addEventListener('pointerdown', event => {
      if (!control.contains(event.target)) close();
    });
    control.addEventListener('focusout', event => {
      if (!control.contains(event.relatedTarget)) close();
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
