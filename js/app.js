// Arranque: carga la edición, enruta (#/, #/s/<id>, #/edicion) y dibuja cabecera, menú y pie.
// El modo edición no se muestra al público: se entra con ?editar en la dirección (o Ctrl+Shift+E)
// y, fuera del computador local, exige un token de GitHub con permiso de escritura.

import { renderSeccion } from "./render.js";
import { activarCrucigramas } from "./crucigrama.js";
import { escapar, limpiar, textoPlano, clonar } from "./util.js";

const CLAVE_BORRADOR = "la-cuestion:borrador";
const CLAVE_GITHUB = "la-cuestion:github";
const $ = (sel) => document.querySelector(sel);
const esLocal = ["localhost", "127.0.0.1"].includes(location.hostname);

export const estado = { edicion: null, secciones: {}, servidor: null, editando: false, despuesDePintar: null };

async function cargarJSON(ruta) {
  const respuesta = await fetch(`${ruta}?v=${Date.now()}`, { cache: "no-store" });
  if (!respuesta.ok) throw new Error(`No se pudo cargar ${ruta} (${respuesta.status})`);
  return respuesta.json();
}

export async function cargarServidor() {
  const edicion = await cargarJSON("contenido/edicion.json");
  const secciones = {};
  await Promise.all(edicion.orden.map(async (id) => {
    try {
      secciones[id] = { ...(await cargarJSON(`contenido/secciones/${id}.json`)), id };
    } catch (error) { console.warn(error); }
  }));
  edicion.orden = edicion.orden.filter((id) => secciones[id]);
  return { edicion, secciones };
}

// ---------------------------------------------------------------- borrador local
export function leerBorrador() {
  try { return JSON.parse(localStorage.getItem(CLAVE_BORRADOR) || "null"); } catch { return null; }
}
export function guardarBorrador() {
  try {
    localStorage.setItem(CLAVE_BORRADOR, JSON.stringify({ guardado: new Date().toISOString(), edicion: estado.edicion, secciones: estado.secciones }));
    return true;
  } catch { return false; }            // almacenamiento lleno (imágenes muy grandes) o bloqueado
}
export function descartarBorrador() {
  try { localStorage.removeItem(CLAVE_BORRADOR); } catch { /* sin almacenamiento */ }
}
export const hayCambios = () =>
  JSON.stringify({ e: estado.edicion, s: estado.secciones }) !== JSON.stringify({ e: estado.servidor.edicion, s: estado.servidor.secciones });

/** Este navegador ya se identificó como editor (tiene una conexión de GitHub guardada). */
function esNavegadorEditor() {
  try { return esLocal || !!(localStorage.getItem(CLAVE_GITHUB) || sessionStorage.getItem(CLAVE_GITHUB)); } catch { return esLocal; }
}

// ---------------------------------------------------------------- piezas globales
const campo = (ruta, valor, etiqueta = "span", clase = "") =>
  `<${etiqueta} class="${clase}${limpiar(valor) ? "" : " vacio"}" data-e="${ruta}">${limpiar(valor ?? "")}</${etiqueta}>`;

function pintarCabecera(compacta) {
  const p = estado.edicion.periodico;
  const cab = $("#cabecera");
  cab.className = `cabecera${compacta ? " compacta" : ""}`;
  cab.dataset.raiz = "edicion";
  cab.innerHTML = `
    <div class="cab-izq">${campo("periodico.numero", p.numero, "span", "cab-numero")}${campo("periodico.datos", p.datos, "span", "cab-datos")}</div>
    <a class="cab-centro" href="#/">${campo("periodico.nombre", p.nombre, "span", "cab-nombre")}${campo("periodico.lema", p.lema, "span", "cab-lema")}</a>
    <div class="cab-der">${campo("periodico.edicion", p.edicion)}<br>${campo("periodico.dia", p.dia, "span", "cab-dia")}<br>${campo("periodico.fecha", p.fecha, "strong")}</div>`;
}

function pintarMenu(activa) {
  const visibles = estado.edicion.orden.map((id) => estado.secciones[id]).filter((s) => s && s.visible !== false);
  $("#menu").innerHTML = `
    <ul>${visibles.map((s) => `<li><a href="#/s/${escapar(s.id)}"${s.id === activa ? ' class="activo" aria-current="page"' : ""}>${escapar(textoPlano(s.menu || s.id))}</a></li>`).join("")}
      <li class="menu-extra"><a href="#/edicion"${activa === "#edicion" ? ' class="activo" aria-current="page"' : ""}>Edición completa</a></li></ul>`;
}

