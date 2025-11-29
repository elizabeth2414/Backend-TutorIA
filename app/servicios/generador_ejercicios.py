from typing import List, Dict
from sqlalchemy.orm import Session

from app.modelos import EjercicioPractica, FragmentoPractica


class GeneradorEjercicios:
    """
    Genera ejercicios de práctica a partir de los errores detectados.
    """

    def __init__(self) -> None:
        self.tipos_ejercicios = {
            "sustitucion": "palabras_aisladas",
            "omision": "oraciones",
            "puntuacion": "puntuacion",
            "fluidez": "ritmo",
            "entonacion": "entonacion",
            "omision_parcial": "palabras_aisladas",
            "insercion": "oraciones",
        }

    def crear_ejercicios_desde_errores(
        self,
        db: Session,
        estudiante_id: int,
        evaluacion_id: int,
        errores: List[Dict],
    ) -> List[int]:
        """
        Crea ejercicios de práctica agrupando errores por tipo.
        Devuelve la lista de IDs de EjercicioPractica creados.
        """
        if not errores:
            return []

        ejercicios_ids: List[int] = []
        errores_por_tipo: Dict[str, List[Dict]] = {}

        for e in errores:
            tipo = e.get("tipo_error", "otros")
            errores_por_tipo.setdefault(tipo, []).append(e)

        for tipo_error, errores_grupo in errores_por_tipo.items():
            tipo_ejercicio = self.tipos_ejercicios.get(tipo_error, "palabras_aisladas")

            palabras_objetivo = list(
                {
                    (e.get("palabra_original") or e.get("palabra_detectada") or "").lower()
                    for e in errores_grupo
                    if (e.get("palabra_original") or e.get("palabra_detectada"))
                }
            )
            palabras_objetivo = [p for p in palabras_objetivo if p]

            if not palabras_objetivo:
                continue

            texto_practica = "Practica estas palabras: " + ", ".join(palabras_objetivo)

            ejercicio = EjercicioPractica(
                estudiante_id=estudiante_id,
                evaluacion_id=evaluacion_id,
                tipo_ejercicio=tipo_ejercicio,
                palabras_objetivo=palabras_objetivo,
                texto_practica=texto_practica,
                dificultad=1,
                completado=False,
            )
            db.add(ejercicio)
            db.flush()
            ejercicios_ids.append(ejercicio.id)

            for palabra in palabras_objetivo:
                frag_text = f"Lee en voz alta la palabra: {palabra}"
                fragmento = FragmentoPractica(
                    ejercicio_id=ejercicio.id,
                    texto_fragmento=frag_text,
                    posicion_inicio=0,
                    posicion_fin=len(frag_text),
                    tipo_error_asociado=tipo_error,
                    completado=False,
                    mejora_lograda=False,
                )
                db.add(fragmento)

        db.commit()
        return ejercicios_ids
