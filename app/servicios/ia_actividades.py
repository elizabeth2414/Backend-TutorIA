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

    prompt = f"""
Genera una actividad educativa para niños de 7 a 10 años basada en el siguiente texto:

TEXTO:
\"""{texto}\"""

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

    inputs = tokenizer(prompt, return_tensors="pt")

    output = model.generate(
        **inputs,
        max_new_tokens=600,
        temperature=0.4
    )

    result = tokenizer.decode(output[0], skip_special_tokens=True)

    # Extraer JSON
    try:
        json_start = result.index("{")
        json_end = result.rindex("}") + 1
        json_str = result[json_start:json_end]
        final_json = json.loads(json_str)

    except Exception as e:
        logger.error(f"❌ Error procesando JSON generado: {e}")
        logger.error(f"Texto recibido: {result}")
        raise ValueError("La IA devolvió un JSON inválido.")

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
