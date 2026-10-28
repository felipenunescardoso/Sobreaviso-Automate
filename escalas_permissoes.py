"""Camada de permissão para alterações feitas na interface de Escalas.
Instalar sobreaviso_auditoria.sql antes de utilizar.
"""
from inicio import conn


def _identidade(usuario):
    if not isinstance(usuario, dict):
        raise PermissionError('Sessão não autenticada.')
    perfil = str(usuario.get('perfil', '')).upper().strip()
    identificador = usuario.get('id_usuario')
    if perfil not in ('ADMIN', 'GESTOR', 'TECNICO') or identificador is None:
        raise PermissionError('Sessão sem perfil ou id_usuario válido.')
    return int(identificador), perfil


def _subordinados(cur, id_gestor):
    cur.execute('''
      WITH RECURSIVE subordinados AS (
        SELECT id_usuario FROM sobreaviso.usuarios WHERE id_gestor=%s AND ativo=TRUE
        UNION
        SELECT u.id_usuario FROM sobreaviso.usuarios u
        JOIN subordinados s ON u.id_gestor=s.id_usuario WHERE u.ativo=TRUE
      ) SELECT id_usuario FROM subordinados
    ''', (id_gestor,))
    return {r[0] for r in cur.fetchall()}


def usuarios_permitidos(usuario):
    executor, perfil = _identidade(usuario)
    if perfil == 'TECNICO':
        return {executor}
    if perfil == 'ADMIN':
        return None  # todos
    with conn.cursor() as cur:
        return _subordinados(cur, executor) | {executor}


def alterar_escala_segura(usuario, id_escala, id_usuario, data_hora_inicio,
                          data_hora_fim, ordem, replicacao):
    executor, perfil = _identidade(usuario)
    if data_hora_fim <= data_hora_inicio:
        raise ValueError('Fim deve ser posterior ao início.')
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT id_usuario, ordem, replicacao, encerrada
                           FROM sobreaviso.escalas WHERE id_escala=%s FOR UPDATE''', (id_escala,))
            antiga = cur.fetchone()
            if not antiga:
                raise ValueError('Escala não encontrada.')
            dono, ordem_antiga, replica_antiga, encerrada = antiga
            permitidos = usuarios_permitidos(usuario)
            if permitidos is not None and (dono not in permitidos or id_usuario not in permitidos):
                raise PermissionError('Sem permissão para alterar esta escala.')
            if perfil == 'TECNICO':
                if encerrada:
                    raise PermissionError('Escala encerrada: procure seu gestor.')
                if (id_usuario != dono or int(ordem) != ordem_antiga or bool(replicacao) != replica_antiga):
                    raise PermissionError('Técnico só pode editar datas e horários da própria escala.')
                # Impede alterar escalas já iniciadas/encerradas, para preservar apuração.
                cur.execute('SELECT data_hora_inicio FROM sobreaviso.escalas WHERE id_escala=%s', (id_escala,))
                from datetime import datetime
                if cur.fetchone()[0] <= datetime.now():
                    raise PermissionError('Escala já iniciada: procure seu gestor.')
            # Não permitir mudar intervalo deixando acionamentos fora da escala.
            cur.execute('''SELECT EXISTS (
                SELECT 1 FROM sobreaviso.lancamentos l
                JOIN sobreaviso.escala_competencias ec ON ec.id_escala_competencia=l.id_escala_competencia
                WHERE ec.id_escala=%s AND l.tipo='ACIONAMENTO'
                AND (l.data_hora_inicio < %s OR l.data_hora_fim > %s)
            )''', (id_escala, data_hora_inicio, data_hora_fim))
            if cur.fetchone()[0]:
                raise ValueError('Há acionamentos fora do novo período. Ajuste com o gestor.')
            cur.execute("SELECT set_config('sobreaviso.usuario_executor', %s, true)", (str(executor),))
            cur.execute('''UPDATE sobreaviso.escalas
                           SET id_usuario=%s, data_hora_inicio=%s, data_hora_fim=%s,
                               ordem=%s, replicacao=%s WHERE id_escala=%s''',
                        (id_usuario, data_hora_inicio, data_hora_fim, ordem, replicacao, id_escala))
            alterados = cur.rowcount
        conn.commit()
        return alterados > 0
    except Exception:
        conn.rollback()
        raise


def historico_escala(usuario, id_escala):
    permitido = usuarios_permitidos(usuario)
    with conn.cursor() as cur:
        cur.execute('SELECT id_usuario FROM sobreaviso.escalas WHERE id_escala=%s', (id_escala,))
        registro = cur.fetchone()
        if not registro or (permitido is not None and registro[0] not in permitido):
            raise PermissionError('Histórico não autorizado.')
        cur.execute('''SELECT a.data_alteracao, a.operacao, u.nome,
                              a.dados_anteriores, a.dados_novos
                       FROM sobreaviso.escalas_auditoria a
                       LEFT JOIN sobreaviso.usuarios u ON u.id_usuario=a.id_usuario_executor
                       WHERE a.id_escala=%s ORDER BY a.id_auditoria DESC''', (id_escala,))
        return cur.fetchall()
