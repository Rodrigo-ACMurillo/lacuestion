# -*- coding: utf-8 -*-
"""Prueba del borrador local (aviso al recargar) y de la regeneración del crucigrama al editar palabras."""
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/"
errores = []

with sync_playwright() as p:
    nav = p.chromium.launch(channel="msedge", headless=True)
    page = nav.new_page(viewport={"width": 1280, "height": 900})
    page.on("pageerror", lambda e: errores.append(str(e)))
    page.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)

    page.goto(f"{URL}#/s/crucigrama")
    page.wait_for_selector(".celda input")
    antes = page.locator(".celda input").count()
    page.click("#boton-editar")
    page.wait_for_selector(".barra-edicion")
    palabra = page.locator('[data-e="palabras.22.palabra"]')
    palabra.click()
    page.keyboard.press("Control+A")
    page.keyboard.type("ANOMIA")
    page.locator(".titular-l").click()          # sale del campo: la rejilla se rehace
    page.wait_for_timeout(1500)
    despues = page.locator(".celda input").count()
    pistas = page.locator(".cruci-pistas li").count()
    print(f"crucigrama: casillas {antes} → {despues}, pistas={pistas}, palabra guardada='{page.locator('[data-e=\"palabras.22.palabra\"]').inner_text()}'")

    page.reload()
    page.wait_for_selector(".celda input")
    aviso = page.locator(".aviso-borrador")
    print("aviso de borrador al recargar:", aviso.count() == 1)
    page.click(".aviso-borrador [data-b=usar]")
    page.wait_for_selector(".barra-edicion")
    print("borrador recuperado en modo edición:", page.locator('[data-e="palabras.22.palabra"]').inner_text() == "ANOMIA")

    page.click(".barra-edicion [data-accion=salir]")
    page.reload()
    page.wait_for_selector(".aviso-borrador")
    page.click(".aviso-borrador [data-b=descartar]")
    page.reload()
    page.wait_for_selector(".celda input")
    print("borrador descartado:", page.locator(".aviso-borrador").count() == 0 and page.evaluate("localStorage.getItem('la-cuestion:borrador')") is None)

    page.goto(f"{URL}?editar#/s/portada")
    page.wait_for_selector(".barra-edicion")
    print("parámetro ?editar abre el editor:", page.locator("[contenteditable=true]").count() > 0)
    nav.close()

print("Sin errores." if not errores else f"ERRORES: {errores}")
