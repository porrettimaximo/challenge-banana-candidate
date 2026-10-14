---
name: release-delivery-agent
phase: 7-release
description: Agente responsable de consolidar la entrega, verificar sesiones de IA con hash SHA-256, generar el documento Word explicativo y empaquetar el ZIP final reproducible.
author: Maximo Porretti
---

# Agente 7: Release, Empaquetado y Entrega de la Feature (Release Agent)

## Objetivo
Consolidar el paquete final entregable con total reproducibilidad técnica, garantizando la preservación de las sesiones originales de IA, la generación del documento Word formal y la creación del archivo ZIP limpio.

## Protocolo de Empaquetado y Entrega
1. **Verificación de Prerrequisitos:**
   - 29/29 tests aprobados en `npm test`.
   - `npm run typecheck` sin advertencias ni errores.
   - `npm run build` exitoso.
2. **Preservación de Sesiones de Asistencia de IA:**
   - Asegurar que los archivos JSONL de las sesiones de interacción se ubiquen en `submission/ai-sessions/`.
   - Generar/actualizar `manifest.json` con los hashes criptográficos SHA-256 de cada archivo para certificar autenticidad.
3. **Generación del Documento Word Entregable:**
   - Ejecutar el script generador del documento Word (`python scripts/build-word-report.py`).
   - El documento Word consolidará toda la explicación técnica, arquitectura de agentes, comparativas cuantitativas antes/después, capturas de pantalla y evidencias de verificación.
   - Dejar únicamente el archivo Word oficial (`banana-bank-entregable.docx`) como entregable explicativo, eliminando borradores o duplicados innecesarios.
4. **Construcción del Archivo ZIP:**
   - Generar el paquete `delivery/banana-bank-maximo-porretti.zip`.
   - Excluir estrictamente: `node_modules/`, `.next/`, `.data/`, bases de datos SQLite locales, archivos `.env` (excepto `.env.example`), `.git/` y carpetas temporales de testing.
5. **Comprobación de Entrega y Asunto:**
   - Asunto oficial requerido: `Maximo Porretti - Banana Bank Technical Challenge`.
   - Instrucciones claras para la ejecución en una máquina limpia.

## Salida Esperada
- `delivery/banana-bank-maximo-porretti.zip` listo para envío junto al documento Word explicativo.
