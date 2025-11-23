# TSUKI-NO-ME v3 — Especificación de Producto para Ingeniería

## 1) Propósito y resultado esperado
TSUKI-NO-ME v3 es una fábrica de ETL narrativo que transforma obras extensas en una **Biblia Numérica Multiversal**: un dataset auditable escena por escena con métricas cuantitativas y reglas derivadas. El objetivo es **medir, comparar y validar** narrativas para garantizar calidad antes de reescrituras (p.ej., Naruto Shippuden) usando modelos locales (Ollama) y analítica estadística/ML.

**Entregable clave:** matriz de escenas y reportes que permiten tomar decisiones de diseño narrativo (capítulos oro, valles necesarios, detección de relleno, power creep, etc.).

## 2) Arquitectura de alto nivel (híbrida + resiliente)
- **Frontend (React) + API (FastAPI) + Event Bus (Redis).**
- **Message Queue:** Redis dirige jobs asincrónicos.
- **Workers Asyncio** por módulo: `harvester`, `cleaner`, `scene_cutter`, `engines`, `quality_scorer`, `pattern_miner`.
- **Circuit Breaker y Strategy Pattern** en Ollama router para ruteo Phi3/Llama3/Falcon según costo/confianza y degradación automática.
- **Event Sourcing:** registro inmutable de procesamiento para replay/debugging.
- **Health Check Aggregator:** monitoriza todos los microservicios y modelos locales.

## 3) Flujo ETL narrativo (core)
1. **HARVESTER** — ingesta web/archivo (PDF/EPUB/TXT/SRT/CBZ) + OCR + caché. Output: texto canon bruto + checksum.
2. **CLEANER** — normaliza HTML/OCR (remoción de ruido, encoding, desambiguación). Output: texto canon limpio + checksum.
3. **SCENE CUTTER** — segmentación híbrida (reglas + Ollama). Output: `scenes.jsonl` con escenas, offsets y metadata.
4. **ENGINES**
   - **METRICS ENGINE:** sentimiento, complejidad léxica (textstat), tempo, emotional volatility, DTA ratio.
   - **POWER ENGINE:** feat magnitude (log), power creep detector, chakra/energy cost.
   - **THEME/TONE ENGINE:** temas LDA, arcos de personaje, estados HMM/Markov {setup, tensión, clímax, valle}.
5. **QUALITY SCORER** — calcula `EQS_t = σ(w1*S_t + w2*L_t + w3*F_t + w4*N_t + w5*I_t)` (0–100) + validación y anomalías.
6. **PATTERN MINER** — changepoints bayesianos, Isolation Forest, reglas de género (ej. DTA 0.45–0.55 en tensión Shōnen), export a prompts.
7. **WORLD BIBLE DB** — PostgreSQL/SQLite con datasets versionados + reportes (R/ggplot2/Shiny dashboards).

## 4) Modelo de datos (esquema mínimo por escena)
```json
{
  "work_id": "naruto-shippuden",
  "chapter_id": 450,
  "scene_id": "450-07",
  "offsets": {"start_char": 12340, "end_char": 13780},
  "vector": {"S_t": -0.12, "L_t": 63.4, "F_t": 1.9, "N_t": 0.35, "I_t": 0.41},
  "tempo": {"wps": 4.2, "tempo_shift": -0.8},
  "dta_ratio": 0.83,
  "emotional_volatility": 0.12,
  "power_creep_sigma": 2.1,
  "markov_state": "tensión",
  "quality_score": 58.7,
  "anomalies": ["power_creep"],
  "provenance": {"hash": "...", "pipeline_stage": "engines.v1"}
}
```

## 5) Métricas expandibles y algoritmos mínimos
- **Sentimiento (S_t):** polaridad spaCy + ventana móvil para volatilidad.
- **Complejidad (L_t):** textstat (Flesch, Gunning Fog) + Silence/Boredom Index.
- **Feat Magnitude (F_t):** escala log; Ollama judge + keywords; Power Creep si |ΔF_t| > 2σ.
- **Novelty (N_t):** embeddings → PCA/SVD; reconstrucción/autoencoder opcional.
- **Cambio Interno (I_t):** detección de arco; drift temático; transición HMM.
- **Changepoints:** Bayesian/CUSUM/EWMA para ritmo/emoción/poder.
- **Outliers:** Isolation Forest + MAD robusta.

## 6) Estrategia de ruteo de modelos (Ollama)
- **Router (Strategy Pattern):** elige modelo según `task_type`, `target_latency`, `confidence_needed`, historial de éxito.
- **Fallback (Circuit Breaker):** si un modelo falla o degrada, alterna a otro y marca evento en Event Sourcing.
- **Modelos locales:** Phi3 (rápido/clasificación), Llama3 (profundo), Falcon (diálogo/estructura).

## 7) Garantías de robustez
- **Idempotencia:** cada etapa guarda output con checksum; reintentos sin reprocesar.
- **Checkpoints:** JSONL/Arrow por etapa, versionados.
- **Streaming:** procesamiento por chunk; nunca cargar libros completos en RAM.
- **Health Checks agregados:** API de estado por servicio/modelo + panel.
- **Logs estructurados:** trazabilidad completa hasta escena y hash.

## 8) Entregables para el ingeniero
1. **Pipeline operativo** con jobs encolados (Redis) y workers Asyncio por módulo.
2. **Esquema DB**: tablas `works`, `chapters`, `scenes`, `metrics`, `anomalies`, `rules`, `events` (event sourcing), `models` (historial de desempeño).
3. **Datasets exportables** (Arrow/Parquet) y reportes R/Shiny (mapa de calor narrativo, curvas de ritmo, anomalías).
4. **API** REST/GraphQL para consultar escenas, scores, reglas y recomendaciones.
5. **Documentación de routing** de LLM locales y política de degradación.
6. **Pruebas de aceptación**: reingesta idempotente, detección de power creep, cálculo de EQS, extracción de regla de género.

## 9) Indicadores de éxito
- 100% de escenas con `vector` y `quality_score` calculados.
- Reproceso de una obra grande < 10% overhead (idempotencia efectiva).
- Alertas de anomalía con precisión/recall acordes a baseline (definir con dataset de prueba).
- Panel de health checks verde en operación continua.

## 10) Ejemplo de uso (Naruto Shippuden)
- Ingestar temporadas completas → generar `scenes.jsonl`.
- Calcular power creep y detectar clímax injustificados.
- Generar reporte con: DTA ratio recomendado por arco, escenas oro, valles necesarios, reglas extraídas para reescritura.
- Exportar prompts guía: "En escenas de tensión Shōnen, mantener DTA 0.45–0.55 y NB_t alto antes del clímax".

## 11) Próximos pasos sugeridos
- Definir pesos `w1…w5` por género mediante grid search sobre corpus etiquetado.
- Implementar Shiny dashboard básico con mapa de calor de `quality_score` vs tiempo vs emoción.
- Añadir simulador de costo/latencia para ruteo de modelos locales.

---
Este documento es la guía operativa para que el ingeniero implemente TSUKI-NO-ME v3 con los componentes cuantitativos y de resiliencia necesarios para garantizar calidad narrativa medible.
