document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy]");
  if (!button) {
    return;
  }

  const text = button.getAttribute("data-copy");
  try {
    await navigator.clipboard.writeText(text);
    const originalText = button.textContent;
    button.textContent = "ID copiado";
    window.setTimeout(() => {
      button.textContent = originalText;
    }, 1800);
  } catch (_error) {
    button.textContent = text;
  }
});

document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-password-toggle]");
  if (!toggle) {
    return;
  }

  const selector = toggle.getAttribute("data-password-toggle");
  if (!selector) {
    return;
  }

  const input = document.querySelector(selector);
  if (!input || input.type !== "password" && input.type !== "text") {
    return;
  }

  const showing = input.type === "text";
  input.type = showing ? "password" : "text";
  const label = showing ? "Mostrar senha" : "Ocultar senha";
  toggle.setAttribute("aria-label", label);
  toggle.setAttribute("title", label);

  const svg = toggle.querySelector("svg");
  if (svg) {
    svg.innerHTML = showing
      ? '<path d="M12 6.5c3.97 0 7.29 2.72 8.24 6.5-0.95 3.78-4.27 6.5-8.24 6.5s-7.29-2.72-8.24-6.5C4.71 9.22 8.03 6.5 12 6.5zm0 11c2.48 0 4.55-1.58 5.34-3.8-0.79-2.22-2.86-3.8-5.34-3.8s-4.55 1.58-5.34 3.8C7.45 16.92 9.52 17.5 12 17.5zm0-8a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5z"></path>'
      : '<path d="M12 6.5c3.97 0 7.29 2.72 8.24 6.5-0.95 3.78-4.27 6.5-8.24 6.5s-7.29-2.72-8.24-6.5c0.89-2.79 3.25-4.99 6.24-5.68V6.5zm0 11c-2.48 0-4.55-1.58-5.34-3.8 0.79-2.22 2.86-3.8 5.34-3.8 2.48 0 4.55 1.58 5.34 3.8-0.79 2.22-2.86 3.8-5.34 3.8zm0-8a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5z"></path>';
  }
});

const scannerState = new WeakMap();

function getQrElements(form) {
  const panel = form ? form.querySelector(".qr-scanner") : null;
  const button = form ? form.querySelector("[data-scan-qr]") : null;
  const fileButton = form ? form.querySelector("[data-scan-qr-file]") : null;
  const reader = panel ? panel.querySelector("[data-qr-reader], .qr-reader") : null;
  const status = panel ? panel.querySelector("[data-qr-status]") : null;
  return { panel, button, fileButton, reader, status };
}

function resetQrPanel(form) {
  const { panel, button, fileButton, reader } = getQrElements(form);
  if (reader) {
    reader.innerHTML = "";
    reader.hidden = false;
  }
  if (panel) {
    panel.hidden = true;
  }
  if (button) {
    button.disabled = false;
  }
  if (fileButton) {
    fileButton.disabled = false;
  }
}

async function stopQrScanner(form) {
  const state = scannerState.get(form);
  if (!state) {
    resetQrPanel(form);
    return;
  }

  state.stopped = true;
  if (state.fileInput) {
    state.fileInput.remove();
  }

  if (state.scanner) {
    if (state.cameraStarted) {
      try {
        await state.scanner.stop();
      } catch (_error) {
        // The library throws if stop is called while it is not scanning.
      }
    }

    try {
      state.scanner.clear();
    } catch (_error) {
      // Clear is best-effort and can fail while startup is still settling.
    }
  }

  scannerState.delete(form);
  resetQrPanel(form);
}

async function fillAndSubmitQrCode(form, input, code) {
  const value = String(code || "").trim();
  if (!value) {
    return false;
  }

  input.value = value;
  await stopQrScanner(form);
  form.requestSubmit();
  return true;
}

function createHtml5QrScanner(reader) {
  if (typeof window.Html5Qrcode !== "function") {
    return null;
  }

  if (!reader.id) {
    reader.id = `qr-reader-${Date.now()}`;
  }

  const formats = window.Html5QrcodeSupportedFormats
    ? { formatsToSupport: [window.Html5QrcodeSupportedFormats.QR_CODE] }
    : {};
  return new window.Html5Qrcode(reader.id, formats);
}

function canUseLiveCamera() {
  const hostname = (location && location.hostname) ? location.hostname : "";
  const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
  return Boolean(
    (window.isSecureContext || isLocalhost)
      && navigator.mediaDevices
      && typeof navigator.mediaDevices.getUserMedia === "function"
  );
}

