from inicio import conn


# ============================================================
# AUXILIARES
# ============================================================

def _commit():
    conn.commit()


def _rollback():
    conn.rollback()


def _departamentos_tem_id_empresa():
    """
    Retorna True se a coluna sobreaviso.departamentos.id_empresa existir.

    Isso mantém o backend compatível com bancos em que a tabela
    departamentos ainda não recebeu a coluna id_empresa.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS
                (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'sobreaviso'
                      AND table_name = 'departamentos'
                      AND column_name = 'id_empresa'
                );
            """)
            return bool(cur.fetchone()[0])

    except Exception:
        _rollback()
        raise


# ============================================================
# EMPRESAS
# ============================================================

def listar_empresas(apenas_ativas=False):
    with conn.cursor() as cur:
        sql = """
            SELECT
                id_empresa,
                nome_empresa,
                banco_de_horas,
                ativo
            FROM sobreaviso.empresas
        """

        if apenas_ativas:
            sql += " WHERE ativo = TRUE "

        sql += " ORDER BY nome_empresa;"

        cur.execute(sql)
        return cur.fetchall()


def buscar_empresa(id_empresa):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id_empresa,
                nome_empresa,
                banco_de_horas,
                ativo
            FROM sobreaviso.empresas
            WHERE id_empresa = %s;
        """, (id_empresa,))
        return cur.fetchone()


def cadastrar_empresa(nome_empresa, banco_de_horas=False, ativo=True):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sobreaviso.empresas
                (
                    nome_empresa,
                    banco_de_horas,
                    ativo
                )
                VALUES (%s, %s, %s)
                RETURNING id_empresa;
            """, (nome_empresa, banco_de_horas, ativo))

            id_empresa = cur.fetchone()[0]

        _commit()
        return id_empresa

    except Exception:
        _rollback()
        raise


def alterar_empresa(id_empresa, nome_empresa, banco_de_horas=False, ativo=True):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sobreaviso.empresas
                   SET nome_empresa = %s,
                       banco_de_horas = %s,
                       ativo = %s
                 WHERE id_empresa = %s;
            """, (nome_empresa, banco_de_horas, ativo, id_empresa))

            alterados = cur.rowcount

        _commit()
        return alterados > 0

    except Exception:
        _rollback()
        raise


def excluir_empresa(id_empresa):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.empresas
                WHERE id_empresa = %s;
            """, (id_empresa,))

            excluidos = cur.rowcount

        _commit()
        return excluidos > 0

    except Exception:
        _rollback()
        raise


# ============================================================
# DEPARTAMENTOS
# ============================================================

def _validar_gestor_departamento(id_gestor, id_empresa=None):
    """
    Valida o gestor principal do departamento.

    Regras:
    - id_gestor pode ser None;
    - quando informado, deve existir;
    - deve estar ativo;
    - deve possuir perfil GESTOR ou ADMIN;
    - se id_empresa for informado, deve pertencer à mesma empresa.
    """

    if id_gestor is None:
        return True

    with conn.cursor() as cur:

        sql = """
            SELECT
                u.id_usuario
            FROM sobreaviso.usuarios u
            WHERE u.id_usuario = %s
              AND u.ativo = TRUE
              AND u.perfil IN ('GESTOR', 'ADMIN')
        """

        params = [id_gestor]

        if id_empresa is not None:
            sql += " AND u.id_empresa = %s "
            params.append(id_empresa)

        sql += " LIMIT 1;"

        cur.execute(
            sql,
            tuple(params)
        )

        gestor = cur.fetchone()

    if not gestor:
        raise ValueError(
            "O gestor informado não existe, está inativo, "
            "não possui perfil GESTOR/ADMIN ou pertence a outra empresa."
        )

    return True


