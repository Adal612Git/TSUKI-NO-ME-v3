# TSUKI-NO-ME v3

Plataforma para minar narrativas a escala industrial y reconstruirlas con coherencia lógica, emocional y estadística. Incluye
capacidades de auto-reparación, aprendizaje continuo y ruteo inteligente de modelos Ollama locales.

## ¿Qué es?
TSUKI-NO-ME v3 es una fábrica de ETL narrativo: ingesta obras, las limpia, corta en escenas y genera una **Biblia Numérica
Multiversal** con métricas cuantitativas (pacing, emoción, power, tema/tono) y reglas extraídas estadísticamente. Su objetivo no
es resumir, sino medir y garantizar calidad narrativa.

## Documentación para ingeniería
- `docs/TSUKI_NO_ME_v3_producto.md`: guía operativa detallada (arquitectura, flujo ETL, esquema de datos, métricas y
  entregables) para implementar el sistema con resiliencia industrial.

## Stack objetivo
- Backend: FastAPI + Asyncio workers, Redis MQ, PostgreSQL/SQLite, ElasticSearch opcional.
- NLP/ML: spaCy, textstat, Ollama modelos locales (Phi3/Llama3/Falcon), PCA/SVD, Isolation Forest, changepoints bayesianos.
- Análisis/visualización: R + ggplot2 + Shiny, Apache Arrow/Parquet, Dask.
- Frontend: React dashboards.
- Infra: Docker/Kubernetes, Prometheus/Grafana para health checks agregados.
