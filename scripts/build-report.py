from pathlib import Path
from html import escape
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Flowable
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'submission'
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold', 'C:/Windows/Fonts/arialbd.ttf'))
styles=getSampleStyleSheet()
for style in styles.byName.values(): style.fontName='Arial'
styles['Title'].fontName='ArialBold'; styles['Title'].fontSize=25; styles['Title'].leading=30; styles['Title'].textColor=colors.black
styles['Heading1'].fontName='ArialBold'; styles['Heading1'].fontSize=18; styles['Heading1'].leading=23; styles['Heading1'].spaceAfter=13
styles['Heading2'].fontName='ArialBold'; styles['Heading2'].fontSize=12; styles['Heading2'].leading=16
styles['BodyText'].fontSize=10.5; styles['BodyText'].leading=15; styles['BodyText'].spaceAfter=9
styles.add(ParagraphStyle('Caption',fontName='Arial',fontSize=9,leading=12,textColor=colors.HexColor('#526251'),spaceAfter=10))
styles.add(ParagraphStyle('CodeBlock',fontName='Courier',fontSize=8.5,leading=12,spaceAfter=10,backColor=colors.HexColor('#f3f5ef'),borderPadding=8))
story=[]; markdown=[]
def p(text,style='BodyText'):
    story.append(Paragraph(escape(text).replace('\n','<br/>'),styles[style]))
    markdown.append(text+'\n')
def heading(text):
    p(text,'Heading1'); markdown[-1]='# '+text+'\n'
def h2(text):
    p(text,'Heading2'); markdown[-1]='## '+text+'\n'
def page():
    story.append(PageBreak()); markdown.append('\n---\n')
