// Modo edición: textos en el propio periódico, listas, imágenes, enlaces, secciones y publicación.

import { limpiar, leer, escribir, clonar, slug, retrasar, escapar, textoPlano } from "./util.js";
import { TIPOS } from "./render.js";
import { PLANTILLAS, elementoNuevo } from "./plantillas.js";
import { prepararArchivos, crearZip, publicarEnGitHub, probarConexion, detectarRepositorio } from "./github.js";
import { cifrarAcceso, abrirAcceso } from "./acceso.js";

const CLAVE_GITHUB = "la-cuestion:github";
const MARCADORES = {
  titulo: "Titular", antetitulo: "Antetítulo", subtitulo: "Subtítulo", entradilla: "Entradilla", firma: "Firma",
  pie: "Pie de foto", cita: "Cita destacada", ladillo: "Subtítulo interno", texto: "Texto", personaje: "Personaje (vacío = narrador)",
  termino: "Concepto", definicion: "Definición", cifra: "Cifra", pregunta: "Pregunta guía", palabra: "PALABRA", pista: "Pista",
};

let api = null;
let control = null;          // AbortController de los eventos del editor
let barra = null;
let flotante = null;
let historial = [];
let instantaneaPendiente = null;
const $ = (sel, raiz = document) => raiz.querySelector(sel);

// ---------------------------------------------------------------- estado y cambios
function raizDe(elemento) {
  const marca = elemento.closest("[data-raiz]")?.dataset.raiz || "";
  if (marca === "edicion") return { objeto: api.estado.edicion, marca };
  const id = marca.replace(/^seccion:/, "");
  return { objeto: api.estado.secciones[id], marca, id };
}

const instantanea = () => clonar({ edicion: api.estado.edicion, secciones: api.estado.secciones });

function recordar(foto = instantanea()) {
  historial.push(foto);
  if (historial.length > 60) historial.shift();
}

const autoguardar = retrasar(() => {
  if (!api.hayCambios()) { api.descartarBorrador(); actualizarEstado(); return; }
  if (!api.guardarBorrador()) avisar("No se pudo guardar el borrador en este navegador (¿imágenes muy pesadas?). Descarga el ZIP para no perder cambios.", true);
  actualizarEstado();
}, 700);

/** Cambio estructural: guarda historial, aplica y vuelve a pintar. */
function cambio(funcion, { foco } = {}) {
  recordar();
  funcion();
  autoguardar();
  api.pintar({ mantenerScroll: true });
  if (foco) enfocar(foco.marca, foco.ruta);
}

function enfocar(marca, ruta) {
  const raiz = document.querySelector(`[data-raiz="${marca}"]`);
  const destino = raiz?.querySelector(`[data-item="${ruta}"]`);
  const campo = destino?.matches("[data-e]") ? destino : destino?.querySelector("[data-e]");
  campo?.focus();
  destino?.scrollIntoView({ block: "center", behavior: "smooth" });
}

function actualizarEstado() {
  const texto = $(".estado-edicion", barra || document);
  if (!texto) return;
  texto.textContent = api.hayCambios() ? "Cambios guardados en este navegador · sin publicar" : "Sin cambios pendientes";
}

function avisar(mensaje, error = false) {
  document.querySelectorAll(".aviso-flotante").forEach((x) => x.remove());
  const aviso = document.createElement("div");
  aviso.className = `aviso-flotante${error ? " error" : ""}`;
  aviso.setAttribute("role", error ? "alert" : "status");
  aviso.textContent = mensaje;
  document.body.append(aviso);
  setTimeout(() => aviso.remove(), error ? 9000 : 4500);
}

// ---------------------------------------------------------------- preparar el DOM pintado
function prepararDOM() {
  document.querySelectorAll("[data-e]").forEach((campo) => {
    campo.contentEditable = "true";
    campo.spellcheck = true;
    const clave = campo.dataset.e.split(".").filter((p) => !/^\d+$/.test(p)).pop();
    campo.dataset.ph = MARCADORES[clave] || "Escribe aquí";
  });
  document.querySelectorAll("[data-lista]").forEach((lista) => {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "agregar-item";
    boton.dataset.agregar = lista.dataset.lista;
    const clave = lista.dataset.lista.split(".").filter((p) => !/^\d+$/.test(p)).pop();
    boton.textContent = `+ Añadir ${{ filas: "fila", parrafos: "párrafo", columnas: "párrafo", cronica: "párrafo", lente: "párrafo",
      punto_ciego: "párrafo", terminos: "concepto", vinetas: "viñeta", textos: "cartela", tarjetas: "tarjeta", palabras: "palabra",
      fuentes: "fuente", referencias: "referencia", datos: "dato", sumario: "punto", items: "paso" }[clave] || "elemento"}`;
    const ancla = lista.tagName === "TBODY" ? lista.closest(".tabla-envoltura") : lista;
    ancla.after(boton);
  });
  flotante?.remove();
  flotante = null;
  actualizarEstado();
}

