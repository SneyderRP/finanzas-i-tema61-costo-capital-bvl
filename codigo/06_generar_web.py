# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: 2026-11-01

"""
GENERADOR DE LA PAGINA WEB.

Lee las tablas de salidas/ y el panel procesado, y escribe docs/, que
GitHub Pages sirve en https://<usuario>.github.io/<repositorio>/

Produce:
  docs/index.html          la pagina, con los datos incrustados
  docs/datos/*.csv         las ocho tablas, para quien las quiera crudas
  docs/datos/tablas.xlsx   las ocho tablas en un libro de Excel con formato
  docs/zips/*.zip          una descarga por carpeta, solo del material propio

Por que una pagina estatica y no un servidor: una pagina es un archivo, de
modo que carga en un segundo a cualquier hora y no se duerme por inactividad.
Un tablero servido por un plan gratuito se apaga tras unos dias sin visitas,
y quien escanea el codigo QR del poster se encuentra una pantalla de espera.

Sobre el material de terceros: los articulos en ingles pertenecen a sus
editoriales y las traducciones al espanol son obras derivadas, de modo que
el arbol de carpetas los lista pero la pagina no ofrece su descarga. Se
consultan por su DOI, que figura en las referencias del articulo.

ENTRADA
    salidas/tabla0_composicion_carteras.csv
    salidas/tabla1_descriptiva.csv
    salidas/tabla3_correlaciones.csv
    salidas/tabla4_betas.csv
    salidas/tabla5_costo_capital.csv
    salidas/tabla8_frontera_carteras.csv
    salidas/tabla9_desempeno_ajustado.csv
    salidas/tabla10_ganancia_diversificacion.csv
    datos_procesados/datos_procesados_2024200522B.csv
    codigo/plantilla_web.html

SALIDA
    docs/

Se ejecuta despues de 05_markowitz.py. No toca los datos crudos ni el panel.
"""

import csv
import io
import json
import math
import os
import re
import shutil
import sys
import zipfile
from collections import defaultdict
from pathlib import Path


def carpeta_del_codigo():
    """Ubica codigo/ tanto si esto corre como archivo como si se pega en una celda."""
    try:
        return Path(__file__).resolve().parent
    except NameError:
        pass
    cand = []
    if "C3" in globals():
        cand.append(Path(str(globals()["C3"])) / "codigo")
    cand += [Path.cwd(), Path.cwd() / "codigo", Path.cwd().parent / "codigo"]
    for c in cand:
        if (c / "utilidades.py").exists():
            return c.resolve()
    raise SystemExit("No encuentro utilidades.py. Ejecuta esto desde codigo/, "
                     "o define C3 antes de pegar la celda.")


AQUI = carpeta_del_codigo()
RAIZ = AQUI.parent          # la Carpeta 3
UNIDAD = RAIZ.parent        # la carpeta que contiene las tres
DOCS = RAIZ / "docs"
SALIDAS = RAIZ / "salidas"

DIAS_ANIO = 252
ORDEN = ["mineria", "banca", "construccion", "consumo"]

TABLAS = {
    "composicion":     ("tabla0_composicion_carteras", "0. Composición de las carteras"),
    "descriptiva":     ("tabla1_descriptiva", "1. Descriptiva de los retornos"),
    "adf":             ("tabla2_adf", "2. Prueba de raíz unitaria"),
    "correlaciones":   ("tabla3_correlaciones", "3. Correlaciones entre sectores"),
    "betas":           ("tabla4_betas", "4. Betas sectoriales"),
    "costo":           ("tabla5_costo_capital", "5. Costo de capital"),
    "robustez":        ("tabla6_betas_robustez", "6. Betas, prueba de robustez"),
    "diagnostico":     ("tabla7_diagnostico", "7. Diagnóstico de los residuos"),
    "frontera":        ("tabla8_frontera_carteras", "8. Carteras de la frontera"),
    "desempeno":       ("tabla9_desempeno_ajustado", "9. Desempeño ajustado por riesgo"),
    "diversificacion": ("tabla10_ganancia_diversificacion", "10. Ganancia de diversificar"),
}

# Los tres productos finales, que el script busca solo dentro de la carpeta de
# Productos y copia a docs/productos/. Asi, cuando se actualiza el journal, el
# poster o el beamer, basta volver a correr este script para que la web los tome.
#
#   (etiqueta, que es, nombre de salida, palabras que debe tener, palabras que no)
#
# Las palabras se comparan sin tildes y en minusculas, y cubren las dos grafias
# que aparecen en las carpetas ("journal" y "jorunal").
PRODUCTOS = [
    ("Journal", "El artículo completo", "journal.pdf",
     ("journal", "jorunal"), ("poster", "beamer")),
    ("Póster del journal", "El póster de la investigación", "poster.pdf",
     ("poster",), ("beamer",)),
    ("Beamer", "La presentación de la exposición", "beamer.pdf",
     ("beamer",), ()),
]

