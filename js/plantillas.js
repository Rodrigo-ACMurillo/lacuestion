// Plantillas para crear secciones nuevas y elementos nuevos dentro de las listas.

import { clonar } from "./util.js";

const cintillo = (seccion, detalle) => ({ seccion, detalle, derecha1: "NUEVA SECCIÓN", derecha2: "Fecha o sesión" });

export const PLANTILLAS = {
  columna: () => ({
    tipo: "columna", menu: "Nueva columna", visible: true,
    cintillo: cintillo("Análisis", "Columna N · Teoría"),
    antetitulo: "Problema social · Territorio",
    titulo: "Titular periodístico de impacto: llamativo pero analítico",
    subtitulo: "Subtítulo: breve síntesis que ubica el fenómeno social en Colombia y la teoría que se usará para leerlo.",
    firma: "Mesa de redacción · Ciudad",
    imagen: "", pie: "",
    glosario: { titulo: "Glosario teórico", terminos: [
      { termino: "Concepto 1.", definicion: "Definición sintética del primer concepto clave de la teoría." },
      { termino: "Concepto 2.", definicion: "Definición sintética del segundo concepto clave." },
      { termino: "Concepto 3.", definicion: "Definición sintética del tercer concepto clave." }] },
    cronica: ["La crónica del problema: describe el problema social real en Colombia con fuentes confiables y cítalas (Autor, año)."],
    lente: ["El lente sociológico: explica técnicamente cómo la teoría desglosa las causas profundas del problema, evitando el sentido común."],
    cita: "«Cita destacada del autor o de la columna»",
    punto_ciego: ["El punto ciego: ¿qué ignoran la prensa sensacionalista o la política pública tradicional al no usar esta teoría?"],
    pasos: { titulo: "", items: [] },
    datos: [{ cifra: "00 %", texto: "dato clave con su fuente (Autor, año)" }],
    conclusion: { titulo: "Conclusión · Recomendación desde el Trabajo Social Crítico",
      parrafos: ["Recomendación técnica, ética y operativa de intervención, coherente con la teoría analizada."] },
    fuentes: ["Apellido, N. (Año). <em>Título de la obra o informe</em>. Editorial o entidad. https://…"],
  }),
  articulo: () => ({
    tipo: "articulo", menu: "Nuevo artículo", visible: true,
    cintillo: cintillo("Sección", "Detalle"),
    antetitulo: "Antetítulo", titulo: "Titular del artículo", subtitulo: "Subtítulo o entradilla del artículo.",
    firma: "Mesa de redacción", imagen: "", pie: "",
    bloques: [{ ladillo: "Subtítulo interno", parrafos: ["Escribe aquí el primer párrafo."] }],
    cita: "", fuentes: [],
  }),
  editorial: () => ({
    tipo: "editorial", menu: "Nuevo editorial", visible: true,
    cintillo: cintillo("Opinión", "Editorial"),
    titulo: "Titular del editorial", entradilla: "Entradilla del editorial.", firma: "Editorial · Mesa de redacción",
    imagen: "", pie: "",
    recuadro: { titulo: "Recuadro", cargos: [{ titulo: "Título", texto: "Texto" }] },
    bloques: [{ ladillo: "Subtítulo", parrafos: ["Primer párrafo del editorial."] }],
    cita: "", cajas: [{ titulo: "Caja", texto: "Texto de la caja." }],
  }),
  tira: () => ({
    tipo: "tira", menu: "Nueva tira", visible: true,
    cintillo: cintillo("Humor gráfico", "Tira cómica"),
    titulo: "Título de la tira", entradilla: "Una frase que presenta la historia.",
    vinetas: [{ imagen: "", textos: [{ personaje: "", texto: "Narrador: dónde y cuándo ocurre." }] }],
    claves: [{ titulo: "Clave de lectura", texto: "Qué concepto teórico ilustra la viñeta." }],
  }),
  crucigrama: () => ({
    tipo: "crucigrama", menu: "Nuevo crucigrama", visible: true,
    cintillo: cintillo("Pasatiempos", "Crucigrama"),
    titulo: "Crucigrama", entradilla: "Escribe sin tildes, una letra por casilla.",
    palabras: [{ palabra: "CAPITAL", pista: "Recurso que, según Bourdieu, puede ser económico, cultural o social." },
      { palabra: "AGENCIA", pista: "Capacidad de actuar y provocar cambios según los propios valores (Sen)." }],
    sabias: { titulo: "¿Sabías que...?", texto: "" },
  }),
  agenda: () => ({
    tipo: "agenda", menu: "Nueva agenda", visible: true,
    cintillo: cintillo("Agenda", "Próximas ediciones"),
    titulo: "Lo que viene",
    tarjetas: [{ imagen: "", fecha: "Fecha · Columna", titulo: "Título", teoria: "Teoría · Autores", texto: "Resumen.", pregunta: "¿Pregunta guía?", enlace: "" }],
    cronograma: { titulo: "Cronograma", encabezados: ["Sesión", "Fecha", "Tema", "Teoría"], filas: [["1", "", "", ""]] },
    cartas: { titulo: "Cartas a la redacción", parrafos: ["Texto."] },
    titulo_referencias: "Referencias", referencias: [],
  }),
  portada: () => ({
    tipo: "portada", menu: "Portada", visible: true,
    avance: { etiqueta: "Avance", texto: "Texto del avance", imagen: "", enlace: "" },
    principal: { imagen: "", pie: "", credito: "", antetitulo: "Antetítulo", titulo: "Titular principal", sumario: ["Punto del sumario"],
      firma: "Mesa de redacción", lugar: "Ciudad", columnas: ["Primer párrafo."], cita: "", enlace: "" },
    lateral: [{ titulo: "Nota lateral", entradilla: "", firma: "", autor: "", texto: "", enlace: "" }],
    franja: [{ etiqueta: "Etiqueta", titulo: "Nota", texto: "", imagen: "", enlace: "" }],
  }),
};

