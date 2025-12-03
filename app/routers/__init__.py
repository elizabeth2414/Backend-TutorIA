from fastapi import APIRouter

from app.routers import (
    auth,
    usuarios,
    docentes,
    estudiantes,
    cursos,
    contenido,
    evaluaciones,
    ejercicios,
    actividades,
    gamificacion,
    estadisticas,
    ia_routes,
    admin,
    admin_docentes,
)

api_router = APIRouter()

# Incluir todos los routers
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(docentes.router)
api_router.include_router(estudiantes.router)
api_router.include_router(cursos.router)
api_router.include_router(contenido.router)
api_router.include_router(evaluaciones.router)
api_router.include_router(ejercicios.router)
api_router.include_router(actividades.router)
api_router.include_router(gamificacion.router)
api_router.include_router(estadisticas.router)
api_router.include_router(ia_routes.router)

# 👇 AÑADIR ESTE
api_router.include_router(admin.router)
api_router.include_router(admin_docentes.router)