def listar_departamentos():
    """
    Retorna:
        id_departamento,
        nome_departamento,
        email_responsavel_1,
        email_responsavel_2,
        ativo,
        data_cadastro,
        id_empresa,
        nome_empresa,
        id_gestor,
        nome_gestor
    """

    try:
        with conn.cursor() as cur:

            if _departamentos_tem_id_empresa():

                cur.execute("""
                    SELECT
                        d.id_departamento,
                        d.nome_departamento,
                        d.email_responsavel_1,
                        d.email_responsavel_2,
                        d.ativo,
                        d.data_cadastro,
                        d.id_empresa,
                        e.nome_empresa,
                        d.id_gestor,
                        g.nome AS nome_gestor
                    FROM sobreaviso.departamentos d

                    LEFT JOIN sobreaviso.empresas e
                        ON e.id_empresa = d.id_empresa

                    LEFT JOIN sobreaviso.usuarios g
                        ON g.id_usuario = d.id_gestor

                    ORDER BY
                        e.nome_empresa,
                        d.nome_departamento;
                """)

            else:

                cur.execute("""
                    SELECT
                        d.id_departamento,
                        d.nome_departamento,
                        d.email_responsavel_1,
                        d.email_responsavel_2,
                        d.ativo,
                        d.data_cadastro,

                        COALESCE(
                            (
                                SELECT u.id_empresa
                                FROM sobreaviso.usuarios u
                                WHERE u.id_departamento = d.id_departamento
                                  AND u.id_empresa IS NOT NULL
                                ORDER BY u.id_usuario
                                LIMIT 1
                            ),
                            (
                                SELECT e.id_empresa
                                FROM sobreaviso.empresas e
                                WHERE e.ativo = TRUE
                                ORDER BY e.id_empresa
                                LIMIT 1
                            )
                        ) AS id_empresa,

                        COALESCE(
                            (
                                SELECT e.nome_empresa
                                FROM sobreaviso.usuarios u
                                INNER JOIN sobreaviso.empresas e
                                    ON e.id_empresa = u.id_empresa
                                WHERE u.id_departamento = d.id_departamento
                                  AND u.id_empresa IS NOT NULL
                                ORDER BY u.id_usuario
                                LIMIT 1
                            ),
                            (
                                SELECT e.nome_empresa
                                FROM sobreaviso.empresas e
                                WHERE e.ativo = TRUE
                                ORDER BY e.id_empresa
                                LIMIT 1
                            )
                        ) AS nome_empresa,

                        d.id_gestor,
                        g.nome AS nome_gestor

                    FROM sobreaviso.departamentos d

                    LEFT JOIN sobreaviso.usuarios g
                        ON g.id_usuario = d.id_gestor

                    ORDER BY d.nome_departamento;
                """)

            return cur.fetchall()

    except Exception:
        _rollback()
        raise


def buscar_departamento(id_departamento):
    """
    Retorna:
        id_departamento,
        nome_departamento,
        email_responsavel_1,
        email_responsavel_2,
        ativo,
        data_cadastro,
        id_empresa,
        nome_empresa,
        id_gestor,
        nome_gestor
    """

    try:
        with conn.cursor() as cur:

            if _departamentos_tem_id_empresa():

                cur.execute("""
                    SELECT
                        d.id_departamento,
                        d.nome_departamento,
                        d.email_responsavel_1,
                        d.email_responsavel_2,
                        d.ativo,
                        d.data_cadastro,
                        d.id_empresa,
                        e.nome_empresa,
                        d.id_gestor,
                        g.nome AS nome_gestor
                    FROM sobreaviso.departamentos d

                    LEFT JOIN sobreaviso.empresas e
                        ON e.id_empresa = d.id_empresa

                    LEFT JOIN sobreaviso.usuarios g
                        ON g.id_usuario = d.id_gestor

                    WHERE d.id_departamento = %s;
                """, (id_departamento,))

            else:

                cur.execute("""
                    SELECT
                        d.id_departamento,
                        d.nome_departamento,
                        d.email_responsavel_1,
                        d.email_responsavel_2,
                        d.ativo,
                        d.data_cadastro,

                        COALESCE(
                            (
                                SELECT u.id_empresa
                                FROM sobreaviso.usuarios u
                                WHERE u.id_departamento = d.id_departamento
                                  AND u.id_empresa IS NOT NULL
                                ORDER BY u.id_usuario
                                LIMIT 1
                            ),
                            (
                                SELECT e.id_empresa
                                FROM sobreaviso.empresas e
                                WHERE e.ativo = TRUE
                                ORDER BY e.id_empresa
                                LIMIT 1
                            )
                        ) AS id_empresa,

                        COALESCE(
                            (
                                SELECT e.nome_empresa
                                FROM sobreaviso.usuarios u
                                INNER JOIN sobreaviso.empresas e
                                    ON e.id_empresa = u.id_empresa
                                WHERE u.id_departamento = d.id_departamento
                                  AND u.id_empresa IS NOT NULL
                                ORDER BY u.id_usuario
                                LIMIT 1
                            ),
                            (
                                SELECT e.nome_empresa
                                FROM sobreaviso.empresas e
                                WHERE e.ativo = TRUE
                                ORDER BY e.id_empresa
                                LIMIT 1
                            )
                        ) AS nome_empresa,

                        d.id_gestor,
                        g.nome AS nome_gestor

                    FROM sobreaviso.departamentos d

                    LEFT JOIN sobreaviso.usuarios g
                        ON g.id_usuario = d.id_gestor

                    WHERE d.id_departamento = %s;
                """, (id_departamento,))

            return cur.fetchone()

    except Exception:
        _rollback()
        raise


