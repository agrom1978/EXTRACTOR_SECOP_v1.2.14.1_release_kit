    const CONSTANCIA_RE = /\b(\d{2}-\d{1,2}-\d{4,12})\b/g;
    const CONSTANCIA_TEST_RE = /^\d{2}-\d{1,2}-\d{4,12}$/;
    const DASHES_UNICODE = ["\u2013", "\u2014", "\u2212", "\u2010", "\u2011", "\u2012", "\u2043"];
    function normalizeText(s){
      let result = (s || "");
      result = result.replace(/\u00A0/g, " ");
      for (let dash of DASHES_UNICODE) {
        result = result.replace(new RegExp(dash.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), "-");
      }
      return result;
    }

    function detectConstancias(){
      const t = normalizeText(document.getElementById("raw").value);
      const m = t.match(CONSTANCIA_RE) || [];
      const seen = new Set();
      const out = [];
      for (const x of m){
        const v = x.replace(/\s+/g, "");
        if (!seen.has(v)){
          seen.add(v);
          out.push(v);
        }
      }
      return out;
    }

    const validationList = document.getElementById("validationList");
    const raw = document.getElementById("raw");
    const stageChips = document.querySelectorAll(".stage-chip");
    const validationPanel = document.querySelector(".validation-panel");
    const inputPanel = document.querySelector(".input-panel");
    let hadConstancias = false;

    function setStage(stage) {
      stageChips.forEach((chip) => {
        chip.classList.toggle("active", chip.getAttribute("data-stage") === String(stage));
      });
    }
    
    function buildValidationItems(text){
      const t = normalizeText(text);
      const parts = t.split(/[\s,;|]+/);
      const items = [];
      const seen = new Map();
      const invalidSeen = new Set();
      for (const part of parts) {
        const token = part.replace(/[^\d\-]/g, "");
        if (!token) continue;
        if (CONSTANCIA_TEST_RE.test(token)) {
          if (seen.has(token)) {
            const idx = seen.get(token);
            items[idx].status = "dup";
          } else {
            items.push({ value: token, status: "valid" });
            seen.set(token, items.length - 1);
          }
        } else {
          const dashes = (token.match(/-/g) || []).length;
          if (dashes >= 2 && !invalidSeen.has(token)) {
            items.push({ value: token, status: "invalid" });
            invalidSeen.add(token);
          }
        }
      }
      return items;
    }

    function renderValidation(){
      if (!validationList) return;
      const items = buildValidationItems(raw.value);
      validationList.innerHTML = "";
      if (items.length === 0) {
        if (validationPanel) {
          validationPanel.classList.remove("is-active", "is-flash");
        }
        if (inputPanel) {
          inputPanel.classList.remove("is-active", "is-flash");
        }
        hadConstancias = false;
        const empty = document.createElement("div");
        empty.className = "validation-empty";
        empty.textContent = "Sin datos para validar.";
        validationList.appendChild(empty);
        return;
      }
      if (validationPanel) {
        validationPanel.classList.add("is-active");
        if (!hadConstancias) {
          validationPanel.classList.add("is-flash");
          window.setTimeout(() => {
            validationPanel.classList.remove("is-flash");
          }, 800);
        }
      }
      if (inputPanel) {
        inputPanel.classList.add("is-active");
        if (!hadConstancias) {
          inputPanel.classList.add("is-flash");
          window.setTimeout(() => {
            inputPanel.classList.remove("is-flash");
          }, 800);
        }
      }
      hadConstancias = true;
      for (const item of items) {
        const row = document.createElement("div");
        row.className = `validation-item status-${item.status}`;
        const value = document.createElement("span");
        value.className = "validation-value";
        value.textContent = item.value;
        const badge = document.createElement("span");
        badge.className = "validation-badge";
        badge.textContent = item.status === "valid" ? "Valida" : item.status === "dup" ? "Duplicada" : "Invalida";
        row.appendChild(value);
        row.appendChild(badge);
        validationList.appendChild(row);
      }
    }

    function updatePreinfo(){
      renderValidation();
    }
    
    raw.addEventListener("input", updatePreinfo);
    updatePreinfo();

    const resultPanel = document.getElementById("resultPanel");
    if (resultPanel && resultPanel.getAttribute("data-has-result") === "1") {
      setStage(3);
    } else {
      setStage(1);
    }

    const downloadModal = document.getElementById("downloadModal");
    const modalDownload = document.getElementById("modalDownload");
    const modalClose = document.getElementById("modalClose");

    function openDownloadModal() {
      if (downloadModal) {
        downloadModal.classList.add("is-open");
      }
    }

    function closeDownloadModal() {
      if (downloadModal) {
        downloadModal.classList.remove("is-open");
      }
    }

    if (downloadModal) {
      let downloadUrl = downloadModal.getAttribute("data-download") || "";
      if (downloadUrl) {
        openDownloadModal();
      }
      if (modalDownload) {
        modalDownload.addEventListener("click", () => {
          if (downloadUrl) {
            triggerDownload(downloadUrl);
            clearInputOnly();
            downloadUrl = "";
            downloadModal.setAttribute("data-download", "");
          }
          closeDownloadModal();
        });
      }
      if (modalClose) {
        modalClose.addEventListener("click", closeDownloadModal);
      }
      downloadModal.addEventListener("click", (event) => {
        if (event.target === downloadModal) {
          closeDownloadModal();
        }
      });
    }

    function resetFormAfterDownload() {
      const progress = document.getElementById("progressContainer");
      if (progress) {
        progress.style.display = "none";
      }
      const runtime = document.getElementById("runtime");
      if (runtime) {
        runtime.style.display = "none";
      }
      raw.value = "";
      updatePreinfo();
      document.getElementById("btnIcon").textContent = ">";
    }

    function clearInputOnly() {
      raw.value = "";
      updatePreinfo();
    }

    function triggerDownload(url) {
      const frame = document.createElement("iframe");
      frame.style.display = "none";
      frame.src = url;
      document.body.appendChild(frame);
      window.setTimeout(() => {
        document.body.removeChild(frame);
      }, 2000);
    }

    async function openPath(endpoint, pathValue) {
      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: pathValue }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.ok) {
          alert(data.error || "No se pudo abrir la ruta.");
        }
      } catch (e) {
        alert("No se pudo abrir la ruta.");
      }
    }

    document.querySelectorAll("[data-open-folder]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const pathValue = btn.getAttribute("data-open-folder") || "";
        if (pathValue) {
          openPath("/open-folder", pathValue);
        }
      });
    });

    document.querySelectorAll("[data-open-file]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const pathValue = btn.getAttribute("data-open-file") || "";
        if (pathValue) {
          openPath("/open-file", pathValue);
        }
      });
    });

    const themeToggle = document.getElementById("themeToggle");
    const themeLabel = document.getElementById("themeLabel");
    const root = document.documentElement;

    function applyTheme(theme) {
      root.setAttribute("data-theme", theme);
      localStorage.setItem("secop-theme", theme);
      const label = theme === "dark" ? "Modo oscuro" : "Modo claro";
      themeLabel.textContent = label;
      themeToggle.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    }

    function initTheme() {
      const saved = localStorage.getItem("secop-theme");
      if (saved === "light" || saved === "dark") {
        applyTheme(saved);
        return;
      }
      const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      applyTheme(prefersDark ? "dark" : "light");
    }

    if (themeToggle) {
      initTheme();
      themeToggle.addEventListener("click", () => {
        const current = root.getAttribute("data-theme") || "light";
        applyTheme(current === "dark" ? "light" : "dark");
      });
    }


    document.getElementById("btnClear").addEventListener("click", () => {
      raw.value = "";
      updatePreinfo();
      const status = document.querySelector(".status");
      if (status) { status.style.display = "none"; }
      document.getElementById("runtime").style.display = "none";
      document.getElementById("progressContainer").style.display = "none";
      const btn = document.getElementById("btnExtract");
      btn.disabled = false;
      document.getElementById("btnIcon").textContent = ">";
      document.getElementById("btnText").textContent = "Procesar";
      setStage(1);
      raw.focus();
    });

    document.getElementById("form").addEventListener("submit", (e) => {
      const raw_val = raw.value.trim();
      const constancias = detectConstancias();
      
      if (!raw_val || constancias.length === 0) {
        e.preventDefault();
        alert("Ingresa al menos una constancia valida (formato: YY-XX-NNNN)");
        raw.focus();
        return false;
      }
      
      document.getElementById("btnExtract").disabled = true;
      document.getElementById("btnIcon").innerHTML = "<span class=\"spinner\"></span>";
      document.getElementById("btnText").textContent = "Procesando...";
      document.getElementById("runtime").style.display = "block";
      document.getElementById("progressContainer").style.display = "block";
      setStage(2);
      
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress > 90) progress = 90;
        document.getElementById("progressFill").style.width = progress + "%";
      }, 500);
      
      window.addEventListener("beforeunload", () => clearInterval(interval));
    });

  