# Como se llama cada carpeta de la unidad y que etiqueta lleva en la pagina.
# Se buscan por una palabra suya porque los nombres varian entre maquinas.
CARPETAS = [
    ("producto",   "1. Productos",              ("producto",)),
    ("desarrollo", "2. Desarrollo",             ("desarr",)),
    ("base",       "3. Base de datos y código", ("base de datos",)),
]

# Subcarpetas cuyo contenido es de terceros: se listan, no se empaquetan
AJENO = ("articulos ingles", "articulos ingles", "traducidos", "traducidos")


def sin_tildes(texto):
    """Minusculas y sin acentos, para cruzar nombres de sector entre tablas.

    Hace falta porque unas tablas escriben Minería y Construcción con tilde y
    otras sin ella.
    """
    import unicodedata
    t = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower().strip()


def limpiar(nombre):
    """Deshace los escapes #UXXXX que deja la descompresion de algunos equipos."""
    return re.sub(r"#U([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), nombre)


def leer_tabla(nombre):
    ruta = SALIDAS / f"{nombre}.csv"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta.relative_to(RAIZ)}. Ejecuta antes "
                         "04_analisis.py y 05_markowitz.py.")
    with io.open(ruta, encoding="utf-8", newline="") as f:
        filas = list(csv.reader(f))
    cab = [c if c else "Sector" for c in filas[0]]
    return cab, [dict(zip(cab, fila)) for fila in filas[1:]]


def derivados():
    """Indice acumulado por sector y matriz de covarianzas, desde el panel."""
    ruta = RAIZ / "datos_procesados" / "datos_procesados_2024200522B.csv"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta.relative_to(RAIZ)}.")
    filas = list(csv.DictReader(io.open(ruta, encoding="utf-8")))

    por_sec = defaultdict(dict)
    fechas = []
    vistas = set()
    for f in filas:
        por_sec[f["sector"]][f["fecha"]] = float(f["Y_retorno_sector"])
        if f["fecha"] not in vistas:
            vistas.add(f["fecha"])
            fechas.append(f["fecha"])
    fechas.sort()

    # El primer dia es la base y vale 100 exacto; su retorno no se aplica porque
    # no hay dia anterior contra el cual medirlo. Del segundo en adelante se
    # capitaliza el retorno logaritmico diario.
    indice = {}
    for s in ORDEN:
        acum, v = 100.0, [100.0]
        for fe in fechas[1:]:
            acum *= math.exp(por_sec[s].get(fe, 0.0) / 100.0)
            v.append(round(acum, 2))
        indice[s] = v

    ret = {s: [por_sec[s].get(fe, 0.0) for fe in fechas] for s in ORDEN}
    media = {s: sum(ret[s]) / len(fechas) for s in ORDEN}
    n = len(fechas)
    cov = {}
    for a in ORDEN:
        for b in ORDEN:
            c = sum((ret[a][i] - media[a]) * (ret[b][i] - media[b])
                    for i in range(n)) / (n - 1)
            cov[a + "|" + b] = round(c * DIAS_ANIO, 6)

    # Que sector rindio mas cada dia, una letra por sesion. Se calcula aqui y no
    # en el navegador porque alli solo llega el indice redondeado a dos decimales,
    # y en las sesiones donde dos sectores quedan casi empatados ese redondeo
    # basta para cambiar el ganador: contra el panel original fallaba en nueve de
    # las 917. La primera fecha no entra: es la base y no tiene dia anterior.
    letra = {s: s[0] for s in ORDEN}        # m, b, c, consumo comparte la c
    letra["consumo"] = "u"
    ganador = ""
    for fe in fechas[1:]:
        hoy = {s: por_sec[s][fe] for s in ORDEN if fe in por_sec[s]}
        ganador += letra[max(hoy, key=hoy.get)] if hoy else "-"

    # El panel en crudo, que es lo que permite rehacer las betas en el navegador
    # para cualquier ventana de fechas. Sin esto, mover la ventana solo podria
    # recortar los graficos, no reestimar nada. Los regresores son los mismos
    # tres que usa 04_analisis.py, de modo que la cuenta del navegador es la
    # misma del articulo y no una aproximacion.
    reg = {"X1": [], "X2": [], "X3": []}
    for fe in fechas:
        fila = next((f for f in filas if f["fecha"] == fe), None)
        reg["X1"].append(float(fila["X1_retorno_mercado"]) if fila else 0.0)
        reg["X2"].append(float(fila["X2_treasury_10a"]) if fila else 0.0)
        reg["X3"].append(float(fila["X3_tipo_cambio"]) if fila else 0.0)

    return {
        "fechas": fechas, "indice": indice, "dias": DIAS_ANIO,
        "mu": {s: round(media[s] * DIAS_ANIO, 6) for s in ORDEN},
        "cov": cov,
        "gana": ganador,
        "letra": {v: k for k, v in letra.items()},
        "y": {s: [round(por_sec[s].get(fe, 0.0), 4) for fe in fechas] for s in ORDEN},
        "x": {k: [round(v, 4) for v in reg[k]] for k in reg},
        "rezagos": 5,                      # los mismos de Newey-West en Python
    }


