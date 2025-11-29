from fastapi import APIRouter

from app.routers import auth, usuarios, docentes, estudiantes, cursos, contenido
from app.routers import evaluaciones, ejercicios, actividades, gamificacion, estadisticas,ia_routes

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
