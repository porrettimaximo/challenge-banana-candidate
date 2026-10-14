import os
import sys
from pathlib import Path
import json
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def clear_headers_footers(doc):
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)
        
        # Eliminar encabezados y pies de pagina por completo
        s.different_first_page_header_footer = False
        header = s.header
        for p in header.paragraphs:
            p.text = ""
        footer = s.footer
        for p in footer.paragraphs:
            p.text = ""

def main():
    root = Path(__file__).resolve().parent.parent
    sub_dir = root / 'submission'
    screenshots_dir = sub_dir / 'screenshots'
    out_docx = sub_dir / 'banana-bank-entregable.docx'

    doc = Document()
    clear_headers_footers(doc)

    # Estilos Generales - PALETA MONOCROMÁTICA / NEUTRA (SIN NINGÚN TONO AZUL)
    COLOR_TITLE = RGBColor(17, 17, 17)        # Negro puro elegante
    COLOR_H1 = RGBColor(25, 25, 25)           # Carbón oscuro
    COLOR_H2 = RGBColor(45, 45, 45)           # Gris grafito oscuro
    COLOR_BODY = RGBColor(35, 35, 35)         # Texto oscuro lectura
    COLOR_MUTED = RGBColor(90, 90, 90)        # Gris neutro secundario
    COLOR_CAPTION = RGBColor(100, 100, 100)   # Gris neutro caption
    COLOR_CODE = RGBColor(30, 30, 30)         # Monospace dark
    HEX_TABLE_HEADER = '262626'               # Carbón oscuro para cabeceras
    HEX_ROW_ALT = 'F5F5F5'                    # Gris muy suave alternado

    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Arial'
    normal_style.font.size = Pt(10)
    normal_style.font.color.rgb = COLOR_BODY
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    # Funciones de formateo
    def title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.color.rgb = COLOR_TITLE
        return p

    def subtitle(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(14)
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(11.5)
        run.font.italic = True
        run.font.color.rgb = COLOR_MUTED
        return p

    def h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(14.5)
        run.font.bold = True
        run.font.color.rgb = COLOR_H1
        return p

    def h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(11.5)
        run.font.bold = True
        run.font.color.rgb = COLOR_H2
        return p

    def p_body(text):
        p = doc.add_paragraph()
        run = p.add_run(text)
        return p

    def bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        run_b = p.add_run(bold_prefix)
        run_b.font.bold = True
        run_b.font.color.rgb = COLOR_H1
        p.add_run(text)
        return p

    def code_box(code_text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.left_indent = Inches(0.2)
        run = p.add_run(code_text)
        run.font.name = 'Consolas'
        run.font.size = Pt(9)
        run.font.color.rgb = COLOR_CODE
        return p

    def add_styled_table(headers, rows, col_widths=None):
        table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Cabecera de tabla
        hdr_cells = table.rows[0].cells
        for i, header_text in enumerate(headers):
            hdr_cells[i].text = header_text
            set_cell_background(hdr_cells[i], HEX_TABLE_HEADER)
            set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
            for paragraph in hdr_cells[i].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in paragraph.runs:
                    r.font.name = 'Arial'
                    r.font.bold = True
                    r.font.size = Pt(9.5)
                    r.font.color.rgb = RGBColor(255, 255, 255)

        # Filas de datos
        for r_idx, row in enumerate(rows):
            row_cells = table.rows[r_idx + 1].cells
            bg_color = HEX_ROW_ALT if r_idx % 2 == 1 else 'FFFFFF'
            for c_idx, cell_value in enumerate(row):
                row_cells[c_idx].text = cell_value
                set_cell_background(row_cells[c_idx], bg_color)
                set_cell_margins(row_cells[c_idx], top=90, bottom=90, left=130, right=130)
                for paragraph in row_cells[c_idx].paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for r in paragraph.runs:
                        r.font.name = 'Arial'
                        r.font.size = Pt(9)
                        r.font.color.rgb = COLOR_BODY

        if col_widths:
            for row in table.rows:
                for idx, width in enumerate(col_widths):
                    row.cells[idx].width = Inches(width)

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def add_image_with_caption(filename, caption_text, width=Inches(6.0)):
        img_path = screenshots_dir / filename
        if img_path.exists():
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(2)
            run = p_img.add_run()
            run.add_picture(str(img_path), width=width)

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(10)
            run_cap = p_cap.add_run(f"Captura: {caption_text}")
            run_cap.font.name = 'Arial'
            run_cap.font.size = Pt(8.5)
            run_cap.font.italic = True
            run_cap.font.color.rgb = COLOR_CAPTION

    # ------------------ CONTENIDO COMPLETO ------------------

    # ENCABEZADO Y METADATOS
    title("Desarrollo y Entrega de Banana Bank")
    subtitle("Documentación Técnica Integral: Requerimientos del Challenge, Flujo de Agentes (.agents), Fixes Financieros y Asistente de Soporte con Evidencia")

    meta_headers = ["Elemento de Entrega", "Detalle Registrado"]
    meta_rows = [
        ["Candidato", "Maximo Porretti"],
        ["Fecha de Entrega", "14 de octubre de 2026"],
        ["Asunto Oficial del Correo", "Maximo Porretti - Banana Bank Technical Challenge"],
        ["Destino de Entrega", "hr@tdots.es (canal documentado en starter)"],
        ["Archivo Comprimido Entregable", "delivery/banana-bank-maximo-porretti.zip"],
        ["Resultado de Verificación", "29 de 29 pruebas aprobadas, typecheck limpio, build de producción exitoso"]
    ]
    add_styled_table(meta_headers, meta_rows, [2.3, 4.2])

    # SECCION 1: QUÉ NOS PEDÍA EL TRABAJO
    h1("1. ¿Qué nos pedía el trabajo? (Alcance Oficial del Challenge)")
    p_body(
        "El challenge Banana Bank ubica al candidato en la situación de unirse al equipo técnico de un banco ficticio que "
        "planea lanzar su asistente de inteligencia artificial para clientes y operadores el próximo lunes. La empresa facilitó "
        "un proyecto funcional inicial (aplicación web Next.js con chat de IA, datos simulados y un servicio bancario externo en simulator/), "
        "pero requería evidencia rigurosa de confiabilidad y una funcionalidad innovadora. El requerimiento formal exigió abordar dos partes "
        "principales más la entrega en un paquete único:"
    )

    bullet("Parte 1 - Preparar la app para el lunes (40% de la evaluación): ", 
           "Explorar el código starter, encontrar problemas reales y reproducibles, y corregir a fondo los defectos críticos elegidos. "
           "Se exigió enfocarse en la integridad de las transferencias, la integración con el banco y la seguridad, sin alterar el simulador "
           "bancario externo (tratado como caja negra). Aportar evidencia cuantitativa y demostrable de 'Antes vs. Después'.")

    bullet("Parte 2 - Construir algo distintivo (40% de la evaluación): ", 
           "Diseñar e implementar una funcionalidad creativa, útil y no genérica para el agente de Banana Bank, integrada en el flujo operativo "
           "del banco (para clientes o soporte de operadores). Demostrarla en vivo con casos de uso concretos.")

    bullet("Metodología, Verificación y Entrega (20% de la evaluación): ", 
           "Explicar las decisiones técnicas, ejecutar pruebas automatizadas completas y empaquetar todo en un único archivo ZIP reproducible. "
           "El ZIP debe incluir el código completo, las sesiones originales de IA (en submission/ai-sessions/), y el documento o video explicativo, "
           "excluyendo node_modules, .next, .data, bases de datos locales y credenciales privadas.")

    bullet("Requerimiento Adicional del Candidato: ", 
           "Maximo Porretti solicitó diseñar, estructurar y documentar un flujo modular de agentes (.agents/roles/ y .agents/skills/) "
           "que cubra de punta a punta el desarrollo (desde la captura de requerimientos hasta el empaquetado final), documentando su autoría "
           "en el diseño del flujo y la dirección de la asistencia de IA.")

    # SECCION 2: AUTORÍA Y USO DE IA
    h1("2. Mi Participación, Autoría y Asistencia de IA")
    p_body(
        "Maximo Porretti concibió, definió y dirigió la totalidad del flujo de desarrollo de esta solución. Establecí la estructura "
        "de delegación de agentes, definí los criterios de aceptación de ambas partes del challenge, y tomé las decisiones arquitectónicas "
        "clave: la propuesta inmutable de transferencias, la idempotencia estricta por intent, y la creación de un Copilot de soporte basado "
        "exclusivamente en evidencia estructurada que opere sin dependencia de claves externas."
    )
    p_body(
        "La inteligencia artificial (Codex / Antigravity) operó como asistente técnico de ejecución bajo mi estricta supervisión, "
        "encargándose de redactar el código de los roles, implementar los módulos de backend y frontend, ejecutar las pruebas automatizadas "
        "y generar los registros de evidencia. Las sesiones originales de IA se conservan intactas en formato JSONL dentro de submission/ai-sessions/ "
        "con sus respectivos hashes criptográficos SHA-256 en manifest.json, garantizando absoluta transparencia."
    )

    # SECCION 3: FLUJO DE AGENTES (.AGENTS)
    h1("3. Arquitectura y Flujo de Desarrollo con Agentes (.agents)")
    p_body(
        "Para profesionalizar el ciclo de desarrollo y garantizar un proceso repetible, se implementó un sistema gobernado por "
        "AGENTS.md y roles modulares en .agents/roles/. El procedimiento operativo cubre el ciclo de vida completo de cada funcionalidad:"
    )

    h2("3.1 Justificación Estratégica: Optimización ante la Restricción de Tiempo")
    p_body(
        "La adopción de este flujo de agentes modulares y asistidos por IA fue una decisión estratégica fundamentada en la gestión óptima "
        "del tiempo disponible. Ante la envergadura del challenge (reparar integralmente la lógica financiera, diseñar una nueva feature "
        "compleja de soporte y documentar rigurosamente los resultados) dentro de un plazo acotado de entrega, un enfoque manual tradicional "
        "habría forzado compromisos indeseables: recortar la profundidad de las pruebas o simplificar la funcionalidad de soporte.\n\n"
        "Estructurar el desarrollo en roles desacoplados (.agents/roles/) permitió maximizar la velocidad de ejecución sin resignar rigor técnico: "
        "permitió concentrar la atención y supervisión humana de Maximo Porretti en las decisiones arquitectónicas de mayor impacto "
        "(inmutabilidad de propuestas, idempotencia atómica, invariantes de seguridad y observabilidad de evidencia), delegando en los asistentes "
        "de IA la codificación ágil de módulos, la ejecución de suites de pruebas exhaustivas y la generación de trazabilidad técnica reproducible."
    )

    h2("3.2 Estructura y Componentes del Sistema de Agentes")

    bullet("Punto de Entrada (AGENTS.md): ", "Define las políticas globales del repositorio, reglas de delegación, segregación de archivos y restricciones críticas de la versión moderna de Next.js.")
    bullet("Skill Procedimental (.agents/skills/feature-delivery/SKILL.md): ", "Codifica el procedimiento estándar de 7 etapas obligatorias: 1. Intake -> 2. Discovery -> 3. Design -> 4. Implement -> 5. Verify -> 6. Release -> 7. Handoff.")
    bullet("Instrucciones de Rol Desacopladas (.agents/roles/): ", "Instrucciones reutilizables que asignan responsabilidades claras a cada etapa:")

    roles_headers = ["Rol (.agents/roles/)", "Misión y Responsabilidad", "Entrada / Salida"]
    roles_rows = [
        ["requirements.md", "Capturar objetivos del candidato, congelar el alcance y redactar criterios de aceptación observables.", "In: Challenge brief / Out: submission/requirements.md"],
        ["architect.md", "Diseñar máquinas de estados, límites de componentes y garantías de idempotencia bancaria.", "In: Criterios / Out: Contratos y estados de transferencia"],
        ["implementer.md", "Implementar la lógica financiera segura (propuestas con TTL, confirmación atómica y reconciliación).", "In: Diseño / Out: src/banking/* y tests/banking.test.ts"],
        ["agent-builder.md", "Construir el Copilot de soporte, telemetría de eventos y control de vacíos de evidencia.", "In: Requerimientos / Out: src/operator/* y src/telemetry.ts"],
        ["qa.md", "Ejecutar suites de pruebas, verificar invariantes contables y evaluar escenarios de degradación de red.", "In: Módulos / Out: npm test (29/29) y reportes de QA"],
        ["reviewer.md", "Auditoría de código independiente, detección de bypass de autorización y revisión de edge cases.", "In: Código / Out: Correcciones previas al release"],
        ["release.md", "Verificación final, exportación de sesiones JSONL, generación documental y empaquetado ZIP reproducible.", "In: Todo verificado / Out: delivery/*.zip con manifiesto"]
    ]
    add_styled_table(roles_headers, roles_rows, [1.6, 3.2, 1.7])

    p_body(
        "El registro cronológico de cómo Maximo Porretti dirigió cada una de estas etapas se encuentra documentado en submission/workflow-log.md."
    )

    # SECCION 4: PARTE 1 - FIXES
    h1("4. Parte 1: Transferencias Confiables (Fixes del Starter)")
    p_body(
        "El análisis estático y dinámico del starter original reveló vulnerabilidades críticas que impedían un lanzamiento seguro a producción. "
        "Se priorizó corregir la integridad de las transacciones financieras y la resiliencia ante fallos de red."
    )

    h2("4.1 Defectos Detectados en el Starter Original")
    bullet("Débitos sin Confirmación: ", "Al solicitar una transferencia, el backend original completaba la transacción inmediatamente sin requerir una revisión ni confirmación explícita del usuario.")
    bullet("Doble Cobro ante Pérdida de Respuesta (Lost Response): ", "Cuando un fallo de red provocaba un timeout tras procesarse el cobro en el banco, el reintento del cliente generaba una nueva referencia bancaria, debitando dinero dos veces por la misma intención.")
    bullet("Falta de Reconciliación: ", "Ante errores transitorios de transporte, la aplicación original asumía rechazo o descartaba la operación, perdiendo la trazabilidad de operaciones completadas.")
    bullet("Ausencia de Validación de Sesión: ", "No se validaba rigurosamente que el titular autenticado coincidiera con la cuenta de origen.")

    h2("4.2 Soluciones Implementadas")
    bullet("Propuestas Inmutables con TTL: ", "Cada solicitud crea una propuesta en estado 'requires_confirmation' que dura 10 minutos. Es inmutable y solo puede confirmarla el usuario titular de la cuenta.")
    bullet("Idempotencia Atómica con Referencia Única: ", "Se asocia de forma determinista y atómica un único 'reference' bancario al intentId. Peticiones simultáneas o reintentos tras caídas de red reutilizan exactamente la misma referencia bancaria.")
    bullet("Reconciliación Activa (GET /v1/operations/:reference): ", "Ante timeouts de red, la aplicación consulta el estado real en el simulador bancario. Si el resultado es incierto, preserva el estado 'unknown' / 'pending' en el dashboard para su resolución posterior.")

    h2("4.3 Tabla Comparativa de Resultados (submission/before-after.json)")
    cmp_headers = ["Escenario de Prueba", "Comportamiento Starter Original", "Versión Final Corregida"]
    cmp_rows = [
        ["Solicitud de EUR 10 sin confirmar", "completed; Débito EUR 10; 1 operación efectuada", "requires_confirmation; Débito EUR 0; 0 operaciones"],
        ["Confirmación explícita del usuario", "No requerida en el starter (débito directo)", "Exigida; Débito EUR 10; 1 operación efectuada"],
        ["Respuesta perdida de red (Lost Response)", "Débito EUR 20; 2 operaciones; 2 referencias distintas (DUPLICACIÓN)", "Débito EUR 10; 1 operación; 1 referencia bancaria única"]
    ]
    add_styled_table(cmp_headers, cmp_rows, [2.0, 2.2, 2.3])

    add_image_with_caption("transfer-proposal.png", "Interfaz de Lucía: Propuesta de transferencia pendiente de confirmación explícita.")
    add_image_with_caption("transfer-completed.png", "Confirmación de transferencia exitosa con saldo actualizado y referencia atómica.")

    # SECCION 5: PARTE 2 - COPILOT DE SOPORTE
    h1("5. Parte 2: Asistente de Soporte para Operadores (Operator Case Copilot)")
    p_body(
        "Como nueva funcionalidad distintiva (Parte 2), se diseñó e implementó un Operator Case Copilot. En lugar de un chatbot genérico, "
        "se creó una herramienta operativa que asiste a los operadores bancarios a resolver disputas e incidentes reconstruyendo la verdad factual."
    )

    h2("5.1 Características Clave del Copilot")
    bullet("Funcionamiento 100% Determinista sin API Key: ", "Reconstruye la cronología completa a partir de mensajes, eventos de herramientas (tools), intents registrados y consultas autenticadas de solo lectura al banco. Funciona de manera completa y confiable sin depender de OpenAI.")
    bullet("Detección Explícita de Vacíos de Evidencia: ", "Si un caso histórico no tiene registros de conversación o eventos, el sistema no inventa ni alucina lo ocurrido; declara formalmente un 'vacío de evidencia' para alertar al operador.")
    bullet("Detección de Discrepancias Financieras: ", "Identifica automáticamente inconsistencias (por ejemplo, si el intent figura 'failed' localmente pero el dinero fue debitado con éxito en el banco), recomendando reconciliación y evitando cobros repetidos.")
    bullet("Protección de Privacidad: ", "Las vistas y APIs del operador están estrictamente segregadas y bloqueadas para usuarios con rol cliente.")
    bullet("Briefing Opcional asistido por IA: ", "Se implementó el endpoint /api/incidents/:id/briefing para generar resúmenes en lenguaje natural cuando se configure una clave, manteniéndose siempre anclado a los hechos registrados.")

    add_image_with_caption("support-historic-detail.png", "Caso histórico de Lucía: Detección de discrepancia financiera y recomendación de reconciliación.")
    add_image_with_caption("support-new-case.png", "Caso nuevo generado por script: Trazabilidad de 8 eventos, intent verificado y operación bancaria coincidente.")
    add_image_with_caption("support-copilot.png", "Panel del Copilot de Soporte con hallazgos, próximos pasos y borrador de respuesta para el cliente.")

    # SECCION 6: VERIFICACIÓN
    h1("6. Verificación, Pruebas y Resultados de Calidad")
    p_body(
        "Se ejecutó una rigurosa suite de pruebas automáticas y manuales que certifican el cumplimiento de todos los invariantes:"
    )

    test_headers = ["Tipo de Verificación", "Detalle de Cobertura", "Resultado Oficial"]
    test_rows = [
        ["Pruebas Unitarias e Invariantes", "Invariantes de cuentas, balance contable, idempotencia y seed determinista", "13 de 13 aprobadas"],
        ["Integración Bancaria HTTP", "Propuestas, TTL, reintentos concurrentes, lost-response, read-unavailable", "9 de 9 aprobadas"],
        ["Soporte, Copilot y Corpus", "Trazabilidad de eventos, permisos de operador, vacíos de evidencia y metadatos", "7 de 7 aprobadas"],
        ["Total de Tests Automatizados", "npm test (node --import tsx --test tests/*.test.ts)", "29 de 29 aprobadas (100%)"],
        ["Chequeo de Tipos (Typecheck)", "next typegen && tsc --noEmit", "Aprobado (0 errores)"],
        ["Compilación de Producción", "npm run build (Next.js App Router)", "Compilación exitosa"],
        ["Revisión Independiente", "Auditoría de seguridad y edge cases de reintento", "Aprobada sin bloqueos"]
    ]
    add_styled_table(test_headers, test_rows, [1.8, 3.2, 1.5])

    h2("6.1 Pasos para Reproducir Localmente")
    code_box(
        "npm ci --ignore-scripts\n"
        "npm run setup\n"
        "npm test\n"
        "npm run typecheck\n"
        "npm run dev"
    )
    p_body(
        "1. Abrir http://127.0.0.1:3000.\n"
        "2. Seleccionar 'Lucía' para crear y confirmar una propuesta de transferencia hacia 'Bruno'.\n"
        "3. Cambiar al usuario 'Marta' (Operador) y abrir el caso de soporte para observar el análisis del Copilot y la discrepancia histórica.\n"
        "4. En una terminal adicional, ejecutar 'node scripts/demo-support.mjs' para simular un caso nuevo con 8 eventos y verificar su trazabilidad en vivo."
    )

    # SECCION 7: EMPAQUETADO
    h1("7. Empaquetado, Entregables y Compromiso de Entrega")
    p_body(
        "La entrega se consolidó en un archivo comprimido reproducible, cumpliendo con la lista de verificación del challenge brief:"
    )
    bullet("banana-bank-maximo-porretti.zip: ", "Ubicado en delivery/. Contiene el código fuente completo, .agents/, AGENTS.md, la suite de tests, fixtures, evidencias JSON, capturas de pantalla, las sesiones originales de IA y este documento explicativo.")
    bullet("Exclusiones Estrictas: ", "Se excluyeron node_modules, .next, .data, bases de datos locales, archivos .env con credenciales y .git, asegurando un empaquetado limpio y sin fugas de secretos.")
    bullet("Sesiones Originales de IA: ", "Almacenadas en submission/ai-sessions/ con su archivo manifest.json y hashes SHA-256 para verificación de autenticidad.")
    bullet("Borrador de Envío: ", "Preparado en submission/email-draft.txt dirigido a hr@tdots.es con el asunto exacto requerido: Maximo Porretti - Banana Bank Technical Challenge.")

    # Guardar
    doc.save(str(out_docx))
    print(f"Documento Word actualizado exitosamente en: {out_docx}")

if __name__ == '__main__':
    main()