// ---------------------------------------------------------------- controles de elementos de lista
function mostrarControl(item) {
  if (!flotante) {
    flotante = document.createElement("div");
    flotante.className = "control-item";
    flotante.innerHTML = `<button type="button" data-c="subir" aria-label="Subir" title="Subir">↑</button>
      <button type="button" data-c="bajar" aria-label="Bajar" title="Bajar">↓</button>
      <button type="button" data-c="duplicar" aria-label="Duplicar" title="Duplicar">⧉</button>
      <button type="button" data-c="eliminar" aria-label="Eliminar" title="Eliminar">✕</button>`;
    document.body.append(flotante);
  }
  document.querySelectorAll(".item-actual").forEach((x) => x.classList.remove("item-actual"));
  item.classList.add("item-actual");
  flotante.dataset.ruta = item.dataset.item;
  flotante.dataset.marca = raizDe(item).marca;
  const r = item.getBoundingClientRect();
  const ancho = 130;
  flotante.style.left = `${Math.max(8, Math.min(window.scrollX + r.right - ancho, window.scrollX + document.documentElement.clientWidth - ancho - 8))}px`;
  flotante.style.top = `${Math.max(8, window.scrollY + r.top - 32)}px`;
}

function accionElemento(accion) {
  const { ruta, marca } = flotante.dataset;
  const raiz = document.querySelector(`[data-raiz="${marca}"]`);
  const { objeto } = raizDe(raiz);
  const partes = ruta.split(".");
  const indice = Number(partes.pop());
  const rutaLista = partes.join(".");
  const lista = leer(objeto, rutaLista);
  if (!Array.isArray(lista)) return;
  if (accion === "eliminar") {
    const texto = textoPlano(JSON.stringify(lista[indice])).slice(0, 80);
    if (!confirm(`¿Eliminar este elemento?\n\n${texto}`)) return;
    cambio(() => lista.splice(indice, 1));
  } else if (accion === "duplicar") {
    cambio(() => lista.splice(indice + 1, 0, clonar(lista[indice])), { foco: { marca, ruta: `${rutaLista}.${indice + 1}` } });
  } else {
    const destino = accion === "subir" ? indice - 1 : indice + 1;
    if (destino < 0 || destino >= lista.length) return;
    cambio(() => { [lista[indice], lista[destino]] = [lista[destino], lista[indice]]; }, { foco: { marca, ruta: `${rutaLista}.${destino}` } });
  }
}

// ---------------------------------------------------------------- diálogos
function dialogo(titulo, cuerpo, pie, { ancho = false } = {}) {
  const dlg = document.createElement("dialog");
  dlg.className = `dialogo${ancho ? " ancho" : ""}`;
  dlg.innerHTML = `<header><span>${escapar(titulo)}</span><button type="button" data-cerrar aria-label="Cerrar">×</button></header>
    <div class="cuerpo-dialogo">${cuerpo}</div><footer>${pie}</footer>`;
  document.body.append(dlg);
  dlg.addEventListener("click", (e) => { if (e.target.closest("[data-cerrar]")) dlg.close(); });
  dlg.addEventListener("close", () => dlg.remove());
  dlg.showModal();
  return dlg;
}

async function comprimirImagen(archivo) {
  if (archivo.type === "image/svg+xml" || archivo.type === "image/gif") {
    return new Promise((ok) => { const lector = new FileReader(); lector.onload = () => ok(lector.result); lector.readAsDataURL(archivo); });
  }
  const mapa = await createImageBitmap(archivo);
  const escala = Math.min(1, 1600 / mapa.width);
  const lienzo = document.createElement("canvas");
  lienzo.width = Math.round(mapa.width * escala);
  lienzo.height = Math.round(mapa.height * escala);
  lienzo.getContext("2d").drawImage(mapa, 0, 0, lienzo.width, lienzo.height);
  const webp = lienzo.toDataURL("image/webp", 0.85);
  return webp.startsWith("data:image/webp") ? webp : lienzo.toDataURL("image/jpeg", 0.85);
}

