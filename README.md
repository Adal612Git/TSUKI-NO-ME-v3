# TSUKI-NO-ME v3

Plataforma para minar narrativas a escala industrial y reconstruirlas con coherencia lógica, emocional y estadística. Incluye
capacidades de auto-reparación, aprendizaje continuo y ruteo inteligente de modelos Ollama locales.

## ¿Qué es?
TSUKI-NO-ME v3 es una fábrica de ETL narrativo: ingesta obras, las limpia, corta en escenas y genera una **Biblia Numérica
Multiversal** con métricas cuantitativas (pacing, emoción, power, tema/tono) y reglas extraídas estadísticamente. Su objetivo no
es resumir, sino medir y garantizar calidad narrativa.

### Modo automático
- Ejecuta `python -m narrative_quantifier --auto` para que el pipeline localice obras `.txt/.md` en `./examples` (o el directorio
  que definas en `--local-root`), scrapee URLs listadas en `examples/seed_urls.txt` y procese todo en lote.
- Exporta dataset completo en `outputs/auto/scenes.jsonl` + patrones (`patterns.json`), analíticas (`analytics.json`) y gráficas
  de correlación (`quality_trends.png`, `dta_vs_quality.png`).
- Si quieres que genere las gráficas, instala previamente `matplotlib` (`pip install matplotlib`).

## Documentación para ingeniería
- `docs/TSUKI_NO_ME_v3_producto.md`: guía operativa detallada (arquitectura, flujo ETL, esquema de datos, métricas y
  entregables) para implementar el sistema con resiliencia industrial.

## Stack objetivo
- Backend: FastAPI + Asyncio workers, Redis MQ, PostgreSQL/SQLite, ElasticSearch opcional.
- NLP/ML: spaCy, textstat, Ollama modelos locales (Phi3/Llama3/Falcon), PCA/SVD, Isolation Forest, changepoints bayesianos.
- Análisis/visualización: R + ggplot2 + Shiny, Apache Arrow/Parquet, Dask.
- Frontend: React dashboards.
- Infra: Docker/Kubernetes, Prometheus/Grafana para health checks agregados.
