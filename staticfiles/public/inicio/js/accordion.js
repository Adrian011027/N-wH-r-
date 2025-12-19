export function setupAccordion() {
  const toggles = document.querySelectorAll('.accordion-toggle');

  toggles.forEach(toggle => {
    toggle.addEventListener('click', () => {
      const content = toggle.nextElementSibling;
      const isOpen = content.classList.contains('open');
      content.classList.toggle('open', !isOpen);
      toggle.classList.toggle('active', !isOpen);
    });
  });
}
