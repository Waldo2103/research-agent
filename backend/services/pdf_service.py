"""
Servicio de generación de PDF usando WeasyPrint.

Convierte el InformeResearch a un PDF profesional a través de un
template HTML/CSS. El template usa la misma paleta visual que el frontend.
"""

import logging
from pathlib import Path
from datetime import datetime

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from models.report import InformeResearch

logger = logging.getLogger(__name__)


class GeneracionPDFError(Exception):
    """Error al generar el PDF del informe."""

    def __init__(self, informe_id: str, mensaje: str) -> None:
        self.informe_id = informe_id
        super().__init__(f"Error generando PDF [{informe_id}]: {mensaje}")


class PDFService:
    """
    Servicio para generar PDFs de informes de investigación.

    Genera el PDF a partir de un template HTML embebido,
    lo que permite usar CSS estándar para el diseño.
    """

    def __init__(self, directorio_salida: str) -> None:
        """
        Inicializa el servicio PDF.

        Args:
            directorio_salida: Directorio donde se guardarán los PDFs generados
        """
        self._directorio = Path(directorio_salida)
        self._directorio.mkdir(parents=True, exist_ok=True)
        logger.info("PDFService inicializado: directorio=%s", directorio_salida)

    def generar(self, informe: InformeResearch) -> Path:
        """
        Genera el PDF del informe y lo guarda en disco.

        Args:
            informe: El informe a convertir a PDF

        Returns:
            Path al archivo PDF generado

        Raises:
            GeneracionPDFError: Si falla la generación del PDF
        """
        ruta_pdf = self._directorio / f"{informe.id}.pdf"

        try:
            logger.info("Generando PDF para informe: %s", informe.id)
            html_contenido = self._renderizar_html(informe)

            font_config = FontConfiguration()
            documento_html = HTML(string=html_contenido, base_url=None)
            documento_html.write_pdf(
                target=str(ruta_pdf),
                font_config=font_config,
            )

            logger.info("PDF generado correctamente: %s (%.1f KB)",
                        ruta_pdf.name, ruta_pdf.stat().st_size / 1024)
            return ruta_pdf

        except Exception as e:
            raise GeneracionPDFError(
                informe_id=informe.id,
                mensaje=str(e),
            ) from e

    def _renderizar_html(self, informe: InformeResearch) -> str:
        """
        Genera el HTML completo del informe para ser convertido a PDF.

        Args:
            informe: El informe con todos sus datos

        Returns:
            String con el HTML completo y CSS embebido
        """
        fecha_formateada = informe.fecha_creacion.strftime("%d de %B de %Y, %H:%M hs")

        # Sección de puntos a favor y en contra
        pros_html = "".join(
            f"<li>{self._escapar(p)}</li>" for p in informe.puntos_a_favor
        )
        contras_html = "".join(
            f"<li>{self._escapar(c)}</li>" for c in informe.puntos_en_contra
        )

        # Sección de recomendaciones
        recomendaciones_html = "".join(
            f"<li>{self._escapar(r)}</li>" for r in informe.recomendaciones
        )

        # Sección de fuentes
        fuentes_html = ""
        for i, fuente in enumerate(informe.fuentes, 1):
            fecha_consulta = fuente.fecha_consulta.strftime("%d/%m/%Y %H:%M")
            fuentes_html += f"""
            <tr>
                <td class="fuente-num">{i}</td>
                <td>{self._escapar(fuente.titulo)}</td>
                <td><a href="{self._escapar(fuente.url)}">{self._escapar(fuente.url[:60])}...</a></td>
                <td class="fuente-fecha">{fecha_consulta}</td>
            </tr>"""

        # Sección de sentimiento
        sentimiento = informe.analisis_sentimiento
        color_sentimiento = {
            "positivo": "#27ae60",
            "negativo": "#e74c3c",
            "neutro": "#f39c12",
        }.get(sentimiento.clasificacion, "#7f8c8d")

        # Barra de puntaje (-1 a 1, convertida a 0-100% para CSS)
        puntaje_pct = int((sentimiento.puntaje + 1.0) / 2.0 * 100)

        # Párrafos del resumen ejecutivo
        parrafos_resumen = informe.resumen_ejecutivo.split("\n\n")
        resumen_html = "".join(
            f"<p>{self._escapar(p.strip())}</p>"
            for p in parrafos_resumen if p.strip()
        )

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  /* ── Reset y base ── */
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "DejaVu Sans", "Arial", sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #2c3e50;
    background: white;
  }}

  /* ── Portada / Encabezado ── */
  .encabezado {{
    background: linear-gradient(135deg, #1a3a5c 0%, #2980b9 100%);
    color: white;
    padding: 32px 40px;
    margin-bottom: 24px;
  }}
  .encabezado .etiqueta {{
    font-size: 8pt;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.8;
    margin-bottom: 8px;
  }}
  .encabezado h1 {{
    font-size: 20pt;
    font-weight: bold;
    margin-bottom: 12px;
    line-height: 1.3;
  }}
  .encabezado .meta {{
    font-size: 9pt;
    opacity: 0.85;
  }}

  /* ── Cuerpo del documento ── */
  .contenido {{ padding: 0 40px 40px 40px; }}

  /* ── Secciones ── */
  .seccion {{ margin-bottom: 28px; page-break-inside: avoid; }}
  .seccion-titulo {{
    font-size: 12pt;
    font-weight: bold;
    color: #1a3a5c;
    border-bottom: 2px solid #2980b9;
    padding-bottom: 4px;
    margin-bottom: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .seccion p {{ margin-bottom: 10px; text-align: justify; }}

  /* ── Tabla de pros/contras ── */
  .tabla-analisis {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
  }}
  .tabla-analisis th {{
    padding: 10px 14px;
    font-size: 9pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: bold;
    text-align: left;
  }}
  .th-favor {{ background: #eafaf1; color: #1e8449; border-bottom: 2px solid #27ae60; }}
  .th-contra {{ background: #fdedec; color: #a93226; border-bottom: 2px solid #e74c3c; }}
  .tabla-analisis td {{
    padding: 8px 14px;
    vertical-align: top;
    width: 50%;
  }}
  .tabla-analisis ul {{ padding-left: 18px; }}
  .tabla-analisis li {{ margin-bottom: 6px; font-size: 9.5pt; }}
  .col-favor {{ background: #f9fefe; border-right: 1px solid #d5f5e3; }}
  .col-contra {{ background: #fefefe; }}

  /* ── Sentimiento ── */
  .sentimiento-caja {{
    background: #f8f9fa;
    border-left: 4px solid {color_sentimiento};
    padding: 14px 18px;
    border-radius: 0 4px 4px 0;
  }}
  .sentimiento-badge {{
    display: inline-block;
    background: {color_sentimiento};
    color: white;
    padding: 3px 12px;
    border-radius: 12px;
    font-size: 9pt;
    font-weight: bold;
    text-transform: uppercase;
    margin-bottom: 10px;
  }}
  .barra-contenedor {{
    background: #e0e0e0;
    height: 8px;
    border-radius: 4px;
    margin: 8px 0;
    position: relative;
  }}
  .barra-progreso {{
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    width: {puntaje_pct}%;
    background: {color_sentimiento};
    border-radius: 4px;
  }}
  .barra-etiquetas {{
    display: flex;
    justify-content: space-between;
    font-size: 7pt;
    color: #7f8c8d;
    margin-top: 2px;
  }}
  .sentimiento-justificacion {{ margin-top: 10px; font-size: 9.5pt; font-style: italic; }}

  /* ── Recomendaciones ── */
  .lista-recomendaciones {{ padding-left: 20px; }}
  .lista-recomendaciones li {{ margin-bottom: 8px; }}

  /* ── Tabla de fuentes ── */
  .tabla-fuentes {{
    width: 100%;
    border-collapse: collapse;
    font-size: 8pt;
  }}
  .tabla-fuentes th {{
    background: #1a3a5c;
    color: white;
    padding: 8px 10px;
    text-align: left;
  }}
  .tabla-fuentes td {{
    padding: 6px 10px;
    border-bottom: 1px solid #ecf0f1;
    vertical-align: top;
  }}
  .tabla-fuentes tr:nth-child(even) td {{ background: #f8f9fa; }}
  .tabla-fuentes a {{ color: #2980b9; text-decoration: none; }}
  .fuente-num {{ text-align: center; width: 30px; font-weight: bold; }}
  .fuente-fecha {{ white-space: nowrap; color: #7f8c8d; }}

  /* ── Pie de página ── */
  @page {{
    margin: 20mm 15mm;
    @bottom-center {{
      content: "Agente de Research — Página " counter(page) " de " counter(pages);
      font-size: 8pt;
      color: #95a5a6;
    }}
  }}
</style>
</head>
<body>

<div class="encabezado">
  <div class="etiqueta">Informe de Investigación</div>
  <h1>{self._escapar(informe.tema)}</h1>
  <div class="meta">Generado el {fecha_formateada} &nbsp;|&nbsp; ID: {informe.id[:8]}...</div>
</div>

<div class="contenido">

  <!-- 1. Resumen Ejecutivo -->
  <div class="seccion">
    <div class="seccion-titulo">1. Resumen Ejecutivo</div>
    {resumen_html}
  </div>

  <!-- 2. Puntos a Favor y en Contra -->
  <div class="seccion">
    <div class="seccion-titulo">2. Análisis de Puntos</div>
    <table class="tabla-analisis">
      <thead>
        <tr>
          <th class="th-favor">✓ Puntos a Favor</th>
          <th class="th-contra">✗ Puntos en Contra</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="col-favor"><ul>{pros_html}</ul></td>
          <td class="col-contra"><ul>{contras_html}</ul></td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- 3. Análisis de Sentimiento -->
  <div class="seccion">
    <div class="seccion-titulo">3. Análisis de Sentimiento</div>
    <div class="sentimiento-caja">
      <div class="sentimiento-badge">{sentimiento.clasificacion.upper()}</div>
      <div class="barra-contenedor">
        <div class="barra-progreso"></div>
      </div>
      <div class="barra-etiquetas">
        <span>Muy Negativo</span>
        <span>Neutro</span>
        <span>Muy Positivo</span>
      </div>
      <div class="sentimiento-justificacion">{self._escapar(sentimiento.justificacion)}</div>
    </div>
  </div>

  <!-- 4. Conclusiones y Recomendaciones -->
  <div class="seccion">
    <div class="seccion-titulo">4. Conclusiones y Recomendaciones</div>
    <p>{self._escapar(informe.conclusiones)}</p>
    <br>
    <strong>Recomendaciones:</strong>
    <ul class="lista-recomendaciones">{recomendaciones_html}</ul>
  </div>

  <!-- 5. Fuentes Citadas -->
  <div class="seccion">
    <div class="seccion-titulo">5. Fuentes Citadas</div>
    <table class="tabla-fuentes">
      <thead>
        <tr>
          <th>#</th>
          <th>Título</th>
          <th>URL</th>
          <th>Fecha de Consulta</th>
        </tr>
      </thead>
      <tbody>{fuentes_html}</tbody>
    </table>
  </div>

</div>
</body>
</html>"""

    @staticmethod
    def _escapar(texto: str) -> str:
        """
        Escapa caracteres HTML especiales para prevenir inyección en el template.

        Args:
            texto: Texto a escapar

        Returns:
            Texto con caracteres HTML escapados
        """
        return (
            str(texto)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
