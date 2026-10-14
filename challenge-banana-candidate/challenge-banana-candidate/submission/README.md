# Banana Bank Technical Challenge - Submission

**Candidate**: Maximo Porretti  
**Date**: 14 de octubre de 2026  
**Subject**: Maximo Porretti - Banana Bank Technical Challenge  
**Email Target**: hr@tdots.es (ver borrador en [submission/email-draft.txt](file:///c:/Users/Maxi/Desktop/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/submission/email-draft.txt))  
**Primary Deliverable Document**: [submission/banana-bank-entregable.pdf](file:///c:/Users/Maxi/Desktop/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/submission/banana-bank-entregable.pdf) (y su versión markdown en [submission/explicacion.md](file:///c:/Users/Maxi/Desktop/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/submission/explicacion.md))

---

## Resumen del Flujo de Trabajo (.agents)
Maximo Porretti diseñó y dirigió el flujo completo de desarrollo de la aplicación utilizando especificaciones de agentes (`.agents/` y `AGENTS.md`) desde la captura de requerimientos hasta el release reproducible:
- **`AGENTS.md`**: Punto de entrada del proyecto con directivas y reglas de delegación.
- **`.agents/skills/feature-delivery/SKILL.md`**: Skill operativa con el procedimiento de entrega de punta a punta.
- **`.agents/roles/`**:
  - `requirements.md`: Definición y congelamiento de requerimientos y criterios de aceptación.
  - `architect.md`: Diseño de máquinas de estado, garantías de idempotencia y contratos.
  - `implementer.md`: Implementación bancaria segura (propuestas, confirmación y reconciliación).
  - `agent-builder.md`: Implementación del copilot de soporte, telemetría y evidencia estructurada.
  - `qa.md`: Pruebas de integración, verificación de invariantes y edge cases.
  - `reviewer.md`: Revisión independiente de código y auditoría de seguridad.
  - `release.md`: Verificación final, generación de PDF, exportación de sesiones y empaquetado ZIP.

El registro cronológico de la ejecución del flujo se encuentra documentado en [submission/workflow-log.md](file:///c:/Users/Maxi/Desktop/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/submission/workflow-log.md).

> **Justificación Estratégica ante la Restricción de Tiempo**: La elección de este flujo modular gobernado por agentes y asistido por IA fue una decisión deliberada de Maximo Porretti motivada por los estrictos plazos de entrega del challenge. Ante una ventana de tiempo acotada, un desarrollo manual tradicional habría obligado a recortar el alcance funcional o relajar la rigurosidad de las pruebas. La estructuración en roles especializados permitió maximizar la velocidad de ejecución: la supervisión humana se concentró en la arquitectura de estados, los invariantes financieros y las decisiones de seguridad, mientras que la IA aceleró la implementación, la batería de pruebas y la generación de evidencia técnica auditable.

---

## Part 1 - Fixes (Transferencias Confiables)
- **Defectos encontrados en el starter**:
  - Débitos inmediatos sin confirmación explícita del usuario.
  - Doble cobro ante respuestas perdidas de red (generación de un nuevo reference bancario por cada reintento).
  - Estado bancario inconsistente o desconocido no reconciliado tras fallos de red.
  - Bypass de autorización de cuentas.
- **Solución implementada**:
  - Flujo de propuesta inmutable con TTL (10 min) ligada a la sesión del titular (`requires_confirmation`).
  - Idempotencia estricta: un único `reference` bancario asociado de forma atómica al intent ID, preservado a través de reinicios y reintentos concurrentes.
  - Reconciliación activa vía `GET /v1/operations/:reference` ante timeouts/errores de transporte, preservando estado pendiente sin asumir rechazo.
  - Verificación en [submission/before-after.json](file:///c:/Users/Maxi/Desktop/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/submission/before-after.json).

---

## Part 2 - Agent Feature (Operator Case Copilot con Evidencia)
- **Propósito**: Asistente para operadores bancarios que reconstruye la cronología y estado de un caso a partir de evidencia estructurada (mensajes, eventos de herramientas, intents y estado de cuenta bancario).
- **Características clave**:
  - **Sin dependencia de API key**: Funciona de manera determinista analizando discrepancias, evidencias y recomendando próximos pasos sin costo ni riesgos de alucinación.
  - **Detección de vacíos de evidencia**: Reporta explícitamente eventos históricos ausentes en vez de asumir hechos no registrados.
  - **Briefing opcional por IA**: Endpoint `/api/incidents/:id/briefing` para resúmenes complementarios cuando se configura una clave.
  - **Acceso restringido**: Interfaz de operador protegida contra accesos de rol cliente.

---

## Verificación y Demostración
- **Pruebas automáticas**: 29/29 tests aprobados (`npm test`).
- **Typecheck**: Limpio (`npm run typecheck`).
- **Build de producción**: Aprobado (`npm run build`).
- **Instrucciones para reproducir localmente**:
  ```bash
  npm ci --ignore-scripts
  npm run setup
  npm test
  npm run typecheck
  npm run dev
  ```
  Abrir `http://127.0.0.1:3000`. Probar propuesta y confirmación con Lucía. Probar el caso histórico de Marta en Soporte. Ejecutar `node scripts/demo-support.mjs` para simular un caso nuevo con evidencia.

---

## Materiales de Entrega
- **Sesiones originales de IA**: [submission/ai-sessions/](file:///c:/Users/Maxi/Desktop/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/submission/ai-sessions/) (4 archivos JSONL completos con manifiesto y hashes SHA-256 en `manifest.json`).
- **Documento explicativo**: [submission/banana-bank-entregable.pdf](file:///c:/Users/Maxi/Desktop/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/challenge-banana-candidate/submission/banana-bank-entregable.pdf) (8 páginas con capturas de pantalla, tablas comparativas y análisis).
- **Paquete de entrega**: `delivery/banana-bank-maximo-porretti.zip` generado con `npm run package:submission`.
