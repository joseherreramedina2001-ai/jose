"""
Cubre la sección 25 del prompt: usuario no autorizado, archivo no permitido,
endpoint protegido.
"""
import io

from tests.conftest import token_for


def test_endpoint_protegido_sin_token_rechaza_acceso(client):
    r = client.get("/api/documents")
    assert r.status_code == 401


def test_endpoint_protegido_con_token_invalido_rechaza_acceso(client):
    r = client.get("/api/documents", headers={"Authorization": "Bearer token-falso"})
    assert r.status_code == 401


def test_usuario_consulta_no_puede_subir_documentos(client, consulta_user):
    token = token_for(consulta_user)
    files = {"file": ("circular.txt", io.BytesIO(b"contenido"), "text/plain")}
    data = {"nombre": "Circular de prueba"}
    r = client.post(
        "/api/documents/upload",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


def test_usuario_consulta_no_puede_eliminar_documentos(client, consulta_user):
    token = token_for(consulta_user)
    r = client.delete("/api/documents/algun-id", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403  # el rol se valida antes que la existencia del documento


def test_usuario_consulta_no_accede_a_estadisticas_admin(client, consulta_user):
    token = token_for(consulta_user)
    r = client.get("/api/admin/statistics", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_admin_si_accede_a_estadisticas(client, admin_user):
    token = token_for(admin_user)
    r = client.get("/api/admin/statistics", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_archivo_con_extension_no_permitida_es_rechazado(client, admin_user):
    token = token_for(admin_user)
    files = {"file": ("virus.exe", io.BytesIO(b"MZ..."), "application/octet-stream")}
    data = {"nombre": "Archivo sospechoso"}
    r = client.post(
        "/api/documents/upload",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


def test_login_con_credenciales_invalidas_rechaza_acceso(client, admin_user):
    r = client.post("/api/auth/login", json={"email": admin_user.email, "password": "clave-incorrecta"})
    assert r.status_code == 401


def test_pregunta_vacia_es_rechazada(client, consulta_user):
    token = token_for(consulta_user)
    r = client.post("/api/chat/query", json={"pregunta": "   "}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
