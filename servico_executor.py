import time as time_module
import subprocess
import threading
import sys
from pathlib import Path

from datetime import datetime, date, time, timedelta

from inicio import conn
from extrator_pdf import calcular_competencia
from executor import encerrar_escala_sistema


NOME_SERVICO = "Executor Automático"
INTERVALO_VERIFICACAO_SEGUNDOS = 1200


# ============================================================
# AUXILIARES DE BANCO
# ============================================================

def _commit():
    conn.commit()


def _rollback():
    conn.rollback()


# ============================================================
# CONFIGURAÇÃO DO SERVIÇO
# ============================================================

def buscar_configuracao_servico():
    """
    Busca a configuração do serviço Executor Automático.
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id,
                nome,
                periodicidade,
                dia,
                hora,
                ativo
            FROM sobreaviso.configuracao_servicos
            WHERE LOWER(nome) = LOWER(%s)
            LIMIT 1;
        """, (NOME_SERVICO,))

        linha = cur.fetchone()

    if not linha:
        return None

    return {
        "id": linha[0],
        "nome": linha[1],
        "periodicidade": linha[2],
        "dia": linha[3],
        "hora": linha[4],
        "ativo": linha[5],
    }


def buscar_ultima_execucao_concluida(id_servico):
    """
    Considera apenas o log de conclusão do lote.

    Isso evita que um log individual de uma escala impeça
    a retomada do lote caso o processo seja interrompido no meio.
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT MAX(data_hora_execucao)
            FROM sobreaviso.logs_servicos
            WHERE id_servico = %s
              AND status = 'SUCESSO'
              AND mensagem LIKE 'LOTE FINALIZADO%%';
        """, (id_servico,))

        linha = cur.fetchone()

    return linha[0] if linha and linha[0] else None


def deve_executar(config, agora=None):
    """
    Periodicidades suportadas:
        DIARIO  -> 1 dia
        SEMANAL -> 7 dias
        MENSAL  -> 30 dias
        ANUAL   -> 365 dias

    O campo dia funciona como o dia mínimo para a primeira execução.
    O campo hora funciona como o horário mínimo.
    Depois da primeira execução, vale a periodicidade configurada.
    """

    if agora is None:
        agora = datetime.now()

    if not config["ativo"]:
        return False

    periodicidade = str(
        config["periodicidade"]
    ).upper().strip()

    intervalos = {
        "DIARIO": timedelta(days=1),
        "SEMANAL": timedelta(days=7),
        "MENSAL": timedelta(days=30),
        "ANUAL": timedelta(days=365),
    }

    if periodicidade not in intervalos:
        raise ValueError(
            f"Periodicidade inválida: "
            f"{config['periodicidade']}"
        )

    hora_configurada = config["hora"]

    if isinstance(hora_configurada, str):
        hora_configurada = time.fromisoformat(
            hora_configurada
        )

    # Primeira execução:
    # respeita dia e hora configurados.
    ultima_execucao = buscar_ultima_execucao_concluida(
        config["id"]
    )

    if not ultima_execucao:

        if agora.day < int(config["dia"]):
            return False

        horario_minimo = datetime.combine(
            agora.date(),
            hora_configurada
        )

        return agora >= horario_minimo

    # Próximas execuções:
    # seguem a periodicidade pedida.
    proxima_execucao = (
        ultima_execucao
        + intervalos[periodicidade]
    )

    # Ainda respeita a hora mínima do dia.
    if agora.date() >= proxima_execucao.date():

        horario_minimo = datetime.combine(
            agora.date(),
            hora_configurada
        )

        return agora >= horario_minimo

    return False


# ============================================================
# LOG
# ============================================================

def gravar_log(
    id_servico,
    nome_servico,
    status,
    mensagem
):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sobreaviso.logs_servicos
                (
                    id_servico,
                    nome_servico,
                    status,
                    mensagem
                )
                VALUES (%s, %s, %s, %s);
            """, (
                id_servico,
                nome_servico,
                status,
                mensagem
            ))

        _commit()

    except Exception:
        _rollback()
        raise


# ============================================================
# ESCALAS DA COMPETÊNCIA
# ============================================================

def buscar_escalas_para_encerrar(
    data_referencia=None
):
    """
    Busca escalas ainda não encerradas que terminam dentro
    da competência já fechada.

    Exemplo em 12/08:
        competência = 11/07 -> 10/08

    A regra da V1 prevê que escalas que cruzem a fronteira
    de competência sejam divididas. Por segurança, esta consulta
    NÃO encerra uma escala cujo fim esteja depois da competência.
    """

    competencia_inicio, competencia_fim = (
        calcular_competencia(
            data_referencia
        )
    )

    inicio = datetime.combine(
        competencia_inicio,
        time(0, 0)
    )

    fim_exclusivo = datetime.combine(
        competencia_fim + timedelta(days=1),
        time(0, 0)
    )

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                e.id_escala,
                e.id_usuario,
                u.nome,
                e.data_hora_inicio,
                e.data_hora_fim,
                e.encerrada
            FROM sobreaviso.escalas e

            INNER JOIN sobreaviso.usuarios u
                ON u.id_usuario = e.id_usuario

            WHERE e.encerrada = FALSE
              AND e.data_hora_fim >= %s
              AND e.data_hora_fim < %s

            ORDER BY
                e.data_hora_fim,
                e.id_escala;
        """, (
            inicio,
            fim_exclusivo
        ))

        linhas = cur.fetchall()

    escalas = [
        {
            "id_escala": linha[0],
            "id_usuario": linha[1],
            "nome_usuario": linha[2],
            "data_hora_inicio": linha[3],
            "data_hora_fim": linha[4],
            "encerrada": linha[5],
        }
        for linha in linhas
    ]

    return (
        competencia_inicio,
        competencia_fim,
        escalas
    )


