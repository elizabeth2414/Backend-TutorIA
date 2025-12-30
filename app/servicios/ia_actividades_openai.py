# app/servicios/ia_actividades_openai.py
"""
ALTERNATIVA: Generación de actividades usando OpenAI API

Este archivo proporciona una alternativa más confiable al uso de FLAN-T5-Small.
OpenAI genera JSON estructurado de manera mucho más consistente.

Para usar esta alternativa:
1. Instala: pip install openai
2. Configura OPENAI_API_KEY en tu archivo .env
3. Importa generar_actividad_ia_para_contenido_openai en lugar de la versión FLAN-T5
"""

import json
from sqlalchemy.orm import Session
from openai import OpenAI

from app.modelos import ContenidoLectura, Actividad, Pregunta
from app.esquemas.actividad_ia import GenerarActividadesIARequest
from app.logs.logger import logger
from app import settings


# Inicializar cliente de OpenAI (requiere OPENAI_API_KEY en .env)
try:
    client = OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', None))
    OPENAI_DISPONIBLE = True
except Exception as e:
    logger.warning(f"⚠️ OpenAI no está configurado: {e}")
    OPENAI_DISPONIBLE = False


def generar_json_actividad_ia_openai(texto: str, opciones: GenerarActividadesIARequest) -> dict:
    """
    Genera una actividad en formato JSON usando OpenAI API.
    Más confiable que FLAN-T5-Small para generación estructurada.
    """

    if not OPENAI_DISPONIBLE:
        raise ValueError("OpenAI no está configurado. Verifica tu OPENAI_API_KEY en el archivo .env")

    # Truncar el texto si es muy largo
    texto_truncado = texto[:2000] if len(texto) > 2000 else texto

    prompt = f"""
Eres un asistente educativo especializado en crear actividades para niños de 7 a 10 años.

Basándote en el siguiente texto, genera {opciones.num_preguntas} preguntas educativas:

TEXTO:
\"\"\"{texto_truncado}\"\"\"

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:

{{
  "titulo": "Título descriptivo de la actividad",
  "descripcion": "Breve descripción de la actividad",
  "preguntas": [
    {{
      "tipo": "multiple_choice",
      "pregunta": "¿Pregunta de opción múltiple?",
      "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
      "respuesta_correcta": "Opción A",
      "explicacion": "Explicación de por qué es correcta"
    }},
    {{
      "tipo": "verdadero_falso",
      "pregunta": "¿Afirmación verdadera o falsa?",
      "opciones": ["verdadero", "falso"],
      "respuesta_correcta": "verdadero",
      "explicacion": "Explicación de la respuesta"
    }},
    {{
      "tipo": "texto_libre",
      "pregunta": "Pregunta abierta para reflexión",
      "explicacion": "Guía sobre qué se espera en la respuesta"
    }}
  ]
}}

IMPORTANTE:
- Genera exactamente {opciones.num_preguntas} preguntas
- Incluye preguntas de opción múltiple: {"Sí" if opciones.incluir_multiple_choice else "No"}
- Incluye preguntas verdadero/falso: {"Sí" if opciones.incluir_verdadero_falso else "No"}
- Nivel de dificultad: {opciones.dificultad}/5
- Las preguntas deben estar en español
- Asegúrate de que el JSON sea válido
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo económico pero efectivo
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en crear actividades educativas. Siempre respondes con JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}  # Fuerza respuesta en JSON
        )

        result = response.choices[0].message.content
        final_json = json.loads(result)

        # Validar estructura
        if "titulo" not in final_json or "preguntas" not in final_json:
            logger.error(f"❌ JSON generado no tiene la estructura esperada")
            raise ValueError("El modelo de IA generó un JSON con estructura incorrecta.")

        if not isinstance(final_json["preguntas"], list) or len(final_json["preguntas"]) == 0:
            logger.error(f"❌ El JSON no contiene preguntas válidas")
            raise ValueError("El modelo de IA no generó preguntas válidas.")

        logger.info(f"✅ JSON generado exitosamente con {len(final_json['preguntas'])} preguntas (OpenAI)")
        return final_json

    except json.JSONDecodeError as e:
        logger.error(f"❌ Error al decodificar JSON de OpenAI: {e}")
        raise ValueError("El modelo de IA generó un formato inválido.")

    except Exception as e:
        logger.error(f"❌ Error generando actividad con OpenAI: {e}")
        raise ValueError(f"Error generando actividad con IA: {str(e)}")


def generar_actividad_ia_para_contenido_openai(
    db: Session,
    contenido: ContenidoLectura,
    opciones: GenerarActividadesIARequest
):
    """
    Crea una actividad y sus preguntas usando OpenAI API.
    """
    logger.info(f"Generando actividades IA (OpenAI) para contenido_id={contenido.id}")

    texto = contenido.contenido
    json_data = generar_json_actividad_ia_openai(texto, opciones)

    # Crear la actividad
    actividad = Actividad(
        contenido_id=contenido.id,
        tipo="preguntas",
        titulo=json_data["titulo"],
        descripcion=json_data.get("descripcion", "Actividad de comprensión lectora"),
        configuracion={"generado_por_ia": True, "modelo": "openai-gpt-4o-mini"},
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

    logger.info(f"Actividad IA (OpenAI) creada con {len(actividad.preguntas)} preguntas.")

    return actividad