def nodo(ruta, nombre, heredado=False):
    es_ajeno = heredado or any(a in limpiar(nombre).lower() for a in AJENO)
    subs, archivos, peso = [], [], 0
    try:
        entradas = sorted(os.listdir(ruta))
    except OSError:
        entradas = []
    for e in entradas:
        p = ruta / e
        if e.startswith(".") or e in ("__pycache__", "docs"):
            continue
        if p.is_dir():
            h = nodo(p, e, es_ajeno)
            subs.append(h)
            peso += h["b"]
        elif p.is_file():
            s = p.stat().st_size
            archivos.append({"n": limpiar(e), "b": s})
            peso += s
    return {"n": limpiar(nombre), "b": peso, "d": subs, "f": archivos,
            "ajeno": es_ajeno}


def arbol():
    """Recorre las tres carpetas de la unidad. Las que no esten, se omiten."""
    fuera = []
    salida = []
    for slug, etiqueta, pistas in CARPETAS:
        hallada = None
        for p in sorted(UNIDAD.iterdir()) if UNIDAD.exists() else []:
            if p.is_dir() and any(x in p.name.lower() for x in pistas):
                hallada = p
                break
        if hallada is None:
            fuera.append(etiqueta)
            continue
        h = nodo(hallada, etiqueta)
        h["slug"] = slug
        h["ruta"] = hallada.name
        salida.append(h)
    return salida, fuera


def cuenta(n):
    return len(n["f"]) + sum(cuenta(d) for d in n["d"])


def zip_carpeta(origen, destino, saltar_ajeno=True):
    """Comprime una carpeta conservando sus subcarpetas. Omite lo ajeno."""
    n = 0
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for d, subs, archivos in os.walk(origen):
            subs[:] = [s for s in subs
                       if s not in ("__pycache__", ".ipynb_checkpoints", ".git", "docs")]
            rel = Path(d).relative_to(origen)
            if saltar_ajeno and any(a in limpiar(str(rel)).lower() for a in AJENO):
                subs[:] = []
                continue
            for a in sorted(archivos):
                # Los .zip propios si entran: los posters de la carpeta 2 son
                # archivos comprimidos. La recursion no ocurre porque docs/ ya
                # queda fuera del recorrido unas lineas mas arriba.
                if a.startswith("."):
                    continue
                p = Path(d) / a
                z.write(p, Path(origen.name) / rel / limpiar(a))
                n += 1
    return n


# Pie de cada figura. El titulo ya va dentro de la imagen, de modo que el pie
# dice que mira quien la ve y en que seccion del articulo aparece. Una figura
# que no este aqui se publica igual, con su nombre de archivo como pie.
PIES = {
    "figura1": ("Evolución acumulada", "Resultados",
                "Cuanto acumula cada cartera a lo largo de los cinco años. "
                "La minería despega desde 2025 y el consumo se queda plano."),
    "figura2": ("Retornos diarios", "Resultados",
                "Un panel por sector. Las barras largas son las sesiones de "
                "mayor movimiento y se ven agrupadas, que es lo que corrigen "
                "los errores de Newey y West."),
    "figura3": ("Minería frente al mercado", "Resultados",
                "Cada punto es una sesión. La pendiente de la recta es la beta: "
                "la más inclinada de las cuatro."),
    "figura4": ("Banca frente al mercado", "Resultados",
                "La nube más ajustada a la recta después de la minería, con un "
                "R cuadrado de 0,59."),
    "figura5": ("Consumo frente al mercado", "Resultados",
                "La pendiente más plana: el consumo amortigua el movimiento "
                "del mercado."),
    "figura6": ("Construcción frente al mercado", "Resultados",
                "Nube más dispersa que las anteriores; el mercado explica "
                "menos de la mitad de su variación."),
    "figura7": ("Betas por sector", "Resultados",
                "Las cuatro betas ordenadas, con la línea del mercado en 1,0 "
                "como referencia."),
    "figura8": ("Costo de capital por sector", "Resultados",
                "El resultado principal del artículo, con la tasa libre de "
                "riesgo marcada."),
    "figura9": ("Frontera eficiente", "Resultados",
                "200 000 carteras con semilla 522. El color es el ratio de "
                "Sharpe y las marcas son la cartera tangente y la de mínima "
                "varianza."),
    "figura10": ("Línea del mercado de valores", "Resultados",
                 "Dónde cae cada sector respecto de lo que el CAPM le exigiría "
                 "por su beta."),
}

ANCHO_MINIATURA = 1000


