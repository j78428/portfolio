// Joseph Wu Portfolio — v2 interactions (no dependencies)
(() => {
  // Header border once the page scrolls
  const header = document.querySelector('.site-header');
  if (header) {
    const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Tabs (WAI-ARIA tabs pattern, arrow-key navigation)
  document.querySelectorAll('[data-tabs]').forEach((root) => {
    const tabs = [...root.querySelectorAll('[role="tab"]')];
    const select = (tab, focus) => {
      tabs.forEach((t) => {
        const on = t === tab;
        t.setAttribute('aria-selected', on);
        t.tabIndex = on ? 0 : -1;
        const panel = document.getElementById(t.getAttribute('aria-controls'));
        panel.hidden = !on;
        if (on) {
          panel.classList.remove('is-entering');
          void panel.offsetWidth;
          panel.classList.add('is-entering');
        }
      });
      if (focus) tab.focus();
    };
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => select(tab));
      tab.addEventListener('keydown', (e) => {
        const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
        if (step) { e.preventDefault(); select(tabs[(i + step + tabs.length) % tabs.length], true); }
        if (e.key === 'Home') { e.preventDefault(); select(tabs[0], true); }
        if (e.key === 'End') { e.preventDefault(); select(tabs[tabs.length - 1], true); }
      });
    });
  });

  // Before / after comparison slider
  document.querySelectorAll('.compare').forEach((el) => {
    const input = el.querySelector('input[type="range"]');
    const set = () => el.style.setProperty('--pos', input.value + '%');
    input.addEventListener('input', set);
    set();
  });

  // Table of contents: highlight the section in view
  const tocLinks = [...document.querySelectorAll('.toc a')];
  if (tocLinks.length) {
    const sections = tocLinks.map((a) => document.getElementById(a.hash.slice(1))).filter(Boolean);
    let ticking = false;
    const update = () => {
      ticking = false;
      const line = window.innerHeight * 0.35;
      let current = sections[0];
      sections.forEach((s) => { if (s.getBoundingClientRect().top <= line) current = s; });
      tocLinks.forEach((a) => a.classList.toggle('is-active', a.hash === '#' + current.id));
    };
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  }

  // Lightbox for zoomable figures
  const zooms = document.querySelectorAll('button.zoom');
  if (zooms.length && 'HTMLDialogElement' in window) {
    const dlg = document.createElement('dialog');
    dlg.className = 'lightbox';
    dlg.innerHTML = '<button type="button" aria-label="關閉">×</button><img alt=""><p></p>';
    document.body.append(dlg);
    const [closeBtn, big, cap] = dlg.children;
    closeBtn.addEventListener('click', () => dlg.close());
    dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
    zooms.forEach((b) => b.addEventListener('click', () => {
      const img = b.querySelector('img');
      big.src = img.currentSrc || img.src;
      big.alt = img.alt;
      cap.textContent = b.closest('figure')?.querySelector('figcaption')?.textContent || '';
      dlg.showModal();
    }));
  }
})();
