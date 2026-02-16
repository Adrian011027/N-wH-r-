export function setupZoomEffect() {
  const header   = document.querySelector('header');
  const banners  = Array.from(document.querySelectorAll('.banner-zoom'));

  /* ── Altura fija: se captura UNA VEZ y no cambia con address bar ── */
  const root = document.documentElement;
  root.style.setProperty('--app-h', `${window.innerHeight}px`);

  const setHeaderH = () =>
    root.style.setProperty(
      '--header-h', `${header.getBoundingClientRect().height}px`);
  setHeaderH();

  /* Solo recalcular header si cambia el ANCHO (rotación / resize real) */
  let lastW = window.innerWidth;
  addEventListener('resize', () => {
    if (Math.abs(window.innerWidth - lastW) > 1) {
      lastW = window.innerWidth;
      root.style.setProperty('--app-h', `${window.innerHeight}px`);
      setHeaderH();
    }
  });

  const onScroll = () => {
    const sy = window.scrollY;
    const hHeader = header.offsetHeight;

    banners.forEach((banner, i) => {
      const topDoc   = banner.offsetTop;
      const hBanner  = banner.offsetHeight;
      const start    = topDoc - hHeader;
      const end      = start + hBanner;
      const nextTop  = banners[i+1]
                       ? banners[i+1].offsetTop - hHeader
                       : end + hBanner;

      const zoomable = banner.querySelector('.zoomable');
      const progress = Math.min(Math.max((sy - start) / hBanner, 0), 1);

      zoomable.style.transform = `scale(${1 + progress * 0.20})`;
      banner.style.opacity     = `${1 - progress}`;

      if (sy >= nextTop) banner.style.opacity = '0';
      if (sy < start)   banner.style.opacity = '1';
    });
  };

  addEventListener('scroll', onScroll, { passive:true });
  onScroll();
}
