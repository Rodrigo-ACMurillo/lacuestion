// Exportación: archivos de contenido, ZIP descargable y publicación en GitHub (un solo commit).

import { clonar } from "./util.js";

const API = "https://api.github.com";
const codificador = new TextEncoder();

// ---------------------------------------------------------------- archivos a partir del estado
async function huella(bytes) {
  const digest = await crypto.subtle.digest("SHA-1", bytes);
  return [...new Uint8Array(digest)].slice(0, 8).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function dataUrlABytes(url) {
  const [cabecera, datos] = url.split(",");
  const tipo = (cabecera.match(/data:([^;]+)/) || [])[1] || "application/octet-stream";
  const binario = atob(datos);
  const bytes = new Uint8Array(binario.length);
  for (let i = 0; i < binario.length; i++) bytes[i] = binario.charCodeAt(i);
  return { tipo, bytes };
}

/** Convierte el estado en la lista de archivos del sitio. Las imágenes subidas (data:) pasan a imagenes/subidas/. */
export async function prepararArchivos(edicion, secciones) {
  const archivos = [];
  const copia = clonar(secciones);
  const imagenes = new Map();
  const extraer = async (valor) => {
    if (typeof valor === "string" && valor.startsWith("data:")) {
      if (!imagenes.has(valor)) {
        const { tipo, bytes } = dataUrlABytes(valor);
        const ext = { "image/webp": "webp", "image/png": "png", "image/jpeg": "jpg", "image/gif": "gif", "image/svg+xml": "svg" }[tipo] || "bin";
        const ruta = `imagenes/subidas/${await huella(bytes)}.${ext}`;
        imagenes.set(valor, ruta);
        archivos.push({ ruta, datos: bytes });
      }
      return imagenes.get(valor);
    }
    if (Array.isArray(valor)) return Promise.all(valor.map(extraer));
    if (valor && typeof valor === "object") {
      for (const clave of Object.keys(valor)) valor[clave] = await extraer(valor[clave]);
    }
    return valor;
  };
  for (const id of Object.keys(copia)) await extraer(copia[id]);
  const edicionFinal = { ...clonar(edicion), orden: edicion.orden.filter((id) => copia[id]) };
  archivos.push({ ruta: "contenido/edicion.json", datos: JSON.stringify(edicionFinal, null, 2) + "\n" });
  for (const id of edicionFinal.orden) {
    const { id: _omitido, ...datos } = copia[id];
    archivos.push({ ruta: `contenido/secciones/${id}.json`, datos: JSON.stringify(datos, null, 2) + "\n" });
  }
  return archivos;
}

// ---------------------------------------------------------------- ZIP (método «store», sin compresión)
const TABLA_CRC = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; }
  return t;
})();
const crc32 = (bytes) => { let c = 0xffffffff; for (const b of bytes) c = TABLA_CRC[(c ^ b) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };

export function crearZip(archivos) {
  const partes = [], central = [];
  let desplazamiento = 0;
  const ahora = new Date();
  const hora = (ahora.getHours() << 11) | (ahora.getMinutes() << 5) | (ahora.getSeconds() >> 1);
  const fecha = ((ahora.getFullYear() - 1980) << 9) | ((ahora.getMonth() + 1) << 5) | ahora.getDate();
  for (const { ruta, datos } of archivos) {
    const nombre = codificador.encode(ruta);
    const bytes = typeof datos === "string" ? codificador.encode(datos) : datos;
    const crc = crc32(bytes);
    const local = new DataView(new ArrayBuffer(30));
    [[0, 0x04034b50, 4], [4, 20, 2], [6, 0x0800, 2], [8, 0, 2], [10, hora, 2], [12, fecha, 2], [14, crc, 4],
      [18, bytes.length, 4], [22, bytes.length, 4], [26, nombre.length, 2], [28, 0, 2]]
      .forEach(([pos, valor, tam]) => (tam === 4 ? local.setUint32(pos, valor, true) : local.setUint16(pos, valor, true)));
    partes.push(local, nombre, bytes);
    const cen = new DataView(new ArrayBuffer(46));
    [[0, 0x02014b50, 4], [4, 20, 2], [6, 20, 2], [8, 0x0800, 2], [10, 0, 2], [12, hora, 2], [14, fecha, 2], [16, crc, 4],
      [20, bytes.length, 4], [24, bytes.length, 4], [28, nombre.length, 2], [30, 0, 2], [32, 0, 2], [34, 0, 2], [36, 0, 2],
      [38, 0, 4], [42, desplazamiento, 4]]
      .forEach(([pos, valor, tam]) => (tam === 4 ? cen.setUint32(pos, valor, true) : cen.setUint16(pos, valor, true)));
    central.push(cen, nombre);
    desplazamiento += 30 + nombre.length + bytes.length;
  }
  const tamCentral = central.reduce((s, p) => s + p.byteLength, 0);
  const fin = new DataView(new ArrayBuffer(22));
  [[0, 0x06054b50, 4], [4, 0, 2], [6, 0, 2], [8, archivos.length, 2], [10, archivos.length, 2], [12, tamCentral, 4], [16, desplazamiento, 4], [20, 0, 2]]
    .forEach(([pos, valor, tam]) => (tam === 4 ? fin.setUint32(pos, valor, true) : fin.setUint16(pos, valor, true)));
  return new Blob([...partes, ...central, fin], { type: "application/zip" });
}

// ---------------------------------------------------------------- GitHub
export function detectarRepositorio() {
  const [, usuario] = location.hostname.match(/^([^.]+)\.github\.io$/i) || [];
  if (!usuario) return { propietario: "", repositorio: "" };
  const primera = location.pathname.split("/").filter(Boolean)[0];
  return { propietario: usuario, repositorio: primera && !primera.includes(".") ? primera : `${usuario}.github.io` };
}

async function llamar(config, ruta, opciones = {}) {
  const respuesta = await fetch(`${API}/repos/${config.propietario}/${config.repositorio}${ruta}`, {
    ...opciones,
    headers: {
      Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
      Authorization: `Bearer ${config.token}`, ...(opciones.body ? { "Content-Type": "application/json" } : {}),
    },
  });
  if (!respuesta.ok) {
    let detalle = "";
    try { detalle = (await respuesta.json()).message || ""; } catch { /* sin cuerpo */ }
    const pistas = { 401: "El token no es válido o expiró.", 403: "El token no tiene permiso de escritura (Contents: Read and write).",
      404: "No se encontró el repositorio o la rama, o el token no tiene acceso a ese repositorio.", 409: "El repositorio está vacío: crea al menos un commit.",
      422: "GitHub rechazó los datos enviados." };
    throw new Error(`${pistas[respuesta.status] || `Error ${respuesta.status} de GitHub.`} ${detalle}`.trim());
  }
  return respuesta.status === 204 ? null : respuesta.json();
}

export async function probarConexion(config) {
  const repo = await llamar(config, "");
  if (!repo.permissions?.push) throw new Error("El token puede leer el repositorio, pero no escribir en él.");
  return repo;
}

const aBase64 = (bytes) => {
  let binario = "";
  for (let i = 0; i < bytes.length; i += 0x8000) binario += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binario);
};

