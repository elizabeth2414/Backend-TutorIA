import logging
import re
from typing import Dict, List

from difflib import SequenceMatcher
from sqlalchemy.orm import Session
import whisper

from app.modelos import (
    ContenidoLectura,
    EvaluacionLectura,
    AnalisisIA,
    DetalleEvaluacion,
    ErrorPronunciacion,
    Estudiante,
)

logger = logging.getLogger(__name__)


class ServicioAnalisisLectura:
    """
    Servicio principal para:
    - transcribir audio con Whisper local
    - comparar con el texto de referencia
    - calcular métricas
    - guardar resultados en la BD
    """

    def __init__(self, modelo: str = "small") -> None:
        # Carga del modelo Whisper solo una vez
        logger.info(f"Cargando modelo Whisper '{modelo}'...")
        self.model = whisper.load_model(modelo)
        logger.info("Modelo Whisper cargado correctamente.")

    # ---------- UTILIDADES ----------

    def _normalizar_texto(self, texto: str) -> List[str]:
        """
        Convierte el texto a minúsculas, limpia símbolos y devuelve lista de tokens.
        """
        texto = texto.lower()
        texto = re.sub(r"[^\wáéíóúüñ]+", " ", texto, flags=re.UNICODE)
        tokens = [t for t in texto.split() if t]
        return tokens

    def _transcribir_audio(self, audio_path: str) -> Dict:
        """
        Transcribe el audio usando Whisper local.
        Retorna diccionario con:
        - text (str)
        - duration (float)
        - language (str)
        - segments (si lo necesitas más adelante)
        """
        try:
            # Whisper ya maneja el resample a 16k internamente
            logger.info(f"Transcribiendo audio: {audio_path}")
            result = self.model.transcribe(
                audio_path,
                language="es",     # forzar español
                fp16=False,        # en CPU debe ser False
            )
            texto = (result.get("text") or "").strip()
            # duración aproximada (Whisper da tiempos por segmentos)
            duration = 0.0
            segments = result.get("segments") or []
            if segments:
                duration = float(segments[-1]["end"] - segments[0].get("start", 0.0))
            language = result.get("language", "es")

            return {
                "texto": texto,
                "duracion": duration,
                "idioma": language,
                "segments": segments,
            }
        except Exception as e:
            logger.error(f"Error al transcribir audio con Whisper: {e}")
            return {
                "texto": "",
                "duracion": 0.0,
                "idioma": "es",
                "segments": [],
            }

    def _comparar_textos(
        self,
        texto_referencia: str,
        texto_leido: str,
        duracion_segundos: float,
    ) -> Dict:
        """
        Compara el texto de referencia con el texto leído y genera:
        - precisión global (por palabra)
        - lista de errores detectados
        - palabras por minuto
        """
        ref_tokens = self._normalizar_texto(texto_referencia)
        leido_tokens = self._normalizar_texto(texto_leido)

        matcher = SequenceMatcher(a=ref_tokens, b=leido_tokens)
        errores: List[Dict] = []
        palabras_correctas = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                palabras_correctas += (i2 - i1)
            elif tag in ("replace", "delete", "insert"):
                # reemplazos / omisiones
                if tag in ("replace", "delete"):
                    for i in range(i1, i2):
                        palabra_original = ref_tokens[i] if i < len(ref_tokens) else None
                        palabra_detectada = None
                        if tag == "replace":
                            idx = j1 + (i - i1)
                            if j1 <= idx < j2 and idx < len(leido_tokens):
                                palabra_detectada = leido_tokens[idx]
                        tipo_error = "sustitucion" if palabra_detectada else "omision"

                        errores.append(
                            {
                                "tipo_error": tipo_error,
                                "palabra_original": palabra_original,
                                "palabra_detectada": palabra_detectada,
                                "severidad": 3,
                            }
                        )

                # inserciones (palabras extra)
                if tag == "insert":
                    for j in range(j1, j2):
                        if j < len(leido_tokens):
                            errores.append(
                                {
                                    "tipo_error": "insercion",
                                    "palabra_original": None,
                                    "palabra_detectada": leido_tokens[j],
                                    "severidad": 2,
                                }
                            )

        total_palabras_ref = len(ref_tokens)
        if total_palabras_ref > 0:
            precision_global = (palabras_correctas / total_palabras_ref) * 100.0
        else:
            precision_global = 0.0

        if duracion_segundos > 0:
            palabras_por_minuto = len(leido_tokens) / (duracion_segundos / 60.0)
        else:
            palabras_por_minuto = 0.0

        resultado = {
            "precision_global": precision_global,
            "palabras_detectadas": leido_tokens,
            "errores_detectados": errores,
            "palabras_por_minuto": palabras_por_minuto,
            "pausas_detectadas": [],        # se puede mejorar luego
            "entonacion_score": None,       # se puede añadir en el futuro
            "ritmo_score": None,
        }
        return resultado

    def _generar_retroalimentacion(self, analisis: Dict) -> str:
        """
        Crea un mensaje de feedback general para el estudiante.
        """
        precision = analisis.get("precision_global", 0.0)
        wpm = analisis.get("palabras_por_minuto", 0.0)

        if precision >= 90:
            msg_precision = "Excelente pronunciación 😄"
        elif precision >= 75:
            msg_precision = "Muy buena pronunciación, sigue practicando 💪"
        elif precision >= 50:
            msg_precision = "Vas bien, pero aún puedes mejorar en varias palabras 🙂"
        else:
            msg_precision = "Necesitas practicar más la pronunciación. ¡No te desanimes! 🌟"

        if wpm < 60:
            msg_velocidad = "La lectura es un poco lenta, intenta leer un poco más fluido."
        elif wpm > 130:
            msg_velocidad = "La lectura es muy rápida, trata de pausar en comas y puntos."
        else:
            msg_velocidad = "La velocidad de lectura es adecuada. ¡Buen ritmo!"

        return f"{msg_precision} {msg_velocidad}"

    # ---------- MÉTODO PRINCIPAL ----------

    def analizar_lectura(
        self,
        db: Session,
        estudiante_id: int,
        contenido_id: int,
        audio_path: str,
    ) -> Dict:
        """
        Flujo principal:
        - valida estudiante y contenido
        - transcribe audio
        - compara con el texto base
        - guarda evaluación + análisis IA + errores
        - retorna resultado para el frontend
        """

        # 1) Validar estudiante y contenido
        estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
        if not estudiante:
            raise ValueError("Estudiante no encontrado")

        contenido = (
            db.query(ContenidoLectura)
            .filter(ContenidoLectura.id == contenido_id)
            .first()
        )
        if not contenido:
            raise ValueError("Contenido de lectura no encontrado")

        texto_referencia = contenido.contenido  # ajusta al nombre real de tu campo

        # 2) Transcribir audio
        transcripcion = self._transcribir_audio(audio_path)
        texto_leido = transcripcion["texto"]
        duracion = transcripcion["duracion"]

        # 3) Analizar comparación
        analisis = self._comparar_textos(
            texto_referencia=texto_referencia,
            texto_leido=texto_leido,
            duracion_segundos=duracion,
        )

        # 4) Crear EvaluacionLectura
        evaluacion = EvaluacionLectura(
            estudiante_id=estudiante_id,
            contenido_id=contenido_id,
            puntuacion_pronunciacion=analisis["precision_global"],
            precision_palabras=analisis["precision_global"],
            velocidad_lectura=analisis["palabras_por_minuto"],
            fluidez=None,
            retroalimentacion_ia=self._generar_retroalimentacion(analisis),
            audio_url=audio_path,  # o ruta relativa si prefieres
            duracion_audio=int(duracion) if duracion else None,
            estado="completado",
        )
        db.add(evaluacion)
        db.flush()  # para tener evaluacion.id

        # 5) Guardar AnalisisIA
        analisis_ia = AnalisisIA(
            evaluacion_id=evaluacion.id,
            modelo_usado="whisper-small-local",
            precision_global=analisis["precision_global"],
            palabras_detectadas=analisis["palabras_detectadas"],
            errores_detectados=analisis["errores_detectados"],
            tiempo_procesamiento=duracion,
            palabras_por_minuto=analisis["palabras_por_minuto"],
            pausas_detectadas=analisis["pausas_detectadas"],
            entonacion_score=analisis["entonacion_score"],
            ritmo_score=analisis["ritmo_score"],
        )
        db.add(analisis_ia)

        # 6) Guardar detalles y errores por palabra (simplificado)
        ref_tokens = self._normalizar_texto(texto_referencia)
        for idx, palabra in enumerate(ref_tokens):
            detalle = DetalleEvaluacion(
                evaluacion_id=evaluacion.id,
                palabra=palabra,
                posicion_en_texto=idx,
                precision_pronunciacion=100.0,  # simple; se puede refinar
                retroalimentacion_palabra=None,
                timestamp_inicio=None,
                timestamp_fin=None,
                tipo_tokenizacion="palabra",
            )
            db.add(detalle)

        # errores concretos
        for error in analisis["errores_detectados"]:
            palabra = error.get("palabra_original") or (error.get("palabra_detectada") or "")
            detalle = DetalleEvaluacion(
                evaluacion_id=evaluacion.id,
                palabra=palabra,
                posicion_en_texto=0,
                precision_pronunciacion=0.0,
                retroalimentacion_palabra="Palabra con error de pronunciación",
                timestamp_inicio=None,
                timestamp_fin=None,
                tipo_tokenizacion="palabra",
            )
            db.add(detalle)
            db.flush()
            db.add(
                ErrorPronunciacion(
                    detalle_evaluacion_id=detalle.id,
                    tipo_error=error.get("tipo_error", "desconocido"),
                    palabra_original=error.get("palabra_original"),
                    palabra_detectada=error.get("palabra_detectada"),
                    timestamp_inicio=None,
                    timestamp_fin=None,
                    severidad=error.get("severidad", 3),
                    sugerencia_correccion="Vuelve a practicar esta palabra en voz alta.",
                )
            )

        db.commit()
        db.refresh(evaluacion)

        return {
            "success": True,
            "evaluacion_id": evaluacion.id,
            "precision_global": analisis["precision_global"],
            "palabras_por_minuto": analisis["palabras_por_minuto"],
            "errores": analisis["errores_detectados"],
            "texto_transcrito": texto_leido,
            "retroalimentacion": evaluacion.retroalimentacion_ia,
        }
