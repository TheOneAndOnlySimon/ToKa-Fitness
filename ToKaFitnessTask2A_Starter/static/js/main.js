document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const larger = document.getElementById("text-larger");
  const smaller = document.getElementById("text-smaller");
  const contrast = document.getElementById("contrast-toggle");

  let fontSize = Number(localStorage.getItem("toka-font-size")) || 18;
  const applySize = () => {
    body.style.fontSize = `${fontSize}px`;
    localStorage.setItem("toka-font-size", String(fontSize));
  };
  applySize();

  larger?.addEventListener("click", () => {
    fontSize = Math.min(fontSize + 2, 26);
    applySize();
  });
  smaller?.addEventListener("click", () => {
    fontSize = Math.max(fontSize - 2, 14);
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
