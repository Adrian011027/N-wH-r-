export function setupZoomEffect() {
  const header   = document.querySelector('header');
  const banners  = Array.from(document.querySelectorAll('.banner-zoom'));
  const cards    = document.querySelectorAll('.categoria-card');

  const setHeaderH = () =>
    document.documentElement.style.setProperty(
      '--header-h', `${header.getBoundingClientRect().height}px`);
  setHeaderH();
  addEventListener('resize', setHeaderH);

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

    cards.forEach(card => {
      if (card.getBoundingClientRect().top < innerHeight - 50){
        card.classList.add('visible');
      }
    });
  };

  addEventListener('scroll', onScroll, { passive:true });
  onScroll();
}