def cadastrar_departamento(
    id_empresa,
    nome_departamento,
    email_responsavel_1=None,
    email_responsavel_2=None,
    id_gestor=None
):
    try:

        _validar_gestor_departamento(
            id_gestor=id_gestor,
            id_empresa=id_empresa
        )

        with conn.cursor() as cur:

            if _departamentos_tem_id_empresa():

                cur.execute("""
                    INSERT INTO sobreaviso.departamentos
                    (
                        id_empresa,
                        nome_departamento,
                        email_responsavel_1,
                        email_responsavel_2,
                        id_gestor
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id_departamento;
                """, (
                    id_empresa,
                    nome_departamento,
                    email_responsavel_1,
                    email_responsavel_2,
                    id_gestor
                ))

            else:

                cur.execute("""
                    INSERT INTO sobreaviso.departamentos
                    (
                        nome_departamento,
                        email_responsavel_1,
                        email_responsavel_2,
                        id_gestor
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id_departamento;
                """, (
                    nome_departamento,
                    email_responsavel_1,
                    email_responsavel_2,
                    id_gestor
                ))

            id_departamento = cur.fetchone()[0]

        _commit()
        return id_departamento

    except Exception:
        _rollback()
        raise


def alterar_departamento(
    id_departamento,
    id_empresa,
    nome_departamento,
    email_responsavel_1=None,
    email_responsavel_2=None,
    ativo=True,
    id_gestor=None
):
    try:

        _validar_gestor_departamento(
            id_gestor=id_gestor,
            id_empresa=id_empresa
        )

        with conn.cursor() as cur:

            if _departamentos_tem_id_empresa():

                cur.execute("""
                    UPDATE sobreaviso.departamentos
                       SET id_empresa = %s,
                           nome_departamento = %s,
                           email_responsavel_1 = %s,
                           email_responsavel_2 = %s,
                           ativo = %s,
                           id_gestor = %s
                     WHERE id_departamento = %s;
                """, (
                    id_empresa,
                    nome_departamento,
                    email_responsavel_1,
                    email_responsavel_2,
                    ativo,
                    id_gestor,
                    id_departamento
                ))

            else:

                cur.execute("""
                    UPDATE sobreaviso.departamentos
                       SET nome_departamento = %s,
                           email_responsavel_1 = %s,
                           email_responsavel_2 = %s,
                           ativo = %s,
                           id_gestor = %s
                     WHERE id_departamento = %s;
                """, (
                    nome_departamento,
                    email_responsavel_1,
                    email_responsavel_2,
                    ativo,
                    id_gestor,
                    id_departamento
                ))

            alterados = cur.rowcount

        _commit()
        return alterados > 0

    except Exception:
        _rollback()
        raise


def excluir_departamento(id_departamento):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.departamentos
                WHERE id_departamento = %s;
            """, (id_departamento,))

            excluidos = cur.rowcount

        _commit()
        return excluidos > 0

    except Exception:
        _rollback()
        raise

def buscar_gestor_departamento(id_departamento):
    """
    Retorna:
        id_gestor,
        nome_gestor

    Retorna None quando o departamento não possui gestor definido.
    """

    with conn.cursor() as cur:

        cur.execute("""
            SELECT
                d.id_gestor,
                g.nome
            FROM sobreaviso.departamentos d

            LEFT JOIN sobreaviso.usuarios g
                ON g.id_usuario = d.id_gestor

            WHERE d.id_departamento = %s;
        """, (id_departamento,))

        gestor = cur.fetchone()

    if not gestor or gestor[0] is None:
        return None

    return gestor


def listar_usuarios_departamento(id_departamento):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id_usuario,
                nome,
                chapa
            FROM sobreaviso.usuarios
            WHERE id_departamento = %s
              AND ativo = TRUE
            ORDER BY nome;
        """, (id_departamento,))

        return cur.fetchall()