/** Publica todos los archivos en un único commit y elimina secciones que ya no existen. */
export async function publicarEnGitHub(config, archivos, mensaje, alProgresar = () => {}, podar = true) {
  const rama = config.rama || "main";
  alProgresar("Leyendo la rama…");
  const ref = await llamar(config, `/git/ref/heads/${encodeURIComponent(rama)}`);
  const commitBase = await llamar(config, `/git/commits/${ref.object.sha}`);
  const arbolBase = await llamar(config, `/git/trees/${commitBase.tree.sha}?recursive=1`);
  const rutasNuevas = new Set(archivos.map((a) => a.ruta));
  const entradas = [];
  for (const [i, archivo] of archivos.entries()) {
    alProgresar(`Subiendo ${i + 1} de ${archivos.length}: ${archivo.ruta}`);
    const bytes = typeof archivo.datos === "string" ? codificador.encode(archivo.datos) : archivo.datos;
    const blob = await llamar(config, "/git/blobs", { method: "POST", body: JSON.stringify({ content: aBase64(bytes), encoding: "base64" }) });
    entradas.push({ path: archivo.ruta, mode: "100644", type: "blob", sha: blob.sha });
  }
  for (const item of podar ? arbolBase.tree : []) {
    if (item.type === "blob" && item.path.startsWith("contenido/secciones/") && !rutasNuevas.has(item.path)) {
      entradas.push({ path: item.path, mode: "100644", type: "blob", sha: null });
    }
  }
  alProgresar("Creando el commit…");
  const arbol = await llamar(config, "/git/trees", { method: "POST", body: JSON.stringify({ base_tree: commitBase.tree.sha, tree: entradas }) });
  const commit = await llamar(config, "/git/commits", { method: "POST", body: JSON.stringify({ message: mensaje, tree: arbol.sha, parents: [ref.object.sha] }) });
  await llamar(config, `/git/refs/heads/${encodeURIComponent(rama)}`, { method: "PATCH", body: JSON.stringify({ sha: commit.sha }) });
  return commit;
}