function dialogoImagen(img) {
  const { objeto } = raizDe(img);
  const ruta = img.dataset.img;
  let valor = leer(objeto, ruta) || "";
  const dlg = dialogo("Imagen", `
    <img class="vista-imagen" alt="Vista previa" src="${escapar(valor)}">
    <label for="img-archivo">Subir una imagen desde el computador</label>
    <input id="img-archivo" type="file" accept="image/*">
    <p class="ayuda">Se reduce a 1600 px de ancho. Al publicar en GitHub se guarda en <code>imagenes/subidas/</code>.</p>
    <label for="img-url">O escribe la ruta o dirección de la imagen</label>
    <input id="img-url" type="text" placeholder="imagenes/portada_principal.webp o https://…" value="${valor.startsWith("data:") ? "" : escapar(valor)}">
    <p class="ayuda" id="img-info">${valor.startsWith("data:") ? `Imagen subida (${Math.round(valor.length * 0.75 / 1024)} KB).` : ""}</p>`,
    `<button class="boton" type="button" data-quitar>Quitar imagen</button><button class="boton" type="button" data-cerrar>Cancelar</button>
     <button class="boton primario" type="button" data-guardar>Guardar</button>`);
  const vista = $(".vista-imagen", dlg);
  $("#img-archivo", dlg).addEventListener("change", async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    try {
      valor = await comprimirImagen(archivo);
      vista.src = valor;
      $("#img-url", dlg).value = "";
      $("#img-info", dlg).textContent = `Imagen subida (${Math.round(valor.length * 0.75 / 1024)} KB).`;
    } catch { $("#img-info", dlg).textContent = "No se pudo leer esa imagen."; }
  });
  $("#img-url", dlg).addEventListener("input", (e) => { valor = e.target.value.trim(); vista.src = valor; $("#img-info", dlg).textContent = ""; });
  dlg.addEventListener("click", (e) => {
    if (e.target.closest("[data-quitar]")) valor = "";
    else if (!e.target.closest("[data-guardar]")) return;
    cambio(() => escribir(objeto, ruta, valor));
    dlg.close();
  });
}

function opcionesSecciones(actual = "") {
  return api.estado.edicion.orden.map((id) =>
    `<option value="${escapar(id)}"${id === actual ? " selected" : ""}>${escapar(textoPlano(api.estado.secciones[id].menu || id))}</option>`).join("");
}

