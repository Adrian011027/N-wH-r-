export function setupLoginPanel() {
  const loginBtn = document.getElementById("btn-login");
  const loginPanel = document.getElementById("login-panel");
  const closeLoginPanel = document.getElementById("close-login-panel");
  const pageOverlay = document.querySelector(".page-overlay");
  const contactPanel = document.getElementById("contact-panel");

  if (!loginBtn || !loginPanel || !closeLoginPanel || !pageOverlay) return;

  loginBtn.addEventListener("click", () => {
    loginPanel.classList.add("open");
    pageOverlay.classList.add("active");
  });

  closeLoginPanel.addEventListener("click", () => {
    loginPanel.classList.remove("open");
    pageOverlay.classList.remove("active");
  });

  pageOverlay.addEventListener("click", () => {
    loginPanel.classList.remove("open");
    contactPanel?.classList.remove("open");
    pageOverlay.classList.remove("active");
  });
}
