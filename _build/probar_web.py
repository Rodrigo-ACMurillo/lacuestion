# -*- coding: utf-8 -*-
"""Prueba del sitio web con Edge (Playwright): lectura, móvil, crucigrama y modo edición completo."""
import json, os, re, sys, zipfile
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/"
OUT = "L:/periodico/_build/web_pruebas/"
os.makedirs(OUT, exist_ok=True)
errores, peticiones_github = [], []


def registrar(page):
    page.on("console", lambda m: errores.append(f"consola {m.type}: {m.text}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: errores.append(f"excepción: {e}"))
    page.on("requestfailed", lambda r: errores.append(f"falló {r.url}") if "api.github.com" not in r.url else None)


def github_simulado(route):
    req = route.request
    cuerpo = req.post_data or ""
    peticiones_github.append((req.method, req.url.split("/repos/")[-1], cuerpo[:3000]))
    url = req.url
    if req.method == "GET" and url.endswith("/repos/prueba/la-cuestion"):
        data = {"full_name": "prueba/la-cuestion", "permissions": {"push": True}}
    elif "/git/ref/heads/main" in url:
        data = {"object": {"sha": "c0"}}
    elif re.search(r"/git/commits/c0$", url):
        data = {"tree": {"sha": "t0"}}
    elif "/git/trees/t0" in url:
        data = {"tree": [{"path": "contenido/secciones/portada.json", "type": "blob"},
                         {"path": "contenido/secciones/seccion-vieja.json", "type": "blob"}]}
    elif url.endswith("/git/blobs"):
        data = {"sha": f"b{len(peticiones_github)}"}
    elif url.endswith("/git/trees"):
        data = {"sha": "t1"}
    elif url.endswith("/git/commits"):
        data = {"sha": "c1"}
    elif "/git/refs/heads/main" in url:
        data = {"ref": "refs/heads/main"}
    else:
        data = {}
    route.fulfill(status=200, content_type="application/json", body=json.dumps(data),
                  headers={"Access-Control-Allow-Origin": "*"})


with sync_playwright() as p:
    nav = p.chromium.launch(channel="msedge", headless=True)
    ctx = nav.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
    page = ctx.new_page()
    registrar(page)
    page.goto(URL)
    page.wait_for_selector(".seccion-portada")
    orden = json.load(open("L:/periodico/la-cuestion-web/contenido/edicion.json", encoding="utf8"))["orden"]
    menu = page.locator(".menu ul a").all_inner_texts()
    print("menú:", menu)

    # ---------------- lectura de cada sección
    for sid in orden:
        page.goto(f"{URL}#/s/{sid}")
        page.wait_for_selector(f'[data-raiz="seccion:{sid}"]')
        page.wait_for_timeout(400)
        alto = page.evaluate("document.documentElement.scrollHeight")
        page.screenshot(path=f"{OUT}{sid}.png", full_page=True)
        vacios = page.locator(f'[data-raiz="seccion:{sid}"] .vacio').count()
        print(f"sección {sid:12} alto={alto}px  campos vacíos ocultos={vacios}  título='{page.title()}'")

    # ---------------- crucigrama
    page.goto(f"{URL}#/s/crucigrama")
    page.wait_for_selector(".celda input")
    celdas = page.locator(".celda input").count()
    h = page.locator(".cruci-pistas ol").nth(0).locator("li").count()
    v = page.locator(".cruci-pistas ol").nth(1).locator("li").count()
    page.locator(".celda input").first.click()
    page.keyboard.type("X")
    page.click("[data-accion=comprobar]")
    estado1 = page.locator(".cruci-estado").first.inner_text()
    page.click("[data-accion=solucion]")
    estado2 = page.locator(".cruci-estado").first.inner_text()
    faltan = page.locator(".cruci-palabras").count()
    print(f"crucigrama: {celdas} casillas, {h} horizontales + {v} verticales = {h + v} palabras | '{estado1}' | '{estado2}'")
    page.screenshot(path=f"{OUT}crucigrama_resuelto.png", full_page=False)

    # ---------------- móvil
    movil = nav.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2).new_page()
    registrar(movil)
    for sid in ("portada", "columna-3", "tira"):
        movil.goto(f"{URL}#/s/{sid}")
        movil.wait_for_selector(f'[data-raiz="seccion:{sid}"]')
        movil.wait_for_timeout(300)
        desborde = movil.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        movil.screenshot(path=f"{OUT}movil_{sid}.png", full_page=False)
        print(f"móvil {sid}: desborde horizontal = {desborde}px")

    # ---------------- modo edición
    page.goto(URL)
    page.wait_for_selector(".seccion-portada")
    page.click("#boton-editar")
    page.wait_for_selector(".barra-edicion")
    editables = page.locator("[contenteditable=true]").count()
    botones = page.locator(".agregar-item").count()
    titular = page.locator(".titular-apertura")
    titular.click()
    page.keyboard.press("End")
    page.keyboard.type(" (editado)")
    page.wait_for_timeout(1000)
    borrador = page.evaluate("localStorage.getItem('la-cuestion:borrador')")
    ok_borrador = borrador and "(editado)" in borrador
    print(f"edición: {editables} campos editables, {botones} botones «Añadir», borrador guardado={bool(ok_borrador)}")

    # añadir un elemento a la franja y deshacer
    antes = page.locator(".franja [data-item]").count()
    page.locator('.agregar-item[data-agregar="franja"]').click()
    despues = page.locator(".franja [data-item]").count()
    page.click(".barra-edicion [data-accion=deshacer]")
    tras_deshacer = page.locator(".franja [data-item]").count()
    print(f"franja: {antes} → añadir {despues} → deshacer {tras_deshacer}")

    # controles de elemento: mover la primera nota lateral hacia abajo
    primera = page.locator(".lateral [data-item]").first
    texto_antes = primera.locator("h2").inner_text()
    primera.hover()
    page.click(".control-item [data-c=bajar]")
    texto_despues = page.locator(".lateral [data-item]").nth(1).locator("h2").inner_text()
    print(f"mover nota lateral: {'OK' if texto_antes == texto_despues else 'FALLÓ'}")

    # nueva sección desde el panel
    page.click(".barra-edicion [data-accion=nueva]")
    page.wait_for_selector("dialog .nueva-seccion")
    page.select_option("#nueva-tipo", "columna")
    page.fill("#nueva-nombre", "Columna 6 · Prueba")
    page.click("dialog .nueva-seccion button[type=submit]")
    page.wait_for_selector('[data-raiz="seccion:columna-6-prueba"]')
    page.locator('[data-raiz="seccion:columna-6-prueba"] h1').click()
    page.keyboard.press("Control+A")
    page.keyboard.type("Titular de la nueva columna")
    page.wait_for_timeout(900)
    print("nueva sección en menú:", "columna 6 · prueba" in page.locator(".menu ul").inner_text().lower(), "| hash:", page.url.split("#")[-1])
    page.screenshot(path=f"{OUT}edicion_nueva_seccion.png", full_page=False)

    # imagen: abrir diálogo y poner una ruta
    page.locator('[data-raiz="seccion:columna-6-prueba"] img[data-img]').first.click()
    page.wait_for_selector("dialog #img-url")
    page.fill("#img-url", "imagenes/miniatura_calle.webp")
    page.click("dialog [data-guardar]")
    src = page.locator('[data-raiz="seccion:columna-6-prueba"] img[data-img]').first.get_attribute("src")
    print("imagen asignada:", src)

    # descarga ZIP
    with page.expect_download() as descarga:
        page.click(".barra-edicion [data-accion=descargar]")
    ruta_zip = OUT + "contenido.zip"
    descarga.value.save_as(ruta_zip)
    with zipfile.ZipFile(ruta_zip) as z:
        nombres = z.namelist()
        prueba = zipfile.ZipFile(ruta_zip).testzip()
        nueva = json.loads(z.read("contenido/secciones/columna-6-prueba.json"))
        edicion = json.loads(z.read("contenido/edicion.json"))
    print(f"ZIP: {len(nombres)} archivos, integridad={'OK' if prueba is None else prueba}, "
          f"nueva sección en orden={'columna-6-prueba' in edicion['orden']}, titular='{nueva['titulo']}'")

    # publicación con GitHub simulado
    page.route("https://api.github.com/**", github_simulado)
    page.evaluate("""localStorage.setItem('la-cuestion:github', JSON.stringify({propietario:'prueba', repositorio:'la-cuestion', rama:'main', token:'token-falso'}))""")
    page.click(".barra-edicion [data-accion=publicar]")
    page.wait_for_selector("dialog [data-publicar]")
    page.click("dialog [data-publicar]")
    page.wait_for_selector("#pub-progreso.ok, #pub-progreso.error", timeout=20000)
    print("publicación:", page.locator("#pub-progreso").inner_text())
    arbol = next((c for m, u, c in peticiones_github if m == "POST" and u.endswith("/git/trees")), "{}")
    entradas = json.loads(arbol)["tree"]
    borradas = [e["path"] for e in entradas if e["sha"] is None]
    subidas = [e["path"] for e in entradas if e["sha"]]
    print(f"commit simulado: {len(subidas)} archivos, eliminados={borradas}, incluye nueva={'contenido/secciones/columna-6-prueba.json' in subidas}")
    print("borrador tras publicar:", page.evaluate("localStorage.getItem('la-cuestion:borrador')") is None)
    page.keyboard.press("Escape")

    page.click(".barra-edicion [data-accion=salir]")
    print("salir de edición:", page.locator(".barra-edicion").count() == 0 and page.locator("[contenteditable=true]").count() == 0)
    nav.close()

print("\nERRORES:" if errores else "\nSin errores de consola ni excepciones.")
for e in errores:
    print("  ", e)
