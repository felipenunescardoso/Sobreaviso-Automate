"""Replicador de escalas de sobreaviso por departamento.

Padrão: SIMULAÇÃO. --aplicar persiste numa única transação.
Somente projeta departamentos com início de escala nos últimos 30 dias
e cuja última escala já terminou.
O horizonte é fixo: última segunda-feira do mês seguinte (inclusive).
"""
import argparse
import calendar
import sys
from datetime import date, datetime, time, timedelta
from inicio import conn

INICIO = time(18, 0)
FIM = time(8, 0)
SEMANA = timedelta(days=7)


def log(mensagem):
    print(mensagem, flush=True)


def ultimo_inicio_mes_seguinte(referencia):
    ano = referencia.year + (referencia.month == 12)
    mes = referencia.month % 12 + 1
    ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])
    segunda = ultimo - timedelta(days=ultimo.weekday())
    return datetime.combine(segunda, INICIO)


def carregar(cur):
    cur.execute('''
        SELECT e.id_escala, e.id_usuario, u.nome, u.id_departamento,
               e.data_hora_inicio, e.data_hora_fim, e.ordem,
               e.replicacao, u.ativo
          FROM sobreaviso.escalas e
          JOIN sobreaviso.usuarios u ON u.id_usuario = e.id_usuario
         WHERE u.id_departamento IS NOT NULL
         ORDER BY u.id_departamento, e.data_hora_inicio, e.id_escala
    ''')
    campos = ('id', 'usuario', 'nome', 'depto', 'inicio', 'fim', 'ordem', 'replicacao', 'ativo')
    return [dict(zip(campos, linha)) for linha in cur.fetchall()]


def montar_rodizio(historico):
    """Último titular conhecido por ordem, inclusive escalas manuais.

    Mantém a ordem relativa dos participantes ativos, sem alterar o histórico.
    """
    por_ordem = {}
    for e in sorted(historico, key=lambda x: (x['inicio'], x['id']), reverse=True):
        if e['ordem'] in (1, 2, 3, 4):
            por_ordem.setdefault(e['ordem'], e)
    if not por_ordem:
        raise ValueError('nenhuma escala com ordem de 1 a 4')
    ordens = sorted(por_ordem)
    if ordens != list(range(1, max(ordens) + 1)):
        raise ValueError(f'ordens históricas incompletas: {ordens}')
    titulares = [por_ordem[o] for o in ordens]
    if len({e['usuario'] for e in titulares}) != len(titulares):
        raise ValueError('mesmo usuário em mais de uma posição; revisar cadastro')
    ativos = [e for e in titulares if e['ativo']]
    if not ativos:
        raise ValueError('nenhum técnico ativo no rodízio')
    return titulares, ativos


def indice_seguinte(ultima, titulares, ativos):
    # A última posição pode ser de alguém desativado: seguir a próxima ativa.
    if ultima['ordem'] not in [e['ordem'] for e in titulares]:
        raise ValueError(f'última escala #{ultima["id"]} não tem ordem válida')
    for i, e in enumerate(ativos):
        if e['ordem'] > ultima['ordem']:
            return i
    return 0


