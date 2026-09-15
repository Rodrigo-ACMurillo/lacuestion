// Crucigrama: genera la rejilla a partir de la lista {palabra, pista} y la vuelve jugable.

import { escapar, limpiar, normalizarPalabra } from "./util.js";

const cache = new Map();

function azar(semilla) {
  return () => {
    semilla |= 0; semilla = (semilla + 0x6d2b79f5) | 0;
    let t = Math.imul(semilla ^ (semilla >>> 15), 1 | semilla);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function intentar(palabras, N, semilla) {
  const rnd = azar(semilla);
  const g = Array.from({ length: N }, () => Array(N).fill(null));
  const puestas = [];
  const cabe = (w, r, c, d) => {
    const L = w.length;
    if (r < 0 || c < 0) return -1;
    if (d === "H") {
      if (c + L > N || (c > 0 && g[r][c - 1]) || (c + L < N && g[r][c + L])) return -1;
    } else if (r + L > N || (r > 0 && g[r - 1][c]) || (r + L < N && g[r + L][c])) return -1;
    let cruces = 0;
    for (let i = 0; i < L; i++) {
      const rr = d === "H" ? r : r + i, cc = d === "H" ? c + i : c;
      const actual = g[rr][cc];
      if (actual) { if (actual !== w[i]) return -1; cruces++; }
      else if (d === "H" ? ((rr > 0 && g[rr - 1][cc]) || (rr + 1 < N && g[rr + 1][cc]))
                         : ((cc > 0 && g[rr][cc - 1]) || (cc + 1 < N && g[rr][cc + 1]))) return -1;
    }
    return cruces;
  };
  const poner = (item, r, c, d) => {
    for (let i = 0; i < item.w.length; i++) g[d === "H" ? r : r + i][d === "H" ? c + i : c] = item.w[i];
    puestas.push({ ...item, r, c, d });
  };
  const orden = [...palabras].sort((a, b) => b.w.length - a.w.length + (rnd() - 0.5) * 2.5);
  const primera = orden.shift();
  poner(primera, Math.floor(N / 2), Math.floor((N - primera.w.length) / 2), "H");
  let resto = orden;
  for (let pasada = 0; pasada < 5 && resto.length; pasada++) {
    const quedan = [];
    for (const item of resto) {
      let mejor = null;
      for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) {
        const letra = g[r][c];
        if (!letra) continue;
        for (let i = 0; i < item.w.length; i++) {
          if (item.w[i] !== letra) continue;
          for (const [rr, cc, d] of [[r, c - i, "H"], [r - i, c, "V"]]) {
            const cr = cabe(item.w, rr, cc, d);
            if (cr > 0) {
              const puntaje = cr * 8 - 0.6 * (Math.abs(rr - N / 2) + Math.abs(cc - N / 2)) + rnd() * 6;
              if (!mejor || puntaje > mejor[0]) mejor = [puntaje, rr, cc, d];
            }
          }
        }
      }
      if (mejor) poner(item, mejor[1], mejor[2], mejor[3]); else quedan.push(item);
    }
    resto = quedan;
  }
  return { g, puestas, faltan: resto };
}

export function generarCrucigrama(lista = []) {
  const palabras = lista.map((p, indice) => ({ w: normalizarPalabra(p.palabra), pista: p.pista, indice }))
    .filter((p) => p.w.length >= 2);
  const clave = palabras.map((p) => p.w).join("|");
  if (cache.has(clave)) return cache.get(clave);
  if (!palabras.length) return { H: 0, W: 0, celdas: [], horizontales: [], verticales: [], faltan: [] };
  const base = Math.min(24, Math.max(13, Math.max(...palabras.map((p) => p.w.length)) + 4));
  let mejor = null;
  // prueba rejillas cada vez más holgadas hasta que quepan todas las palabras
  buscar: for (const N of [base, base + 2, base + 4]) {
    for (let s = 1; s <= 700; s++) {
      const res = intentar(palabras, N, s * 7919);
      if (!mejor || res.puestas.length > mejor.puestas.length) mejor = res;
      if (!res.faltan.length) { mejor = res; break buscar; }
    }
  }
  const N = mejor.g.length;
  // recorta la rejilla y numera
  const { g, puestas } = mejor;
  const filas = g.map((f, r) => (f.some(Boolean) ? r : -1)).filter((r) => r >= 0);
  const cols = [...Array(N).keys()].filter((c) => g.some((f) => f[c]));
  const r0 = filas[0], c0 = cols[0], H = filas.at(-1) - r0 + 1, W = cols.at(-1) - c0 + 1;
  const celdas = Array.from({ length: H }, (_, r) => Array.from({ length: W }, (_, c) => g[r + r0][c + c0]));
  const numeros = {};
  let n = 0;
  for (let r = 0; r < H; r++) for (let c = 0; c < W; c++) {
    if (!celdas[r][c]) continue;
    const h = (c === 0 || !celdas[r][c - 1]) && c + 1 < W && celdas[r][c + 1];
    const v = (r === 0 || !celdas[r - 1][c]) && r + 1 < H && celdas[r + 1][c];
    if (h || v) numeros[`${r},${c}`] = ++n;
  }
  const conNumero = puestas.map((p) => ({ ...p, r: p.r - r0, c: p.c - c0, num: numeros[`${p.r - r0},${p.c - c0}`] }))
    .sort((a, b) => a.num - b.num);
  const resultado = {
    H, W, celdas, numeros,
    horizontales: conNumero.filter((p) => p.d === "H"),
    verticales: conNumero.filter((p) => p.d === "V"),
    faltan: mejor.faltan.map((p) => p.w),
  };
  cache.set(clave, resultado);
  return resultado;
}

const campo = (ruta, valor, etiqueta, clase = "", extra = "") =>
  `<${etiqueta} class="${clase}" data-e="${ruta}"${extra}>${limpiar(valor ?? "")}</${etiqueta}>`;

export function renderCrucigrama(s) {
  const cr = generarCrucigrama(s.palabras || []);
  const celdas = [];
  for (let r = 0; r < cr.H; r++) for (let c = 0; c < cr.W; c++) {
    const letra = cr.celdas[r][c];
    if (!letra) { celdas.push("<div></div>"); continue; }
    const num = cr.numeros[`${r},${c}`];
    celdas.push(`<div class="celda" data-f="${r}" data-c="${c}">${num ? `<span class="celda-num">${num}</span>` : ""}` +
      `<input maxlength="1" autocomplete="off" autocapitalize="characters" spellcheck="false" data-sol="${letra}" aria-label="Fila ${r + 1}, columna ${c + 1}${num ? `, casilla ${num}` : ""}"></div>`);
  }
  const pistas = (lista, dir) => lista.map((p) =>
    `<li data-num="${p.num}" data-dir="${dir}" data-f="${p.r}" data-c="${p.c}"><strong>${p.num}.</strong> ${limpiar(p.pista || "")} (${p.w.length})</li>`).join("");
  const faltan = cr.faltan.length
    ? `<p class="cruci-estado solo-edicion">No caben en la rejilla: ${cr.faltan.map(escapar).join(", ")}. Cambia o acorta palabras.</p>` : "";
  return `
  <div class="cruci-grid-envoltura" data-cruci>
    <div>
      <div class="cruci" style="grid-template-columns: repeat(${cr.W}, minmax(0, 1fr))">${celdas.join("")}</div>
      <div class="cruci-acciones">
        <button class="boton" type="button" data-accion="comprobar">Comprobar</button>
        <button class="boton" type="button" data-accion="solucion">Ver solución</button>
        <button class="boton" type="button" data-accion="borrar">Borrar</button>
        <span class="cruci-estado" aria-live="polite"></span>
      </div>
      ${faltan}
    </div>
    <div class="cruci-pistas">
      <h3 class="caja-titulo">Horizontales</h3><ol>${pistas(cr.horizontales, "H")}</ol>
      <h3 class="caja-titulo">Verticales</h3><ol>${pistas(cr.verticales, "V")}</ol>
    </div>
  </div>
  <div class="solo-edicion caja cruci-palabras">
    <h3 class="caja-titulo">Palabras y pistas (la rejilla se rehace al salir de cada palabra)</h3>
    <div data-lista="palabras">${(s.palabras || []).map((p, i) => `
      <p data-item="palabras.${i}">${campo(`palabras.${i}.palabra`, p.palabra, "strong", "", " data-regenerar")} — ${campo(`palabras.${i}.pista`, p.pista, "span", "", " data-regenerar")}</p>`).join("")}
    </div>
  </div>`;
}

/** Activa la interacción (una vez por página; usa delegación de eventos). */
export function activarCrucigramas(raiz) {
  let direccion = "H";
  const celdaDe = (input) => input.closest(".celda");
  const buscar = (cont, f, c) => cont.querySelector(`.celda[data-f="${f}"][data-c="${c}"] input`);
  const resaltar = (input) => {
    const cont = input.closest("[data-cruci]");
    cont.querySelectorAll(".activa").forEach((x) => x.classList.remove("activa"));
    const { f, c } = celdaDe(input).dataset;
    let fi = +f, ci = +c;
    const paso = direccion === "H" ? [0, -1] : [-1, 0];
    while (buscar(cont, fi + paso[0], ci + paso[1])) { fi += paso[0]; ci += paso[1]; }
    const avance = direccion === "H" ? [0, 1] : [1, 0];
    for (let x = buscar(cont, fi, ci); x; fi += avance[0], ci += avance[1], x = buscar(cont, fi, ci)) celdaDe(x).classList.add("activa");
  };
  const mover = (input, delta) => {
    const cont = input.closest("[data-cruci]");
    const { f, c } = celdaDe(input).dataset;
    const sig = direccion === "H" ? buscar(cont, +f, +c + delta) : buscar(cont, +f + delta, +c);
    if (sig) sig.focus();
  };

  raiz.addEventListener("input", (e) => {
    const input = e.target.closest?.(".celda input");
    if (!input) return;
    input.value = input.value.slice(-1).toUpperCase();
    celdaDe(input).classList.remove("bien", "mal");
    if (input.value) mover(input, 1);
  });
  raiz.addEventListener("keydown", (e) => {
    const input = e.target.closest?.(".celda input");
    if (!input) return;
    const flechas = { ArrowRight: ["H", 1], ArrowLeft: ["H", -1], ArrowDown: ["V", 1], ArrowUp: ["V", -1] };
    if (flechas[e.key]) {
      e.preventDefault();
      [direccion] = flechas[e.key];
      mover(input, flechas[e.key][1]);
    } else if (e.key === "Backspace" && !input.value) {
      e.preventDefault(); mover(input, -1);
    }
  });
  raiz.addEventListener("focusin", (e) => {
    const input = e.target.closest?.(".celda input");
    if (input) resaltar(input);
  });
  raiz.addEventListener("click", (e) => {
    const input = e.target.closest?.(".celda input");
    if (input && document.activeElement === input && e.detail > 1) { direccion = direccion === "H" ? "V" : "H"; resaltar(input); }
    const pista = e.target.closest?.(".cruci-pistas li");
    if (pista) {
      direccion = pista.dataset.dir;
      buscar(pista.closest("[data-cruci]"), +pista.dataset.f, +pista.dataset.c)?.focus();
    }
    const boton = e.target.closest?.("[data-cruci] [data-accion]");
    if (!boton) return;
    const cont = boton.closest("[data-cruci]");
    const inputs = [...cont.querySelectorAll(".celda input")];
    const estado = cont.querySelector(".cruci-estado");
    if (boton.dataset.accion === "comprobar") {
      let bien = 0;
      inputs.forEach((i) => {
        const celda = celdaDe(i);
        celda.classList.remove("bien", "mal");
        if (!i.value) return;
        const ok = i.value === i.dataset.sol;
        celda.classList.add(ok ? "bien" : "mal");
        if (ok) bien++;
      });
      estado.textContent = `${bien} de ${inputs.length} casillas correctas.`;
    } else if (boton.dataset.accion === "solucion") {
      inputs.forEach((i) => { i.value = i.dataset.sol; celdaDe(i).classList.remove("mal"); });
      estado.textContent = "Solución completa.";
    } else {
      inputs.forEach((i) => { i.value = ""; celdaDe(i).classList.remove("bien", "mal"); });
      estado.textContent = "";
    }
  });
}