function dialogoEnlace(enlace) {
  const { objeto } = raizDe(enlace);
  const ruta = enlace.dataset.enlace;
  const actual = leer(objeto, ruta) || "";
  const externo = /^(https?:|#)/.test(actual);
  const dlg = dialogo("Enlace", `
    <label for="enl-seccion">Llevar a una sección del periódico</label>
    <select id="enl-seccion"><option value="">— Sin enlace —</option>${opcionesSecciones(externo ? "" : actual)}</select>
    <label for="enl-url">O a una dirección externa</label>
    <input id="enl-url" type="url" placeholder="https://…" value="${externo ? escapar(actual) : ""}">`,
    `<button class="boton" type="button" data-cerrar>Cancelar</button><button class="boton primario" type="button" data-guardar>Guardar</button>`);
  dlg.addEventListener("click", (e) => {
    if (!e.target.closest("[data-guardar]")) return;
    const url = $("#enl-url", dlg).value.trim();
    cambio(() => escribir(objeto, ruta, url || $("#enl-seccion", dlg).value));
    dlg.close();
  });
}

function panelSecciones({ nueva = false } = {}) {
  const dlg = dialogo("Secciones del periódico", "", `<button class="boton primario" type="button" data-cerrar>Listo</button>`, { ancho: true });
  const cuerpo = $(".cuerpo-dialogo", dlg);
  const pintarPanel = () => {
    const { orden } = api.estado.edicion;
    cuerpo.innerHTML = `
      <p class="ayuda">Ordena, renombra, oculta o elimina secciones. El nombre es el que aparece en el menú.</p>
      <table class="tabla-secciones"><thead><tr><th>Orden</th><th>Nombre en el menú</th><th>Tipo</th><th>Visible</th><th>Acciones</th></tr></thead><tbody>
      ${orden.map((id, i) => { const s = api.estado.secciones[id]; return `<tr data-id="${escapar(id)}">
        <td class="acciones"><button type="button" data-p="subir" aria-label="Subir"${i ? "" : " disabled"}>↑</button> <button type="button" data-p="bajar" aria-label="Bajar"${i < orden.length - 1 ? "" : " disabled"}>↓</button></td>
        <td><input type="text" data-p="menu" value="${escapar(textoPlano(s.menu || ""))}" aria-label="Nombre en el menú"><small>/s/${escapar(id)}</small></td>
        <td>${escapar(TIPOS[s.tipo]?.nombre || s.tipo)}</td>
        <td><input type="checkbox" data-p="visible"${s.visible !== false ? " checked" : ""} aria-label="Visible"></td>
        <td class="acciones"><button type="button" data-p="ir">Ir</button> <button type="button" data-p="duplicar">Duplicar</button> <button type="button" data-p="eliminar">Eliminar</button></td>
      </tr>`; }).join("")}
      </tbody></table>
      <form class="nueva-seccion">
        <div><label for="nueva-tipo">Nueva sección · tipo</label><select id="nueva-tipo">
          ${Object.entries(TIPOS).map(([k, t]) => `<option value="${k}"${k === "columna" ? " selected" : ""}>${escapar(t.nombre)}</option>`).join("")}</select></div>
        <div><label for="nueva-nombre">Nombre en el menú</label><input id="nueva-nombre" type="text" required placeholder="Ej.: Columna 6"></div>
        <button class="boton primario" type="submit">Crear sección</button>
      </form>`;
  };
  pintarPanel();
  cuerpo.addEventListener("change", (e) => {
    const fila = e.target.closest("tr[data-id]");
    if (!fila) return;
    const s = api.estado.secciones[fila.dataset.id];
    if (e.target.dataset.p === "menu") cambio(() => { s.menu = e.target.value.trim() || s.id; });
    if (e.target.dataset.p === "visible") cambio(() => { s.visible = e.target.checked; });
  });
  cuerpo.addEventListener("click", (e) => {
    const accion = e.target.closest("button[data-p]")?.dataset.p;
    const id = e.target.closest("tr[data-id]")?.dataset.id;
    if (!accion || !id) return;
    const { orden } = api.estado.edicion;
    const i = orden.indexOf(id);
    if (accion === "ir") { dlg.close(); location.hash = `#/s/${id}`; return; }
    if (accion === "subir" || accion === "bajar") {
      const j = accion === "subir" ? i - 1 : i + 1;
      cambio(() => { [orden[i], orden[j]] = [orden[j], orden[i]]; });
    } else if (accion === "duplicar") {
      const nuevoId = idUnico(`${id}-copia`);
      cambio(() => { api.estado.secciones[nuevoId] = { ...clonar(api.estado.secciones[id]), id: nuevoId, menu: `${textoPlano(api.estado.secciones[id].menu)} (copia)` }; orden.splice(i + 1, 0, nuevoId); });
    } else if (accion === "eliminar") {
      if (orden.length === 1) return avisar("El periódico necesita al menos una sección.", true);
      if (!confirm(`¿Eliminar la sección «${textoPlano(api.estado.secciones[id].menu || id)}»? Podrás deshacerlo mientras no publiques.`)) return;
      cambio(() => { orden.splice(i, 1); delete api.estado.secciones[id]; });
      if (location.hash === `#/s/${id}`) location.hash = "#/";
    }
    pintarPanel();
  });
  cuerpo.addEventListener("submit", (e) => {
    e.preventDefault();
    const tipo = $("#nueva-tipo", cuerpo).value;
    const nombre = $("#nueva-nombre", cuerpo).value.trim();
    if (!nombre) return;
    const id = idUnico(slug(nombre));
    const vista = decodeURIComponent((location.hash.match(/^#\/s\/(.+)$/) || [])[1] || "");
    const { orden } = api.estado.edicion;
    const posicion = orden.includes(vista) ? orden.indexOf(vista) + 1 : orden.length;
    cambio(() => {
      api.estado.secciones[id] = { ...PLANTILLAS[tipo](), id, menu: nombre };
      orden.splice(posicion, 0, id);
    });
    dlg.close();
    location.hash = `#/s/${id}`;
    avisar(`Sección «${nombre}» creada. Haz clic en cualquier texto para escribir.`);
  });
  if (nueva) $("#nueva-tipo", cuerpo).focus();
}

function idUnico(base) {
  let id = base || "seccion", n = 2;
  while (api.estado.secciones[id]) id = `${base}-${n++}`;
  return id;
}

// ---------------------------------------------------------------- GitHub y descarga
function leerConfig() {
  let guardada = {};
  try { guardada = JSON.parse(localStorage.getItem(CLAVE_GITHUB) || sessionStorage.getItem(CLAVE_GITHUB) || "{}"); } catch { /* nada */ }
  return { rama: "main", ...detectarRepositorio(), ...guardada };
}

function guardarConfig(config, recordarToken) {
  try {
    localStorage.removeItem(CLAVE_GITHUB); sessionStorage.removeItem(CLAVE_GITHUB);
    (recordarToken ? localStorage : sessionStorage).setItem(CLAVE_GITHUB, JSON.stringify(config));
  } catch { /* sin almacenamiento: la configuración dura solo esta página */ }
}

function dialogoGitHub(despues) {
  const c = leerConfig();
  const dlg = dialogo("Administrador · Conexión con GitHub", `
    <p class="ayuda">Solo para quien administra el repositorio. Crea un token <em>fine-grained</em> con permiso
      <em>Contents: Read and write</em> únicamente sobre este repositorio y con fecha de vencimiento.</p>
    <label for="gh-propietario">Usuario u organización</label><input id="gh-propietario" type="text" value="${escapar(c.propietario || "")}" placeholder="mi-usuario">
    <label for="gh-repo">Repositorio</label><input id="gh-repo" type="text" value="${escapar(c.repositorio || "")}" placeholder="lacuestion">
    <label for="gh-rama">Rama publicada</label><input id="gh-rama" type="text" value="${escapar(c.rama || "main")}">
    <label for="gh-token">Token</label><input id="gh-token" type="password" value="${escapar(c.token || "")}" placeholder="github_pat_…" autocomplete="off">
    <label><input id="gh-recordar" type="checkbox"${localStorage.getItem(CLAVE_GITHUB) ? " checked" : ""}> Recordar en este navegador (no lo marques en computadores compartidos)</label>
    <div class="caja" style="margin-top:1rem">
      <h3 class="caja-titulo">Clave para la mesa de redacción</h3>
      <p class="ayuda">Tus compañeros entrarán con <code>?editar</code> y esta clave, sin cuenta de GitHub. La conexión se guarda
        cifrada en <code>contenido/acceso.json</code>. Usa una frase larga (mínimo 12 caracteres) y compártela solo con el grupo.
        Para cambiarla o quitarle el acceso a alguien, crea una clave nueva.</p>
      <label for="gh-clave">Clave del grupo</label><input id="gh-clave" type="password" autocomplete="new-password">
      <label for="gh-clave2">Repite la clave</label><input id="gh-clave2" type="password" autocomplete="new-password">
      <p><button class="boton" type="button" data-crear-acceso>Guardar la clave del grupo en GitHub</button></p>
    </div>
    <p id="gh-resultado" aria-live="polite"></p>`,
    `<button class="boton" type="button" data-probar>Probar conexión</button><button class="boton" type="button" data-cerrar>Cancelar</button>
     <button class="boton primario" type="button" data-guardar>Guardar y entrar</button>`);
  const valores = () => ({ propietario: $("#gh-propietario", dlg).value.trim(), repositorio: $("#gh-repo", dlg).value.trim(),
    rama: $("#gh-rama", dlg).value.trim() || "main", token: $("#gh-token", dlg).value.trim() });
  dlg.addEventListener("click", async (e) => {
    const resultado = $("#gh-resultado", dlg);
    const mostrar = (texto, ok) => { resultado.className = ok === undefined ? "" : ok ? "ok" : "error"; resultado.textContent = texto; };
    if (e.target.closest("[data-probar]")) {
      mostrar("Probando…");
      try { const repo = await probarConexion(valores()); mostrar(`Conexión correcta con ${repo.full_name}.`, true); }
      catch (error) { mostrar(error.message, false); }
    }
    if (e.target.closest("[data-guardar]")) {
      mostrar("Comprobando el token…");
      try {
        await probarConexion(valores());
        guardarConfig(valores(), $("#gh-recordar", dlg).checked);
        dlg.close();
        despues?.();
      } catch (error) { mostrar(error.message, false); }
    }
    const crear = e.target.closest("[data-crear-acceso]");
    if (crear) {
      const clave = $("#gh-clave", dlg).value;
      if (clave.length < 12) return mostrar("La clave del grupo debe tener al menos 12 caracteres.", false);
      if (clave !== $("#gh-clave2", dlg).value) return mostrar("Las dos claves no coinciden.", false);
      crear.disabled = true;
      try {
        await probarConexion(valores());
        mostrar("Cifrando la conexión…");
        const archivo = await cifrarAcceso(valores(), clave);
        await publicarEnGitHub(valores(), [{ ruta: "contenido/acceso.json", datos: JSON.stringify(archivo, null, 2) + "\n" }],
          "Configura el acceso de la mesa de redacción", (t) => mostrar(t), false);
        guardarConfig(valores(), $("#gh-recordar", dlg).checked);
        mostrar("Clave guardada. En uno o dos minutos tus compañeros podrán entrar con ?editar y la clave del grupo.", true);
      } catch (error) { mostrar(error.message, false); }
      crear.disabled = false;
    }
  });
}

function dialogoClave(apiApp, acceso) {
  const configurado = acceso && acceso.datos;
  const dlg = dialogo("Acceso para la mesa de redacción", configurado ? `
    <p class="ayuda">Escribe la clave del grupo que compartió el administrador del periódico.</p>
    <label for="acc-clave">Clave del grupo</label><input id="acc-clave" type="password" autocomplete="current-password">
    <label><input id="acc-recordar" type="checkbox"> Recordar en este navegador (no lo marques en computadores compartidos)</label>
    <p id="acc-resultado" class="error" aria-live="polite"></p>` : `
    <p>El acceso de la mesa de redacción todavía no está configurado.</p>
    <p class="ayuda">El administrador del repositorio debe entrar una vez con su token y guardar la clave del grupo.</p>`,
    `<button class="boton" type="button" data-admin>Soy el administrador</button><button class="boton" type="button" data-cerrar>Cancelar</button>
     ${configurado ? '<button class="boton primario" type="button" data-entrar>Entrar</button>' : ""}`);
  const entrar = async () => {
    const resultado = $("#acc-resultado", dlg);
    const boton = $("[data-entrar]", dlg);
    boton.disabled = true;
    resultado.className = "ayuda";
    resultado.textContent = "Comprobando…";
    try {
      const config = await abrirAcceso(acceso, $("#acc-clave", dlg).value);
      guardarConfig(config, $("#acc-recordar", dlg).checked);
      dlg.close();
      activarEditor(apiApp);
    } catch (error) {
      resultado.className = "error";
      resultado.textContent = error.name === "OperationError" ? "La clave no es correcta." : error.message;
      boton.disabled = false;
    }
  };
  $("#acc-clave", dlg)?.focus();
  dlg.addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.id === "acc-clave") { e.preventDefault(); entrar(); } });
  dlg.addEventListener("click", (e) => {
    if (e.target.closest("[data-entrar]")) entrar();
    if (e.target.closest("[data-admin]")) { dlg.close(); dialogoGitHub(() => activarEditor(apiApp)); }
  });
}

/** Punto de entrada oculto (?editar o Ctrl+Shift+E): pide la clave del grupo antes de mostrar herramientas. */
export async function solicitarAcceso(apiApp) {
  api = apiApp;
  const url = new URL(location.href);
  if (url.searchParams.has("editar")) {
    url.searchParams.delete("editar");
    history.replaceState(null, "", url.pathname + url.search + url.hash);   // el enlace compartido no delata el modo edición
  }
  if (apiApp.estado.editando) return;
  if (leerConfig().token || ["localhost", "127.0.0.1"].includes(location.hostname)) return activarEditor(apiApp);
  let acceso = null;
  try {
    const respuesta = await fetch(`contenido/acceso.json?v=${Date.now()}`, { cache: "no-store" });
    if (respuesta.ok) acceso = await respuesta.json();
  } catch { /* sin archivo de acceso */ }
  dialogoClave(apiApp, acceso);
}

function cerrarSesion() {
  try { localStorage.removeItem(CLAVE_GITHUB); sessionStorage.removeItem(CLAVE_GITHUB); } catch { /* sin almacenamiento */ }
  desactivarEditor();
  avisar("Sesión de editor cerrada en este navegador.");
}

function dialogoPublicar() {
  const config = leerConfig();
  if (!config.token || !config.propietario || !config.repositorio) return dialogoGitHub(dialogoPublicar);
  const dlg = dialogo("Publicar en GitHub Pages", `
    <p>Se publicará la edición completa en <strong>${escapar(config.propietario)}/${escapar(config.repositorio)}</strong> (rama ${escapar(config.rama)}) en un solo commit.</p>
    <label for="pub-mensaje">Descripción del cambio</label>
    <input id="pub-mensaje" type="text" value="Actualiza el contenido de LA CUESTIÓN">
    <p id="pub-progreso" class="ayuda" aria-live="polite"></p>`,
    `<button class="boton" type="button" data-config>Cambiar conexión</button><button class="boton" type="button" data-cerrar>Cancelar</button>
     <button class="boton primario" type="button" data-publicar>Publicar</button>`);
  dlg.addEventListener("click", async (e) => {
    if (e.target.closest("[data-config]")) { dlg.close(); dialogoGitHub(dialogoPublicar); return; }
    const boton = e.target.closest("[data-publicar]");
    if (!boton) return;
    const progreso = $("#pub-progreso", dlg);
    boton.disabled = true;
    try {
      const archivos = await prepararArchivos(api.estado.edicion, api.estado.secciones);
      await publicarEnGitHub(config, archivos, $("#pub-mensaje", dlg).value.trim() || "Actualiza el contenido", (t) => { progreso.textContent = t; });
      api.estado.servidor = instantanea();
      api.descartarBorrador();
      actualizarEstado();
      progreso.className = "ok";
      progreso.textContent = "¡Publicado! GitHub Pages tarda uno o dos minutos en mostrar los cambios.";
      boton.textContent = "Publicado";
    } catch (error) {
      progreso.className = "error";
      progreso.textContent = error.message;
      boton.disabled = false;
    }
  });
}

async function descargarZip() {
  const archivos = await prepararArchivos(api.estado.edicion, api.estado.secciones);
  const url = URL.createObjectURL(crearZip(archivos));
  const a = Object.assign(document.createElement("a"), { href: url, download: `la-cuestion-contenido-${new Date().toISOString().slice(0, 10)}.zip` });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
  avisar("ZIP descargado. Descomprímelo en la raíz del repositorio (reemplaza «contenido» e «imagenes/subidas»).");
}

// ---------------------------------------------------------------- barra y eventos
function montarBarra() {
  barra = document.createElement("div");
  barra.className = "barra-edicion";
  barra.setAttribute("role", "toolbar");
  barra.setAttribute("aria-label", "Herramientas de edición");
  barra.innerHTML = `<strong>Modo edición</strong>
    <div class="formato" aria-label="Formato del texto seleccionado">
      <button type="button" data-f="bold" title="Negrita"><b>N</b></button><button type="button" data-f="italic" title="Cursiva"><i>K</i></button>
      <button type="button" data-f="link" title="Enlace">🔗</button><button type="button" data-f="removeFormat" title="Quitar formato">⌫</button></div>
    <button class="boton" type="button" data-accion="secciones">Secciones</button>
    <button class="boton" type="button" data-accion="nueva">+ Nueva sección</button>
    <button class="boton" type="button" data-accion="deshacer">Deshacer</button>
    <span class="separador"></span><span class="estado-edicion" aria-live="polite"></span>
    <button class="boton" type="button" data-accion="descargar">Descargar ZIP</button>
    <button class="boton" type="button" data-accion="github">GitHub</button>
    <button class="boton primario" type="button" data-accion="publicar">Publicar</button>
    <button class="boton" type="button" data-accion="sesion" title="Olvida la clave en este navegador">Cerrar sesión</button>
    <button class="boton" type="button" data-accion="salir">Salir</button>`;
  document.getElementById("editor-raiz").append(barra);
  barra.addEventListener("mousedown", (e) => { if (e.target.closest("[data-f]")) e.preventDefault(); });
  barra.addEventListener("click", (e) => {
    const formato = e.target.closest("[data-f]")?.dataset.f;
    if (formato === "link") {
      const url = prompt("Dirección del enlace (https://…)");
      if (url) document.execCommand("createLink", false, url);
    } else if (formato) document.execCommand(formato);
    const accion = e.target.closest("[data-accion]")?.dataset.accion;
    if (accion === "secciones") panelSecciones();
    if (accion === "nueva") panelSecciones({ nueva: true });
    if (accion === "deshacer") deshacer();
    if (accion === "descargar") descargarZip().catch((error) => avisar(error.message, true));
    if (accion === "github") dialogoGitHub();
    if (accion === "publicar") dialogoPublicar();
    if (accion === "salir") desactivarEditor();
    if (accion === "sesion") cerrarSesion();
  });
}

function deshacer() {
  const foto = historial.pop();
  if (!foto) return avisar("No hay más cambios para deshacer.");
  api.estado.edicion = foto.edicion;
  api.estado.secciones = foto.secciones;
  autoguardar();
  api.pintar({ mantenerScroll: true });
}

function registrarEventos() {
  control = new AbortController();
  const { signal } = control;
  document.addEventListener("focusin", (e) => {
    if (e.target.closest?.("[data-e]")) instantaneaPendiente = instantanea();
    const item = e.target.closest?.("[data-item]");
    if (item) mostrarControl(item);
  }, { signal });
  document.addEventListener("input", (e) => {
    const campo = e.target.closest?.("[data-e]");
    if (!campo) return;
    if (instantaneaPendiente) { recordar(instantaneaPendiente); instantaneaPendiente = null; }
    const { objeto } = raizDe(campo);
    escribir(objeto, campo.dataset.e, limpiar(campo.innerHTML));
    campo.classList.remove("vacio");
    autoguardar();
  }, { signal });
  document.addEventListener("focusout", (e) => {
    const campo = e.target.closest?.("[data-e]");
    if (!campo) return;
    if (campo.matches("[data-regenerar]")) api.pintar({ mantenerScroll: true });
    else if (campo.closest("#menu, .cabecera") || campo.dataset.e === "menu") api.pintar({ mantenerScroll: true });
  }, { signal });
  document.addEventListener("paste", (e) => {
    if (!e.target.closest?.("[data-e]")) return;
    e.preventDefault();
    document.execCommand("insertText", false, e.clipboardData.getData("text/plain"));
  }, { signal });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.closest?.("[data-e]")) { e.preventDefault(); document.execCommand("insertLineBreak"); }
    if (e.key === "Escape") flotante?.remove(), (flotante = null);
  }, { signal });
  document.addEventListener("mouseover", (e) => {
    const item = e.target.closest?.("[data-item]");
    if (item && !e.target.closest(".control-item")) mostrarControl(item);
  }, { signal });
  document.addEventListener("click", (e) => {
    if (e.target.closest(".barra-edicion, dialog")) return;
    const boton = e.target.closest(".control-item button");
    if (boton) { accionElemento(boton.dataset.c); return; }
    const agregar = e.target.closest("[data-agregar]");
    if (agregar) {
      const { objeto, marca } = raizDe(agregar);
      const ruta = agregar.dataset.agregar;
      const lista = leer(objeto, ruta) || [];
      cambio(() => escribir(objeto, ruta, [...lista, elementoNuevo(ruta, lista)]), { foco: { marca, ruta: `${ruta}.${lista.length}` } });
      return;
    }
    const img = e.target.closest("img[data-img]");
    if (img) { e.preventDefault(); dialogoImagen(img); return; }
    const enlace = e.target.closest("[data-enlace]");
    if (enlace && !e.target.closest("[data-e]")) { e.preventDefault(); dialogoEnlace(enlace); return; }
    if (e.target.closest("a") && e.target.closest("[data-e]")) e.preventDefault();   // escribir dentro de un enlace sin navegar
  }, { signal });
}

// ---------------------------------------------------------------- activar / desactivar
export function activarEditor(apiApp) {
  if (apiApp.estado.editando) return;
  api = apiApp;
  api.estado.editando = true;
  historial = [];
  document.body.classList.add("editando");
  api.estado.despuesDePintar = prepararDOM;
  montarBarra();
  registrarEventos();
  api.pintar({ mantenerScroll: true });
  avisar("Modo edición: haz clic en cualquier texto para cambiarlo. Los cambios se guardan en este navegador hasta que publiques.");
}

export function desactivarEditor() {
  if (!api?.estado.editando) return;
  api.estado.editando = false;
  api.estado.despuesDePintar = null;
  control?.abort();
  barra?.remove();
  flotante?.remove();
  barra = flotante = null;
  document.body.classList.remove("editando");
  api.pintar({ mantenerScroll: true });
  if (api.hayCambios()) avisar("Tus cambios siguen guardados en este navegador. Publícalos o descarga el ZIP cuando termines.");
}