# ============================================================
# EXECUÇÃO DO LOTE
# ============================================================

def executar_lote():
    """
    Para cada escala da competência:

      - se não houver acionamentos:
          encerrar_escala_sistema() gera todo o SOBREAVISO;

      - se houver acionamentos:
          encerrar_escala_sistema() preserva os ACIONAMENTOS
          e completa os intervalos restantes com SOBREAVISO.

    O motor permanece centralizado em executor.py.
    """

    config = buscar_configuracao_servico()

    if not config:
        raise ValueError(
            "Serviço Executor Automático não cadastrado."
        )

    (
        competencia_inicio,
        competencia_fim,
        escalas
    ) = buscar_escalas_para_encerrar(
        data_referencia=date.today()
    )

    print("=" * 70)

    print(
        f"COMPETÊNCIA: "
        f"{competencia_inicio:%d/%m/%Y} "
        f"até "
        f"{competencia_fim:%d/%m/%Y}"
    )

    print(
        f"ESCALAS PARA PROCESSAR: "
        f"{len(escalas)}"
    )

    print("=" * 70)

    sucesso = 0
    erros = 0

    for escala in escalas:

        try:

            resultado = encerrar_escala_sistema(
                id_escala=escala["id_escala"],
                data_hora_encerramento=(
                    escala["data_hora_fim"]
                )
            )

            mensagem = (
                f"Escala {escala['id_escala']} | "
                f"Usuário: "
                f"{escala['nome_usuario']} "
                f"(ID {escala['id_usuario']}) | "
                f"Período: "
                f"{escala['data_hora_inicio']:%d/%m/%Y %H:%M} "
                f"até "
                f"{escala['data_hora_fim']:%d/%m/%Y %H:%M} | "
                f"Encerrada automaticamente com sucesso."
            )

            gravar_log(
                id_servico=config["id"],
                nome_servico=config["nome"],
                status="SUCESSO",
                mensagem=mensagem
            )

            sucesso += 1

            print(
                f"SUCESSO | "
                f"ESCALA {escala['id_escala']} | "
                f"{escala['nome_usuario']}"
            )

        except Exception as erro:

            mensagem = (
                f"Escala {escala['id_escala']} | "
                f"Usuário: "
                f"{escala['nome_usuario']} "
                f"(ID {escala['id_usuario']}) | "
                f"Erro: {erro}"
            )

            try:
                gravar_log(
                    id_servico=config["id"],
                    nome_servico=config["nome"],
                    status="ERRO",
                    mensagem=mensagem
                )

            except Exception as erro_log:
                print(
                    f"ERRO AO GRAVAR LOG | "
                    f"ESCALA "
                    f"{escala['id_escala']} | "
                    f"{erro_log}"
                )

            erros += 1

            print(
                f"ERRO | "
                f"ESCALA {escala['id_escala']} | "
                f"{escala['nome_usuario']} | "
                f"{erro}"
            )

    # Só considera o lote concluído quando terminou
    # de percorrer todas as escalas.
    mensagem_final = (
        f"LOTE FINALIZADO | "
        f"Competência: "
        f"{competencia_inicio:%d/%m/%Y} a "
        f"{competencia_fim:%d/%m/%Y} | "
        f"Escalas encontradas: {len(escalas)} | "
        f"Sucesso: {sucesso} | "
        f"Erros: {erros}"
    )

    # Se houve erro em alguma escala, o lote é registrado
    # como erro para facilitar acompanhamento.
    status_final = (
        "SUCESSO"
        if erros == 0
        else "ERRO"
    )

    gravar_log(
        id_servico=config["id"],
        nome_servico=config["nome"],
        status=status_final,
        mensagem=mensagem_final
    )

    print(mensagem_final)

    return {
        "competencia_inicio": competencia_inicio,
        "competencia_fim": competencia_fim,
        "quantidade": len(escalas),
        "sucesso": sucesso,
        "erros": erros,
    }


# ============================================================
# REPLICADOR DE ESCALAS (INDEPENDENTE DO EXECUTOR)
# ============================================================

NOME_REPLICADOR = "Replicador de Escalas"


def buscar_configuracao_replicador():
    """Lê configuração independente na tabela configuracao_servicos."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, nome, periodicidade, dia, hora, ativo
            FROM sobreaviso.configuracao_servicos
            WHERE LOWER(nome) = LOWER(%s)
            LIMIT 1
        """, (NOME_REPLICADOR,))
        linha = cur.fetchone()
    if not linha:
        return None
    return dict(zip(("id", "nome", "periodicidade", "dia", "hora", "ativo"), linha))