def table(rows,widths):
    data=[[Paragraph(escape(str(c)),styles['Caption']) for c in row] for row in rows]
    t=Table(data,colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eef2e7')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),0.5,colors.HexColor('#cad3bf'))]))
    story.extend([t,Spacer(1,12)])
    markdown.extend([' | '.join(map(str,r))+'\n' for r in rows])
def pic(name,maxh=340,maxw=480):
    im=Image(str(OUT/'screenshots'/name))
    scale=min(maxw/im.imageWidth,maxh/im.imageHeight)
    im.drawWidth=im.imageWidth*scale; im.drawHeight=im.imageHeight*scale
    im.hAlign='CENTER'; story.extend([im,Spacer(1,8)])
    markdown.append('![Captura](screenshots/'+name+')\n')
class ScreenshotDetail(Flowable):
    def __init__(self,filename,top,height,maxh=465):
        Flowable.__init__(self); self.reader=ImageReader(str(filename)); self.iw,self.ih=self.reader.getSize()
        self.scale=min(460/self.iw,maxh/height);self.width=self.iw*self.scale;self.height=height*self.scale;self.top=top
        self.hAlign='CENTER'
    def draw(self):
        c=self.canv;c.saveState();clip=c.beginPath();clip.rect(0,0,self.width,self.height);c.clipPath(clip,stroke=0)
        c.drawImage(self.reader,0,self.height-(self.ih-self.top)*self.scale,width=self.iw*self.scale,height=self.ih*self.scale)
        c.restoreState()
p('Desarrollo y entrega de Banana Bank','Title')
p('Maximo Porretti  |  14 de octubre de 2026','Caption')
p('Implementé un flujo de desarrollo con agentes para abordar las dos partes del challenge: transferencias confiables y un asistente de soporte que reconstruye cada caso a partir de evidencia. El proyecto incluye código, pruebas, capturas y las sesiones originales de IA.')
h2('Mi participación y el uso de IA')
p('Definí la necesidad de crear los .agents, el alcance del flujo desde el requerimiento hasta la entrega y la elección del asistente de soporte con evidencia. Codex redactó los archivos e implementó y verificó los cambios bajo mis instrucciones. Esta entrega identifica esa asistencia y conserva los registros originales; no atribuye a trabajo manual los archivos generados por IA.')
h2('Resultado y alcance')
p('La reproducción del código original mostró un débito sin confirmación y un pago duplicado tras perderse la respuesta. La versión corregida exige una propuesta explícita y conserva una referencia bancaria por intención. Las 29 pruebas pasan. También se verificaron tipos, una compilación de producción y los flujos de navegador.')
p('El copilot funciona con evidencia estructurada sin una clave de OpenAI. La generación opcional de un resumen con el modelo quedó pendiente de validación real por no contar con una clave configurada. El simulador bancario se conservó como dependencia externa.')
h2('Cómo recorrer esta entrega')
p('El documento explica el flujo, las decisiones, los resultados antes y después, la función nueva y los pasos de reproducción. submission/ contiene las capturas, evidencia JSON, sesiones originales y un borrador de correo con mi nombre completo en el asunto.')
page()
heading('Flujo desde el requerimiento hasta la entrega')
p('AGENTS.md es el punto de entrada del proyecto. Deriva al flujo reutilizable .agents/skills/feature-delivery/SKILL.md. Los archivos de .agents/roles/ son instrucciones para asignar trabajo; no son agentes registrados automáticamente en la aplicación.')
table([['Etapa y rol','Entrada','Salida y criterio de avance'],
['Requerimientos','Challenge y contrato','Alcance y criterios en submission/requirements.md'],
['Arquitectura','Criterios aceptados','Estados, límites del banco y archivos asignados'],
['Implementación bancaria','Diseño de pagos','Propuestas, referencias estables y pruebas HTTP'],
['Desarrollo del agente','Casos y evidencia','Copilot, trazabilidad y fuentes aplicables'],
['QA y revisión','Cambios ejecutables','Pruebas, tipos, build, UI y revisión independiente'],
['Entrega','Resultados verificados','PDF, sesiones, manifiesto y ZIP reproducible']],[112,120,255])
h2('Cómo usamos el flujo en este challenge')
p('El coordinador leyó los requerimientos, fijó criterios y dividió los archivos. El agente banking implementó el flujo financiero; agent_support trabajó en soporte, documentación y luego empaquetado. reviewer revisó de forma independiente y reprodujo los fallos originales. El coordinador integró API e interfaz y preparó la demostración y el documento.')
p('Los roles de requisitos, arquitectura y QA se ejecutaron desde la sesión coordinadora. La delegación real y sus resultados están en los JSONL originales. Los cambios de dirección y verificaciones se registran en submission/workflow-log.md.')
h2('Aplicarlo a la próxima feature')
p('Abrir una sesión en la raíz del proyecto y pedir: “Usá feature-delivery para implementar [requerimiento] con estos criterios de aceptación”. El agente debe leer AGENTS.md, definir alcance, diseñar, implementar, verificar, revisar y preparar la entrega. Un destino remoto se configura cuando corresponde; no se declara una publicación que no se realizó.')
page()
heading('Parte uno transferencias confiables')
p('Priorizamos confirmación y reintentos porque un error puede mover dinero sin una revisión explícita o repetir un pago. La comparación usa el starter original, bancos y bases temporales y escenarios reproducibles. No se cambió el comportamiento del banco para obtener resultados favorables.')
before=json.loads((OUT/'before-after.json').read_text())
table([['Escenario','Original observado','Versión corregida'],
['Solicitud de EUR 10 sin confirmar','completed; débito EUR 10; 1 operación','requires_confirmation; EUR 0; 0 operaciones'],
['Confirmación explícita','No requerida en starter','Débito EUR 10; 1 operación'],
['Respuesta perdida al enviar EUR 10','Débito EUR 20; 2 operaciones; 2 referencias','Débito EUR 10; 1 operación; 1 referencia']],[115,179,193])
h2('Decisiones de implementación')
p('Cada propuesta dura diez minutos y queda vinculada a usuario, intención y payload inmutable. Solo la sesión de su titular puede confirmarla. La confirmación consume la aprobación y persiste una referencia bancaria de forma atómica. Las solicitudes simultáneas y los reintentos posteriores al reinicio reutilizan esa referencia.')
p('Un timeout no se interpreta como rechazo. La integración consulta GET /v1/operations/:reference. Si el resultado sigue sin verificarse, conserva unknown. El dashboard muestra la transferencia pendiente y permite consultar la intención original después de recargar.')
h2('Cambios y evidencia')
p('Archivos principales: src/banking/actions.ts, authorization.ts y dispatch.ts; app/api/[...path]/route.ts y app/page.tsx. Pruebas: tests/banking.test.ts. La comparación original está en submission/before-after.json; scripts/reproduce-baseline.ts conserva el procedimiento.')
h2('Revisión que cambió el resultado')
p('La revisión encontró que una aprobación consumida desaparecía aunque el resultado fuera desconocido. Se agregó pendingTransfers y una prueba de recarga y consulta con la aprobación original: el banco conserva un único efecto. También se hicieron visibles los identificadores que permiten resolver las citas del copilot.')
page()
heading('Demostración de confirmación')
p('En la interfaz de Lucía creamos una transferencia nueva de EUR 12,34 hacia Bruno. La aplicación mostró una propuesta con importe, origen, destino y descripción. Tras pulsar Confirm these details, verificamos el aviso de finalización y el saldo actualizado.')
story.extend([ScreenshotDetail(OUT/'screenshots'/'transfer-proposal.png',575,620),Spacer(1,8)])
p('Detalle ampliado de la captura real de la propuesta pendiente. El botón inicial fue renombrado luego a Review transfer para describir mejor su efecto. La captura original completa está en submission/screenshots/transfer-proposal.png.','Caption')
p('Comprobación automatizada complementaria: una propuesta no modifica el saldo; las confirmaciones simultáneas y la repetición tras reiniciar la conexión local devuelven una única operación.')
page()
heading('Parte dos asistente de soporte con evidencia')
p('La función nueva ayuda al operador a decidir el próximo paso sin reconstruir acciones que nunca fueron registradas. Combina mensajes, eventos de herramientas, intenciones y una consulta autenticada de solo lectura al banco. Presenta discrepancias, fuentes identificables, vacíos históricos y un borrador de respuesta.')
pic('support-historic-detail.png',maxh=330,maxw=480)
p('Caso histórico de Lucía. El banco muestra el pago completado aunque la intención local esté marcada failed. El copilot recomienda reconciliar la referencia original y evitar un pago nuevo. Los eventos históricos faltantes se reconocen como evidencia ausente.','Caption')
h2('Valor y límites del asistente')
p('El análisis estructurado está integrado en el flujo del agente y soporte y funciona sin clave. Prepare operator briefing ofrece un resumen de IA cuando hay una clave, manteniendo la evidencia a disposición del operador. El texto generado se presenta como borrador; no ejecuta pagos ni autoriza transferencias.')
p('Archivos: src/operator/view.ts y copilot.ts, src/telemetry.ts y la ruta /api/incidents/:id/briefing. La interfaz muestra las citas, los eventos y las intenciones. Los clientes no pueden acceder al detalle de los operadores.')
page()
heading('Caso nuevo y calidad de las fuentes')
p('Creamos una conversación nueva por la API pública, propusimos y confirmamos EUR 2,50 y solicitamos soporte mediante request_human. El caso conserva ocho eventos, una intención y una operación bancaria coincidente. Esta demostración usa las herramientas HTTP; no pretende representar una conversación generada por el modelo.')
pic('support-new-case.png',maxh=285,maxw=480)
p('Captura real del caso nuevo con el hallazgo transfer_verified. submission/demo-evidence.json conserva los identificadores y el resultado. La ausencia de mensajes en esta demostración se muestra como un vacío de evidencia.','Caption')
h2('Información documental más confiable')
p('Los fragmentos conservan título, versión, vigencia y audiencia. La búsqueda filtra por la fecha de referencia del ejercicio, 24 de septiembre de 2026, y por el rol. El índice incluido se adapta desde el manifest sin regenerar embeddings. El prompt exige citas y reconocer la información faltante, en vez de completar condiciones con estimaciones bancarias.')
p('Se probaron la conservación de metadatos, la exclusión de documentos obsoletos y fuentes internas para clientes, y los casos de falta de evidencia. No se ejecutaron llamadas reales de embeddings o generación con OpenAI.')
page()
heading('Verificación y pasos para probar')
table([['Verificación','Resultado'],
['Pruebas públicas','13 de 13 aprobadas'],
['Integración bancaria HTTP','9 de 9 aprobadas'],
['Soporte y fuentes','7 de 7 aprobadas'],
['npm run typecheck','Aprobado'],
['npm run build','Compilación de producción aprobada'],
['Navegador y API pública','Propuesta, confirmación, caso histórico y caso nuevo verificados'],
['Revisión independiente','Hallazgos corregidos; sin bloqueos adicionales en el alcance']],[205,282])
h2('Instalación y ejecución')
p('Node 24 o superior. En este equipo Windows se usó Node 24.19.0. npm ci activó el fallo de compilación de SQLite documentado por el starter; npm ci --ignore-scripts funcionó con el binario nativo incluido. La carga de SQLite se comprobó antes de continuar.')
p('npm ci --ignore-scripts\nnpm run setup\nnpm test\nnpm run typecheck\nnpm run dev','CodeBlock')
p('Abrir http://127.0.0.1:3000. Seleccionar Lucía para crear una propuesta y confirmarla. Seleccionar Marta y abrir el caso del pago de la cena para ver la discrepancia histórica. Con los servicios activos, node scripts/demo-support.mjs crea un caso nuevo. Cada ejecución de ese script representa una nueva intención simulada.')
h2('Escenarios de errores')
p('npm run scenario -- lost-response y npm run scenario -- read-unavailable permiten probar respuestas perdidas y reconciliación no disponible. Volver a normal para una línea de base. Las pruebas usan bases y puertos temporales; no requieren una clave y no alteran la actividad de la aplicación abierta.')
page()
heading('Entrega reproducible y pendientes')
h2('Sesiones originales y archivos')
p('submission/ai-sessions/ contiene los JSONL originales de la sesión coordinadora y los agentes banking, agent_support y reviewer. manifest.json identifica cada sesión y su SHA256. No se reemplazan por este resumen. Los guardian internos de permisos se omiten y esa exclusión se declara en el manifiesto.')
p('El ZIP contiene el código completo, .agents, AGENTS.md, las fixtures, templates de configuración, pruebas, PDF, capturas, evidencia JSON y las sesiones originales. Excluye node_modules, .next, .data, archivos .env con configuración local, Git y temporales.')
h2('Actualizar y empaquetar')
p('npm run sessions:export\nnpm run package:submission','CodeBlock')
p('El resultado se crea fuera de la raíz del código, en delivery/banana-bank-maximo-porretti.zip cuando se usa esta estructura de carpetas. El empaquetador conserva los archivos ocultos del flujo y genera un manifiesto de integridad. Revisar el ZIP en una carpeta nueva y ejecutar setup y las verificaciones.')
p('La sesión activa puede crecer después de exportarla. Ejecutar ambos comandos al terminar esta conversación y antes de enviar para incorporar también el cierre y cualquier interacción posterior.')
h2('Asunto y canal')
p('Asunto: Maximo Porretti - Banana Bank Technical Challenge. submission/email-draft.txt prepara el correo para hr@tdots.es según el starter. El repositorio provisto sirve de referencia del challenge; esta ejecución prepara un ZIP local y no realizó push ni envío de correo.')
h2('Límites y trabajo pendiente')
p('Sin clave de OpenAI, no se validó generación real del chat, embeddings ni el briefing opcional con el proveedor. No se pretende certificar un lanzamiento completo: se priorizaron los fallos financieros y la evidencia de soporte. npm audit reportó avisos altos en next, sharp y source-map-js; revisar y actualizar esas dependencias antes de exposición pública. La selección de personas sigue siendo una conveniencia de simulación, no autenticación de producción.')
p('La publicación remota o el envío se realiza sobre el paquete revisado y con el destino concreto. El flujo está preparado para ese último paso y conserva la distinción entre paquete listo y entrega efectivamente enviada.')
def footer(c,doc):
    c.setFont('Arial',8);c.setFillColor(colors.HexColor('#65705f'))
    c.drawString(48,28,'Banana Bank  |  Maximo Porretti  |  14 octubre 2026')
    c.drawRightString(A4[0]-48,28,str(doc.page))
doc=SimpleDocTemplate(str(OUT/'banana-bank-entregable.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=45,bottomMargin=48,title='Desarrollo y entrega de Banana Bank',author='Maximo Porretti')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'explicacion.md').write_text('\n'.join(markdown),encoding='utf-8')
# Render all final PDF pages through the bundled PDFium package.
import pypdfium2 as pdfium
render_dir=ROOT/'.tmp'/'pdf-review';render_dir.mkdir(parents=True,exist_ok=True)
pdf=pdfium.PdfDocument(str(OUT/'banana-bank-entregable.pdf'))
for i in range(len(pdf)):
    page_=pdf[i]; image_=page_.render(scale=1.5).to_pil();image_.save(render_dir/f'page-{i+1}.png')
print(json.dumps({'pdf':str(OUT/'banana-bank-entregable.pdf'),'pages':len(pdf),'renders':str(render_dir)}))