def aviso_betas_figuras():
    """Avisa cuando la beta dibujada en una figura no es la de la tabla 4.

    Las figuras 3 a 6 trazan la recta con una regresion simple del sector
    contra el mercado, mientras que la tabla 4 estima una regresion multiple
    que ademas controla por el Tesoro y el tipo de cambio. Las dos betas son
    correctas pero no son la misma, y quien compare la figura con la tabla
    vera dos numeros distintos. El pie lo declara, con las cifras calculadas
    aqui y no escritas a mano, de modo que siguen siendo ciertas si el
    analisis se reestima.
    """
    panel = RAIZ / "datos_procesados" / "datos_procesados_2024200522B.csv"
    t4 = SALIDAS / "tabla4_betas.csv"
    if not panel.exists() or not t4.exists():
        return {}

    try:
        tabla = {sin_tildes(f["Sector"]): float(f["Beta"])
                 for f in csv.DictReader(io.open(t4, encoding="utf-8"))}
        filas = list(csv.DictReader(io.open(panel, encoding="utf-8")))
    except (KeyError, ValueError, OSError):
        return {}

    # Las figuras 3 a 6 van en el orden en que 04_analisis.py recorre las
    # carteras: mineria, banca, consumo y construccion.
    ORDEN_FIG = ["mineria", "banca", "consumo", "construccion"]
    avisos = {}
    for i, sector in enumerate(ORDEN_FIG, start=3):
        xs = [(float(f["X1_retorno_mercado"]), float(f["Y_retorno_sector"]))
              for f in filas if f["sector"] == sector]
        if len(xs) < 50 or sin_tildes(sector) not in tabla:
            continue
        n = len(xs)
        mx = sum(a for a, _ in xs) / n
        my = sum(b for _, b in xs) / n
        sxy = sum((a - mx) * (b - my) for a, b in xs)
        sxx = sum((a - mx) ** 2 for a, _ in xs)
        if sxx == 0:
            continue
        simple = sxy / sxx                       # la pendiente que dibuja la figura
        multiple = tabla[sin_tildes(sector)]
        if abs(simple - multiple) < 0.005:
            continue                             # practicamente la misma, no hay que avisar
        avisos[f"figura{i}"] = (
            f" La recta dibujada tiene pendiente {simple:.4f}".replace(".", ",") +
            f", y la tabla 4 da {multiple:.4f}".replace(".", ",") +
            " para este sector: la figura traza una regresión simple contra el "
            "mercado y la tabla estima una múltiple que además controla por el "
            "Tesoro y el tipo de cambio.")
    return avisos


def copiar_figuras():
    """Lleva las figuras a docs/figuras/ y hace una miniatura de cada una.

    Las originales van a 300 puntos por pulgada y pesan hasta un megabyte, de
    modo que mostrarlas enteras en una galeria haria la pagina lenta. Se
    publica la miniatura para mirar y la original para descargar.
    """
    origen = SALIDAS
    destino = DOCS / "figuras"
    destino.mkdir(exist_ok=True)

    try:
        from PIL import Image
    except ImportError:
        Image = None

    extra = aviso_betas_figuras()

    salida = []
    for p in sorted(origen.glob("figura*.png"),
                    key=lambda x: int(re.match(r"figura(\d+)", x.name).group(1))):
        clave = re.match(r"figura\d+", p.name).group(0)
        shutil.copy2(p, destino / p.name)

        mini = None
        if Image is not None:
            try:
                with Image.open(p) as im:
                    an, al = im.size
                    if an > ANCHO_MINIATURA:
                        nueva = im.convert("RGB").resize(
                            (ANCHO_MINIATURA, round(al * ANCHO_MINIATURA / an)),
                            Image.LANCZOS)
                        nombre = p.stem + "_mini.jpg"
                        nueva.save(destino / nombre, "JPEG", quality=86,
                                   optimize=True)
                        mini = f"figuras/{nombre}"
            except Exception:
                mini = None

        titulo, seccion, pie = PIES.get(
            clave, (p.stem.replace("_", " "), "", ""))
        salida.append({
            "n": int(clave.replace("figura", "")),
            "t": titulo, "s": seccion, "p": pie + extra.get(clave, ""),
            "img": mini or f"figuras/{p.name}",
            "full": f"figuras/{p.name}",
            "kb": round(p.stat().st_size / 1024),
        })
    return salida


