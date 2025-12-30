import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from sqlalchemy.orm import Session

from app.modelos import ContenidoLectura, Actividad, Pregunta
from app.esquemas.actividad_ia import GenerarActividadesIARequest
from app.logs.logger import logger


# ================================
# 📌 Cargar modelo IA liviano (FLAN-T5-SMALL)
# ================================
logger.info("Cargando modelo FLAN-T5-Small...")

tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
model = AutoModelForSeq2SeqLM.from_pretrained(
    "google/flan-t5-small",
    torch_dtype=torch.float32
)

logger.info("Modelo cargado correctamente en CPU.")


# ================================
# 🚀 IA — Generación del JSON estructurado
# ================================
def generar_json_actividad_ia(texto: str, opciones: GenerarActividadesIARequest) -> dict:
    """
    Genera una actividad en formato JSON usando FLAN-T5.
    """

    # Truncar el texto si es muy largo para evitar problemas con el modelo
    texto_truncado = texto[:500] if len(texto) > 500 else texto

    prompt = f"""
Genera una actividad educativa para niños de 7 a 10 años basada en el siguiente texto:

TEXTO:
\"""{texto_truncado}\"""

Devuelve ÚNICAMENTE un JSON válido con esta estructura:

{{
  "titulo": "Actividad generada por IA",
  "descripcion": "Actividad de comprensión lectora",
  "preguntas": [
    {{
      "tipo": "multiple_choice",
      "pregunta": "Pregunta...",
      "opciones": ["A", "B", "C"],
      "respuesta_correcta": "A",
      "explicacion": "Explicación corta"
    }},
    {{
      "tipo": "verdadero_falso",
      "pregunta": "Pregunta...",
      "opciones": ["verdadero", "falso"],
      "respuesta_correcta": "verdadero",
      "explicacion": "Explicación corta"
    }},
    {{
      "tipo": "texto_libre",
      "pregunta": "Pregunta abierta...",
      "explicacion": "Explicación corta"
    }}
  ]
}}

NO agregues texto adicional.
"""

    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)

    try:
        output = model.generate(
            **inputs,
            max_new_tokens=600,
            temperature=0.4,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=2.0,  # Penaliza repeticiones
            no_repeat_ngram_size=3   # Evita repetir n-gramas de 3 palabras
        )

        result = tokenizer.decode(output[0], skip_special_tokens=True)

        # Verificar si hay repeticiones excesivas (señal de que el modelo falló)
        palabras = result.lower().split()
        if len(palabras) > 10:
            palabra_mas_comun = max(set(palabras), key=palabras.count)
            repeticiones = palabras.count(palabra_mas_comun)
            if repeticiones > len(palabras) * 0.3:  # Más del 30% son la misma palabra
                logger.error(f"❌ El modelo generó texto con repeticiones excesivas")
                logger.error(f"Palabra repetida: '{palabra_mas_comun}' ({repeticiones} veces)")
                raise ValueError("El modelo de IA no pudo generar una respuesta válida. Por favor, intenta con un texto más corto o diferente.")

        # Extraer JSON
        if "{" not in result or "}" not in result:
            logger.error(f"❌ No se encontró JSON en la respuesta del modelo")
            logger.error(f"Texto recibido: {result[:200]}...")
            raise ValueError("El modelo de IA no generó un JSON válido. Por favor, intenta nuevamente.")

        json_start = result.index("{")
        json_end = result.rindex("}") + 1
        json_str = result[json_start:json_end]
        final_json = json.loads(json_str)

        # Validar estructura del JSON
        if "titulo" not in final_json or "preguntas" not in final_json:
            logger.error(f"❌ JSON generado no tiene la estructura esperada")
            logger.error(f"JSON recibido: {final_json}")
            raise ValueError("El modelo de IA generó un JSON con estructura incorrecta.")

        if not isinstance(final_json["preguntas"], list) or len(final_json["preguntas"]) == 0:
            logger.error(f"❌ El JSON no contiene preguntas válidas")
            raise ValueError("El modelo de IA no generó preguntas válidas.")

    except json.JSONDecodeError as e:
        logger.error(f"❌ Error al decodificar JSON: {e}")
        logger.error(f"Texto recibido: {result[:200]}...")
        raise ValueError("El modelo de IA generó un formato inválido. Por favor, intenta nuevamente.")

    except Exception as e:
        logger.error(f"❌ Error procesando respuesta del modelo: {e}")
        logger.error(f"Tipo de error: {type(e).__name__}")
        raise ValueError(f"Error generando actividad con IA: {str(e)}")

    logger.info(f"✅ JSON generado exitosamente con {len(final_json['preguntas'])} preguntas")
    return final_json


# ================================
# 🧩 Crear Actividad y Preguntas en BD
# ================================
def generar_actividad_ia_para_contenido(
    db: Session,
    contenido: ContenidoLectura,
    opciones: GenerarActividadesIARequest
):
    logger.info(f"Generando actividades IA para contenido_id={contenido.id}")

    texto = contenido.contenido
    json_data = generar_json_actividad_ia(texto, opciones)

    # Crear la actividad
    actividad = Actividad(
        contenido_id=contenido.id,
        tipo="preguntas",
        titulo=json_data["titulo"],
        descripcion=json_data["descripcion"],
        configuracion={"generado_por_ia": True},
        puntos_maximos=len(json_data["preguntas"]) * 10,
        tiempo_estimado=len(json_data["preguntas"]) * 2,
        dificultad=opciones.dificultad,
        activo=True
    )

    db.add(actividad)
    db.flush()

    # Crear preguntas
    orden = 1
    for p in json_data["preguntas"]:
        pregunta = Pregunta(
            actividad_id=actividad.id,
            texto_pregunta=p["pregunta"],
            tipo_respuesta=p["tipo"],
            opciones=p.get("opciones"),
            respuesta_correcta=p.get("respuesta_correcta"),
            puntuacion=10,
            explicacion=p.get("explicacion", ""),
            orden=orden
        )
        db.add(pregunta)
        orden += 1

    db.commit()
    db.refresh(actividad)

    logger.info(f"Actividad IA creada con {len(actividad.preguntas)} preguntas.")

    # 🔥🔥🔥 IMPORTANTE: devolver SOLO actividad (NO tupla)
    return actividad
