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

    # Estilos Generales - PALETA MONOCROMÁTICA / NEUTRA ELEGANTE
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

    # ENCABEZADO Y METADATOS OFICIALES
    title("Desarrollo y Entrega Técnica de Banana Bank")
    subtitle("Documento Explicativo Oficial: Flujo de Agentes (.agent), Fixes Financieros, Copilot de Soporte y Evidencias de Verificación")

    meta_headers = ["Elemento de Entrega", "Detalle Registrado"]
    meta_rows = [
        ["Candidato (Autor)", "Maximo Porretti"],
        ["Asunto Oficial del Correo", "Maximo Porretti - Banana Bank Technical Challenge"],
        ["Fecha de Entrega", "14 de octubre de 2026"],
        ["Destino de Entrega", "hr@tdots.es (según especificación del challenge)"],
        ["Archivo Comprimido Entregable", "delivery/banana-bank-maximo-porretti.zip"],
        ["Sesiones de IA Incluidas", "submission/ai-sessions/ (formato JSONL original con hashes SHA-256)"],
        ["Resultado de Verificación", "29 de 29 pruebas aprobadas, typecheck limpio, build de producción exitoso"]
    ]
    add_styled_table(meta_headers, meta_rows, [2.3, 4.2])

    # SECCION 1: CONTEXTO Y ALCANCE
    h1("1. Alcance Oficial del Challenge y Requerimientos")
    p_body(
        "El challenge Banana Bank ubica al candidato en la situación de unirse al equipo técnico de una entidad bancaria ficticia que "
        "planea lanzar su asistente de inteligencia artificial para clientes y operadores el próximo lunes. La empresa facilitó "
        "un proyecto funcional inicial (aplicación web Next.js con chat de IA, datos simulados y un servicio bancario externo en simulator/), "
        "pero requería evidencia rigurosa de confiabilidad y una funcionalidad innovadora. El requerimiento formal exigió abordar dos partes "
        "principales más la entrega en un paquete único y reproducible:"
    )

    bullet("Parte 1 - Preparar la app para el lunes (40% de la evaluación): ", 
           "Explorar el código starter, encontrar problemas reales y reproducibles, y corregir a fondo los defectos críticos elegidos. "
           "Se exigió enfocarse en la integridad de las transferencias, la integración con el banco y la seguridad, sin alterar el simulador "
           "bancario externo (tratado como caja negra inmutable). Aportar evidencia cuantitativa y demostrable de 'Antes vs. Después'.")

    bullet("Parte 2 - Construir algo distintivo (40% de la evaluación): ", 
           "Diseñar e implementar una funcionalidad creativa, útil y no genérica para el agente de Banana Bank, integrada en el flujo operativo "
           "del banco (para clientes o soporte de operadores). Demostrarla en vivo con casos de uso concretos.")

    bullet("Metodología, Verificación y Entrega (20% de la evaluación): ", 
           "Explicar las decisiones técnicas, ejecutar pruebas automatizadas completas y empaquetar todo en un único archivo ZIP reproducible. "
           "El ZIP debe incluir el código completo, las sesiones originales de IA (en submission/ai-sessions/), y el documento explicativo en Word, "
           "excluyendo node_modules, .next, .data, bases de datos locales y credenciales privadas.")

    bullet("Requerimiento de Autoría y Flujo de Agentes: ", 
           "Maximo Porretti diseñó, estructuró y creó los archivos de agentes (.agent) para gobernar el flujo integral de desarrollo "
           "de la aplicación, desde la captura del requerimiento hasta la subida y empaquetado de la feature, documentando cómo se utilizó dicho flujo "
           "para resolver el challenge.")

    # SECCION 2: AUTORÍA Y DIRECCIÓN DEL CANDIDATO
    h1("2. Autoría, Liderazgo del Candidato y Asistencia de IA")
    p_body(
        "Maximo Porretti concibió, definió y dirigió la totalidad de la solución técnica presentada en este proyecto. Diseñé la arquitectura "
        "de agentes modulares (.agent), formulé los criterios de aceptación de ambas partes del challenge, y tomé las decisiones de ingeniería "
        "fundamentales: la adopción de propuestas inmutables con TTL para autorizaciones de transferencias, la garantía de idempotencia estricta "
        "asociando deterministamente un único reference bancario a cada intentId, y el diseño de un Copilot de soporte para operadores que opera "
        "de forma 100% determinista sobre evidencia factual estructurada sin requerir claves de API externas."
    )
    p_body(
        "La inteligencia artificial (asistente Antigravity / Gemini) actuó como un par programador y acelerador de ejecución bajo mi estricta "
        "dirección y supervisión, asistiendo en la redacción de código tipado, la creación de suites de tests de red y la recolección de métricas. "
        "Las sesiones de interacción con la IA se preservan de manera íntegra e inalterada en formato JSONL dentro de submission/ai-sessions/ "
        "con sus respectivas sumas criptográficas SHA-256 en manifest.json, garantizando máxima transparencia sobre el proceso."
    )

    # SECCION 3: FLUJO COMPLETO DE AGENTES (.AGENT)
    h1("3. Flujo Integral de Desarrollo Asistido por Agentes (.agent)")
    p_body(
        "Para transformar el desarrollo en un proceso predecible, seguro y repetible, Maximo Porretti estructuró un sistema de 7 agentes especializados "
        "en el directorio .agent/ (replicados en .agents/roles/). Este pipeline abarca de extremo a extremo el ciclo de vida del software, "
        "desde que se recibe la necesidad de negocio hasta que la feature es subida y empaquetada para entrega:"
    )

    h2("3.1 Descripción de las 7 Etapas del Flujo de Agentes")

    bullet("1. Intake y Requerimientos (01-requirements.agent.md): ", 
           "Toma el brief o requerimiento de negocio. Analiza el dominio, congela el alcance (separando requerimientos esenciales de secundarios), "
           "identifica invariantes contables inmutables y redacta criterios de aceptación cuantitativos y observables en submission/requirements.md.")

    bullet("2. Arquitectura y Diseño Técnico (02-architect.agent.md): ", 
           "Traduce los requerimientos en contratos de software. Diseña la máquina de estados de las transferencias (proposal -> requires_confirmation -> "
           "in_flight -> completed / failed / unknown), establece la regla de idempotencia atómica 1 a 1 entre intentId y referencia bancaria, "
           "y asigna conjuntos de archivos disjuntos para evitar conflictos de integración.")

    bullet("3. Implementación Core Bancario (03-implementer.agent.md): ", 
           "Implementa la lógica financiera en src/banking/ y componentes web. Construye propuestas con TTL de 10 minutos, valida criptográficamente "
           "el titular de la sesión para impedir transferencias no autorizadas, y programa la reconciliación activa mediante GET /v1/operations/:reference "
           "sin modificar en ningún momento el simulador externo.")

    bullet("4. Construcción del Copilot de Soporte (04-agent-builder.agent.md): ", 
           "Desarrolla la funcionalidad de valor agregado en src/operator/ y src/telemetry.ts. Reconstruye líneas de tiempo de incidentes a partir "
           "de eventos de chat y herramientas, detecta vacíos de evidencia de forma honesta (sin alucinar hechos) y guía al operador en la resolución "
           "de discrepancias bancarias sin depender obligatoriamente de OpenAI.")

    bullet("5. Aseguramiento de Calidad y Testing (05-qa-tester.agent.md): ", 
           "Ejecuta suites automatizadas exhaustivas (29 tests). Simula condiciones adversas de transporte de red (lost-response, slow-response, "
           "read-unavailable) para demostrar que no existen dobles cobros y que las referencias permanecen idempotentes ante fallos de red.")

    bullet("6. Auditoría de Código y Seguridad (06-code-reviewer.agent.md): ", 
           "Revisión de código independiente previa a la liberación. Audita controles de acceso (garantizando que clientes no puedan acceder a APIs de operador), "
           "verifica la inmutabilidad de payloads y valida que el simulador bancario se haya preservado intacto como caja negra.")

    bullet("7. Release, Empaquetado y Entrega de la Feature (07-release-delivery.agent.md): ", 
           "Ejecuta typecheck y build de producción, consolida las sesiones de IA en submission/ai-sessions/ con hashes SHA-256, compila el informe "
           "Word oficial y empaqueta el archivo comprimido reproducible delivery/banana-bank-maximo-porretti.zip excluyendo dependencias y credenciales.")

    h2("3.2 Matriz Resumen de Agentes y Responsabilidades")
    roles_headers = ["Agente (.agent)", "Fase Operativa", "Responsabilidad Central", "Artefactos Principales"]
    roles_rows = [
        ["01-requirements.agent.md", "1. Intake", "Congelamiento de alcance y criterios medibles.", "submission/requirements.md"],
        ["02-architect.agent.md", "2. Diseño", "Máquina de estados, idempotencia y contratos.", "docs/contracts.md, interfaces"],
        ["03-implementer.agent.md", "3. Core Bancario", "Propuestas con TTL, sesión y reconciliación.", "src/banking/*, UI transferencias"],
        ["04-agent-builder.agent.md", "4. Feature IA", "Copilot de soporte, telemetría y vacíos de evidencia.", "src/operator/*, UI operador"],
        ["05-qa-tester.agent.md", "5. Testing / QA", "Batería de 29 tests, fallos de red simulados.", "tests/*.test.ts, npm test"],
        ["06-code-reviewer.agent.md", "6. Code Review", "Auditoría de seguridad, RBAC y caja negra simulator/.", "Control de calidad y revisión"],
        ["07-release-delivery.agent.md", "7. Release", "Compilación de producción, sesiones IA y empaquetado ZIP.", "delivery/*.zip, informe Word"]
    ]
    add_styled_table(roles_headers, roles_rows, [1.7, 1.0, 2.5, 1.8])

    h2("3.3 Cómo Usamos el Flujo para Desarrollar el Challenge Banana Bank")
    p_body(
        "El desarrollo del challenge siguió rigurosamente la secuencia definida por Maximo Porretti en los .agent:\n\n"
        "1. Intake: El Requirements Agent examinó docs/challenge.md y fijó que la Parte 1 requería erradicar el doble cobro y la falta de confirmación, "
        "mientras que la Parte 2 exigía una herramienta operativa no trivial que resolviera disputas de clientes sin inventar hechos.\n"
        "2. Arquitectura: El Architect Agent diseñó la máquina de estados con proposals inmutables y la estrategia de idempotencia con reference único, "
        "aislando el core bancario del nuevo subsistema de soporte para operadores.\n"
        "3. Implementación: El Implementer Agent codificó en src/banking/ la creación y confirmación atómica de propuestas con validación de titular.\n"
        "4. Feature Copilot: El Agent Builder Agent programó el Operator Case Copilot, dotándolo de capacidad para reconstruir hechos a partir "
        "de telemetría de eventos y reportar vacíos de evidencia en casos históricos.\n"
        "5. Verificación: El QA Agent ejecutó las 29 pruebas automatizadas bajo escenarios de red inestable (lost-response y slow-response), certificando cero fallos.\n"
        "6. Auditoría: El Reviewer Agent confirmó que los clientes no pueden ver datos de operador ni alterar montos de propuestas aprobadas.\n"
        "7. Release: El Release Agent certificó la compilación de producción con Next.js, exportó las sesiones de IA con hash SHA-256 y empaquetó el entregable final."
    )

    # SECCION 4: PARTE 1 - FIXES DEL STARTER
    h1("4. Parte 1: Transferencias Confiables (Fixes del Starter)")
    p_body(
        "La evaluación inicial del código starter reveló tres vulnerabilidades graves que afectaban la integridad contable y la seguridad "
        "de la entidad financiera:"
    )

    bullet("Débito Directo sin Confirmación: ", 
           "El starter debitaba fondos de forma inmediata tras recibir el comando del usuario, sin presentar un resumen formal de la transacción "
           "ni solicitar una confirmación explícita con los detalles finales.")

    bullet("Doble Cobro ante Pérdida de Respuesta (Lost Response): ", 
           "Cuando el simulador bancario procesaba exitosamente el débito pero la respuesta HTTP se perdía por un corte transitorio de red, "
           "el reintento automático del cliente generaba una nueva referencia bancaria, debitando dinero dos veces por una misma intención.")

    bullet("Ausencia de Reconciliación Activa: ", 
           "Frente a errores de transporte o timeouts, el sistema original asumía un fallo o descartaba la operación, perdiendo la trazabilidad "
           "de transacciones efectivamente cobradas por el banco.")

    h2("4.1 Soluciones de Ingeniería Implementadas")
    bullet("Propuestas Inmutables con TTL: ", 
           "Cada solicitud genera una propuesta formal en estado 'requires_confirmation' con un tiempo de expiración de 10 minutos. Es inmutable, "
           "contiene el monto exacto, cuenta origen y cuenta destino, y solo puede ser confirmada por el usuario titular autenticado.")

    bullet("Idempotencia Atómica con Referencia Única: ", 
           "Se vincula atómicamente un único identificador bancario determinista a cada intentId. Peticiones simultáneas o reintentos posteriores "
           "a una caída de red reutilizan exactamente la misma referencia bancaria, evitando la duplicación de transferencias.")

    bullet("Reconciliación Activa y Estado Unknown: ", 
           "Ante respuestas ambiguas o caídas de red, la aplicación interroga a GET /v1/operations/:reference en el banco. Si el resultado no puede "
           "determinarse de inmediato, la operación se preserva en estado 'unknown' / 'pending' para que el usuario o el operador puedan conciliarla "
           "sin generar débitos repetidos.")

    h2("4.2 Tabla Comparativa de Resultados: Antes vs. Después")
    cmp_headers = ["Escenario de Prueba", "Comportamiento Starter Original", "Versión Final Corregida"]
    cmp_rows = [
        ["Solicitud de EUR 10 sin confirmar", "completed; Débito EUR 10; 1 operación efectuada", "requires_confirmation; Débito EUR 0; 0 operaciones"],
        ["Confirmación explícita del usuario", "No requerida en el starter (débito directo)", "Exigida; Débito EUR 10; 1 operación efectuada"],
        ["Respuesta perdida de red (Lost Response)", "Débito EUR 20; 2 operaciones; 2 referencias distintas (DUPLICACIÓN)", "Débito EUR 10; 1 operación; 1 referencia bancaria única"]
    ]
    add_styled_table(cmp_headers, cmp_rows, [2.0, 2.2, 2.3])

    add_image_with_caption("transfer-proposal.png", "Interfaz de Lucía: Propuesta de transferencia emitida en estado requires_confirmation.")
    add_image_with_caption("transfer-completed.png", "Confirmación de transferencia exitosa con saldo debitado y referencia bancaria única.")

    # SECCION 5: PARTE 2 - COPILOT DE SOPORTE
    h1("5. Parte 2: Asistente Operativo de Casos (Operator Case Copilot)")
    p_body(
        "Como funcionalidad innovadora y de alto valor para el banco (Parte 2), Maximo Porretti concibió e implementó el Operator Case Copilot. "
        "En lugar de un chatbot superficial, se construyó una herramienta orientada al equipo de operaciones y soporte para resolver "
        "disputas y reclamos de clientes con evidencia factual verificable."
    )

    h2("5.1 Características Técnicas del Copilot")
    bullet("Funcionamiento Determinista sin Dependencia de Claves: ", 
           "Reconstruye la cronología completa del reclamo a partir de eventos de conversación, ejecuciones de herramientas (tools), intents registrados "
           "y llamadas autenticadas de solo lectura al banco, funcionando de forma 100% confiable y autónoma sin requerir una clave de OpenAI.")

    bullet("Declaración Explícita de Vacíos de Evidencia (Evidence Gaps): ", 
           "Cuando se inspecciona un caso histórico sin registros de telemetría, el Copilot no inventa ni alucina lo ocurrido; declara formalmente "
           "un 'vacío de evidencia' para alertar al operador de que los hechos no están documentados en el sistema.")

    bullet("Detección Automática de Discrepancias Financieras: ", 
           "Identifica de manera inmediata inconsistencias contables (por ejemplo, si el intent figura 'failed' en la aplicación pero el dinero "
           "fue debitado exitosamente en el banco), recomendando al operador conciliar la cuenta sin volver a cobrarle al cliente.")

    bullet("Segregación de Roles y Control de Privacidad: ", 
           "Las vistas y APIs del operador están estrictamente protegidas mediante validación de sesión de servidor, impidiendo el acceso a clientes.")

    bullet("Briefing Opcional Asistido por IA: ", 
           "Se implementó el endpoint /api/incidents/:id/briefing para generar resúmenes en lenguaje natural cuando se configure una API key, "
           "manteniendo las conclusiones firmemente ancladas en la evidencia registrada.")

    add_image_with_caption("support-historic-detail.png", "Caso histórico de Lucía: Detección de discrepancia financiera y sugerencia de conciliación.")
    add_image_with_caption("support-new-case.png", "Caso nuevo generado por script de telemetría: Trazabilidad completa de 8 eventos e intent verificado.")
    add_image_with_caption("support-copilot.png", "Panel de control del Copilot de Soporte con hallazgos, próximos pasos y borrador de respuesta al cliente.")

    # SECCION 6: VERIFICACIÓN Y CALIDAD
    h1("6. Verificación, Pruebas y Resultados de Calidad")
    p_body(
        "Se ejecutó una rigurosa suite de pruebas automatizadas y chequeos estáticos que certifican el 100% de cumplimiento de los contratos:"
    )

    test_headers = ["Tipo de Verificación", "Detalle de Cobertura", "Resultado Oficial"]
    test_rows = [
        ["Invariantes Contables y Unitarias", "Invariantes de balance contable, idempotencia y seed determinista", "13 de 13 aprobadas"],
        ["Integración Bancaria HTTP", "Propuestas, TTL, concurrencia, lost-response, read-unavailable", "9 de 9 aprobadas"],
        ["Soporte, Copilot y Corpus", "Telemetría de eventos, permisos de operador, vacíos de evidencia y metadatos", "7 de 7 aprobadas"],
        ["Total de Tests Automatizados", "npm test (node --import tsx --test tests/*.test.ts)", "29 de 29 aprobadas (100%)"],
        ["Chequeo de Tipos (Typecheck)", "next typegen && tsc --noEmit", "Aprobado (0 errores)"],
        ["Compilación de Producción", "npm run build (Next.js App Router)", "Compilación exitosa (0 errores)"]
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
        "1. Iniciar la aplicación y navegar a http://127.0.0.1:3000.\n"
        "2. Iniciar sesión como 'Lucía' para crear y confirmar una transferencia hacia 'Bruno'.\n"
        "3. Cambiar de usuario a 'Marta' (Operador) y acceder a la sección de soporte para observar el análisis del Copilot y la discrepancia detectada.\n"
        "4. En una terminal paralela, ejecutar 'node scripts/demo-support.mjs' para inyectar un caso nuevo con 8 eventos de telemetría y ver la actualización en vivo."
    )

    # SECCION 7: EMPAQUETADO Y ENTREGABLES
    h1("7. Empaquetado, Entregables y Compromiso de Entrega")
    p_body(
        "La entrega se consolidó en un archivo comprimido reproducible, cumpliendo con la lista de verificación del challenge brief:"
    )
    bullet("banana-bank-maximo-porretti.zip: ", 
           "Ubicado en delivery/. Contiene el código fuente completo, .agent/, .agents/, AGENTS.md, la suite de tests, fixtures, evidencias JSON, "
           "capturas de pantalla, las sesiones originales de IA y este documento explicativo oficial en formato Word.")

    bullet("Exclusiones Estrictas: ", 
           "Se excluyeron rigurosamente node_modules, .next, .data, bases de datos locales, archivos .env con credenciales y .git, asegurando un empaquetado "
           "completamente limpio y reproducible.")

    bullet("Sesiones Originales de IA: ", 
           "Almacenadas en submission/ai-sessions/ con su archivo manifest.json y hashes criptográficos SHA-256 para verificación de autenticidad.")

    bullet("Documento Explicativo Oficial: ", 
           "Este documento Word (banana-bank-entregable.docx) constituye el único artefacto explicativo formal de entrega, habiéndose depurado "
           "documentación y borradores redundantes.")

    bullet("Asunto Oficial de Envío: ", 
           "Maximo Porretti - Banana Bank Technical Challenge (destinado a hr@tdots.es).")

    # Guardar en submission/banana-bank-entregable.docx
    doc.save(str(out_docx))
    print(f"Documento Word actualizado exitosamente en: {out_docx}")

    # Guardar copia en delivery/
    delivery_dir = root / 'delivery'
    delivery_dir.mkdir(parents=True, exist_ok=True)
    doc.save(str(delivery_dir / 'banana-bank-entregable.docx'))
    print(f"Copia guardada en delivery: {delivery_dir / 'banana-bank-entregable.docx'}")

    # Guardar copias en directorio padre de trabajo si existe
    if root.parent.exists() and root.parent != root:
        parent_delivery = root.parent / 'delivery'
        if parent_delivery.exists():
            doc.save(str(parent_delivery / 'banana-bank-entregable.docx'))
        parent_root_docx = root.parent / 'banana-bank-entregable.docx'
        doc.save(str(parent_root_docx))
        print(f"Copia sincronizada en workspace exterior: {parent_root_docx}")

if __name__ == '__main__':
    main()
