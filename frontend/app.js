/**
 * app.js — Lógica del frontend del Agente de Research
 *
 * Maneja:
 * - Envío del formulario de investigación
 * - Estados de UI (cargando, error, resultado)
 * - Renderizado del informe en el DOM
 * - Tabs de navegación
 */

"use strict";

// URL base de la API — al usar nginx como proxy, /api/ apunta al backend
const API_BASE = "/api";

// Referencias a elementos del DOM
const formResearch = document.getElementById("form-research");
const inputTema = document.getElementById("input-tema");
const btnInvestigar = document.getElementById("btn-investigar");
const contadorChars = document.getElementById("contador-chars");

const seccionCargando = document.getElementById("seccion-cargando");
const cargandoEstado = document.getElementById("cargando-estado");
const seccionError = document.getElementById("seccion-error");
const errorMensaje = document.getElementById("error-mensaje");
const seccionInforme = document.getElementById("seccion-informe");

// ─────────────────────────────────────────────────────────────────────────────
// INICIALIZACIÓN
// ─────────────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  configurarFormulario();
  configurarTabs();
  configurarContadorChars();
});

// ─────────────────────────────────────────────────────────────────────────────
// FORMULARIO
// ─────────────────────────────────────────────────────────────────────────────

function configurarFormulario() {
  formResearch.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const tema = inputTema.value.trim();
    if (!tema) return;

    await ejecutarInvestigacion(tema);
  });
}

async function ejecutarInvestigacion(tema) {
  // Mostrar estado de carga
  mostrarCargando(true);
  ocultarError();
  ocultarInforme();
  deshabilitarFormulario(true);

  // Simular progreso visual
  const intervaloProgreso = simularProgreso();

  try {
    const inicio = Date.now();

    const respuesta = await fetch(`${API_BASE}/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tema }),
    });

    clearInterval(intervaloProgreso);

    if (!respuesta.ok) {
      const datos = await respuesta.json().catch(() => ({}));
      throw new Error(datos.detail || `Error del servidor: ${respuesta.status}`);
    }

    const datos = await respuesta.json();
    const duracion = ((Date.now() - inicio) / 1000).toFixed(1);

    // Marcar paso 3 como activo y luego mostrar el informe
    marcarPaso(3, "activo");
    await esperar(400);

    mostrarCargando(false);
    renderizarInforme(datos.informe, duracion);

  } catch (error) {
    clearInterval(intervaloProgreso);
    mostrarCargando(false);
    mostrarError(error.message || "Error inesperado. Intentá de nuevo.");
    console.error("Error en investigación:", error);

  } finally {
    deshabilitarFormulario(false);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// RENDERIZADO DEL INFORME
// ─────────────────────────────────────────────────────────────────────────────

function renderizarInforme(informe, duracion) {
  // Encabezado
  document.getElementById("informe-tema").textContent = informe.tema;
  document.getElementById("informe-fecha").textContent = formatearFecha(informe.fecha_creacion);
  document.getElementById("informe-duracion").textContent = `Generado en ${duracion}s`;

  // Botón PDF
  const btnPdf = document.getElementById("btn-pdf");
  if (informe.url_pdf) {
    btnPdf.href = informe.url_pdf;
    btnPdf.style.display = "inline-flex";
  } else {
    btnPdf.style.display = "none";
  }

  // Banner de sentimiento
  renderizarSentimiento(informe.analisis_sentimiento);

  // Resumen ejecutivo
  const resumenDiv = document.getElementById("contenido-resumen");
  resumenDiv.innerHTML = informe.resumen_ejecutivo
    .split("\n\n")
    .filter((p) => p.trim())
    .map((p) => `<p>${escaparHTML(p.trim())}</p>`)
    .join("");

  // Puntos a favor y en contra
  document.getElementById("lista-pros").innerHTML = informe.puntos_a_favor
    .map((p) => `<li>${escaparHTML(p)}</li>`)
    .join("") || "<li>Sin información disponible</li>";

  document.getElementById("lista-contras").innerHTML = informe.puntos_en_contra
    .map((c) => `<li>${escaparHTML(c)}</li>`)
    .join("") || "<li>Sin información disponible</li>";

  // Conclusiones y recomendaciones
  document.getElementById("contenido-conclusiones").innerHTML = informe.conclusiones
    .split("\n\n")
    .filter((p) => p.trim())
    .map((p) => `<p>${escaparHTML(p.trim())}</p>`)
    .join("");

  document.getElementById("lista-recomendaciones").innerHTML = informe.recomendaciones
    .map((r) => `<li>${escaparHTML(r)}</li>`)
    .join("") || "<li>Sin recomendaciones específicas</li>";

  // Fuentes
  renderizarFuentes(informe.fuentes);

  // Mostrar sección y activar primer tab
  seccionInforme.classList.remove("oculto");
  activarTab("resumen");

  // Scroll suave hacia el informe
  seccionInforme.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderizarSentimiento(sentimiento) {
  const badge = document.getElementById("sentimiento-badge");
  badge.textContent = sentimiento.clasificacion;
  badge.className = `sentimiento-badge ${sentimiento.clasificacion}`;

  document.getElementById("sentimiento-justificacion").textContent =
    sentimiento.justificacion;

  // Barra de progreso: puntaje de -1.0 a 1.0 → 0% a 100%
  const porcentaje = Math.round((sentimiento.puntaje + 1.0) / 2.0 * 100);
  const colores = {
    positivo: "#27ae60",
    negativo: "#e74c3c",
    neutro: "#f39c12",
  };
  const color = colores[sentimiento.clasificacion] || "#7f8c8d";

  const barra = document.getElementById("sentimiento-barra");
  barra.style.setProperty("--puntaje", `${porcentaje}%`);
  barra.style.setProperty("background", `
    linear-gradient(to right,
      var(--gris-borde) 0%,
      var(--gris-borde) ${porcentaje}%
    )
  `);
  barra.style.cssText += `--color-barra: ${color};`;

  // Sobreescribir el ::after de CSS con el color correcto via inline style
  const style = document.createElement("style");
  style.textContent = `.sentimiento-barra::after { background: ${color} !important; width: ${porcentaje}% !important; }`;
  document.head.appendChild(style);
}

function renderizarFuentes(fuentes) {
  const contenedor = document.getElementById("tabla-fuentes");

  if (!fuentes || fuentes.length === 0) {
    contenedor.innerHTML = "<p>No hay fuentes disponibles.</p>";
    return;
  }

  const filas = fuentes
    .map(
      (f, i) => `
    <tr>
      <td class="fuente-num">${i + 1}</td>
      <td>${escaparHTML(f.titulo)}</td>
      <td><a href="${escaparAtrib(f.url)}" target="_blank" rel="noopener noreferrer">${escaparHTML(recortarUrl(f.url))}</a></td>
      <td class="fuente-fecha">${formatearFecha(f.fecha_consulta)}</td>
    </tr>`
    )
    .join("");

  contenedor.innerHTML = `
    <table class="tabla-fuentes">
      <thead>
        <tr>
          <th>#</th>
          <th>Título</th>
          <th>URL</th>
          <th>Fecha de Consulta</th>
        </tr>
      </thead>
      <tbody>${filas}</tbody>
    </table>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// TABS
// ─────────────────────────────────────────────────────────────────────────────

function configurarTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      activarTab(tab.dataset.tab);
    });
  });
}