# ============================================================
# CIDADES
# ============================================================

def listar_cidades(uf=None):
    try:
        with conn.cursor() as cur:
            if uf:
                cur.execute("""
                    SELECT id_cidade, nome_cidade, uf
                    FROM sobreaviso.cidades
                    WHERE uf = %s
                    ORDER BY nome_cidade;
                """, (uf.upper(),))
            else:
                cur.execute("""
                    SELECT id_cidade, nome_cidade, uf
                    FROM sobreaviso.cidades
                    ORDER BY uf, nome_cidade;
                """)

            return cur.fetchall()

    except Exception:
        _rollback()
        raise


def buscar_cidade(id_cidade):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id_cidade, nome_cidade, uf
            FROM sobreaviso.cidades
            WHERE id_cidade = %s;
        """, (id_cidade,))
        return cur.fetchone()


def cadastrar_cidade(nome_cidade, uf):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sobreaviso.cidades
                (
                    nome_cidade,
                    uf
                )
                VALUES (%s, %s)
                RETURNING id_cidade;
            """, (nome_cidade, uf.upper()))

            id_cidade = cur.fetchone()[0]

        _commit()
        return id_cidade

    except Exception:
        _rollback()
        raise


def alterar_cidade(id_cidade, nome_cidade, uf):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sobreaviso.cidades
                   SET nome_cidade = %s,
                       uf = %s
                 WHERE id_cidade = %s;
            """, (nome_cidade, uf.upper(), id_cidade))

            alterados = cur.rowcount

        _commit()
        return alterados > 0

    except Exception:
        _rollback()
        raise


def excluir_cidade(id_cidade):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.cidades
                WHERE id_cidade = %s;
            """, (id_cidade,))

            excluidos = cur.rowcount

        _commit()
        return excluidos > 0

    except Exception:
        _rollback()
        raise


# ============================================================
# USUÁRIOS
# ============================================================

def listar_usuarios(apenas_ativos=False):
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    u.id_usuario,
                    u.nome,
                    u.chapa,
                    u.email,
                    u.login,
                    u.perfil,
                    u.ativo,
                    u.id_departamento,
                    d.nome_departamento,
                    u.id_cidade,
                    c.nome_cidade,
                    u.uf,
                    u.data_cadastro,
                    u.id_empresa,
                    e.nome_empresa,
                    u.id_gestor,
                    g.nome AS nome_gestor
                FROM sobreaviso.usuarios u
                INNER JOIN sobreaviso.departamentos d
                    ON d.id_departamento = u.id_departamento
                INNER JOIN sobreaviso.empresas e
                    ON e.id_empresa = u.id_empresa
                LEFT JOIN sobreaviso.cidades c
                    ON c.id_cidade = u.id_cidade
                LEFT JOIN sobreaviso.usuarios g
                    ON g.id_usuario = u.id_gestor
            """

            if apenas_ativos:
                sql += " WHERE u.ativo = TRUE "

            sql += " ORDER BY e.nome_empresa, u.nome;"

            cur.execute(sql)
            return cur.fetchall()

    except Exception:
        _rollback()
        raise


def buscar_usuario(id_usuario):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                u.id_usuario,
                u.nome,
                u.chapa,
                u.email,
                u.login,
                u.perfil,
                u.ativo,
                u.id_departamento,
                d.nome_departamento,
                u.id_cidade,
                c.nome_cidade,
                u.uf,
                u.data_cadastro,
                u.id_empresa,
                e.nome_empresa,
                u.id_gestor,
                g.nome AS nome_gestor
            FROM sobreaviso.usuarios u
            INNER JOIN sobreaviso.departamentos d
                ON d.id_departamento = u.id_departamento
            INNER JOIN sobreaviso.empresas e
                ON e.id_empresa = u.id_empresa
            LEFT JOIN sobreaviso.cidades c
                ON c.id_cidade = u.id_cidade
            LEFT JOIN sobreaviso.usuarios g
                ON g.id_usuario = u.id_gestor
            WHERE u.id_usuario = %s;
        """, (id_usuario,))
        return cur.fetchone()