def copiar_productos(arb):
    """Busca el journal, el poster y el beamer en la carpeta de Productos.

    Devuelve la lista que va a la pagina: (etiqueta, descripcion, ruta, existe).
    Si un producto no aparece, la pagina lo muestra apagado en lugar de ofrecer
    un enlace roto. Entre varios candidatos se queda con el mas reciente.
    """
    destino = DOCS / "productos"
    destino.mkdir(exist_ok=True)

    origen = None
    for c in arb:
        if c["slug"] == "producto":
            origen = UNIDAD / c["ruta"]
    candidatos = []
    if origen and origen.exists():
        for d, subs, archivos in os.walk(origen):
            if any(a in limpiar(d).lower() for a in AJENO):
                subs[:] = []
                continue
            for a in archivos:
                if a.lower().endswith(".pdf"):
                    candidatos.append(Path(d) / a)

    salida = []
    for etiqueta, que, nombre, tiene, nolleva in PRODUCTOS:
        hallados = []
        for p in candidatos:
            # Se mira la ruta entera porque el nombre del archivo no siempre
            # dice de que producto se trata, pero su carpeta si.
            t = limpiar(str(p)).lower()
            if any(x in t for x in tiene) and not any(x in t for x in nolleva):
                # "Posters" (los treinta de las apreciaciones) no es el poster
                # del journal, de modo que esa carpeta queda fuera.
                if nombre == "poster.pdf" and "posters" in t:
                    continue
                hallados.append(p)
        if hallados:
            # Cuando hay varias versiones del mismo producto, gana la que se
            # declara oficial en su nombre. Solo si ninguna lo dice se recurre
            # a la mas reciente: en la carpeta llegaron a convivir el journal
            # oficial de 28 paginas y un borrador de 30 guardado dos minutos
            # despues, y por fecha se habria publicado el borrador.
            oficiales = [p for p in hallados
                         if "oficial" in limpiar(p.name).lower()]
            mejor = max(oficiales or hallados, key=lambda p: p.stat().st_mtime)
            shutil.copy2(mejor, destino / nombre)
            paginas = contar_paginas(destino / nombre)
            detalle = que + (f", {paginas} paginas" if paginas and paginas > 1
                             else ", 1 pagina" if paginas == 1 else "")
            salida.append([etiqueta, detalle, f"productos/{nombre}", True,
                           round((destino / nombre).stat().st_size / 1048576, 1)])
        else:
            salida.append([etiqueta, que, f"productos/{nombre}", False, 0])
    return salida


def leer_log(maximo=420):
    """Lleva el registro de ejecucion a la pagina, para mostrarlo tal cual.

    El log es la prueba de que el proceso ocurrio: lleva las marcas de tiempo,
    los codigos HTTP, los conteos de filas y el SHA-256 del panel. Se publica
    con el numero de linea real de cada entrada, de modo que cualquiera pueda
    abrir el archivo y comprobar que dice eso en ese sitio.

    De las 657 lineas se escogen las que informan, no todas: interesan las
    peticiones, los conteos y los hashes, no los encabezados repetidos.
    """
    ruta = RAIZ / "log_ejecucion.txt"
    if not ruta.exists():
        return {"lineas": [], "total": 0}

    try:
        crudas = io.open(ruta, encoding="utf-8", errors="replace").read().split("\n")
    except OSError:
        return {"lineas": [], "total": 0}

    INTERESA = re.compile(
        r"HTTP \d{3}|filas=|SHA-256|sha256|descarta|Descartad|GET |guardad|Guardad|"
        r"Tabla final|Salida generada|congelad|CONGELAD|Analisis:|ventana", re.I)

    lineas = []
    for i, L in enumerate(crudas, start=1):
        t = L.rstrip()
        if not t or not INTERESA.search(t):
            continue
        m = re.match(r"\[([\d-]+) ([\d:]+)\]\s*(.*)$", t)
        lineas.append({
            "n": i,
            "f": (m.group(1)[5:] + " " + m.group(2)) if m else "",
            "t": (m.group(3) if m else t)[:200],
        })

    # Si hay mas de las que caben, se conserva el principio y el final, que es
    # donde estan el arranque de la extraccion y el hash de la tabla final.
    if len(lineas) > maximo:
        mitad = maximo // 2
        lineas = lineas[:mitad] + [{"n": 0, "f": "", "t": "..."}] + lineas[-mitad:]

    return {"lineas": lineas, "total": len([x for x in crudas if x.strip()])}


def leer_flujo():
    """De que cartera viene cada accion y en cual acabo.

    La tabla 0 lleva, por accion, el sector que le da la BVL y el que le
    asigna el articulo. Diez de las dieciseis no coinciden, y ese es el punto
    que mas se le puede discutir al trabajo, de modo que la pagina lo dibuja
    en lugar de esconderlo en una tabla.
    """
    ruta = SALIDAS / "tabla0_composicion_carteras.csv"
    if not ruta.exists():
        return []
    try:
        filas = list(csv.DictReader(io.open(ruta, encoding="utf-8")))
    except OSError:
        return []
    if not filas:
        return []

    cols = list(filas[0].keys())
    def busca(*pistas):
        for c in cols:
            if any(p in sin_tildes(c) for p in pistas):
                return c
        return None

    c_nem = busca("nemo", "simbolo", "ticker")
    c_emp = busca("empresa", "razon", "nombre")
    c_bvl = busca("bvl", "oficial", "clasificacion")
    c_mio = busca("cartera", "asignad")
    c_mon = busca("moneda")
    c_rea = busca("reasignad")
    if not ((c_nem or c_emp) and c_mio):
        return []

    salida = []
    for f in filas:
        destino = (f.get(c_mio) or "").strip()
        if not destino:
            continue
        origen = (f.get(c_bvl) or "").strip()
        # La tabla trae una columna que ya dice si la accion cambio de cartera.
        # Se prefiere a comparar los dos nombres, porque la BVL escribe sus
        # sectores en plural y en mayusculas (MINERAS) y el articulo en
        # singular (Mineria), de modo que la comparacion directa marcaria como
        # movidas las dieciseis.
        if c_rea:
            movida = sin_tildes(f.get(c_rea) or "").startswith("s")
        else:
            movida = bool(origen) and sin_tildes(origen) != sin_tildes(destino)
        salida.append({
            "n": (f.get(c_nem) or "").strip(),
            "e": (f.get(c_emp) or "").strip(),
            "o": origen,
            "d": destino,
            "m": (f.get(c_mon) or "").strip(),
            "mov": movida,
        })
    return salida


