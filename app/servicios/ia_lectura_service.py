import re
import time
import unicodedata
from typing import Dict, List, Optional

from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from faster_whisper import WhisperModel

from app.logs.logger import logger
from app.modelos import (
    ContenidoLectura,
    EvaluacionLectura,
    AnalisisIA,
    DetalleEvaluacion,
    ErrorPronunciacion,
    Estudiante,
    IntentoLectura,
)


class ServicioAnalisisLectura:
    TOKEN_REGEX = r"[A-Za-zÁÉÍÓÚÜáéíóúüñÑ0-9]+|[¿\?¡!.,;:]"

    def __init__(self, modelo: str = "small") -> None:
        logger.info(f"Cargando modelo Faster-Whisper '{modelo}' en CPU...")
        self.model = WhisperModel(modelo, device="cpu", compute_type="int8")
        logger.info("Modelo Faster-Whisper cargado correctamente.")

    # ------------------- utilidades texto -------------------
    def _normalizar_texto(self, texto: str) -> str:
        if not texto:
            return ""
        texto = texto.replace("\n", " ").strip()
        texto = re.sub(r"\s+", " ", texto)
        texto = texto.lower()
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
        return texto

    def _tokenizar(self, texto: str) -> List[str]:
        texto_norm = self._normalizar_texto(texto)
        return re.findall(self.TOKEN_REGEX, texto_norm, flags=re.UNICODE)

    def _es_puntuacion(self, token: str) -> bool:
        return bool(re.fullmatch(r"[¿\?¡!.,;:]", token or ""))

    # ------------------- transcripción -------------------
    def _transcribir_audio(self, audio_path: str) -> Dict:
        inicio = time.time()
        logger.info(f"Transcribiendo audio con Faster-Whisper: {audio_path}")

        segments, info = self.model.transcribe(
            audio_path,
            language="es",
            beam_size=5,
            vad_filter=True,
        )

        texto = "".join(segment.text for segment in segments).strip()
        duracion = float(getattr(info, "duration", 0.0) or 0.0)
        fin = time.time()

        logger.info(
            f"Transcripción completada. Duración audio={duracion:.2f}s, "
            f"tiempo_proceso={fin - inicio:.2f}s"
        )

        return {
            "texto": texto,
            "duracion": duracion,
            "idioma": getattr(info, "language", "es"),
            "tiempo_procesamiento": fin - inicio,
        }

    # ------------------- comparación textos -------------------
    def _comparar_textos(
        self,
        texto_referencia: str,
        texto_leido: str,
        duracion_segundos: float,
    ) -> Dict:
        ref_tokens = self._tokenizar(texto_referencia)
        leido_tokens = self._tokenizar(texto_leido)

        matcher = SequenceMatcher(a=ref_tokens, b=leido_tokens)
        errores_detectados: List[Dict] = []

        total_tokens_ref = len(ref_tokens)
        tokens_correctos = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                tokens_correctos += (i2 - i1)
                continue

            for i in range(i1, i2 or i1 + 1):
                palabra_original = ref_tokens[i] if i < len(ref_tokens) else None
                idx_leido = j1 + (i - i1)
                palabra_leida = (
                    leido_tokens[idx_leido]
                    if 0 <= idx_leido < len(leido_tokens)
                    else None
                )

                if tag == "insert" and palabra_original is None and j1 < len(leido_tokens):
                    palabra_leida = leido_tokens[j1]

                if self._es_puntuacion(palabra_original or "") or self._es_puntuacion(
                    palabra_leida or ""
                ):
                    tipo_error = "puntuacion"
                elif tag == "replace":
                    tipo_error = "sustitucion"
                elif tag == "delete":
                    tipo_error = "omision"
                elif tag == "insert":
                    tipo_error = "insercion"
                else:
                    tipo_error = "otro"

                errores_detectados.append(
                    {
                        "tipo_error": tipo_error,
                        "palabra_original": palabra_original,
                        "palabra_leida": palabra_leida,
                        "posicion": i,
                        "es_puntuacion": self._es_puntuacion(palabra_original or "")
                        or self._es_puntuacion(palabra_leida or ""),
                        "severidad": 3,
                    }
                )

        # --------- precisión básica ---------
        precision_global = 0.0
        if total_tokens_ref > 0:
            precision_global = (tokens_correctos / total_tokens_ref) * 100.0

        # --------- TOLERANCIA / REDONDEO ---------
        if errores_detectados:
            solo_puntuacion = all(
                (e.get("tipo_error") == "puntuacion") for e in errores_detectados
            )
        else:
            solo_puntuacion = False

        # 1) Si la precisión es muy alta (>= 97), asumimos 100%
        if precision_global >= 95.0:
            precision_global = 100.0

        # 2) Si los únicos errores son de puntuación y la precisión es alta (>= 90),
        #    también subimos a 100%, para no castigar lecturas muy buenas
        elif solo_puntuacion and precision_global >= 93.0:
            precision_global = 100.0

        # 3) Aseguramos rango 0–100
        precision_global = max(0.0, min(precision_global, 100.0))

        # Velocidad lectora
        num_palabras_leidas = len(
            [t for t in leido_tokens if not self._es_puntuacion(t)]
        )
        palabras_por_minuto = 0.0
        if duracion_segundos > 0:
            palabras_por_minuto = num_palabras_leidas / (duracion_segundos / 60.0)

        return {
            "precision_global": precision_global,
            "palabras_por_minuto": palabras_por_minuto,
            "errores_detectados": errores_detectados,
            "tokens_referencia": ref_tokens,
            "tokens_leidos": leido_tokens,
        }

    # ------------------- feedback -------------------
    def _generar_feedback(self, analisis: Dict) -> str:
        precision = analisis.get("precision_global", 0.0)
        errores = analisis.get("errores_detectados", [])

        tiene_puntuacion = any(e.get("tipo_error") == "puntuacion" for e in errores)

        if precision >= 90:
            mensaje = "¡Excelente lectura! Casi no cometiste errores."
        elif precision >= 75:
            mensaje = "Muy bien, tu lectura es buena, pero podemos mejorar algunas palabras."
        else:
            mensaje = "Vamos a practicar las palabras y partes donde tuviste más dificultad."

        if tiene_puntuacion:
            mensaje += " También revisaremos el uso de comas, puntos y signos de pregunta."

        if not errores:
            mensaje += " No se detectaron errores importantes. ¡Sigue así!"

        return mensaje

    # ------------------- flujo principal -------------------
    def analizar_lectura(
        self,
        db: Session,
        estudiante_id: int,
        contenido_id: int,
        audio_path: str,
        evaluacion_id: Optional[int] = None,
    ) -> Dict:
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

        texto_referencia = contenido.contenido or ""

        transcripcion = self._transcribir_audio(audio_path)
        texto_leido = transcripcion["texto"]
        duracion = transcripcion["duracion"]
        tiempo_procesamiento = transcripcion["tiempo_procesamiento"]

        analisis = self._comparar_textos(
            texto_referencia=texto_referencia,
            texto_leido=texto_leido,
            duracion_segundos=duracion,
        )

        precision_global = analisis["precision_global"]
        palabras_por_minuto = analisis["palabras_por_minuto"]
        errores = analisis["errores_detectados"]
        feedback = self._generar_feedback(analisis)

        # Evaluación
        if evaluacion_id is not None:
            evaluacion = (
                db.query(EvaluacionLectura)
                .filter(
                    EvaluacionLectura.id == evaluacion_id,
                    EvaluacionLectura.estudiante_id == estudiante_id,
                    EvaluacionLectura.contenido_id == contenido_id,
                )
                .first()
            )
            if not evaluacion:
                raise ValueError("Evaluación de lectura no encontrada para actualizar.")
        else:
            evaluacion = EvaluacionLectura(
                estudiante_id=estudiante_id,
                contenido_id=contenido_id,
            )
            db.add(evaluacion)
            db.flush()

        evaluacion.puntuacion_pronunciacion = precision_global
        evaluacion.velocidad_lectura = palabras_por_minuto
        evaluacion.precision_palabras = precision_global
        evaluacion.retroalimentacion_ia = feedback
        evaluacion.audio_url = audio_path
        evaluacion.duracion_audio = int(duracion) if duracion else None
        evaluacion.estado = "completado"

        # Intento
        ultimo_intento = (
            db.query(IntentoLectura)
            .filter(IntentoLectura.evaluacion_id == evaluacion.id)
            .order_by(IntentoLectura.numero_intento.desc())
            .first()
        )
        numero_intento = 1 if not ultimo_intento else ultimo_intento.numero_intento + 1

        intento = IntentoLectura(
            evaluacion_id=evaluacion.id,
            numero_intento=numero_intento,
            puntuacion_pronunciacion=precision_global,
            velocidad_lectura=palabras_por_minuto,
            fluidez=None,
            audio_url=audio_path,
        )
        db.add(intento)
        db.flush()

        # AnalisisIA
        analisis_ia = AnalisisIA(
            evaluacion_id=evaluacion.id,
            modelo_usado="faster-whisper",
            precision_global=precision_global,
            palabras_detectadas=analisis["tokens_leidos"],
            errores_detectados=errores,
            tiempo_procesamiento=tiempo_procesamiento,
            palabras_por_minuto=palabras_por_minuto,
        )
        db.add(analisis_ia)
        db.flush()

        # Detalle + errores
        for e in errores:
            palabra = e.get("palabra_original") or e.get("palabra_leida") or ""
            posicion = e.get("posicion", 0)

            detalle = DetalleEvaluacion(
                evaluacion_id=evaluacion.id,
                palabra=palabra,
                posicion_en_texto=posicion,
                precision_pronunciacion=max(0.0, precision_global - 20.0),
                retroalimentacion_palabra="Necesitamos practicar esta parte.",
                timestamp_inicio=None,
                timestamp_fin=None,
                tipo_tokenizacion="palabra_puntuacion",
            )
            db.add(detalle)
            db.flush()

            error_db = ErrorPronunciacion(
                detalle_evaluacion_id=detalle.id,
                tipo_error=e.get("tipo_error", "otro"),
                palabra_original=e.get("palabra_original"),
                palabra_detectada=e.get("palabra_leida"),
                timestamp_inicio=None,
                timestamp_fin=None,
                severidad=e.get("severidad", 3),
                sugerencia_correccion="Repite esta palabra o signo de puntuación varias veces.",
            )
            db.add(error_db)

        db.commit()
        db.refresh(evaluacion)
        db.refresh(intento)

        return {
            "success": True,
            "evaluacion_id": evaluacion.id,
            "intento_id": intento.id,
            "numero_intento": intento.numero_intento,
            "precision_global": precision_global,
            "palabras_por_minuto": palabras_por_minuto,
            "errores": errores,
            "texto_transcrito": texto_leido,
            "retroalimentacion": feedback,
        }

    def analizar_practica_ejercicio(
        self,
        texto_practica: str,
        audio_path: str,
    ) -> Dict:
        """
        Analiza un audio corto de práctica para un ejercicio específico.
        """
        transcripcion = self._transcribir_audio(audio_path)
        texto_leido = transcripcion["texto"]
        duracion = transcripcion["duracion"]

        analisis = self._comparar_textos(
            texto_referencia=texto_practica,
            texto_leido=texto_leido,
            duracion_segundos=duracion or 0.0,
        )

        feedback = self._generar_feedback(analisis)

        analisis["texto_transcrito"] = texto_leido
        analisis["retroalimentacion"] = feedback
        analisis["duracion"] = duracion
        return analisis
