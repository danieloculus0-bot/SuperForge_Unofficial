(() => {
  const root = document.documentElement;
  const picker = document.getElementById("accent-picker");
  const toggle = document.getElementById("theme-toggle");
  const savedAccent = localStorage.getItem("superforge-accent");
  const savedTheme = localStorage.getItem("superforge-theme") || "dark";
  if (savedAccent) { root.style.setProperty("--accent", savedAccent); picker.value = savedAccent; }
  root.dataset.theme = savedTheme;
  toggle.textContent = savedTheme === "dark" ? "Light mode" : "Dark mode";
  picker.addEventListener("input", e => {
    root.style.setProperty("--accent", e.target.value);
    localStorage.setItem("superforge-accent", e.target.value);
  });
  toggle.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    localStorage.setItem("superforge-theme", next);
    toggle.textContent = next === "dark" ? "Light mode" : "Dark mode";
  });
})();