function activarTab(nombre) {
  // Actualizar botones
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("activo", t.dataset.tab === nombre);
  });

  // Mostrar/ocultar paneles
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("oculto", panel.id !== `tab-${nombre}`);
    panel.classList.toggle("activo", panel.id === `tab-${nombre}`);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// ESTADOS DE UI
// ─────────────────────────────────────────────────────────────────────────────

function mostrarCargando(mostrar) {
  seccionCargando.classList.toggle("oculto", !mostrar);

  if (mostrar) {
    // Resetear pasos de progreso
    [1, 2, 3].forEach((n) => marcarPaso(n, ""));
    marcarPaso(1, "activo");
    cargandoEstado.textContent = "Generando consultas de búsqueda...";
  }
}

function ocultarError() {
  seccionError.classList.add("oculto");
}

function ocultarInforme() {
  seccionInforme.classList.add("oculto");
}

function mostrarError(mensaje) {
  errorMensaje.textContent = mensaje;
  seccionError.classList.remove("oculto");
  seccionError.scrollIntoView({ behavior: "smooth", block: "start" });
}

function deshabilitarFormulario(deshabilitar) {
  inputTema.disabled = deshabilitar;
  btnInvestigar.disabled = deshabilitar;
  btnInvestigar.querySelector(".btn-texto").textContent = deshabilitar
    ? "Investigando..."
    : "Investigar";
}

// Simula el progreso de los pasos mientras espera la respuesta
function simularProgreso() {
  let paso = 1;
  return setInterval(() => {
    paso = Math.min(paso + 1, 3);
    marcarPaso(paso - 1, "completo");
    marcarPaso(paso, "activo");

    const mensajes = [
      "Generando consultas de búsqueda...",
      "Buscando en la web...",
      "Analizando y sintetizando...",
    ];
    cargandoEstado.textContent = mensajes[paso - 1] || "Procesando...";
  }, 8000); // Avanza cada 8 segundos (aprox. para Ollama local)
}

function marcarPaso(numero, estado) {
  const paso = document.getElementById(`paso-${numero}`);
  if (!paso) return;
  paso.className = `paso ${estado}`.trim();
}

// ─────────────────────────────────────────────────────────────────────────────
// CONTADOR DE CARACTERES
// ─────────────────────────────────────────────────────────────────────────────

function configurarContadorChars() {
  inputTema.addEventListener("input", () => {
    const largo = inputTema.value.length;
    contadorChars.textContent = `${largo} / 500`;
    contadorChars.style.color = largo > 450 ? "#e74c3c" : "#adb5bd";
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// FUNCIÓN PÚBLICA — llamada desde el HTML (botón "Nueva búsqueda")
// ─────────────────────────────────────────────────────────────────────────────

function reiniciar() {
  ocultarInforme();
  ocultarError();
  inputTema.value = "";
  contadorChars.textContent = "0 / 500";
  inputTema.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ─────────────────────────────────────────────────────────────────────────────
// UTILIDADES
// ─────────────────────────────────────────────────────────────────────────────

function escaparHTML(texto) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(String(texto)));
  return div.innerHTML;
}

function escaparAtrib(texto) {
  return String(texto)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatearFecha(isoString) {
  if (!isoString) return "";
  try {
    return new Date(isoString).toLocaleString("es-AR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}

function recortarUrl(url) {
  if (!url) return "";
  try {
    const u = new URL(url);
    const ruta = u.pathname.length > 30 ? u.pathname.slice(0, 30) + "..." : u.pathname;
    return u.hostname + ruta;
  } catch {
    return url.length > 60 ? url.slice(0, 60) + "..." : url;
  }
}

function esperar(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