def listar_gestores(id_empresa=None):
    """
    Lista usuários ativos com perfil GESTOR ou ADMIN.
    Se id_empresa for informado, restringe à empresa.
    """

    try:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    u.id_usuario,
                    u.nome,
                    u.id_empresa,
                    e.nome_empresa,
                    u.id_departamento,
                    d.nome_departamento
                FROM sobreaviso.usuarios u
                INNER JOIN sobreaviso.empresas e
                    ON e.id_empresa = u.id_empresa
                INNER JOIN sobreaviso.departamentos d
                    ON d.id_departamento = u.id_departamento
                WHERE u.ativo = TRUE
                  AND u.perfil IN ('GESTOR', 'ADMIN')
            """

            params = []

            if id_empresa is not None:
                sql += " AND u.id_empresa = %s "
                params.append(id_empresa)

            sql += " ORDER BY u.nome;"

            cur.execute(sql, tuple(params))
            return cur.fetchall()

    except Exception:
        _rollback()
        raise


def listar_departamentos_gestor(id_usuario):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                gd.id_gestor_departamento,
                gd.id_usuario,
                gd.id_departamento,
                d.nome_departamento
            FROM sobreaviso.gestor_departamento gd
            INNER JOIN sobreaviso.departamentos d
                ON d.id_departamento = gd.id_departamento
            WHERE gd.id_usuario = %s
            ORDER BY d.nome_departamento;
        """, (id_usuario,))

        return cur.fetchall()


def adicionar_departamento_gestor(id_usuario, id_departamento):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sobreaviso.gestor_departamento
                (
                    id_usuario,
                    id_departamento
                )
                VALUES (%s, %s)
                ON CONFLICT (id_usuario, id_departamento)
                DO NOTHING;
            """, (
                id_usuario,
                id_departamento
            ))

        _commit()

    except Exception:
        _rollback()
        raise


def remover_departamento_gestor(id_usuario, id_departamento):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.gestor_departamento
                WHERE id_usuario = %s
                  AND id_departamento = %s;
            """, (
                id_usuario,
                id_departamento
            ))

        _commit()

    except Exception:
        _rollback()
        raise


def cadastrar_usuario(
    id_empresa,
    id_departamento,
    nome,
    chapa,
    email,
    login,
    senha,
    perfil="TECNICO",
    id_cidade=None,
    uf=None,
    id_gestor=None,
    departamentos_gestor=None
):
    """
    Cadastra o usuário diretamente na tabela sobreaviso.usuarios.

    A inserção direta é necessária porque id_empresa é NOT NULL e
    precisa ser informado no mesmo INSERT. O hash continua utilizando
    sobreaviso.hash_senha(), preservando o padrão de autenticação.
    """

    if not id_empresa:
        raise ValueError("Informe a empresa.")

    if not id_departamento:
        raise ValueError("Informe o departamento.")

    if not nome:
        raise ValueError("Informe o nome.")

    if not email:
        raise ValueError("Informe o e-mail.")

    if not login:
        raise ValueError("Informe o login.")

    if not senha:
        raise ValueError("Informe a senha.")

    perfil = (perfil or "TECNICO").upper()

    if perfil not in ("TECNICO", "GESTOR", "ADMIN"):
        raise ValueError("Perfil inválido.")

    # ADMIN pode não ter gestor.
    # TECNICO/GESTOR devem receber o gestor definido pelo front/departamento.
    if perfil != "ADMIN" and id_gestor is None:
        raise ValueError(
            "Técnicos e gestores precisam possuir gestor definido."
        )

    try:

        with conn.cursor() as cur:

            cur.execute("""
                WITH novo_salt AS
                (
                    SELECT gen_random_bytes(16) AS salt
                )
                INSERT INTO sobreaviso.usuarios
                (
                    id_empresa,
                    id_departamento,
                    nome,
                    chapa,
                    email,
                    login,
                    senha_salt,
                    senha_hash,
                    perfil,
                    id_cidade,
                    uf,
                    id_gestor
                )
                SELECT
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    ns.salt,
                    sobreaviso.hash_senha(%s, ns.salt),
                    %s,
                    %s,
                    %s,
                    %s
                FROM novo_salt ns
                RETURNING id_usuario;
            """, (
                id_empresa,
                id_departamento,
                nome,
                chapa,
                email,
                login,
                senha,
                perfil,
                id_cidade,
                uf.upper() if uf else None,
                id_gestor
            ))

            id_usuario = cur.fetchone()[0]

            if perfil == "GESTOR" and departamentos_gestor:

                for id_depto_gestor in departamentos_gestor:

                    cur.execute("""
                        INSERT INTO sobreaviso.gestor_departamento
                        (
                            id_usuario,
                            id_departamento
                        )
                        VALUES (%s, %s)
                        ON CONFLICT (id_usuario, id_departamento)
                        DO NOTHING;
                    """, (
                        id_usuario,
                        id_depto_gestor
                    ))

        _commit()
        return id_usuario

    except Exception:
        _rollback()
        raise


