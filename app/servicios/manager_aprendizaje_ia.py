from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.servicios.ia_lectura_service import ServicioAnalisisLectura
from app.servicios.generador_ejercicios import GeneradorEjercicios
from app.modelos import EjercicioPractica
from app.modelos import EjercicioPractica, FragmentoPractica


class ManagerAprendizajeIA:
    def __init__(self) -> None:
        self.analizador = ServicioAnalisisLectura()
        self.generador = GeneradorEjercicios()

    def procesar_lectura(
        self,
        db: Session,
        estudiante_id: int,
        contenido_id: int,
        audio_path: str,
        evaluacion_id: Optional[int] = None,
    ) -> Dict:
        resultado_analisis = self.analizador.analizar_lectura(
            db=db,
            estudiante_id=estudiante_id,
            contenido_id=contenido_id,
            audio_path=audio_path,
            evaluacion_id=evaluacion_id,
        )

        evaluacion_id_real = resultado_analisis["evaluacion_id"]
        errores = resultado_analisis.get("errores", [])

        ejercicios_ids = self.generador.crear_ejercicios_desde_errores(
            db=db,
            estudiante_id=estudiante_id,
            evaluacion_id=evaluacion_id_real,
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
                        "dificultad": ej.dificultad,
                        "completado": ej.completado,
                    }
                )

        resultado_analisis["ejercicios_recomendados"] = ejercicios_info
        return resultado_analisis
    def practicar_ejercicio(
        self,
        db: Session,
        estudiante_id: int,
        ejercicio_id: int,
        audio_path: str,
    ) -> Dict:
        """
        El niño practica un ejercicio concreto.
        La IA analiza solo ese texto y decide si hubo mejora.
        """
        ejercicio = (
            db.query(EjercicioPractica)
            .filter(
                EjercicioPractica.id == ejercicio_id,
                EjercicioPractica.estudiante_id == estudiante_id,
            )
            .first()
        )
        if not ejercicio:
            raise ValueError(
                "Ejercicio de práctica no encontrado para este estudiante."
            )

        texto_practica = ejercicio.texto_practica

        analisis = self.analizador.analizar_practica_ejercicio(
            texto_practica=texto_practica,
            audio_path=audio_path,
        )

        precision = analisis.get("precision_global", 0.0)
        errores = analisis.get("errores_detectados", [])

        # Regla sencilla: si precisión >= 85% o casi sin errores => mejora
        mejoro = precision >= 70.0 or not errores

        ejercicio.intentos = (ejercicio.intentos or 0) + 1
        if mejoro:
            ejercicio.completado = True

            # Marcamos fragmentos como mejorados también
            fragmentos = (
                db.query(FragmentoPractica)
                .filter(FragmentoPractica.ejercicio_id == ejercicio.id)
                .all()
            )
            for frag in fragmentos:
                frag.completado = True
                frag.mejora_lograda = True

        db.commit()
        db.refresh(ejercicio)

        if mejoro:
            mensaje_base = (
                "¡Muy bien! Has mejorado mucho en este ejercicio. "
                "Lee igual de claro la próxima vez que practiquemos."
            )
        else:
            mensaje_base = (
                "Aún hay algunos errores en esta práctica. "
                "Intentemos leer más despacio, marcando bien cada palabra y signo."
            )

        analisis["mensaje_practica"] = mensaje_base
        analisis["mejora_lograda"] = mejoro
        analisis["ejercicio_completado"] = bool(ejercicio.completado)
        analisis["ejercicio_intentos"] = int(ejercicio.intentos or 0)

        return analisis
