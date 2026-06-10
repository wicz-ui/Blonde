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
  return Boolean(
    window.isSecureContext
      && navigator.mediaDevices
      && typeof navigator.mediaDevices.getUserMedia === "function",
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
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.setAttribute("capture", "environment");
  fileInput.hidden = true;
  document.body.appendChild(fileInput);
  state.fileInput = fileInput;

  button.disabled = false;
  fileButton.disabled = true;
  reader.hidden = true;
  status.textContent = "A câmera será aberta. Fotografe o QR Code de perto, ocupando boa parte da tela.";

  const keepCancelAvailable = () => {
    window.setTimeout(() => {
      const current = scannerState.get(form);
      const hasSelectedFile = fileInput.files && fileInput.files.length > 0;
      if (current === state && !current.stopped && !hasSelectedFile) {
        button.disabled = false;
        fileButton.disabled = false;
        status.textContent = "Leitura cancelada. Toque em escanear novamente ou digite o código público.";
      }
    }, 500);
  };

  fileInput.addEventListener("change", async () => {
    const current = scannerState.get(form);
    if (!current || current.stopped) {
      return;
    }

    const file = fileInput.files && fileInput.files[0];
    if (!file) {
      status.textContent = "Leitura cancelada. Toque em escanear novamente ou digite o código público.";
      return;
    }

    try {
      status.textContent = "Lendo QR Code da imagem capturada...";
      const code = await scanner.scanFile(file, false);
      if (!(await fillAndSubmitQrCode(form, input, code))) {
        status.textContent = "QR Code não encontrado. Fotografe mais perto, com foco e sem reflexo.";
        button.disabled = false;
        fileButton.disabled = false;
      }
    } catch (_error) {
      status.textContent = "Não foi possível ler o QR Code. Fotografe mais perto ou digite o código público.";
      button.disabled = false;
      fileButton.disabled = false;
    } finally {
      fileInput.remove();
      state.fileInput = null;
    }
  });

  fileInput.addEventListener("cancel", () => {
    fileButton.disabled = false;
    status.textContent = "Leitura cancelada. Toque em escanear novamente ou digite o código público.";
  });

  window.addEventListener("focus", keepCancelAvailable, { once: true });
  fileInput.click();
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
      status.textContent = "A câmera foi liberada, mas o vídeo não apareceu. Toque em usar foto do QR Code ou recarregue a página.";
      button.disabled = false;
      fileButton.disabled = false;
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

  button.disabled = true;
  fileButton.disabled = false;
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
  const fileButton = form.querySelector("[data-scan-qr-file]");

  await stopQrScanner(form);
  panel.hidden = false;
  reader.hidden = false;
  reader.innerHTML = "";

  const scanner = createHtml5QrScanner(reader);
  if (!scanner) {
    status.textContent = "Biblioteca de leitura indisponível. Recarregue a página ou digite o código público.";
    return;
  }

  const state = markScannerReady(form, scanner, panel, reader, button, fileButton);
  if (preferFile || !canUseLiveCamera()) {
    openQrFileCapture(form, input, scanner, state, status, button, fileButton, reader);
    return;
  }

  try {
    await startQrLiveCamera(form, input, scanner, state, status, button, fileButton);
  } catch (_error) {
    openQrFileCapture(form, input, scanner, state, status, button, fileButton, reader);
  }
}

document.addEventListener("click", async (event) => {
  const stopButton = event.target.closest("[data-stop-qr]");
  if (stopButton) {
    await stopQrScanner(stopButton.closest("form"));
    return;
  }

  const fileButton = event.target.closest("[data-scan-qr-file]");
  if (fileButton) {
    await beginQrScan(fileButton.closest("form"), true);
    return;
  }

  const button = event.target.closest("[data-scan-qr]");
  if (button) {
    await beginQrScan(button.closest("form"), false);
  }
});
