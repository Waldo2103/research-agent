"""
Servicio de persistencia de informes en SQLite.

Guarda un resumen de cada informe generado para construir el historial.
Usa SQLAlchemy síncrono (SQLite es síncrono por naturaleza).
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models.report import Base, InformeDB, InformeResearch

logger = logging.getLogger(__name__)


class StorageService:
    """Persiste y recupera informes desde SQLite."""

    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        logger.info("StorageService inicializado: db=%s", db_path)

    def guardar(self, informe: InformeResearch, ruta_pdf: str | None = None) -> None:
        """Persiste el informe en la base de datos."""
        sentimiento = informe.analisis_sentimiento
        registro = InformeDB(
            id=informe.id,
            tema=informe.tema,
            fecha_creacion=informe.fecha_creacion,
            resumen_ejecutivo=informe.resumen_ejecutivo[:500],  # Resumen corto para lista
            puntos_a_favor=json.dumps(informe.puntos_a_favor, ensure_ascii=False),
            puntos_en_contra=json.dumps(informe.puntos_en_contra, ensure_ascii=False),
            sentimiento_clasificacion=sentimiento.clasificacion,
            sentimiento_puntaje=sentimiento.puntaje,
            sentimiento_justificacion=sentimiento.justificacion,
            conclusiones=informe.conclusiones,
            recomendaciones=json.dumps(informe.recomendaciones, ensure_ascii=False),
            fuentes=json.dumps(
                [{"titulo": f.titulo, "url": f.url} for f in informe.fuentes],
                ensure_ascii=False,
            ),
            ruta_pdf=ruta_pdf,
        )
        with Session(self._engine) as session:
            session.add(registro)
            session.commit()
        logger.info("Informe guardado en historial: id=%s tema='%s'", informe.id, informe.tema)

    def listar(self, limite: int = 50) -> list[dict]:
        """
        Retorna los últimos N informes como dicts con los campos del resumen.

        Returns:
            Lista de dicts con: id, tema, fecha_creacion, sentimiento_clasificacion,
            sentimiento_puntaje, num_fuentes, url_pdf
        """
        with Session(self._engine) as session:
            stmt = (
                select(InformeDB)
                .order_by(InformeDB.fecha_creacion.desc())
                .limit(limite)
            )
            registros = session.scalars(stmt).all()

        resultado = []
        for r in registros:
            try:
                fuentes = json.loads(r.fuentes or "[]")
            except (json.JSONDecodeError, TypeError):
                fuentes = []

            resultado.append({
                "id": r.id,
                "tema": r.tema,
                "fecha_creacion": r.fecha_creacion.isoformat() if isinstance(r.fecha_creacion, datetime) else r.fecha_creacion,
                "sentimiento_clasificacion": r.sentimiento_clasificacion,
                "sentimiento_puntaje": r.sentimiento_puntaje,
                "num_fuentes": len(fuentes),
                "url_pdf": f"/api/pdf/{r.id}" if r.ruta_pdf else None,
            })
        return resultado
