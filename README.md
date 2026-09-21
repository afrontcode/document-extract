## 📊 Evaluación y Benchmark

Comparativa de rendimiento entre el enfoque tradicional basado en reglas deterministas (**Regex Baseline**) y la extracción semántica mediante modelos de lenguaje (**Anthropic LLM**) sobre un conjunto de prueba de 4 documentos.

### 1. Métricas de Precisión por Campo

| Campo | Regex Baseline | Anthropic (LLM) | Observación |
| :--- | :---: | :---: | :--- |
| `cliente_nombre` | 50.0% | **100.0%** | El LLM tolera variaciones de encabezados y nombres con formatos no estándar. |
| `cliente_ruc` | 0.0% | **100.0%** | Regex falló por inconsistencias en prefijos y etiquetas previas al número. |
| `fecha_emision` | 50.0% | **100.0%** | Resuelto eficazmente frente a formatos mixtos (`DD/MM/YYYY`, texto, etc.). |
| `moneda` | 50.0% | **75.0%** | 1 documento con ambigüedad o símbolo omitido. |
| `monto_total` | **100.0%** | **100.0%** | Ambos métodos alcanzan consistencia total en patrones numéricos estándar. |

---

### 2. Latencia y Eficiencia Operativa

```text
=============================================================================
REPORTE DE RENDIMIENTO (4 documentos evaluados)
=============================================================================
Latencia promedio:
  - Regex Baseline :  0.23 ms   (Local / In-memory)
  - Anthropic LLM  :  1.88 s    (API Inferencia remota)

Consumo de Tokens (Anthropic):
  - Tokens de entrada (Input)  :  7,330
  - Tokens de salida (Output)  :    951
=============================================================================
```

---

### 3. Conclusiones y Arquitectura Recomendada

1. **Trade-off Precisión vs. Latencia:**
   * **Regex:** Ofrece latencia sub-milisegundo ($0.23\text{ ms}$) y costo computacional nulo, pero es frágil frente a cambios en la maquetación del documento.
   * **LLM:** Ofrece una tasa de acierto significativamente superior en campos no estructurados o dependientes del contexto (`cliente_ruc`, `cliente_nombre`), a expensas de un tiempo de respuesta de red ($\approx 1.88\text{ s}$).

2. **Estrategia Híbrida (Pipeline de Extracción):**
   * Aplicar validaciones deterministas/heurísticas rápidas como primer filtro (`tier 1`).
   * Usar el LLM como fallback inteligente para documentos o campos donde el scoring de confianza del Regex sea bajo.