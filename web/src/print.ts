export function printAs(kind: "deck" | "work") {
  const existing = document.querySelectorAll("style[data-print-page]");
  existing.forEach((node) => node.remove());
  const style = document.createElement("style");
  style.setAttribute("data-print-page", kind);
  style.textContent =
    kind === "deck"
      ? "@page { size: 13.333in 7.5in landscape; margin: 0; }"
      : "@page { size: A4; margin: 14mm; }";
  document.head.appendChild(style);
  document.body.dataset.print = kind;
  const cleanup = () => {
    style.remove();
    delete document.body.dataset.print;
    window.removeEventListener("afterprint", cleanup);
  };
  window.addEventListener("afterprint", cleanup);
  window.setTimeout(() => window.print(), 80);
}