const TEXTO_NUEVO = "Escribe aquí el nuevo texto.";
const FABRICAS = {
  parrafos: () => TEXTO_NUEVO, columnas: () => TEXTO_NUEVO, cronica: () => TEXTO_NUEVO, lente: () => TEXTO_NUEVO,
  punto_ciego: () => TEXTO_NUEVO, sumario: () => "Nuevo punto del sumario", items: () => "Nuevo paso",
  fuentes: () => "Apellido, N. (Año). <em>Título</em>. Editorial. https://…",
  referencias: () => "Apellido, N. (Año). <em>Título</em>. Editorial. https://…",
  lateral: () => ({ titulo: "Nueva nota", entradilla: "Entradilla", firma: "Sección", autor: "Mesa de redacción", texto: TEXTO_NUEVO, enlace: "" }),
  franja: () => ({ etiqueta: "Etiqueta", titulo: "Nueva nota", texto: TEXTO_NUEVO, imagen: "", enlace: "" }),
  cargos: () => ({ titulo: "Cargo", texto: "[Nombre y apellido]" }),
  bloques: () => ({ ladillo: "Nuevo subtítulo", parrafos: [TEXTO_NUEVO] }),
  cajas: () => ({ titulo: "Nueva caja", texto: TEXTO_NUEVO }),
  claves: () => ({ titulo: "Nueva clave", texto: TEXTO_NUEVO }),
  terminos: () => ({ termino: "Concepto.", definicion: "Definición." }),
  datos: () => ({ cifra: "0 %", texto: "dato (Fuente, año)" }),
  vinetas: () => ({ imagen: "", textos: [{ personaje: "", texto: "Narrador..." }] }),
  textos: () => ({ personaje: "PERSONAJE", texto: "Diálogo." }),
  tarjetas: () => ({ imagen: "", fecha: "Fecha", titulo: "Título", teoria: "Teoría", texto: "Resumen.", pregunta: "¿Pregunta?", enlace: "" }),
  palabras: () => ({ palabra: "PALABRA", pista: "Nueva pista." }),
};

function vaciar(valor) {
  if (typeof valor === "string") return "";
  if (Array.isArray(valor)) return valor.length && typeof valor[0] === "string" ? valor.map(() => "") : [];
  if (valor && typeof valor === "object") return Object.fromEntries(Object.entries(valor).map(([k, v]) => [k, vaciar(v)]));
  return valor;
}

/** Elemento nuevo para la lista en `ruta` (usa la clave final del camino). */
export function elementoNuevo(ruta, lista = []) {
  const clave = String(ruta).split(".").filter((p) => !/^\d+$/.test(p)).pop();
  if (clave === "filas") return (lista[0] || ["", "", "", ""]).map(() => "");
  if (FABRICAS[clave]) return FABRICAS[clave]();
  return lista.length ? vaciar(clonar(lista[0])) : TEXTO_NUEVO;
}