def alterar_usuario(id_usuario, id_empresa, id_departamento, nome, chapa, email,
                     login, perfil, id_cidade=None, uf=None, id_gestor=None,
                     ativo=True):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sobreaviso.usuarios
                   SET id_empresa = %s,
                       id_departamento = %s,
                       nome = %s,
                       chapa = %s,
                       email = %s,
                       login = %s,
                       perfil = %s,
                       id_cidade = %s,
                       uf = %s,
                       id_gestor = %s,
                       ativo = %s
                 WHERE id_usuario = %s;
            """, (
                id_empresa,
                id_departamento,
                nome,
                chapa,
                email,
                login,
                perfil,
                id_cidade,
                uf.upper() if uf else None,
                id_gestor,
                ativo,
                id_usuario
            ))

            alterados = cur.rowcount

        _commit()
        return alterados > 0

    except Exception:
        _rollback()
        raise



def alterar_proprio_cadastro(
    id_usuario,
    nome,
    chapa,
    email
):
    """
    Permite a alteração restrita do próprio cadastro.

    Esta função altera somente:
    - nome
    - chapa/matrícula
    - e-mail

    Não altera login, perfil, empresa, departamento,
    cidade, UF, gestor ou status do usuário.
    """

    if not id_usuario:
        raise ValueError("Usuário inválido.")

    if not nome or not nome.strip():
        raise ValueError("Informe o nome.")

    if not email or not email.strip():
        raise ValueError("Informe o e-mail.")

    try:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE sobreaviso.usuarios
                   SET nome = %s,
                       chapa = %s,
                       email = %s
                 WHERE id_usuario = %s
                   AND ativo = TRUE;
            """, (
                nome.strip(),
                chapa.strip() if chapa else None,
                email.strip(),
                id_usuario
            ))

            alterados = cur.rowcount

        _commit()
        return alterados > 0

    except Exception:
        _rollback()
        raise

def alterar_senha(id_usuario, nova_senha):
    if not nova_senha:
        raise ValueError("A nova senha não pode ser vazia.")

    try:
        with conn.cursor() as cur:
            cur.execute("""
                WITH novo_salt AS
                (
                    SELECT gen_random_bytes(16) AS salt
                )
                UPDATE sobreaviso.usuarios u
                   SET senha_salt = ns.salt,
                       senha_hash = sobreaviso.hash_senha(%s, ns.salt)
                  FROM novo_salt ns
                 WHERE u.id_usuario = %s;
            """, (nova_senha, id_usuario))

            alterados = cur.rowcount

        _commit()
        return alterados > 0

    except Exception:
        _rollback()
        raise


def validar_login(login, senha):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT sobreaviso.validar_senha(%s, %s);
        """, (login, senha))
        return bool(cur.fetchone()[0])


def excluir_usuario(id_usuario):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.usuarios
                WHERE id_usuario = %s;
            """, (id_usuario,))

            excluidos = cur.rowcount

        _commit()
        return excluidos > 0

    except Exception:
        _rollback()
        raise


# ============================================================
# RECEBEDORES
# ============================================================