def leer_referencias(pdf):
    """Saca la bibliografia del journal, cada entrada con su DOI si lo tiene.

    Se lee del PDF y no de una lista escrita a mano para que la pagina siga la
    bibliografia del articulo: si cambia el journal, cambia la seccion. Si algo
    no se puede leer se devuelve una lista vacia y la pagina omite la seccion,
    en lugar de mostrar referencias a medias.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return []
    try:
        r = PdfReader(str(pdf))
    except Exception:
        return []

    texto = ""
    for i, p in enumerate(r.pages):
        t = p.extract_text() or ""
        if not texto and "\nReferencias\n" in t:
            texto = t[t.index("\nReferencias\n") + 13:]
        elif texto:
            texto += "\n" + t
    if not texto:
        return []

    # El apendice va despues de la bibliografia y no forma parte de ella.
    for corte in ("Datos, código y verificación", "Datos, codigo y verificacion",
                  "Apéndice", "Apendice", "A.1 Repositorio"):
        if corte in texto:
            texto = texto[:texto.index(corte)]

    # El encabezado y el numero de pagina se repiten en cada hoja y no son parte
    # de ninguna referencia, de modo que se quitan antes de separar.
    texto = "\n".join(
        L for L in texto.split("\n")
        if not re.fullmatch(r"\s*(\d{1,3}|[A-ZÁÉÍÓÚÑ \d.]{12,})\s*", L))

    # Sangria francesa: la entrada empieza pegada al margen y sigue indentada.
    # No basta con que la linea arranque en mayuscula y lleve coma: el nombre de
    # una revista partido por el salto de linea ("Finance, 72(Parte A)...") da el
    # mismo patron y cortaba la referencia en dos. Se exige ademas un anio de
    # cuatro cifras entre parentesis cerca del inicio, que toda entrada trae y
    # ninguna continuacion tiene.
    arranca = re.compile(r"^[A-ZÁÉÍÓÚÑÇÖŞĞİ][\w’'áéíóúñçöşğıİ-]+(?:,| y )")
    anio = re.compile(r"\((?:19|20)\d{2}[a-z]?\)")
    entradas, act = [], ""
    for linea in texto.split("\n"):
        s = linea.strip()
        if not s:
            continue
        nueva = (act and arranca.match(linea) and not linea.startswith(" ")
                 and anio.search(s[:130]))
        if nueva:
            entradas.append(act)
            act = s
        else:
            act = (act + " " + s) if act else s
    if act:
        entradas.append(act)

    salida = []
    for e in entradas:
        t = re.sub(r"\s+", " ", e).replace("https: //", "https://")
        # El salto de linea del PDF parte las direcciones por cualquier sitio
        # ("https://www.jsto r.org/..."). En una referencia APA el enlace es lo
        # ultimo, de modo que se quitan todos los espacios desde que empieza.
        m = re.search(r"https?://", t)
        if m:
            # Se pegan los trozos mientras parezcan parte de la direccion. No se
            # quitan todos los espacios hasta el final porque el encabezado de la
            # pagina del PDF ("BETAS SECTORIALES Y ...") cae justo detras y se
            # colaba dentro del DOI.
            trozos = t[m.start():].split(" ")
            enlace, resto = trozos[0], []
            for i, p in enumerate(trozos[1:]):
                if (not p or re.search(r"[A-ZÁÉÍÓÚÑ]{2,}", p)
                        or re.match(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]", p)):
                    resto = trozos[i+1:]
                    break
                enlace += p
            t = (t[:m.start()] + enlace + (" " + " ".join(resto) if resto else "")).strip()
        # Se busca desde el "https://" y no desde "doi.org/", porque al cortar
        # por este ultimo el prefijo se quedaba pegado al final del texto y
        # cada referencia terminaba en un "https://." suelto.
        m = re.search(r"(?:https?://)?(?:dx\.)?doi\.org/(10\.\d{4,9}/[^\s]+)", t)
        doi, url = None, None
        if m:
            # La extraccion del PDF arrastra tildes sueltas de los nombres
            # turcos, de modo que el DOI se recorta a sus caracteres validos.
            doi = re.match(r"10\.\d{4,9}/[A-Za-z0-9._;()/:<>+\[\]-]*",
                           m.group(1)).group(0).rstrip(".").rstrip(")")
            t = t[:m.start()].rstrip()                 # el enlace va aparte
        else:
            # Las fuentes clasicas (Markowitz, Jensen) no tienen DOI pero si un
            # enlace estable, de modo que ese se usa para que tambien se abran.
            u = re.search(r"https?://\S+", t)
            if u:
                url = u.group(0).rstrip(".").rstrip(")")
                t = t[:u.start()].rstrip()
        # La extraccion separa la cedilla de su letra en los apellidos turcos:
        # "Ta¸ s" tiene que leerse "Taş".
        for suelto, junto in (("¸ s", "ş"), ("¸ S", "Ş"), ("¸ c", "ç"), ("¸ C", "Ç"),
                              ("¸s", "ş"), ("¸c", "ç")):
            t = t.replace(suelto, junto)

        # Tambien despega la primera letra de algunas palabras ("V olatility").
        # Se vuelven a unir salvo cuando esa letra sola es una palabra de pleno
        # derecho: el articulo ingles "A study", la conjuncion "y", "o", "e".
        t = re.sub(r"\b([B-DF-HJ-NP-TV-Z]) ([a-z]{3,})", r"\1\2", t)
        t = re.sub(r"\b([A-Z]) \.", r"\1.", t)      # iniciales: "Y . O." -> "Y. O."

        # El salto de linea del PDF deja espacios antes de la puntuacion
        # ("Review , 22(1)") y a veces ninguno despues de un punto.
        t = re.sub(r"\s+([,.;:)])", r"\1", t)
        t = re.sub(r"(?<=[a-z])\.(?=[A-ZÁÉÍÓÚ])", ". ", t)
        t = re.sub(r"\s{2,}", " ", t).rstrip(" .,;") + "."
        if len(t) > 40:
            salida.append({"t": t, "doi": doi, "url": url})

    # Si la extraccion salio pobre es que el PDF cambio de forma: mejor nada
    # que una bibliografia a medias.
    return salida if len(salida) >= 10 else []


def contar_paginas(pdf):
    """Numero de paginas del PDF, o None si no se puede saber.

    Se usa pypdf y no un conteo de "/Type /Page" sobre los bytes porque un PDF
    moderno guarda el catalogo en flujos comprimidos y ese texto no aparece en
    claro. Si pypdf no esta instalado se devuelve None y la pagina simplemente
    no muestra el numero, en lugar de mostrar uno inventado.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        return len(PdfReader(str(pdf)).pages)
    except Exception:
        return None


