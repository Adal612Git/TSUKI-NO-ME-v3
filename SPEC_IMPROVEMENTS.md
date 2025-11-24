# 🧩 REPORTE TÉCNICO – Fallo en el Scraper Fandom + Requerimientos de Optimización y Blindaje

## 📌 1. Descripción del problema
Durante la ejecución del pipeline en `orchestrator.py`, el scraper Fandom falla con un error:

```
HTTPError: 404 Client Error: Not Found for url: https://naruto.fandom.com/wiki/List_of_Story_Arcs
```

Este error provoca que el módulo `tenacity` reintente varias veces y finalmente el programa completo termina con:

```
tenacity.RetryError
```

Deteniendo todo el pipeline.

---

## 📌 2. Causa raíz confirmada
El scraper apunta a una URL **incorrecta / obsoleta**, la cual ya no existe en Fandom:

```
https://naruto.fandom.com/wiki/List_of_Story_Arcs
```

Fandom cambió la estructura y esa URL ahora responde **404 Not Found**.

Las URLs válidas actualmente son:

```
https://naruto.fandom.com/wiki/Story_Arcs
https://naruto.fandom.com/wiki/Category:Story_Arcs
https://naruto.fandom.com/es/wiki/Arcos_Argumentales
```

---

## 📌 3. Impacto en el pipeline
* Bloquea todo el flujo `scraping → cleaning → metrics → report`.
* Tenacity agota todos los reintentos.
* No se generan:
  * `fandom_arcs.tsv`
  * `naruto_analysis.db`
  * `naruto_analysis.xlsx`
  * `metrics.json`
  * `report.html`

Sistema queda inutilizable.

---

# 🛡️ 4. Requerimientos de BLINDAJE del sistema (Codex debe implementarlo)

## ✔️ 4.1. Manejo inteligente de errores HTTP (soft-fail, no hard-crash)
Nueva política:

* Si un scraper falla (404, 500, timeout), el pipeline **NO debe detenerse**.
* El sistema debe:
  1. Registrar un warning.
  2. Crear un archivo vacío o parcial.
  3. Continuar con las demás fuentes.

Ejemplo:

```
WARNING: FandomScraper failed (404). Continuing pipeline with partial data.
```

---

## ✔️ 4.2. URLs dinámicas + fallback automático
Agregar al scraper:

```python
FANDOM_URLS = [
    "https://naruto.fandom.com/wiki/Story_Arcs",
    "https://naruto.fandom.com/wiki/Category:Story_Arcs",
    "https://naruto.fandom.com/es/wiki/Arcos_Argumentales"  # fallback internacional
]
```

Implementar:

1. Intentar cada URL en orden.
2. Si todas fallan → registrar warning y devolver lista vacía.

---

## ✔️ 4.3. Control de reintentos más inteligente
Cambiar tenacity:

* Retries: 3 → 1
* Delay: 2s → 0.2s
* Stop on 404 immediately (no reintento)

---

## ✔️ 4.4. Blindaje contra cambios en HTML
Fandom cambia DOM frecuentemente.

Implementar:

* Selectores múltiples.
* Si falla el principal, intentar un selector de fallback.
* Si falla todo → warning + continuar.

---

# ⚡ 5. Requerimientos de Velocidad y Optimización

## ✔️ 5.1. Evitar parsear HTML completo
Usar:

```python
soup = BeautifulSoup(response.text, "lxml")
```

(lxml es 5–30x más rápido que html.parser)

---

## ✔️ 5.2. Sesión persistente de requests
Reemplazar:

```python
requests.get(...)
```

Por:

```python
session = requests.Session()
session.get(...)
```

Beneficio:

* Reduce overhead de TCP/TLS hasta 40%
* Más rápido y estable

---

## ✔️ 5.3. Cache local
Agregar opción:

* Guardar HTML de Fandom/MAL/Tropes
* Si existe y `--use-cache` → no scrapea

Evita desgaste y acelera.

---

## ✔️ 5.4. Aceleración del pipeline
Secuencias actuales son secuenciales.
Mejorar:

* Paralelizar scrapers con `asyncio` o `ThreadPoolExecutor`.

---

# 🧼 6. Requerimientos de Ligereza (reducir peso)

## ✔️ Quitar dependencias innecesarias
WeasyPrint — opcional
Selenium — cargar solo si IMDb está activado
Matplotlib — cargar solo si gráfico está habilitado

Implementar:

```python
if args.imdb:
    import selenium
```

---

## ✔️ Archivos grandes en `data/`

* Comprimir TSV a `.gz`
* Comprimir cachés HTML

Reducción esperada: **65%–90%**

---

# 🧪 7. Reproducibilidad (para Codex)

## Para reproducir error:

```powershell
git clone https://github.com/Adal612Git/TSUKI-NO-ME-v3.git
cd TSUKI-NO-ME-v3
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python orchestrator.py
```

❌ Explota en:

```
FandomScraper.fetch()
404 Not Found
RetryError
```

---

# 🧩 8. Qué debe entregar Codex como resultado

### ✔ Fix del FandomScraper (URLs nuevas + fallback)

### ✔ Blindaje completo en scrapers (manejo de errores suave)

### ✔ Pipeline que NO se detiene por fallas externas

### ✔ Velocidad mejorada (sessions, parallel scraping)

### ✔ Ligereza y carga dinámica de módulos

### ✔ Logs profesionales (INFO/WARN/ERROR)

### ✔ Actualización del README

### ✔ Tests mínimos de scraping

### ✔ Compatibilidad con narrativas futuras (Pokémon, One Piece, DBZ, Shingeki)

---

# 🚀 9. Texto FINAL para pegarle a Codex

(Copia y pega esto tal cual)

---

**INSTRUCCIONES PARA CODEX:**

Corrige y mejora TSUKI-NO-ME v3 con los siguientes requerimientos:

1. **Fix crítico:**
   El scraper Fandom usa una URL obsoleta.
   Cambiar a un sistema de URLs dinámicas con fallback:

   * [https://naruto.fandom.com/wiki/Story_Arcs](https://naruto.fandom.com/wiki/Story_Arcs)
   * [https://naruto.fandom.com/wiki/Category:Story_Arcs](https://naruto.fandom.com/wiki/Category:Story_Arcs)
   * [https://naruto.fandom.com/es/wiki/Arcos_Argumentales](https://naruto.fandom.com/es/wiki/Arcos_Argumentales)

2. **Blindaje:**

   * Manejar errores HTTP sin interrumpir pipeline.
   * Si un scraper falla, registrar warning y seguir.
   * Control de reintentos inteligente: reintentar 1 vez, evitar reintentos en 404.
   * Selectores HTML con múltiples fallback.

3. **Optimización:**

   * Reemplazar `requests.get` por `requests.Session`.
   * Usar `lxml` para parsing HTML.
   * Agregar paralelismo en scrapers con ThreadPoolExecutor.
   * Cargar Selenium solo si IMDb es requerido.
   * Reducir dependencias obligatorias.

4. **Ligereza:**

   * Comprimir TSV y HTML cache como `.gz`.
   * Crear modo `--minimal` para correr sin PDFs ni gráficos.

5. **Entrega:**

   * Código actualizado.
   * README actualizado con nuevas instrucciones.
   * Pruebas mínimas de scraping.
   * Logs mejorados.

---

Ricardo, esto es EXACTAMENTE lo que Codex necesita para arreglar el sistema y dejarlo god-tier.

Si quieres, te preparo **directamente un archivo .md** para subirlo al repo como `SPEC_IMPROVEMENTS.md`.