function pintarPie() {
  const pie = $("#pie");
  pie.dataset.raiz = "edicion";
  pie.innerHTML = campo("periodico.pie", estado.edicion.periodico.pie, "p");
}

// ---------------------------------------------------------------- enrutado
function vistaActual() {
  const hash = location.hash.replace(/^#\/?/, "");
  if (hash === "edicion") return { tipo: "edicion" };
  const [, id] = hash.match(/^s\/(.+)$/) || [];
  if (id) return { tipo: "seccion", id: decodeURIComponent(id) };
  const portada = estado.edicion.orden.find((x) => estado.secciones[x]?.tipo === "portada") || estado.edicion.orden[0];
  return { tipo: "seccion", id: portada, inicio: true };
}

export function pintar({ mantenerScroll = false } = {}) {
  if (!estado.edicion) return;
  const vista = vistaActual();
  const main = $("#contenido");
  const scroll = window.scrollY;
  if (vista.tipo === "edicion") {
    const visibles = estado.edicion.orden.map((id) => estado.secciones[id]).filter((s) => s && s.visible !== false);
    pintarCabecera(false);
    pintarMenu("#edicion");
    main.innerHTML = visibles.map(renderSeccion).join("");
    document.title = `${textoPlano(estado.edicion.periodico.nombre)} · Edición completa`;
  } else {
    const seccion = estado.secciones[vista.id];
    pintarCabecera(!(seccion?.tipo === "portada"));
    pintarMenu(vista.id);
    main.innerHTML = seccion
      ? renderSeccion(seccion)
      : `<div class="cargando"><p>No existe la sección «${escapar(vista.id)}».</p><p><a class="boton" href="#/">Volver a la portada</a></p></div>`;
    document.title = seccion && !vista.inicio
      ? `${textoPlano(seccion.menu || seccion.id)} · ${textoPlano(estado.edicion.periodico.nombre)}`
      : `${textoPlano(estado.edicion.periodico.nombre)} · ${textoPlano(estado.edicion.periodico.lema)}`;
  }
  pintarPie();
  if (mantenerScroll) window.scrollTo(0, scroll);
  estado.despuesDePintar?.();
}

// ---------------------------------------------------------------- acceso de editores
export const api = { estado, pintar, guardarBorrador, descartarBorrador, leerBorrador, hayCambios, cargarServidor };

async function pedirAcceso() {
  const { solicitarAcceso } = await import("./editor.js");
  solicitarAcceso(api);
}

function avisoBorrador(borrador) {
  const fecha = new Date(borrador.guardado).toLocaleString("es-CO", { dateStyle: "long", timeStyle: "short" });
  const aviso = document.createElement("div");
  aviso.className = "aviso-borrador";
  aviso.setAttribute("role", "status");
  aviso.innerHTML = `<p>Hay un <strong>borrador sin publicar</strong> guardado en este navegador (${escapar(fecha)}).</p>
    <div><button class="boton primario" data-b="usar">Ver y seguir editando</button> <button class="boton" data-b="descartar">Descartar borrador</button></div>`;
  document.body.prepend(aviso);
  aviso.addEventListener("click", (e) => {
    const accion = e.target.closest("[data-b]")?.dataset.b;
    if (!accion) return;
    if (accion === "usar") {
      estado.edicion = borrador.edicion;
      estado.secciones = borrador.secciones;
      pintar();
      pedirAcceso();
    } else descartarBorrador();
    aviso.remove();
  });
}

async function iniciar() {
  try {
    const datos = await cargarServidor();
    estado.servidor = clonar(datos);
    estado.edicion = datos.edicion;
    estado.secciones = datos.secciones;
  } catch (error) {
    $("#contenido").innerHTML = `<div class="cargando"><p>No se pudo cargar el contenido.</p><p>${escapar(error.message)}</p>
      <p>Si abriste el archivo directamente, usa un servidor local (ver README) o publícalo en GitHub Pages.</p></div>`;
    return;
  }
  activarCrucigramas(document.body);
  window.addEventListener("hashchange", () => { pintar(); window.scrollTo(0, 0); $("#contenido").focus({ preventScroll: true }); });
  window.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "e" && !estado.editando) { e.preventDefault(); pedirAcceso(); }
  });
  pintar();
  const borrador = leerBorrador();
  const distinto = borrador && JSON.stringify({ e: borrador.edicion, s: borrador.secciones }) !== JSON.stringify({ e: estado.edicion, s: estado.secciones });
  if (distinto && esNavegadorEditor()) avisoBorrador(borrador);
  if (new URLSearchParams(location.search).has("editar")) pedirAcceso();
}

iniciar();
