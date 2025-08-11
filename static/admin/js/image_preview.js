(function () {
  function isImageInput(input) {
    if (input.type !== "file") return false;
    if (input.accept && !input.accept.includes("image")) return false;
    // heuristic fallback: field name contains 'image'
    return input.accept || /image/i.test(input.name || input.id || "");
  }

  function ensurePreview(input) {
    let preview = document.getElementById(input.id + "__preview");
    if (!preview) {
      preview = document.createElement("div");
      preview.id = input.id + "__preview";
      preview.style.marginTop = "8px";
      preview.innerHTML = '<img style="max-height:160px;border:1px solid #ddd;padding:4px;border-radius:6px;background:#fff" />';
      input.parentNode.appendChild(preview);
    }
    const img = preview.querySelector("img");

    // initial (existing image on change form)
    if (!img.dataset._initDone) {
      const currentLink = input.parentNode.querySelector("a[href*='/media/'], a[href^='http']");
      if (currentLink && !input.value) img.src = currentLink.href;
      img.dataset._initDone = "1";
    }

    input.addEventListener("change", function () {
      if (!this.files || !this.files[0]) return;
      const file = this.files[0];
      if (!file.type || !file.type.startsWith("image/")) { img.removeAttribute("src"); return; }
      const url = URL.createObjectURL(file);
      img.onload = function () { URL.revokeObjectURL(url); };
      img.src = url;
    });
  }

  function wireAll(container) {
    container.querySelectorAll("input[type=file]").forEach(function (input) {
      if (isImageInput(input)) ensurePreview(input);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireAll(document);

    // support dynamically added inline form rows
    const obs = new MutationObserver(function (muts) {
      muts.forEach(function (m) {
        m.addedNodes.forEach(function (node) {
          if (node.querySelectorAll) wireAll(node);
        });
      });
    });
    obs.observe(document.body, { childList: true, subtree: true });
  });
})();