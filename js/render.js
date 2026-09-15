// Dibuja cada tipo de sección a partir de su JSON.
// Convenciones para el editor: data-e="ruta" (texto editable), data-img="ruta" (imagen),
// data-lista="ruta" (lista con elementos data-item="ruta.i"), data-enlace="ruta" (destino de un enlace).

import { escapar, limpiar, leer } from "./util.js";
import { renderCrucigrama } from "./crucigrama.js";

// ---------------------------------------------------------------- piezas
export function T(ruta, valor, etiqueta = "span", clase = "", extra = "") {
  const html = limpiar(valor ?? "");
  const clases = [clase, html ? "" : "vacio"].filter(Boolean).join(" ");
  return `<${etiqueta}${clases ? ` class="${clases}"` : ""} data-e="${ruta}"${extra}>${html}</${etiqueta}>`;
}

/** Párrafo que a la vez es elemento de una lista. */
const P = (ruta, valor, clase = "") => T(ruta, valor, "p", clase, ` data-item="${ruta}"`);

function L(ruta, elementos, pintar, { etiqueta = "div", clase = "" } = {}) {
  const lista = Array.isArray(elementos) ? elementos : [];
  const html = lista.map((elemento, i) => pintar(elemento, `${ruta}.${i}`, i)).join("");
  return `<${etiqueta}${clase ? ` class="${clase}"` : ""} data-lista="${ruta}">${html}</${etiqueta}>`;
}

function IMG(ruta, src, alt = "", clase = "", pie = null) {
  const vacia = !src;
  const imagen = `<img src="${escapar(src || "")}" alt="${escapar(alt)}" loading="lazy" data-img="${ruta}"${vacia ? ' class="vacio"' : ""}>`;
  return `<figure class="figura ${clase}">${imagen}${pie ?? ""}</figure>`;
}

