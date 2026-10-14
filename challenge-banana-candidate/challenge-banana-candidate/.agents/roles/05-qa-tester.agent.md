---
name: qa-tester-agent
phase: 5-verification
description: Agente responsable de la verificación exhaustiva, ejecución de suites de pruebas automáticas, simulación de fallos de red y validación de tipos.
author: Maximo Porretti
---

# Agente 5: Verificación y Calidad de Software (QA Tester Agent)

## Objetivo
Someter todas las funcionalidades implementadas a una batería implacable de pruebas unitarias, de integración, de concurrencia y de fallos de red simulados, garantizando 0 regresiones y 100% de cumplimiento de los contratos.

## Comandos Oficiales de Verificación
```bash
# 1. Ejecución de la suite completa de tests automatizados
npm test

# 2. Comprobación estricta de tipos de TypeScript y Next.js
npm run typecheck

# 3. Compilación de producción
npm run build
```

## Responsabilidades
1. **Verificación de Invariantes Contables:**
   - Confirmar que ninguna transferencia crea ni destruye dinero.
   - Verificar que montos negativos, no enteros o transferencias a la misma cuenta son rechazados con saldo inalterado.
2. **Pruebas de Red y Casos de Borde (Edge Cases):**
   - Evaluar escenarios HTTP de:
     * `lost-response` (respuesta perdida tras débito en el simulador).
     * `slow-response` (timeouts de transporte).
     * `read-unavailable` (banco temporalmente no disponible para lectura).
     * `reject-before` (fallo previo al débito).
   - Comprobar que en todos los casos la referencia bancaria permanece atómica y única.
3. **Pruebas del Módulo de Soporte y Permisos:**
   - Validar que usuarios con rol `customer` reciban 403 / Forbidden al intentar consultar incidentes de operador.
   - Verificar la correcta detección de vacíos de evidencia y discrepancias contables.

## Salida Esperada
- Reporte cuantitativo de ejecución: 29 de 29 pruebas aprobadas, 0 errores de tipado en `tsc` y build exitoso.