function markScannerReady(form, scanner, panel, reader, button, fileButton) {
  const state = {
    scanner,
    panel,
    reader,
    button,
    fileButton,
    fileInput: null,
    stopped: false,
    cameraStarted: false,
  };
  scannerState.set(form, state);
  return state;
}

function openQrFileCapture(form, input, scanner, state, status, button, fileButton, reader) {
  // Removed file-based QR capture: camera-only flow is used.
}

async function getPreferredCameraId() {
  const cameras = await window.Html5Qrcode.getCameras();
  if (!cameras || cameras.length === 0) {
    throw new Error("Nenhuma câmera encontrada.");
  }

  const rearCamera = cameras.find((camera) => {
    const label = String(camera.label || "").toLowerCase();
    return (
      label.includes("back")
      || label.includes("rear")
      || label.includes("environment")
      || label.includes("traseira")
      || label.includes("externa")
    );
  });
  return (rearCamera || cameras[cameras.length - 1]).id;
}

function warnIfVideoDoesNotAppear(form, state, status, button, fileButton) {
  window.setTimeout(() => {
    const current = scannerState.get(form);
    const video = state.reader ? state.reader.querySelector("video") : null;
    const videoReady = video && video.videoWidth > 0 && video.videoHeight > 0;
    if (current === state && state.cameraStarted && !state.stopped && !videoReady) {
      status.textContent = "A câmera foi liberada, mas o vídeo não apareceu. Recarregue a página ou digite o token privado do cartão.";
      if (button) button.disabled = false;
      if (fileButton) fileButton.disabled = false;
    }
  }, 1800);
}

async function startQrLiveCamera(form, input, scanner, state, status, button, fileButton) {
  const qrbox = (viewfinderWidth, viewfinderHeight) => {
    const size = Math.floor(Math.min(viewfinderWidth, viewfinderHeight) * 0.78);
    return { width: Math.max(180, size), height: Math.max(180, size) };
  };
  const config = { fps: 12, qrbox };
  const onSuccess = async (decodedText) => {
    const current = scannerState.get(form);
    if (!current || current.stopped) {
      return;
    }
    await fillAndSubmitQrCode(form, input, decodedText);
  };

  if (button) button.disabled = true;
  status.textContent = "Abrindo câmera...";
  const cameraId = await getPreferredCameraId();
  await scanner.start(cameraId, config, onSuccess);
  if (state.stopped || scannerState.get(form) !== state) {
    try {
      await scanner.stop();
    } catch (_error) {
      // If startup was cancelled, stopping is best-effort.
    }
    try {
      scanner.clear();
    } catch (_error) {
      // Ignore clear errors after a cancelled startup.
    }
    return;
  }
  state.cameraStarted = true;
  warnIfVideoDoesNotAppear(form, state, status, button, fileButton);
  status.textContent = "Aponte a câmera para o QR Code do cartão.";
}
 
async function beginQrScan(form, preferFile = false) {
  const input = form.querySelector("#cartao_id");
  const panel = form.querySelector(".qr-scanner");
  const reader = panel.querySelector("[data-qr-reader], .qr-reader");
  const status = panel.querySelector("[data-qr-status]");
  const button = form.querySelector("[data-scan-qr]");

  await stopQrScanner(form);
  panel.hidden = false;
  reader.hidden = false;
  reader.innerHTML = "";

  const scanner = createHtml5QrScanner(reader);
  if (!scanner) {
    status.textContent = "Biblioteca de leitura indisponível. Recarregue a página ou digite o token privado do cartão.";
    return;
  }

  const state = markScannerReady(form, scanner, panel, reader, button, null);
  if (!canUseLiveCamera()) {
    status.textContent = "Câmera indisponível. Digite o token privado do cartão.";
    return;
  }

  try {
    await startQrLiveCamera(form, input, scanner, state, status, button, null);
  } catch (error) {
    console.error("Erro ao abrir câmera:", error);
    const msg = error && error.message ? error.message : "Não foi possível abrir a câmera.";
    status.textContent = `${msg} Recarregue a página ou digite o token privado do cartão.`;
  }
}

document.addEventListener("click", async (event) => {
  const stopButton = event.target.closest("[data-stop-qr]");
  if (stopButton) {
    await stopQrScanner(stopButton.closest("form"));
    return;
  }
  const button = event.target.closest("[data-scan-qr]");
  if (button) {
    await beginQrScan(button.closest("form"));
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".turnstile-form");
  if (form) {
    beginQrScan(form);
  }

  // Converter nome para caixa alta
  const nomeInput = document.getElementById("nome_passageiro");
  if (nomeInput) {
    nomeInput.addEventListener("blur", (e) => {
      e.target.value = e.target.value.toUpperCase();
    });
  }
});
