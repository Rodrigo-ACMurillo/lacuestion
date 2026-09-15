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

## 2. Editar el periódico (solo la mesa de redacción)

Quien abre el enlace normal —por ejemplo, el docente— ve únicamente el periódico: no hay botones
ni herramientas de edición. Para editar se entra por una dirección especial y con la **clave del grupo**.

### Configuración inicial (una sola vez, la hace el administrador del repositorio)

1. En GitHub: *foto de perfil → Settings → Developer settings → Personal access tokens → Fine-grained tokens →
   Generate new token*. Ponle **fecha de vencimiento** (por ejemplo, el fin del semestre), en *Repository access*
   elige **Only select repositories → lacuestion** y en *Permissions → Contents* marca **Read and write**.
2. Abre `https://TU-USUARIO.github.io/lacuestion/?editar` y pulsa **Soy el administrador**.
3. Escribe usuario, repositorio, rama (`main`) y el token. Más abajo escribe la **clave del grupo**
   (una frase de al menos 12 caracteres) y pulsa **Guardar la clave del grupo en GitHub**.
   Se crea `contenido/acceso.json` con la conexión **cifrada** con esa clave.
4. Comparte con tus compañeros, por un canal privado, la dirección terminada en `?editar` y la clave.
   Al docente envíale el enlace **sin** `?editar`.

### Para los compañeros (sin cuenta de GitHub)

1. Abrir la dirección terminada en `?editar` (o pulsar **Ctrl + Mayús + E** estando en el periódico).
2. Escribir la clave del grupo → **Entrar**.
3. Editar:
   - **Textos:** clic y escribir. Con la barra inferior: **N** negrita, *K* cursiva, 🔗 enlace.
   - **Listas** (párrafos, conceptos, datos, viñetas, tarjetas, referencias…): **+ Añadir**; al pasar el ratón
     sobre un elemento aparecen ↑ ↓ (mover), ⧉ (duplicar) y ✕ (eliminar).
   - **Imágenes:** clic sobre la imagen para subir otra. **Enlaces «Leer →»:** clic para elegir la sección.
   - **Secciones:** renombrar, ordenar, ocultar o eliminar; **+ Nueva sección** usa plantillas
     (la de *Columna* trae todos los apartados de la rúbrica).
   - **Deshacer** revierte el último cambio. Mientras se edita, todo queda como borrador en ese navegador.
4. **Publicar**: sube todo a GitHub en un solo paso. El sitio se actualiza en uno o dos minutos.
5. En computadores compartidos, terminar con **Cerrar sesión**.

### Seguridad

- `contenido/acceso.json` es público pero está cifrado: sin la clave no sirve. Una clave larga y poco obvia
  es lo que lo protege; no la publiques en grupos abiertos.
- El token solo puede escribir en este repositorio y vence en la fecha elegida. Si la clave se filtra o
  alguien sale del grupo, repite el paso 3 con una clave nueva (y, si quieres, un token nuevo).
- Al terminar el curso, revoca el token en GitHub.

### Otras formas de actualizar

- **Descargar ZIP** (en la barra de edición) genera `contenido/` e `imagenes/subidas/` para subirlos a mano.
- Cada sección es un archivo de `contenido/secciones/` que también se puede editar directamente en GitHub.
  Los textos admiten `<strong>`, `<em>`, `<a href="…">` y `<br>`. Para una sección nueva, crea el archivo y
  añade su nombre (sin `.json`) a `orden` en `contenido/edicion.json`.

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
js/acceso.js            clave del grupo (conexión de GitHub cifrada)
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
