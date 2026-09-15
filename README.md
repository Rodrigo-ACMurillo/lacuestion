# LA CUESTIÓN · Periódico de análisis social

Versión web y editable del periódico de la **Actividad 1 · Problemas sociales contemporáneos**
(docente: Allison Paola Escobar). Es un sitio estático, sin servidor ni base de datos, pensado para
**GitHub Pages**. Todo el contenido vive en archivos JSON y se puede cambiar desde el propio navegador.

## Secciones incluidas

| Sección | Archivo | Tipo |
|---|---|---|
| Portada | `contenido/secciones/portada.json` | portada |
| Editorial general (Columna 1) | `editorial.json` | editorial |
| Columna 2 · Suárez | `columna-2.json` | columna |
| Columna 3 · Habitantes de calle (Sen y Nussbaum) | `columna-3.json` | columna |
| Columna 4 · Desplazamiento intraurbano (Shaw y McKay) | `columna-4.json` | columna |
| Columna 5 · Niñez trabajadora (Bourdieu y Passeron) | `columna-5.json` | columna |
| Crucigrama interactivo | `crucigrama.json` | crucigrama |
| Tira cómica «Calle Cero» | `tira.json` | tira |
| Agenda, cronograma y referencias | `agenda.json` | agenda |

El orden del menú y los datos de la cabecera están en `contenido/edicion.json`.

## 1. Publicar en GitHub Pages

1. Crea un repositorio nuevo en GitHub (por ejemplo `la-cuestion`), público.
2. Sube **todo el contenido de esta carpeta** a la raíz del repositorio: arrástralo en
   *Add file → Upload files* o usa `git`. Incluye el archivo oculto `.nojekyll`.
3. En el repositorio: *Settings → Pages → Build and deployment → Source: Deploy from a branch*,
   rama `main`, carpeta `/ (root)` → *Save*.
4. En uno o dos minutos el sitio queda en `https://TU-USUARIO.github.io/la-cuestion/`.

## 2. Editar el periódico desde el navegador

Pulsa **Editar** en el menú (o abre la dirección con `?editar` al final).

- **Textos:** haz clic en cualquier texto y escribe. Selecciona palabras para aplicar **N** (negrita),
  *K* (cursiva) o 🔗 (enlace) con la barra inferior.
- **Listas** (párrafos, conceptos del glosario, datos, viñetas, tarjetas, referencias, filas del cronograma…):
  usa **+ Añadir**. Al pasar el ratón sobre un elemento aparecen ↑ ↓ (mover), ⧉ (duplicar) y ✕ (eliminar).
- **Imágenes:** haz clic sobre la imagen para subir una desde tu computador o escribir su ruta.
- **Enlaces «Leer →»:** haz clic para elegir a qué sección llevan.
- **Crucigrama:** al editar aparece la lista de palabras y pistas; la rejilla se rehace sola.
- **Secciones:** el botón **Secciones** permite renombrar, reordenar, ocultar, duplicar o eliminar.
  **+ Nueva sección** crea una sección a partir de una plantilla: *Columna de análisis teórico*
  (con todos los apartados que exige la rúbrica), *Artículo libre*, *Editorial*, *Tira cómica*,
  *Crucigrama*, *Agenda* o *Portada*.
- **Deshacer** revierte el último cambio.

Mientras editas, todo se guarda automáticamente **como borrador en ese navegador**. Para que otras
personas vean los cambios tienes dos opciones:

### Opción A · Publicar directamente (recomendada)

1. En GitHub: *Settings (de tu cuenta) → Developer settings → Personal access tokens → Fine-grained tokens →
   Generate new token*.
2. *Repository access: Only select repositories* → elige el repositorio del periódico.
3. *Permissions → Repository permissions → Contents: Read and write*. Genera y copia el token.
4. En el sitio, modo edición → **GitHub** → escribe usuario, repositorio, rama (`main`) y el token →
   **Probar conexión** → **Guardar**.
5. **Publicar**. Se crea un único commit con todo el contenido; GitHub Pages lo muestra en uno o dos minutos.

El token se guarda solo en ese navegador. No marques «Recordar» en computadores compartidos y
revoca el token en GitHub cuando termine el curso.

### Opción B · Descargar y subir a mano

**Descargar ZIP** genera la carpeta `contenido/` (y `imagenes/subidas/` si subiste imágenes).
Descomprímela y súbela al repositorio reemplazando los archivos existentes.

### Opción C · Editar los JSON en GitHub

Cada sección es un archivo de `contenido/secciones/`. Puedes abrirlo en GitHub, pulsar el lápiz y
editarlo. Los textos admiten `<strong>`, `<em>`, `<a href="…">` y `<br>`. Para una sección nueva,
crea el archivo y añade su nombre (sin `.json`) a `orden` en `contenido/edicion.json`.

## 3. Ver el sitio en tu computador

El navegador no permite cargar los JSON abriendo `index.html` con doble clic. Usa un servidor local
desde esta carpeta:

```
python -m http.server 8000
```

y abre `http://localhost:8000`.

## Estructura

```
index.html              página única
css/estilos.css         diseño del periódico (lectura, adaptable a móvil, impresión)
css/editor.css          herramientas del modo edición
js/app.js               carga del contenido, menú y rutas (#/s/<sección>)
js/render.js            cómo se dibuja cada tipo de sección
js/editor.js            modo edición
js/plantillas.js        plantillas de secciones nuevas
js/crucigrama.js        generador y juego del crucigrama
js/github.js            ZIP y publicación en GitHub
contenido/              textos (JSON)
imagenes/               ilustraciones originales (WebP)
fuentes/                Newsreader y Oswald (WOFF2, licencia SIL OFL)
```

«Edición completa» (en el menú) muestra todas las secciones seguidas; desde ahí, *Imprimir → Guardar
como PDF* produce una versión para entregar.

## Fuentes de los datos

Las cifras de las columnas provienen de fuentes verificadas: DANE (pobreza monetaria 2025 y Censo de
Habitantes de la Calle), DNP (CONPES 3877), Personería Distrital de Medellín (desplazamiento
intraurbano 2024), El Tiempo, El Universal y La República. Las referencias completas están en la sección
*Agenda y fuentes*. Revísalas antes de cada entrega si actualizas los datos.