def executar(cur, referencia, aplicar, agora):
    todas = carregar(cur)
    # Departamento elegível somente se iniciou uma escala nos últimos 30 dias.
    # Não exige replicacao=TRUE: escalas manuais também contam.
    inicio_janela = agora - timedelta(days=30)
    departamentos = sorted({
        e['depto'] for e in todas
        if inicio_janela <= e['inicio'] <= agora
    })
    ignorados = sorted({e['depto'] for e in todas} - set(departamentos))
    log(f'JANELA DE ATIVIDADE: {inicio_janela:%d/%m/%Y %H:%M} até {agora:%d/%m/%Y %H:%M}')
    for depto_ignorado in ignorados:
        log(f'DEPTO {depto_ignorado} | IGNORADO: sem início de escala nos últimos 30 dias')
    limite_inicio = ultimo_inicio_mes_seguinte(referencia)
    criadas = 0
    log(f'HORIZONTE: até {limite_inicio:%d/%m/%Y %H:%M} (início da última escala)')
    for depto in departamentos:
        historico = [e for e in todas if e['depto'] == depto]
        ultima = max(historico, key=lambda e: (e['inicio'], e['id']))
        log(f'DEPTO {depto} | última escala #{ultima["id"]} | {ultima["nome"]} | '
            f'ordem {ultima["ordem"]} | fim {ultima["fim"]:%d/%m/%Y %H:%M}')

        # Não criar escalas se ainda existe um plantão em andamento ou futuro.
        if ultima['fim'] > agora:
            log(f'DEPTO {depto} | AGUARDANDO: última escala ainda não expirou')
            continue

        titulares, ativos = montar_rodizio(historico)
        if ultima['inicio'].weekday() != 0 or ultima['inicio'].time() != INICIO:
            raise ValueError(f'Departamento {depto}: escala #{ultima["id"]} não começa segunda às 18:00')
        proxima_segunda = ultima['inicio'].date() + SEMANA
        if ultima['fim'].date() != proxima_segunda or ultima['fim'].time() not in (FIM, time(7, 59)):
            raise ValueError(f'Departamento {depto}: escala #{ultima["id"]} não termina na segunda seguinte às 08:00 (ou 07:59 legado)')

        log(f'DEPTO {depto} | ativos: ' + ', '.join(f'{i+1}={e["nome"]}' for i, e in enumerate(ativos)))
        inicio = datetime.combine(proxima_segunda, INICIO)
        indice = indice_seguinte(ultima, titulares, ativos)
        if inicio > limite_inicio:
            log(f'DEPTO {depto} | SEM NOVAS ESCALAS: calendário já preenchido')
            continue
        while inicio <= limite_inicio:
            fim = datetime.combine(inicio.date() + SEMANA, FIM)
            conflitos = [e for e in historico if e['inicio'] < fim and e['fim'] > inicio]
            if conflitos:
                raise ValueError(f'Departamento {depto}: conflito com escala(s) '
                                 f'{[e["id"] for e in conflitos]} em {inicio:%d/%m/%Y}')
            titular = ativos[indice]
            ordem = indice + 1
            if aplicar:
                cur.execute('''
                    INSERT INTO sobreaviso.escalas
                        (id_usuario, data_hora_inicio, data_hora_fim,
                         ordem, replicacao, id_escala_origem)
                    VALUES (%s, %s, %s, %s, TRUE, %s)
                    RETURNING id_escala
                ''', (titular['usuario'], inicio, fim, ordem, ultima['id']))
                status = f'CRIADA #{cur.fetchone()[0]} | PENDENTE DE COMMIT'
            else:
                status = 'SIMULADA'
            log(f'DEPTO {depto} | {inicio:%d/%m/%Y %H:%M} -> {fim:%d/%m/%Y %H:%M} | '
                f'ordem {ordem} | {titular["nome"]} | {status}')
            criadas += 1
            inicio = datetime.combine(inicio.date() + SEMANA, INICIO)
            indice = (indice + 1) % len(ativos)
    return criadas


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description='Replicador semanal de sobreaviso')
    parser.add_argument('--aplicar', action='store_true')
    parser.add_argument('--mes', help='AAAA-MM (horizonte; não altera data atual de expiração)')
    args = parser.parse_args()
    referencia = datetime.strptime(args.mes, '%Y-%m').date() if args.mes else date.today()
    log(f'MODO: {"APLICAR" if args.aplicar else "SIMULAR"} | MÊS: {referencia:%m/%Y}')
    try:
        with conn.cursor() as cur:
            if args.aplicar:
                cur.execute('SELECT pg_advisory_xact_lock(20261020, 1)')
            quantidade = executar(cur, referencia, args.aplicar, datetime.now())
            if args.aplicar:
                conn.commit()
                log(f'COMMIT CONCLUÍDO | escalas_inseridas={quantidade}')
            else:
                conn.rollback()
                log(f'SIMULAÇÃO CONCLUÍDA | escalas_previstas={quantidade} | nenhuma alteração no banco')
    except Exception:
        conn.rollback()
        log('ROLLBACK EXECUTADO | nenhuma escala desta transação confirmada')
        raise


if __name__ == '__main__':
    main()
