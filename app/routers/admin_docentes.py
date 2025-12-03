from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config import get_db
from app.servicios.seguridad import requiere_admin
from app.modelos import Usuario, UsuarioRol, Docente
from app.servicios.seguridad import get_password_hash

router = APIRouter(prefix="/admin/docentes", tags=["admin-docentes"])


# ===============================
# 1. LISTAR DOCENTES
# ===============================
@router.get("/")
def listar_docentes(db: Session = Depends(get_db), admin=Depends(requiere_admin)):

    docentes = (
        db.query(Docente)
        .join(Usuario, Usuario.id == Docente.usuario_id)
        .all()
    )

    return [
        {
            "id": d.id,
            "usuario_id": d.usuario_id,
            "nombre": d.usuario.nombre,
            "apellido": d.usuario.apellido,
            "email": d.usuario.email,
            "especialidad": d.especialidad,
            "institucion": d.institucion,
            "activo": d.activo,
        }
        for d in docentes
    ]


# ===============================
# 2. CREAR DOCENTE
# ===============================
@router.post("/")
def crear_docente_admin(
    data: dict,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin),
):

    # 1. Crear usuario
    usuario = Usuario(
        nombre=data["nombre"],
        apellido=data["apellido"],
        email=data["email"],
        password_hash=get_password_hash(data["password"]),
        activo=True
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    # 2. Asignar rol
    rol = UsuarioRol(
        usuario_id=usuario.id,
        rol="docente",
        activo=True
    )
    db.add(rol)
    db.commit()

    # 3. Crear registro docente
    docente = Docente(
        usuario_id=usuario.id,
        especialidad=data.get("especialidad"),
        institucion=data.get("institucion"),
        activo=True
    )
    db.add(docente)
    db.commit()
    db.refresh(docente)

    return {"msg": "Docente creado con éxito", "docente_id": docente.id}


# ===============================
# 3. ELIMINAR DOCENTE
# ===============================
@router.delete("/{docente_id}")
def eliminar_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin),
):
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(404, "Docente no encontrado")

    db.delete(docente)
    db.commit()

    return {"msg": "Docente eliminado"}