def replicador_ja_verificado_hoje(id_servico, agora):
    """Evita verificações repetidas no mesmo dia, sem bloquear o mês inteiro."""
    inicio_dia = datetime.combine(agora.date(), time.min)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM sobreaviso.logs_servicos
                WHERE id_servico = %s AND status = 'SUCESSO'
                  AND mensagem LIKE 'REPLICADOR FINALIZADO%%'
                  AND data_hora_execucao >= %s
            )
        """, (id_servico, inicio_dia))
        return bool(cur.fetchone()[0])


def deve_executar_replicador(config, agora=None):
    """Verifica diariamente após o horário configurado.

    A configuração MENSAL permanece compatível, mas o calendário de criação
    é decidido pelo replicador; o serviço apenas verifica uma vez por dia.
    """
    agora = agora or datetime.now()
    if not config or not config['ativo']:
        return False
    if str(config['periodicidade']).upper().strip() != 'MENSAL':
        raise ValueError("Configure 'Replicador de Escalas' com periodicidade MENSAL.")
    horario = config['hora'] or time(8, 0)
    if isinstance(horario, str):
        horario = time.fromisoformat(horario)
    if agora.time() < horario:
        return False
    return not replicador_ja_verificado_hoje(config['id'], agora)


def executar_replicador(config):
    """Executa o replicador, exibindo cada escala em tempo real no console.

    Linhas CRIADA representam INSERTs pendentes até a confirmação do COMMIT.
    """
    caminho = Path(__file__).resolve().parent / "replicador_escala.py"
    if not caminho.is_file():
        raise FileNotFoundError(f"Replicador não encontrado: {caminho}")

    print(f"[{datetime.now():%d/%m/%Y %H:%M:%S}] [REPLICADOR] Iniciando aplicação", flush=True)
    proc = subprocess.Popen(
        [sys.executable, "-u", str(caminho), "--aplicar"],
        cwd=str(caminho.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    linhas = []

    def acompanhar_saida():
        for linha in proc.stdout:
            linha = linha.rstrip("\r\n")
            linhas.append(linha)
            print(f"[{datetime.now():%d/%m/%Y %H:%M:%S}] [REPLICADOR] {linha}", flush=True)

    leitor = threading.Thread(target=acompanhar_saida, daemon=True)
    leitor.start()
    try:
        retorno = proc.wait(timeout=600)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        leitor.join(timeout=5)
        mensagem = "REPLICADOR FALHOU | tempo limite de 600 segundos excedido"
        gravar_log(config["id"], config["nome"], "ERRO", mensagem)
        raise RuntimeError(mensagem)

    leitor.join(timeout=5)
    # O script confirma a transação com esta mensagem, após conn.commit().
    commit_confirmado = any(linha.strip().startswith("COMMIT CONCLUÍDO") for linha in linhas)
    sucesso = retorno == 0 and commit_confirmado
    criadas = sum("| CRIADA #" in linha for linha in linhas)
    mensagem = (
        ("REPLICADOR FINALIZADO" if sucesso else "REPLICADOR FALHOU")
        + f" | retorno={retorno} | escalas_inseridas={criadas}"
        + f" | commit={'SIM' if commit_confirmado else 'NÃO'}"
        + " | saída_final=" + " / ".join(linhas[-8:])[-1800:]
    )
    gravar_log(config["id"], config["nome"], "SUCESSO" if sucesso else "ERRO", mensagem)
    print(f"[{datetime.now():%d/%m/%Y %H:%M:%S}] [REPLICADOR] {mensagem}", flush=True)
    if not sucesso:
        raise RuntimeError(mensagem)


# ============================================================
# LOOP DO SERVIÇO
# ============================================================

def iniciar_servico():
    """
    Processo contínuo para instalação como serviço no servidor.
    """

    print("=" * 70)
    print("SERVIÇO EXECUTOR AUTOMÁTICO - SOBREAVISO")
    print("=" * 70)

    while True:

        try:

            config = buscar_configuracao_servico()

            if not config:

                print(
                    f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                    f"Configuração do serviço não encontrada."
                )

            elif not config["ativo"]:

                print(
                    f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                    f"Serviço inativo."
                )

            elif deve_executar(config):

                print(
                    f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                    f"Iniciando Executor Automático."
                )

                executar_lote()

                print(
                    f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                    f"Executor Automático finalizado."
                )

            # Agendamento separado: não depende de o Executor rodar.
            config_replicador = buscar_configuracao_replicador()
            if config_replicador and deve_executar_replicador(config_replicador):
                print(f"[{datetime.now():%d/%m/%Y %H:%M:%S}] Iniciando replicador.")
                executar_replicador(config_replicador)

        except Exception as erro:

            print(
                f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
                f"Erro no loop do serviço: {erro}"
            )

        time_module.sleep(
            INTERVALO_VERIFICACAO_SEGUNDOS
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    iniciar_servico()