def buscar_recebedores(id_usuario):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id_recebedor,
                id_usuario,
                emails,
                ativo
            FROM sobreaviso.recebedores
            WHERE id_usuario = %s;
        """, (id_usuario,))

        return cur.fetchone()


def cadastrar_recebedores(id_usuario, emails):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sobreaviso.recebedores
                (
                    id_usuario,
                    emails
                )
                VALUES (%s, %s)
                RETURNING id_recebedor;
            """, (
                id_usuario,
                emails
            ))

            id_recebedor = cur.fetchone()[0]

        _commit()
        return id_recebedor

    except Exception:
        _rollback()
        raise


def alterar_recebedores(id_usuario, emails, ativo=True):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sobreaviso.recebedores
                   SET emails = %s,
                       ativo = %s
                 WHERE id_usuario = %s;
            """, (
                emails,
                ativo,
                id_usuario
            ))

            alterados = cur.rowcount

        _commit()
        return alterados > 0

    except Exception:
        _rollback()
        raise


def excluir_recebedores(id_usuario):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.recebedores
                WHERE id_usuario = %s;
            """, (id_usuario,))

            excluidos = cur.rowcount

        _commit()
        return excluidos > 0

    except Exception:
        _rollback()
        raise

# ============================================================
# VALIDAÇÃO DE GESTOR PARA ESCALAS
# ============================================================

def validar_usuario_com_gestor(id_usuario):
    """
    Somente usuários com id_gestor preenchido podem receber escala.
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                u.id_usuario,
                u.nome,
                u.id_gestor,
                g.nome AS nome_gestor
            FROM sobreaviso.usuarios u
            LEFT JOIN sobreaviso.usuarios g
                ON g.id_usuario = u.id_gestor
            WHERE u.id_usuario = %s
              AND u.ativo = TRUE;
        """, (id_usuario,))

        usuario = cur.fetchone()

    if not usuario:
        raise ValueError("Usuário não encontrado ou inativo.")

    if usuario[2] is None:
        raise ValueError(
            f"O usuário {usuario[1]} não possui gestor definido. "
            "Cadastre um gestor antes de criar uma escala."
        )

    return True


# ============================================================
# ESCALAS
# ============================================================

def listar_escalas(id_usuario=None):
    with conn.cursor() as cur:
        if id_usuario:
            cur.execute("""
                SELECT
                    e.id_escala,
                    e.id_usuario,
                    u.nome,
                    e.data_hora_inicio,
                    e.data_hora_fim,
                    e.ordem,
                    e.replicacao,
                    e.id_escala_origem,
                    e.data_cadastro
                FROM sobreaviso.escalas e
                INNER JOIN sobreaviso.usuarios u
                    ON u.id_usuario = e.id_usuario
                WHERE e.id_usuario = %s
                ORDER BY e.data_hora_inicio;
            """, (id_usuario,))
        else:
            cur.execute("""
                SELECT
                    e.id_escala,
                    e.id_usuario,
                    u.nome,
                    e.data_hora_inicio,
                    e.data_hora_fim,
                    e.ordem,
                    e.replicacao,
                    e.id_escala_origem,
                    e.data_cadastro
                FROM sobreaviso.escalas e
                INNER JOIN sobreaviso.usuarios u
                    ON u.id_usuario = e.id_usuario
                ORDER BY e.data_hora_inicio;
            """)

        return cur.fetchall()


def buscar_escala(id_escala):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id_escala,
                id_usuario,
                data_hora_inicio,
                data_hora_fim,
                ordem,
                replicacao,
                id_escala_origem,
                data_cadastro
            FROM sobreaviso.escalas
            WHERE id_escala = %s;
        """, (id_escala,))
        return cur.fetchone()


def cadastrar_escala(id_usuario, data_hora_inicio, data_hora_fim,
                      ordem, replicacao=False, id_escala_origem=None):

    validar_usuario_com_gestor(id_usuario)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sobreaviso.escalas
                (
                    id_usuario,
                    data_hora_inicio,
                    data_hora_fim,
                    ordem,
                    replicacao,
                    id_escala_origem
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id_escala;
            """, (
                id_usuario,
                data_hora_inicio,
                data_hora_fim,
                ordem,
                replicacao,
                id_escala_origem
            ))

            id_escala = cur.fetchone()[0]

        _commit()
        return id_escala

    except Exception:
        _rollback()
        raise


