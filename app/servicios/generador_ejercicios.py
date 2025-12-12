from typing import List, Dict, Set
from collections import defaultdict

from sqlalchemy.orm import Session

from app.modelos import EjercicioPractica, FragmentoPractica, Estudiante


class GeneradorEjercicios:
    def __init__(self) -> None:
        self.mapa_tipo_a_ejercicio = {
            "sustitucion": "palabras_aisladas",
            "omision": "oraciones",
            "insercion": "palabras_aisladas",
            "puntuacion": "puntuacion",
        }

    def _extraer_palabras_por_tipo(
        self, errores: List[Dict]
    ) -> Dict[str, Set[str]]:
        resultado: Dict[str, Set[str]] = defaultdict(set)
        for e in errores:
            tipo = e.get("tipo_error", "otro")
            if tipo not in self.mapa_tipo_a_ejercicio:
                continue
            palabra = e.get("palabra_original") or e.get("palabra_leida")
            if not palabra:
                continue
            resultado[tipo].add(palabra)
        return resultado

    def crear_ejercicios_desde_errores(
        self,
        db: Session,
        estudiante_id: int,
        evaluacion_id: int,
        errores: List[Dict],
    ) -> List[int]:
        estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
        if not estudiante:
            return []

        palabras_por_tipo = self._extraer_palabras_por_tipo(errores)
        ejercicios_ids: List[int] = []

        for tipo_error, palabras_set in palabras_por_tipo.items():
            if not palabras_set:
                continue

            tipo_ejercicio = self.mapa_tipo_a_ejercicio.get(
                tipo_error, "palabras_aisladas"
            )
            palabras_objetivo = list(palabras_set)

            if tipo_error == "puntuacion":
                texto_practica = (
                    "Lee en voz alta las oraciones poniendo especial atención a los puntos y comas."
                )
                dificultad = 2
            elif tipo_error in ("sustitucion", "insercion"):
                texto_practica = (
                    "Repite las palabras indicadas hasta que suenen claras y correctas."
                )
                dificultad = 1
            elif tipo_error == "omision":
                texto_practica = (
                    "Lee nuevamente las oraciones completas, sin saltarte palabras."
                )
                dificultad = 2
            else:
                texto_practica = "Practica las partes indicadas de la lectura."
                dificultad = 1

            ejercicio = EjercicioPractica(
                estudiante_id=estudiante_id,
                evaluacion_id=evaluacion_id,
                tipo_ejercicio=tipo_ejercicio,
                palabras_objetivo=palabras_objetivo,
                texto_practica=texto_practica,
                dificultad=dificultad,
                completado=False,
                intentos=0,
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
