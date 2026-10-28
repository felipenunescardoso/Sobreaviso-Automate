from inicio import conn


# ============================================================
# AUTENTICAR USUÁRIO
# ============================================================

def autenticar_usuario(login, senha):

    login = login.strip()

    if not login or not senha:
        return None

    sql = """
        SELECT
            u.id_usuario,
            u.nome,
            u.login,
            u.perfil,
            u.email,
            u.id_departamento,
            d.nome_departamento
        FROM sobreaviso.usuarios u

        INNER JOIN sobreaviso.departamentos d
            ON d.id_departamento = u.id_departamento

        WHERE LOWER(u.login) = LOWER(%s)
          AND u.ativo = TRUE
          AND sobreaviso.validar_senha(
                u.login,
                %s
              ) = TRUE;
    """

    with conn.cursor() as cur:

        cur.execute(
            sql,
            (
                login,
                senha
            )
        )

        usuario = cur.fetchone()

    if not usuario:
        return None

    return {
        "id_usuario": usuario[0],
        "nome": usuario[1],
        "login": usuario[2],
        "perfil": usuario[3],
        "email": usuario[4],
        "id_departamento": usuario[5],
        "nome_departamento": usuario[6]
    }


# ============================================================
# BUSCAR USUÁRIO PELO ID
# ============================================================

def buscar_usuario_logado(id_usuario):

    sql = """
        SELECT
            u.id_usuario,
            u.nome,
            u.login,
            u.perfil,
            u.email,
            u.id_departamento,
            d.nome_departamento,
            u.ativo
        FROM sobreaviso.usuarios u

        INNER JOIN sobreaviso.departamentos d
            ON d.id_departamento = u.id_departamento

        WHERE u.id_usuario = %s;
    """

    with conn.cursor() as cur:

        cur.execute(
            sql,
            (id_usuario,)
        )

        usuario = cur.fetchone()

    if not usuario:
        return None

    return {
        "id_usuario": usuario[0],
        "nome": usuario[1],
        "login": usuario[2],
        "perfil": usuario[3],
        "email": usuario[4],
        "id_departamento": usuario[5],
        "nome_departamento": usuario[6],
        "ativo": usuario[7]
    }


# ============================================================
# VALIDAR SENHA
# ============================================================

def validar_senha(id_usuario, senha):

    if not senha:
        return False

    sql = """
        SELECT EXISTS
        (
            SELECT 1
            FROM sobreaviso.usuarios u
            WHERE u.id_usuario = %s
              AND u.ativo = TRUE
              AND sobreaviso.validar_senha(
                    u.login,
                    %s
                  ) = TRUE
        );
    """

    with conn.cursor() as cur:

        cur.execute(
            sql,
            (
                id_usuario,
                senha
            )
        )

        resultado = cur.fetchone()

    return bool(
        resultado
        and resultado[0]
    )