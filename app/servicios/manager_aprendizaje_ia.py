from typing import Dict, List
from sqlalchemy.orm import Session

from app.servicios.ia_lectura_service import ServicioAnalisisLectura
from app.servicios.generador_ejercicios import GeneradorEjercicios
from app.modelos import EjercicioPractica


class ManagerAprendizajeIA:
    """
    Orquesta el análisis de lectura y la generación de ejercicios de práctica.
    """

    def __init__(self) -> None:
        self.analizador = ServicioAnalisisLectura()
        self.generador = GeneradorEjercicios()

    async def procesar_lectura(
        self,
        db: Session,
        estudiante_id: int,
        contenido_id: int,
        audio_path: str,
    ) -> Dict:
        """
        Procesa una lectura:
        - analiza pronunciación con Whisper
        - genera ejercicios de práctica
        """
        resultado_analisis = self.analizador.analizar_lectura(
            db=db,
            estudiante_id=estudiante_id,
            contenido_id=contenido_id,
            audio_path=audio_path,
        )

        evaluacion_id = resultado_analisis["evaluacion_id"]
        errores = resultado_analisis["errores"]

        ejercicios_ids = self.generador.crear_ejercicios_desde_errores(
            db=db,
            estudiante_id=estudiante_id,
            evaluacion_id=evaluacion_id,
            errores=errores,
        )

        ejercicios_info: List[Dict] = []
        if ejercicios_ids:
            ejercicios = (
                db.query(EjercicioPractica)
                .filter(EjercicioPractica.id.in_(ejercicios_ids))
                .all()
            )
            for ej in ejercicios:
                ejercicios_info.append(
                    {
                        "id": ej.id,
                        "tipo_ejercicio": ej.tipo_ejercicio,
                        "texto_practica": ej.texto_practica,
                        "palabras_objetivo": ej.palabras_objetivo,
                    }
                )

        resultado_analisis["ejercicios_recomendados"] = ejercicios_info
        return resultado_analisis
