# app/routers/ia_actividades.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_db
from app.modelos import ContenidoLectura, Actividad, Usuario
from app.servicios.seguridad import obtener_usuario_actual
from app.servicios.ia_actividades import generar_actividad_ia_para_contenido
from app.esquemas.actividad_ia import (
    GenerarActividadesIARequest,
    GenerarActividadesIAResponse,
    ActividadResponse
)
from app.logs.logger import logger

router = APIRouter(prefix="/ia", tags=["ia-actividades"])


# =====================================================
# 1️⃣ GENERAR ACTIVIDAD IA PARA UNA LECTURA
# =====================================================
@router.post(
    "/lecturas/{contenido_id}/generar-actividades",
    response_model=GenerarActividadesIAResponse
)
def generar_actividades_ia(
    contenido_id: int,
    opciones: GenerarActividadesIARequest,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):

    contenido = (
        db.query(ContenidoLectura)
        .filter(
            ContenidoLectura.id == contenido_id,
            ContenidoLectura.activo == True
        )
        .first()
    )

    if not contenido:
        raise HTTPException(status_code=404, detail="Contenido de lectura no encontrado")

    # (Opcional) Validar que sea del docente dueño
    # if contenido.docente_id != usuario_actual.docente.id:
    #     raise HTTPException(status_code=403, detail="No autorizado")

    try:
        actividad = generar_actividad_ia_para_contenido(db, contenido, opciones)

        return GenerarActividadesIAResponse(
            contenido_id=contenido.id,
            actividad_id=actividad.id,
            total_preguntas=len(actividad.preguntas),
            mensaje="Actividad generada correctamente por IA.",
            actividad=ActividadResponse.from_attributes(actividad)
        )
    except ValueError as e:
        # Error específico del modelo de IA (JSON inválido, repeticiones, etc.)
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Error generando actividad con IA",
                "mensaje": str(e),
                "sugerencia": "Intenta con un texto diferente o más corto. Si el problema persiste, el modelo de IA local podría no ser suficiente."
            }
        )
    except Exception as e:
        # Cualquier otro error inesperado
        logger.error(f"❌ Error inesperado generando actividad IA: {e}")
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error interno del servidor",
                "mensaje": "Ocurrió un error inesperado al generar la actividad con IA.",
                "sugerencia": "Por favor, contacta al administrador del sistema."
            }
        )


# =====================================================
# 2️⃣ LISTAR ACTIVIDADES GENERADAS PARA UNA LECTURA
# =====================================================
@router.get(
    "/lecturas/{contenido_id}/actividades",
    response_model=list[ActividadResponse]
)
def listar_actividades_lectura(
    contenido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):

    actividades = (
        db.query(Actividad)
        .filter(
            Actividad.contenido_id == contenido_id,
            Actividad.activo == True
        )
        .all()
    )

    return actividades


# =====================================================
# 3️⃣ OBTENER ACTIVIDAD ESPECÍFICA CON SUS PREGUNTAS
# =====================================================
@router.get(
    "/actividades/{actividad_id}",
    response_model=ActividadResponse
)
def obtener_actividad_ia(
    actividad_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):

    actividad = (
        db.query(Actividad)
        .filter(Actividad.id == actividad_id)
        .first()
    )

    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    return actividad