def alterar_escala(id_escala, id_usuario, data_hora_inicio,
                  data_hora_fim, ordem, replicacao, usuario_executor=None):
    """Altera escala com autorização e auditoria transacional.

    usuario_executor: dicionário da sessão autenticada com id_usuario e perfil.
    Exige a instalação de sobreaviso_auditoria.sql.
    """
    from escalas_permissoes import alterar_escala_segura

    if usuario_executor is None:
        raise PermissionError(
            "Informe usuario_executor com os dados da sessão autenticada."
        )

    validar_usuario_com_gestor(id_usuario)
    return alterar_escala_segura(
        usuario=usuario_executor,
        id_escala=id_escala,
        id_usuario=id_usuario,
        data_hora_inicio=data_hora_inicio,
        data_hora_fim=data_hora_fim,
        ordem=ordem,
        replicacao=replicacao,
    )


def listar_historico_escala(id_escala, usuario_executor):
    """Retorna auditoria somente para usuário autorizado."""
    from escalas_permissoes import historico_escala

    return historico_escala(usuario_executor, id_escala)


def excluir_escala(id_escala):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.escalas
                WHERE id_escala = %s;
            """, (id_escala,))

            excluidos = cur.rowcount

        _commit()
        return excluidos > 0

    except Exception:
        _rollback()
        raise


# ============================================================
# FERIADOS
# ============================================================

def listar_feriados(ano=None, uf=None, id_cidade=None):
    with conn.cursor() as cur:
        sql = """
            SELECT
                f.id_feriado,
                f.data_feriado,
                f.descricao,
                f.id_cidade,
                c.nome_cidade,
                f.uf,
                f.ativo,
                f.data_cadastro
            FROM sobreaviso.feriados f
            LEFT JOIN sobreaviso.cidades c
                ON c.id_cidade = f.id_cidade
            WHERE 1 = 1
        """

        params = []

        if ano:
            sql += " AND EXTRACT(YEAR FROM f.data_feriado) = %s "
            params.append(ano)

        if uf:
            sql += " AND f.uf = %s "
            params.append(uf.upper())

        if id_cidade:
            sql += " AND f.id_cidade = %s "
            params.append(id_cidade)

        sql += " ORDER BY f.data_feriado;"

        cur.execute(sql, tuple(params))
        return cur.fetchall()


def buscar_feriado(id_feriado):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id_feriado,
                data_feriado,
                descricao,
                id_cidade,
                uf,
                ativo,
                data_cadastro
            FROM sobreaviso.feriados
            WHERE id_feriado = %s;
        """, (id_feriado,))
        return cur.fetchone()


def cadastrar_feriado(data_feriado, descricao, id_cidade=None, uf=None):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sobreaviso.feriados
                (
                    data_feriado,
                    descricao,
                    id_cidade,
                    uf
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id_feriado;
            """, (
                data_feriado,
                descricao,
                id_cidade,
                uf.upper() if uf else None
            ))

            id_feriado = cur.fetchone()[0]

        _commit()
        return id_feriado

    except Exception:
        _rollback()
        raise


def alterar_feriado(id_feriado, data_feriado, descricao,
                     id_cidade=None, uf=None, ativo=True):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sobreaviso.feriados
                   SET data_feriado = %s,
                       descricao = %s,
                       id_cidade = %s,
                       uf = %s,
                       ativo = %s
                 WHERE id_feriado = %s;
            """, (
                data_feriado,
                descricao,
                id_cidade,
                uf.upper() if uf else None,
                ativo,
                id_feriado
            ))

            alterados = cur.rowcount

        _commit()
        return alterados > 0

    except Exception:
        _rollback()
        raise


def excluir_feriado(id_feriado):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sobreaviso.feriados
                WHERE id_feriado = %s;
            """, (id_feriado,))

            excluidos = cur.rowcount

        _commit()
        return excluidos > 0

    except Exception:
        _rollback()
        raise

# cadastrar_departamento('SISTEMAS', 'dmartins@refit.com.br', email_responsavel_2=None)
# with conn.cursor() as cur:
#     cur.execute("SELECT * FROM sobreaviso.departamentos;")

#     departamentos = cur.fetchall()

#     for departamento in departamentos:
#         print(departamento)