function ENLACE(ruta, destino, texto = "Leer") {
  const href = !destino ? "#/" : /^(https?:|#)/.test(destino) ? destino : `#/s/${destino}`;
  return `<a class="ref${destino ? "" : " vacio"}" href="${escapar(href)}" data-enlace="${ruta}">${escapar(texto)}</a>`;
}

function cintillo(s) {
  const c = s.cintillo || {};
  return `<header class="cintillo">
    <div>${T("cintillo.seccion", c.seccion, "span", "cin-seccion")}${T("cintillo.detalle", c.detalle, "span", "cin-detalle")}</div>
    <div class="cin-der">${T("cintillo.derecha1", c.derecha1, "span", "cin-der1")}${T("cintillo.derecha2", c.derecha2, "span", "cin-der2")}</div>
  </header>`;
}

const caja = (rutaTitulo, titulo, interior, clase = "caja") =>
  `<div class="${clase}">${T(rutaTitulo, titulo, "h3", "caja-titulo")}${interior}</div>`;

const parrafos = (ruta, lista) => L(ruta, lista, (p, r) => P(r, p));

// ---------------------------------------------------------------- tipos de sección
function portada(s) {
  const a = s.avance || {}, pr = s.principal || {};
  return `
  <div class="avance">
    ${T("avance.etiqueta", a.etiqueta, "span", "avance-etq")}
    <img src="${escapar(a.imagen || "")}" alt="" data-img="avance.imagen"${a.imagen ? "" : ' class="vacio"'}>
    <a class="avance-txt" href="#/s/${escapar(a.enlace || "")}" data-enlace="avance.enlace">${T("avance.texto", a.texto)}</a>
  </div>
  <div class="portada-grid">
    <div class="apertura">
      ${IMG("principal.imagen", pr.imagen, pr.titulo, "", `<figcaption class="pie-foto">${T("principal.pie", pr.pie)}${T("principal.credito", pr.credito, "span", "credito")}</figcaption>`)}
      ${T("principal.antetitulo", pr.antetitulo, "p", "antetitulo")}
      ${T("principal.titulo", pr.titulo, "h1", "titular-apertura")}
      ${L("principal.sumario", pr.sumario, (x, r) => T(r, x, "li", "", ` data-item="${r}"`), { etiqueta: "ul", clase: "sumario" })}
      ${T("principal.firma", pr.firma, "p", "firma")}${T("principal.lugar", pr.lugar, "p", "lugar")}
      <div class="col3 cuerpo">${parrafos("principal.columnas", pr.columnas)}
        <p>${ENLACE("principal.enlace", pr.enlace, "Leer el análisis")}</p></div>
      ${T("principal.cita", pr.cita, "p", "subtitular")}
    </div>
    ${L("lateral", s.lateral, (n, r) => `
      <article class="nota-lateral" data-item="${r}">
        ${T(`${r}.titulo`, n.titulo, "h2", "titular-m")}
        ${T(`${r}.entradilla`, n.entradilla, "p", "entradilla-r")}
        ${T(`${r}.firma`, n.firma, "p", "firma")}${T(`${r}.autor`, n.autor, "p", "lugar")}
        <div class="cuerpo">${T(`${r}.texto`, n.texto, "p")}</div>
        ${ENLACE(`${r}.enlace`, n.enlace)}
      </article>`, { etiqueta: "aside", clase: "lateral" })}
  </div>
  ${L("franja", s.franja, (n, r) => `
    <article class="nota-franja" data-item="${r}">
      ${T(`${r}.etiqueta`, n.etiqueta, "p", "etiqueta")}
      ${IMG(`${r}.imagen`, n.imagen, n.titulo)}
      ${T(`${r}.titulo`, n.titulo, "h3", "titular-r")}
      ${T(`${r}.texto`, n.texto, "p")}
      ${ENLACE(`${r}.enlace`, n.enlace)}
    </article>`, { clase: "franja" })}`;
}

function editorial(s) {
  const rec = s.recuadro || {};
  return `${cintillo(s)}
  ${T("titulo", s.titulo, "h1", "titular-xl")}
  ${T("entradilla", s.entradilla, "p", "entradilla")}
  ${T("firma", s.firma, "p", "firma")}
  <div class="fila-figura">
    ${IMG("imagen", s.imagen, s.titulo, "", `<figcaption class="pie-foto">${T("pie", s.pie)}</figcaption>`)}
    ${caja("recuadro.titulo", rec.titulo, L("recuadro.cargos", rec.cargos, (c, r) =>
      `<p data-item="${r}">${T(`${r}.titulo`, c.titulo, "strong")}<br>${T(`${r}.texto`, c.texto)}</p>`))}
  </div>
  <div class="col3 cuerpo">
    ${L("bloques", s.bloques, (b, r) => `<div data-item="${r}">${T(`${r}.ladillo`, b.ladillo, "h3", "ladillo")}${parrafos(`${r}.parrafos`, b.parrafos)}</div>`)}
    ${T("cita", s.cita, "blockquote", "destacado")}
  </div>
  ${L("cajas", s.cajas, (c, r) => `<div class="caja" data-item="${r}">${T(`${r}.titulo`, c.titulo, "h3", "caja-titulo")}${T(`${r}.texto`, c.texto, "p")}</div>`, { clase: "cajas" })}`;
}

function columna(s) {
  const et = { cronica: "La crónica del problema", lente: "El lente sociológico", punto_ciego: "El punto ciego",
    datos: "Datos clave", fuentes: "Fuentes", ...(s.etiquetas || {}) };
  const g = s.glosario || {}, pasos = s.pasos || {}, c = s.conclusion || {};
  return `${cintillo(s)}
  ${T("antetitulo", s.antetitulo, "p", "antetitulo")}
  ${T("titulo", s.titulo, "h1", "titular-xl")}
  ${T("subtitulo", s.subtitulo, "p", "entradilla")}
  ${T("firma", s.firma, "p", "firma")}
  <div class="columna-grid">
    <div>
      ${IMG("imagen", s.imagen, s.titulo, "", `<figcaption class="pie-foto">${T("pie", s.pie)}</figcaption>`)}
      <div class="col2 cuerpo">
        ${T("etiquetas.cronica", et.cronica, "h2", "ladillo")}${parrafos("cronica", s.cronica)}
        ${T("etiquetas.lente", et.lente, "h2", "ladillo")}${parrafos("lente", s.lente)}
        ${T("cita", s.cita, "blockquote", "destacado")}
        ${T("etiquetas.punto_ciego", et.punto_ciego, "h2", "ladillo")}${parrafos("punto_ciego", s.punto_ciego)}
      </div>
    </div>
    <aside class="columna-lateral">
      ${caja("glosario.titulo", g.titulo, L("glosario.terminos", g.terminos, (x, r) =>
        `<p data-item="${r}">${T(`${r}.termino`, x.termino, "strong")} ${T(`${r}.definicion`, x.definicion)}</p>`))}
      <div class="bloque-titulo${(pasos.items || []).length ? "" : " solo-edicion"}">
        ${T("pasos.titulo", pasos.titulo, "h3", "caja-titulo")}
        ${L("pasos.items", pasos.items, (x, r) => `<li data-item="${r}">${T(r, x)}</li>`, { etiqueta: "ol", clase: "pasos" })}
      </div>
      <div class="bloque-titulo datos">
        ${T("etiquetas.datos", et.datos, "h3", "caja-titulo")}
        ${L("datos", s.datos, (x, r) => `<div class="dato" data-item="${r}">${T(`${r}.cifra`, x.cifra, "span", "dato-cifra")}${T(`${r}.texto`, x.texto)}</div>`)}
      </div>
    </aside>
  </div>
  <div class="caja-conclusion">${T("conclusion.titulo", c.titulo, "h2", "caja-titulo")}<div class="cuerpo">${parrafos("conclusion.parrafos", c.parrafos)}</div></div>
  ${T("etiquetas.fuentes", et.fuentes, "h2", "caja-titulo bloque-titulo")}
  ${L("fuentes", s.fuentes, (x, r) => T(r, x, "li", "", ` data-item="${r}"`), { etiqueta: "ol", clase: "fuentes" })}`;
}

function crucigrama(s) {
  const sab = s.sabias || {};
  return `${cintillo(s)}
  ${T("titulo", s.titulo, "h1", "titular-l")}
  ${T("entradilla", s.entradilla, "p", "entradilla")}
  ${renderCrucigrama(s)}
  ${caja("sabias.titulo", sab.titulo, T("sabias.texto", sab.texto, "p"))}`;
}

function tira(s) {
  return `${cintillo(s)}
  ${T("titulo", s.titulo, "h1", "titular-xl")}
  ${T("entradilla", s.entradilla, "p", "entradilla")}
  ${L("vinetas", s.vinetas, (v, r, i) => `
    <figure class="vineta" data-item="${r}">
      ${L(`${r}.textos`, v.textos, (x, rt) => `
        <p class="cartela ${x.personaje ? "cartela-dialogo" : "cartela-narrador"}" data-item="${rt}">${T(`${rt}.personaje`, x.personaje, "span", "personaje")}${T(`${rt}.texto`, x.texto)}</p>`, { clase: "cartelas" })}
      <img src="${escapar(v.imagen || "")}" alt="Viñeta ${i + 1}" loading="lazy" data-img="${r}.imagen"${v.imagen ? "" : ' class="vacio"'}>
    </figure>`, { clase: "tira-grid" })}
  ${L("claves", s.claves, (c, r) => `<div class="caja" data-item="${r}">${T(`${r}.titulo`, c.titulo, "h3", "caja-titulo")}${T(`${r}.texto`, c.texto, "p")}</div>`, { clase: "cajas" })}`;
}

function agenda(s) {
  const cr = s.cronograma || {}, ca = s.cartas || {};
  return `${cintillo(s)}
  ${T("titulo", s.titulo, "h1", "titular-xl")}
  ${L("tarjetas", s.tarjetas, (t, r) => `
    <article class="tarjeta" data-item="${r}">
      ${IMG(`${r}.imagen`, t.imagen, t.titulo)}
      ${T(`${r}.fecha`, t.fecha, "p", "etiqueta-azul")}
      ${T(`${r}.titulo`, t.titulo, "h3", "titular-s")}
      ${T(`${r}.teoria`, t.teoria, "p", "firma")}
      <div class="cuerpo">${T(`${r}.texto`, t.texto, "p")}
      <p><strong>Pregunta guía:</strong> ${T(`${r}.pregunta`, t.pregunta)}</p></div>
      ${ENLACE(`${r}.enlace`, t.enlace, "Leer la columna")}
    </article>`, { clase: "tarjetas" })}
  <div class="fila-agenda">
    <div>
      ${T("cronograma.titulo", cr.titulo, "h2", "caja-titulo")}
      <div class="tabla-envoltura"><table class="tabla">
        <thead><tr>${(cr.encabezados || []).map((h, j) => T(`cronograma.encabezados.${j}`, h, "th")).join("")}</tr></thead>
        ${L("cronograma.filas", cr.filas, (fila, r) => `<tr data-item="${r}">${(fila || []).map((celda, j) => T(`${r}.${j}`, celda, "td")).join("")}</tr>`, { etiqueta: "tbody" })}
      </table></div>
    </div>
    ${caja("cartas.titulo", ca.titulo, parrafos("cartas.parrafos", ca.parrafos))}
  </div>
  ${T("titulo_referencias", s.titulo_referencias, "h2", "caja-titulo bloque-titulo")}
  ${L("referencias", s.referencias, (x, r) => T(r, x, "li", "", ` data-item="${r}"`), { etiqueta: "ul", clase: "referencias" })}`;
}

function articulo(s) {
  return `${cintillo(s)}
  ${T("antetitulo", s.antetitulo, "p", "antetitulo")}
  ${T("titulo", s.titulo, "h1", "titular-xl")}
  ${T("subtitulo", s.subtitulo, "p", "entradilla")}
  ${T("firma", s.firma, "p", "firma")}
  ${IMG("imagen", s.imagen, s.titulo, "", `<figcaption class="pie-foto">${T("pie", s.pie)}</figcaption>`)}
  <div class="col2 cuerpo">
    ${L("bloques", s.bloques, (b, r) => `<div data-item="${r}">${T(`${r}.ladillo`, b.ladillo, "h2", "ladillo")}${parrafos(`${r}.parrafos`, b.parrafos)}</div>`)}
    ${T("cita", s.cita, "blockquote", "destacado")}
  </div>
  ${L("fuentes", s.fuentes, (x, r) => T(r, x, "li", "", ` data-item="${r}"`), { etiqueta: "ol", clase: "fuentes" })}`;
}

export const TIPOS = {
  portada: { nombre: "Portada", pintar: portada },
  editorial: { nombre: "Editorial", pintar: editorial },
  columna: { nombre: "Columna de análisis teórico", pintar: columna },
  crucigrama: { nombre: "Crucigrama", pintar: crucigrama },
  tira: { nombre: "Tira cómica", pintar: tira },
  agenda: { nombre: "Agenda y referencias", pintar: agenda },
  articulo: { nombre: "Artículo libre", pintar: articulo },
};

export function renderSeccion(seccion) {
  const tipo = TIPOS[seccion.tipo] || TIPOS.articulo;
  return `<article class="seccion seccion-${escapar(seccion.tipo)}" id="sec-${escapar(seccion.id)}" data-raiz="seccion:${escapar(seccion.id)}">${tipo.pintar(seccion)}</article>`;
}

export { leer };
