document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const larger = document.getElementById("text-larger");
  const smaller = document.getElementById("text-smaller");
  const display = document.getElementById("text-size-display");
  const contrast = document.getElementById("contrast-toggle");

  const BASE_PX = 18;   // matches the body font-size in style.css
  const MIN = 50;       // lowest percentage
  const MAX = 200;      // highest percentage
  const STEP = 25;      // change per click

  let percent = Number(localStorage.getItem("toka-text-percent")) || 100;
  percent = Math.min(Math.max(percent, MIN), MAX);

  const applySize = () => {
    body.style.fontSize = `${(BASE_PX * percent) / 100}px`;
    if (display) display.textContent = `${percent}%`;
    if (larger) larger.disabled = percent >= MAX;
    if (smaller) smaller.disabled = percent <= MIN;
    localStorage.setItem("toka-text-percent", String(percent));
  };
  applySize();

  larger?.addEventListener("click", () => {
    percent = Math.min(percent + STEP, MAX);
    applySize();
  });
  smaller?.addEventListener("click", () => {
    percent = Math.max(percent - STEP, MIN);
    applySize();
  });

  const setContrast = (enabled) => {
    body.classList.toggle("high-contrast", enabled);
    contrast?.setAttribute("aria-pressed", String(enabled));
    localStorage.setItem("toka-high-contrast", String(enabled));
  };
  setContrast(localStorage.getItem("toka-high-contrast") === "true");
  contrast?.addEventListener("click", () => {
    setContrast(!body.classList.contains("high-contrast"));
  });
});