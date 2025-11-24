# Project Uzumaki: Narrative Optimization Engine v1.0

Pipeline modular para scrapear, limpiar, analizar y reportar métricas narrativas de Naruto Shippuden (extensible a otras series). El sistema sigue la arquitectura solicitada: orquestador, scrapers resilientes, limpieza, cálculo de métricas y generación de reportes.

## Estructura
- `orchestrator.py`: coordina el pipeline completo.
- `uzumaki/scraping/`: scrapers para MyAnimeList, IMDb (Selenium), TV Tropes y Fandom.
- `uzumaki/data_cleaner.py`: unifica datos en un dataset limpio y lo persiste en SQLite/Excel.
- `uzumaki/metrics.py`: funciones de métricas (ritmo, satisfacción, balance de personajes, tropos, relleno).
- `uzumaki/reporting.py` + `uzumaki/templates/report.html`: genera reportes HTML (opcional PDF con WeasyPrint) y gráficos con matplotlib.
- `uzumaki/models.py`: dataclasses para episodios, personajes, arcos y tropos.

## Uso rápido
```bash
python orchestrator.py
```

Requisitos (instalar en un entorno virtual):
```
pip install requests beautifulsoup4 tenacity selenium pandas matplotlib jinja2 weasyprint lxml openpyxl
```

Notas:
- El scraper de IMDb requiere ChromeDriver en el PATH.
- El pipeline escribe artefactos en `data/` (checkpoints TSV, base SQLite, snapshot Excel, métricas JSON, reporte HTML e imágenes de gráficas).
- Los scrapers respetan `robots.txt` y usan retardos aleatorios; se diseñaron para extraer metadatos y no contenido con copyright.
