# app/routers/__init__.py
from fastapi import APIRouter

from app.routers import (
    auth,
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
    admin_docentes,
    categorias,
    lecturas,
    ia_actividades,
    usuarios, 
    padres,# 👈 ESTE VA AL FINAL
)

api_router = APIRouter()


api_router.include_router(auth.router)
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
api_router.include_router(admin_docentes.router)
api_router.include_router(categorias.router)
api_router.include_router(lecturas.router)
api_router.include_router(ia_actividades.router)
api_router.include_router(padres.router)

# 👇 USERS SIEMPRE AL FINAL
api_router.include_router(usuarios.router)