def escribir_excel(tablas):
    """Un libro con una hoja por tabla. Si falta openpyxl, se omite sin fallar."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return None

    wb = Workbook()
    wb.remove(wb.active)
    cab_fill = PatternFill("solid", fgColor="1A4F8A")
    cab_font = Font(color="FFFFFF", bold=True, size=10)
    par_fill = PatternFill("solid", fgColor="EEF3F8")
    borde = Border(bottom=Side(style="thin", color="C9D2DB"))

    # Excel no admite nombres de hoja de mas de 31 caracteres y los corta sin
    # avisar, de modo que aqui se acorta a proposito y con sentido.
    CORTO = {
        "composicion": "0. Composicion de carteras",
        "descriptiva": "1. Descriptiva",
        "adf": "2. Raiz unitaria",
        "correlaciones": "3. Correlaciones",
        "betas": "4. Betas",
        "costo": "5. Costo de capital",
        "robustez": "6. Betas robustez",
        "diagnostico": "7. Diagnostico",
        "frontera": "8. Frontera",
        "desempeno": "9. Desempeno ajustado",
        "diversificacion": "10. Diversificacion",
    }

    for clave, (archivo, titulo) in TABLAS.items():
        cab, filas = tablas[clave]
        hoja = wb.create_sheet(CORTO.get(clave, titulo)[:31])
        hoja.append(cab)
        for c in range(1, len(cab) + 1):
            cel = hoja.cell(row=1, column=c)
            cel.fill, cel.font = cab_fill, cab_font
            cel.alignment = Alignment(horizontal="center", vertical="center",
                                      wrap_text=True)
        for i, f in enumerate(filas):
            fila = []
            for c in cab:
                v = f.get(c, "")
                try:
                    fila.append(float(v) if v not in ("", None) else "")
                except (TypeError, ValueError):
                    fila.append(v)
            hoja.append(fila)
            for c in range(1, len(cab) + 1):
                cel = hoja.cell(row=i + 2, column=c)
                cel.border = borde
                if i % 2:
                    cel.fill = par_fill
                if isinstance(cel.value, float):
                    # Un p-valor de 5e-71 con formato de cuatro decimales se
                    # veria como 0,0000 y pareceria un cero exacto, de modo que
                    # los numeros muy pequenos van en notacion cientifica.
                    v = abs(cel.value)
                    cel.number_format = ("0.00E+00" if 0 < v < 1e-4
                                         else "0" if cel.value == int(cel.value)
                                         else "0.0000")
        for c, nombre in enumerate(cab, start=1):
            ancho = max(len(str(nombre)) + 2,
                        *[len(str(f.get(nombre, ""))[:28]) + 2 for f in filas] or [10])
            hoja.column_dimensions[get_column_letter(c)].width = min(34, ancho)
        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions

    destino = DOCS / "datos" / "tablas.xlsx"
    wb.save(destino)
    return destino


def main():
    tablas = {k: leer_tabla(v[0]) for k, v in TABLAS.items()}
    datos = {k: v[1] for k, v in tablas.items()}

    DOCS.mkdir(exist_ok=True)
    (DOCS / "datos").mkdir(exist_ok=True)
    (DOCS / "zips").mkdir(exist_ok=True)
    for archivo, _ in TABLAS.values():
        shutil.copy2(SALIDAS / f"{archivo}.csv", DOCS / "datos" / f"{archivo}.csv")

    print("Generando la pagina")
    print(f"  {len(TABLAS)} tablas, {sum(len(v) for v in datos.values())} filas")

    xl = escribir_excel(tablas)
    print("  Excel     :", "datos/tablas.xlsx" if xl else
          "omitido, falta openpyxl (pip install openpyxl)")

    der = derivados()
    print(f"  panel     : {len(der['fechas'])} fechas por sector")

    arb, fuera = arbol()
    print(f"  carpetas  : {len(arb)} de 3"
          + (f"  (sin hallar: {', '.join(fuera)})" if fuera else ""))

    productos = copiar_productos(arb)
    for et, _, ruta, hay, mb in productos:
        print(f"    {et:20}", f"{ruta}  {mb} MB" if hay else "NO SE HALLO")

    figuras = copiar_figuras()
    con_mini = sum(1 for f in figuras if "_mini" in f["img"])
    print(f"  figuras   : {len(figuras)}, {con_mini} con miniatura")

    log = leer_log()
    print(f"  registro  : {len(log['lineas'])} lineas publicadas "
          f"de {log['total']} del archivo")

    flujo = leer_flujo()
    movidas = sum(1 for f in flujo if f["mov"])
    print(f"  carteras  : {len(flujo)} acciones, {movidas} reasignadas "
          f"respecto de la BVL")

    refs = []
    journal = DOCS / "productos" / "journal.pdf"
    if journal.exists():
        refs = leer_referencias(journal)
    con_doi = sum(1 for r in refs if r["doi"])
    con_url = sum(1 for r in refs if r.get("url"))
    print(f"  referencias: {len(refs)}" +
          (f", {con_doi} con DOI, {con_url} con otro enlace, "
           f"{len(refs)-con_doi-con_url} sin enlace" if refs
           else "  (no se pudieron leer del journal)"))

    zips = {}
    for c in arb:
        origen = UNIDAD / c["ruta"]
        destino = DOCS / "zips" / f"{c['slug']}.zip"
        n = zip_carpeta(origen, destino)
        zips[c["slug"]] = {"archivos": n,
                           "bytes": destino.stat().st_size,
                           "url": f"zips/{c['slug']}.zip"}
        print(f"    {c['n']}: {n} archivos -> "
              f"{destino.stat().st_size / 1048576:.1f} MB")

    plantilla = AQUI / "plantilla_web.html"
    if not plantilla.exists():
        raise SystemExit(f"Falta {plantilla.name} junto a este script.")
    html = io.open(plantilla, encoding="utf-8").read()
    if "/*__DATOS__*/" not in html:
        raise SystemExit("La plantilla no tiene la marca de los datos.")

    bloque = (
        "const DATOS = " + json.dumps(datos, ensure_ascii=False) + ";\n"
        "const DER = " + json.dumps(der, ensure_ascii=False) + ";\n"
        "const ARBOL = " + json.dumps(arb, ensure_ascii=False) + ";\n"
        "const ZIPS = " + json.dumps(zips, ensure_ascii=False) + ";\n"
        "const PRODUCTOS = " + json.dumps(productos, ensure_ascii=False) + ";\n"
        "const REFS = " + json.dumps(refs, ensure_ascii=False) + ";\n"
        "const FIGURAS = " + json.dumps(figuras, ensure_ascii=False) + ";\n"
        "const LOG = " + json.dumps(log, ensure_ascii=False) + ";\n"
        "const FLUJO = " + json.dumps(flujo, ensure_ascii=False) + ";\n"
        "const TITULOS = " + json.dumps(
            {k: {"t": v[1], "a": v[0] + ".csv"} for k, v in TABLAS.items()},
            ensure_ascii=False) + ";"
    )
    html = html.replace("/*__DATOS__*/", bloque, 1)

    destino = DOCS / "index.html"
    io.open(destino, "w", encoding="utf-8").write(html)
    print(f"  pagina    : docs/index.html ({len(html.encode()) / 1024:.0f} KB)")

    faltan = [et for et, _, _, hay, _ in productos if not hay]
    if faltan:
        print("\nNo se hallo el PDF de: " + ", ".join(faltan) +
              ".\nLa pagina los muestra apagados. Ponlos en la carpeta de Productos "
              "y vuelve a correr este script.")

    print("\nPara publicarla:")
    print('  git add docs && git commit -m "Actualiza la web" && git push')


if __name__ == "__main__":
    main()
