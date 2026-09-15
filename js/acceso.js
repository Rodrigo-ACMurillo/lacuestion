// Acceso de la mesa de redacción: la conexión de GitHub del administrador se guarda cifrada
// (PBKDF2-SHA256 + AES-GCM) en contenido/acceso.json. Solo quien conoce la clave del grupo puede abrirla.

const codificar = new TextEncoder();
const decodificar = new TextDecoder();
const aBase64 = (bytes) => btoa(String.fromCharCode(...new Uint8Array(bytes)));
const deBase64 = (texto) => Uint8Array.from(atob(texto), (c) => c.charCodeAt(0));

async function llave(clave, sal, iteraciones) {
  if (!globalThis.crypto?.subtle) throw new Error("Abre el periódico desde su dirección https (GitHub Pages) para usar la clave del grupo.");
  const base = await crypto.subtle.importKey("raw", codificar.encode(clave), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name: "PBKDF2", salt: sal, iterations: iteraciones, hash: "SHA-256" },
    base, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}

export async function cifrarAcceso({ propietario, repositorio, rama, token }, clave) {
  const sal = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const iteraciones = 600000;
  const datos = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, await llave(clave, sal, iteraciones),
    codificar.encode(JSON.stringify({ propietario, repositorio, rama, token })));
  return { version: 1, algoritmo: "PBKDF2-SHA256 + AES-GCM-256", iteraciones, sal: aBase64(sal), iv: aBase64(iv), datos: aBase64(datos) };
}

/** Devuelve la conexión de GitHub o lanza un error si la clave no es correcta. */
export async function abrirAcceso(archivo, clave) {
  const claro = await crypto.subtle.decrypt({ name: "AES-GCM", iv: deBase64(archivo.iv) },
    await llave(clave, deBase64(archivo.sal), archivo.iteraciones), deBase64(archivo.datos));
  return JSON.parse(decodificar.decode(claro));
}
