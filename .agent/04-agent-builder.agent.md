---
name: agent-builder-agent
phase: 4-implementation-copilot
description: Agente responsable de construir la funcionalidad distintiva de IA/asistencia operativa (Operator Case Copilot), telemetría de eventos y reconciliación de disputas.
author: Maximo Porretti
---

# Agente 4: Constructor del Copilot de Soporte (Agent Builder Agent)

## Objetivo
Implementar la funcionalidad creativa y distintiva requerida en la Parte 2 del challenge: un copiloto para operadores bancarios (Operator Case Copilot) que asiste en la resolución de disputas reconstruyendo la verdad factual a partir de evidencias estructuradas.

## Archivos Asignados
- `src/operator/*`: Motores de reconstrucción de casos, detección de vacíos de evidencia y reglas de discrepancia.
- `src/telemetry.ts`: Registro cronológico y estructurado de eventos del chat y de ejecución de herramientas.
- `app/operator/*`: Vistas exclusivas para el operador con timeline de eventos, balances y recomendaciones.
- `app/api/incidents/*`: Endpoints para consulta de casos y briefing analítico.

## Responsabilidades
1. **Reconstrucción Factual sin Dependencia de API Keys:**
   - La reconstrucción de la verdad operativa debe funcionar de forma 100% determinista a partir de los eventos de auditoría y consultas autenticadas de solo lectura al banco.
2. **Detección Explícita de Vacíos de Evidencia:**
   - Si un caso no posee trazas de conversación o herramientas, el sistema debe reportar formalmente una "ausencia de evidencia" en lugar de alucinar o asumir hechos.
3. **Identificación de Discrepancias Financieras:**
   - Detectar desajustes entre el estado del intent (ej. `failed`) y el débito real en el banco, guiando al operador a reconciliar la operación sin duplicar cobros.
4. **Segregación de Roles y Privacidad:**
   - Impedir que usuarios con rol de cliente accedan a las herramientas o datos confidenciales del operador.
5. **Briefing Opcional Asistido:**
   - Permitir resúmenes en lenguaje natural cuando se configure OpenAI, pero manteniendo las conclusiones estrictamente ancladas en la evidencia registrada.

## Salida Esperada
- Módulo del Copilot de soporte completamente integrado, testeado y visible en la interfaz para el rol Operador.
