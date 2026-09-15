// Utilidades compartidas: escape, saneado de HTML en línea, rutas dentro del contenido.

const ETIQUETAS_PERMITIDAS = new Set(["B", "STRONG", "I", "EM", "U", "A", "BR", "SUB", "SUP"]);

export function escapar(texto = "") {
  return String(texto)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

/** Deja solo formato en línea seguro (negrita, cursiva, enlaces, saltos de línea). */
export function limpiar(html = "") {
  const plantilla = document.createElement("template");
  plantilla.innerHTML = String(html);
  const recorrer = (nodo) => {
    for (const hijo of [...nodo.childNodes]) {
      if (hijo.nodeType === Node.TEXT_NODE) continue;
      if (hijo.nodeType !== Node.ELEMENT_NODE) { hijo.remove(); continue; }
      recorrer(hijo);
      if (!ETIQUETAS_PERMITIDAS.has(hijo.tagName)) {
        // «DIV» y «P» que crea el navegador al pulsar Enter se convierten en salto de línea
        if (hijo.tagName === "DIV" || hijo.tagName === "P") hijo.before(document.createElement("br"));
        hijo.replaceWith(...hijo.childNodes);
        continue;
      }
      for (const atributo of [...hijo.attributes]) {
        const valido = hijo.tagName === "A" && atributo.name === "href" &&
          /^(https?:|mailto:|#)/i.test(atributo.value.trim());
        if (!valido) hijo.removeAttribute(atributo.name);
      }
      if (hijo.tagName === "A") { hijo.setAttribute("rel", "noopener"); }
    }
  };
  recorrer(plantilla.content);
  return plantilla.innerHTML.replace(/^(<br>)+|(<br>)+$/g, "").replace(/&nbsp;/g, " ").trim();
}

/** Texto plano (para títulos de menú, atributos alt, etc.). */
export function textoPlano(html = "") {
  const div = document.createElement("div");
  div.innerHTML = limpiar(html);
  return div.textContent.trim();
}

export function partes(ruta) {
  return String(ruta).split(".").filter(Boolean).map((p) => (/^\d+$/.test(p) ? Number(p) : p));
}

export function leer(obj, ruta) {
  return partes(ruta).reduce((actual, clave) => (actual == null ? undefined : actual[clave]), obj);
}

export function escribir(obj, ruta, valor) {
  const claves = partes(ruta);
  const ultima = claves.pop();
  let actual = obj;
  for (const [i, clave] of claves.entries()) {
    if (actual[clave] == null) actual[clave] = typeof (claves[i + 1] ?? ultima) === "number" ? [] : {};
    actual = actual[clave];
  }
  actual[ultima] = valor;
}

export const clonar = (valor) => JSON.parse(JSON.stringify(valor));

export function slug(texto = "") {
  return String(texto).normalize("NFD").replace(/[̀-ͯ]/g, "")
    .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 48) || "seccion";
}

export function normalizarPalabra(texto = "") {
  return String(texto).normalize("NFD").replace(/[̀-ͯ]/g, "")
    .toUpperCase().replace(/Ñ/g, "N").replace(/[^A-Z]/g, "");
}

export function retrasar(funcion, ms = 600) {
  let temporizador;
  return (...args) => { clearTimeout(temporizador); temporizador = setTimeout(() => funcion(...args), ms); };
}

export function el(html) {
  const plantilla = document.createElement("template");
  plantilla.innerHTML = html.trim();
  return plantilla.content.firstElementChild;
}
