(() => {
    'use strict';

    /* ---------- Tab Switching ---------- */
    const tabs = document.querySelectorAll('.hero-tab');
    const panels = document.querySelectorAll('.hero-panel');

    tabs.forEach((tab) => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');

            tabs.forEach((t) => {
                t.classList.remove('is-active');
                t.setAttribute('aria-selected', 'false');
            });
            tab.classList.add('is-active');
            tab.setAttribute('aria-selected', 'true');

            panels.forEach((panel) => {
                panel.classList.toggle('hidden', panel.getAttribute('data-panel') !== target);
            });
        });
    });

    /* ---------- Swap From / To ---------- */
    const swapBtn = document.getElementById('swap-locations');
    const fromValue = document.getElementById('flight-from-value');
    const toValue = document.getElementById('flight-to-value');
    const fromSub = document.getElementById('flight-from-sub');
    const toSub = document.getElementById('flight-to-sub');

    swapBtn?.addEventListener('click', () => {
        if (!fromValue || !toValue) return;
        [fromValue.textContent, toValue.textContent] = [toValue.textContent, fromValue.textContent];
        [fromSub.textContent, toSub.textContent] = [toSub.textContent, fromSub.textContent];
    });

    /* ---------- Carousel nav buttons ---------- */
    document.querySelectorAll('.carousel-nav-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const track = document.getElementById(btn.getAttribute('data-carousel'));
            const dir = Number(btn.getAttribute('data-dir')) || 1;
            if (!track) return;
            const cardWidth = track.firstElementChild ? track.firstElementChild.getBoundingClientRect().width + 16 : 240;
            track.scrollBy({ left: dir * cardWidth * 2, behavior: 'smooth' });
        });
    });

    /* ---------- Special fare selection ---------- */
    document.querySelectorAll('.fare-chip input').forEach((input) => {
        input.addEventListener('change', () => {
            document.querySelectorAll('.fare-chip').forEach((chip) => chip.classList.remove('is-active'));
            input.closest('.fare-chip')?.classList.add('is-active');
        });
    });
})();