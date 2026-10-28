# ⏱️ Sobreaviso Automate

### Sistema de Gestão de Escalas, Acionamentos e Automação de Sobreaviso

**Python | PostgreSQL | Streamlit | Automação de Processos | Gestão Operacional | Relatórios PDF e Excel**

---

## 📋 1. Apresentação

O **Sobreaviso Automate** é uma aplicação desenvolvida em Python para centralizar, automatizar e gerenciar processos relacionados ao controle de escalas de sobreaviso, acionamentos de profissionais, períodos de competência e geração de relatórios operacionais.

O projeto foi concebido para atender operações corporativas que necessitam organizar a disponibilidade de colaboradores fora do horário regular de trabalho, controlar períodos de sobreaviso e registrar os acionamentos realizados durante essas escalas.

A solução integra uma interface administrativa desenvolvida em **Streamlit**, um banco de dados relacional **PostgreSQL** e serviços automatizados responsáveis pela execução de rotinas periódicas, encerramento de escalas e envio de comunicações por e-mail.

O sistema contempla diferentes níveis de acesso, permitindo que administradores, gestores e técnicos interajam com as funcionalidades de acordo com suas responsabilidades.

### Objetivo principal

Disponibilizar uma plataforma centralizada para gerenciamento do processo de sobreaviso, reduzindo atividades manuais e proporcionando maior organização, padronização e rastreabilidade das informações.

### Objetivos específicos

- Centralizar o cadastro de empresas, departamentos e colaboradores.
- Organizar escalas de sobreaviso.
- Registrar períodos de disponibilidade e acionamentos.
- Aplicar regras de acesso conforme o perfil do usuário.
- Automatizar processos recorrentes.
- Permitir a replicação de escalas.
- Gerar relatórios em PDF e Excel.
- Disponibilizar informações para acompanhamento operacional.
- Automatizar o envio de documentos por e-mail.
- Manter registros das execuções realizadas pelos serviços.

---

# 🏗️ 2. Arquitetura da Solução

O Sobreaviso Automate utiliza uma arquitetura modular, separando as responsabilidades de interface, autenticação, regras de negócio, persistência e serviços automatizados.

Essa organização permite que os componentes sejam mantidos e evoluídos de forma independente.

## 2.1 Visão arquitetural

```text
                    SOBREAVISO AUTOMATE
                            │
                            ▼
                ┌──────────────────────┐
                │   INTERFACE WEB      │
                │      STREAMLIT       │
                └──────────┬───────────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
   ┌────────────┐   ┌────────────┐   ┌────────────┐
   │  USUÁRIOS  │   │   ESCALAS  │   │ RELATÓRIOS │
   │            │   │            │   │            │
   │ Cadastros  │   │ Sobreaviso │   │    PDF     │
   │ Permissões │   │ Acionamento│   │   Excel    │
   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │  REGRAS DE NEGÓCIO   │
                │                      │
                │ Cadastros            │
                │ Autenticação         │
                │ Permissões           │
                │ Gestão de escalas    │
                │ Processamento        │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │      POSTGRESQL      │
                │                      │
                │ Schema: sobreaviso   │
                │                      │
                │ Usuários             │
                │ Empresas             │
                │ Departamentos        │
                │ Escalas              │
                │ Lançamentos          │
                │ Configurações        │
                │ Logs                 │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ SERVIÇOS AUTOMÁTICOS │
                │                      │
                │ Executor             │
                │ Replicador           │
                │ Serviço de e-mail    │
                └──────────────────────┘
```

## 2.2 Camadas da aplicação

| Camada | Responsabilidade |
|---|---|
| Apresentação | Interface administrativa desenvolvida em Streamlit. |
| Autenticação | Identificação de usuários e validação de credenciais. |
| Autorização | Controle de permissões conforme perfil e hierarquia. |
| Regras de negócio | Gestão de escalas, acionamentos e competências. |
| Persistência | Consultas e operações no PostgreSQL. |
| Automação | Execução periódica de processos operacionais. |
| Relatórios | Geração de documentos PDF e Excel. |
| Comunicação | Configuração SMTP e envio de e-mails. |

---

# 👥 3. Gestão de Usuários e Controle de Acesso

O sistema contempla um módulo de autenticação e gerenciamento de usuários.

A aplicação utiliza informações armazenadas no PostgreSQL para identificar os colaboradores e determinar suas permissões.

## 3.1 Autenticação

**Arquivo:** `autenticacao.py`

O processo de autenticação utiliza:

- Login do usuário.
- Senha.
- Situação ativa ou inativa.
- Perfil de acesso.
- Departamento vinculado.

A validação de senha é realizada por meio da função armazenada no PostgreSQL:

```sql
sobreaviso.validar_senha
```

Após a autenticação, as informações necessárias à navegação são disponibilizadas à aplicação.

## 3.2 Perfis de acesso

O sistema contempla três perfis principais.

| Perfil | Responsabilidades |
|---|---|
| ADMIN | Administração geral e acesso aos recursos autorizados do sistema. |
| GESTOR | Gerenciamento de informações relacionadas à sua hierarquia de colaboradores. |
| TECNICO | Acesso às informações e operações permitidas para o próprio usuário. |

As permissões são verificadas tanto na interface quanto em componentes específicos das regras de negócio.

## 3.3 Hierarquia de colaboradores

O sistema utiliza relacionamentos entre gestores e subordinados.

A identificação dos subordinados pode ser realizada por consultas recursivas no PostgreSQL, permitindo percorrer diferentes níveis hierárquicos.

Exemplo da estrutura utilizada:

```sql
WITH RECURSIVE subordinados AS (
    SELECT id_usuario
    FROM sobreaviso.usuarios
    WHERE id_gestor = %s
      AND ativo = TRUE

    UNION

    SELECT u.id_usuario
    FROM sobreaviso.usuarios u
    INNER JOIN subordinados s
        ON u.id_gestor = s.id_usuario
    WHERE u.ativo = TRUE
)
SELECT id_usuario
FROM subordinados;
```

Essa abordagem permite implementar regras de acesso baseadas na estrutura organizacional.

## 3.4 Controle de alterações

O módulo `escalas_permissoes.py` implementa verificações para alterações de escalas.

Entre as restrições estão:

- Validação do perfil autenticado.
- Verificação de acesso ao colaborador.
- Restrições sobre escalas encerradas.
- Restrições para alterações em escalas já iniciadas.
- Validação do intervalo de datas.
- Verificação de acionamentos existentes.

Essas regras ajudam a preservar a consistência das informações registradas.

---

# 🏢 4. Gestão Organizacional

O Sobreaviso Automate possui recursos para representar a estrutura organizacional das empresas.

## 4.1 Cadastro de empresas

O sistema permite cadastrar e administrar empresas.

Entre as informações utilizadas estão:

- Identificação da empresa.
- Nome.
- Configuração relacionada a banco de horas.
- Situação ativa ou inativa.

Os dados são armazenados na tabela:

```sql
sobreaviso.empresas
```

## 4.2 Cadastro de departamentos

**Arquivo:** `front_departamentos.py`

A aplicação permite administrar departamentos e seus respectivos relacionamentos.

O cadastro contempla operações de:

- Inclusão.
- Consulta.
- Alteração.
- Exclusão.
- Associação de gestores.

O módulo também considera a estrutura organizacional utilizada para determinar permissões de acesso.

## 4.3 Cadastro de colaboradores

**Arquivo:** `front_usuarios.py`

A interface de usuários contempla funcionalidades relacionadas a:

- Cadastro de colaboradores.
- Alteração de informações cadastrais.
- Associação a departamentos.
- Identificação de gestores.
- Definição de perfis.
- Ativação e desativação.
- Alteração de senha.
- Administração de relacionamentos organizacionais.

O gerenciamento centralizado facilita a manutenção das informações utilizadas pelas escalas e pelos relatórios.

---

# 📅 5. Gestão de Escalas de Sobreaviso

A gestão de escalas constitui uma das funcionalidades centrais do projeto.

**Arquivo principal da interface:** `front_escalas.py`

O módulo permite organizar os períodos em que determinados colaboradores permanecem disponíveis para eventuais acionamentos.

## 5.1 Estrutura das escalas

Uma escala pode conter informações como:

| Informação | Descrição |
|---|---|
| Colaborador | Profissional responsável pelo período. |
| Data de início | Início da disponibilidade. |
| Data de término | Encerramento previsto. |
| Ordem | Posição do colaborador no rodízio. |
| Replicação | Indicação utilizada pelas rotinas de replicação. |
| Situação | Identificação de escalas encerradas. |

## 5.2 Funcionalidades

O módulo contempla:

- Cadastro de escalas.
- Consulta das escalas existentes.
- Alteração de períodos.
- Exclusão de registros conforme regras aplicáveis.
- Visualização do histórico.
- Organização por departamentos.
- Controle de acesso por usuário.
- Identificação da ordem de participação.

## 5.3 Validações

O sistema implementa verificações para evitar alterações inconsistentes.

Exemplos:

**Validação cronológica**

A data de término deve ser posterior à data de início.

**Restrições por perfil**

Usuários técnicos possuem permissões mais restritas que gestores e administradores.

**Proteção de períodos encerrados**

Escalas encerradas possuem restrições de alteração.

**Preservação de acionamentos**

O sistema verifica se existem acionamentos incompatíveis com uma alteração de período.

Essas regras contribuem para a integridade do histórico operacional.

---

# 🔄 6. Replicação Automática de Escalas

**Arquivo:** `replicador_escala.py`

O projeto possui um componente específico para replicação de escalas.

A finalidade é facilitar a continuidade dos rodízios de sobreaviso, utilizando o histórico de participação dos colaboradores.

## 6.1 Funcionamento

O replicador consulta as escalas existentes e identifica os departamentos elegíveis para geração de novos períodos.

O processamento considera informações como:

- Departamento.
- Histórico das escalas.
- Ordem de participação.
- Situação dos colaboradores.
- Data de início e término.
- Última escala registrada.

## 6.2 Rodízio de colaboradores

O algoritmo utiliza a ordem histórica de participação para identificar os próximos colaboradores.

A implementação considera posições de rodízio de 1 a 4 e valida a consistência da sequência cadastrada.

Também contempla situações em que determinados colaboradores foram desativados.

## 6.3 Simulação antes da execução

O replicador possui um mecanismo de segurança operacional.

Por padrão, sua execução funciona em modo de simulação.

```bash
python replicador_escala.py
```

Para aplicar as alterações:

```bash
python replicador_escala.py --aplicar
```

Essa separação permite visualizar o planejamento antes de efetivar a geração de escalas.

## 6.4 Critérios operacionais

A implementação considera departamentos com início de escala nos últimos 30 dias e cuja última escala já tenha terminado.

A projeção utiliza um horizonte definido pelo algoritmo, alcançando a última segunda-feira do mês seguinte.

A rotina também utiliza transações para efetivar as alterações quando executada em modo de aplicação.

---

# 📞 7. Controle de Acionamentos

O sistema diferencia períodos de sobreaviso dos acionamentos efetivamente realizados.

Essa distinção permite registrar tanto a disponibilidade do colaborador quanto os intervalos em que houve necessidade de atendimento.

## 7.1 Tipos de lançamento

O módulo de execução utiliza os seguintes tipos:

```python
TIPO_SOBREAVISO = "SOBREAVISO"
TIPO_ACIONAMENTO = "ACIONAMENTO"
```

**Sobreaviso**

Representa o período de disponibilidade do colaborador.

**Acionamento**

Representa um intervalo de atendimento realizado durante a operação.

## 7.2 Informações dos lançamentos

Os registros podem conter:

- Tipo de lançamento.
- Data e hora de início.
- Data e hora de término.
- Motivo.
- Escala relacionada.
- Competência.
- Colaborador responsável.

## 7.3 Cálculo de duração

O sistema utiliza funções para calcular a duração dos períodos.

Exemplo:

```python
def calcular_minutos(inicio, fim):
    if fim <= inicio:
        return 0

    return int(
        (fim - inicio).total_seconds() // 60
    )
```

Os resultados podem ser formatados em horas e minutos para apresentação nos relatórios.

---

# 📆 8. Controle de Competências

O Sobreaviso Automate utiliza períodos de competência para organizar os lançamentos.

A regra implementada considera o intervalo entre:

**Dia 11 do mês anterior e dia 10 do mês de referência.**

### Exemplo

Para uma competência de agosto de 2026:

| Informação | Data |
|---|---|
| Início | 11/07/2026 |
| Término | 10/08/2026 |

Essa regra é utilizada pelos componentes de processamento e geração de relatórios.

O sistema também contempla consultas aos lançamentos vinculados às competências, permitindo selecionar os registros correspondentes ao período desejado.

---

# ⚙️ 9. Executor de Escalas

**Arquivo:** `executor.py`

O executor contém regras relacionadas ao processamento operacional das escalas.

Entre suas responsabilidades estão:

- Consulta de escalas.
- Validação dos colaboradores associados.
- Verificação de permissões.
- Tratamento de competências.
- Cálculo de períodos.
- Processamento de lançamentos.
- Encerramento de escalas.

A separação dessas operações em um módulo específico evita concentrar toda a lógica de negócio na interface Streamlit.

---

# 🤖 10. Serviço de Execução Automática

**Arquivo:** `servico_executor.py`

O sistema possui um serviço responsável por verificar periodicamente a necessidade de executar rotinas operacionais.

## 10.1 Configuração

As configurações são consultadas no PostgreSQL:

```sql
sobreaviso.configuracao_servicos
```

O serviço utiliza a identificação:

```python
NOME_SERVICO = "Executor Automático"
```

## 10.2 Periodicidade

A implementação contempla quatro modalidades:

| Periodicidade | Intervalo |
|---|---|
| DIARIO | 1 dia |
| SEMANAL | 7 dias |
| MENSAL | 30 dias |
| ANUAL | 365 dias |

Os intervalos são utilizados para determinar quando uma nova execução pode ocorrer.

Na implementação atual, as periodicidades mensal e anual correspondem, respectivamente, a intervalos fixos de 30 e 365 dias.

## 10.3 Controle de execução

O serviço consulta o histórico de execuções para determinar se existe necessidade de iniciar um novo processamento.

A implementação utiliza registros de conclusão do lote, evitando considerar uma execução parcial como processamento integralmente finalizado.

## 10.4 Verificação periódica

O intervalo configurado para verificação é de:

```python
INTERVALO_VERIFICACAO_SEGUNDOS = 1200
```

Equivalente a 20 minutos.

Esse intervalo representa a frequência de verificação do serviço, não necessariamente a frequência de execução das rotinas.

## 10.5 Registro de logs

As informações são registradas na tabela:

```sql
sobreaviso.logs_servicos
```

O histórico permite acompanhar as execuções realizadas e seus respectivos resultados.

---

# ✉️ 11. Automação de E-mails

O Sobreaviso Automate possui um módulo para envio automatizado de comunicações.

Os principais componentes são:

```text
configurador_email.py
servico_email.py
front_config_email.py
```

## 11.1 Configuração SMTP

A aplicação permite cadastrar configurações de envio por empresa.

Entre os parâmetros estão:

- Servidor SMTP.
- Porta.
- Usuário.
- Senha.
- Utilização de TLS.
- Utilização de SSL.
- Endereço do remetente.
- Nome do remetente.
- Situação ativa ou inativa.

As configurações são armazenadas na tabela:

```sql
sobreaviso.configuracao_email
```

## 11.2 Teste de conexão

O módulo administrativo disponibiliza uma operação de teste de envio SMTP.

Esse recurso permite validar a configuração antes de utilizar o serviço automatizado.

## 11.3 Serviço automático

**Arquivo:** `servico_email.py`

O serviço consulta sua configuração operacional e verifica a necessidade de realizar novos envios.

A implementação contempla:

- Consulta da configuração.
- Verificação da periodicidade.
- Identificação da última execução.
- Preparação dos documentos.
- Envio por SMTP.
- Registro dos resultados.

## 11.4 Periodicidade

O serviço utiliza os seguintes intervalos:

```text
DIARIO  → 1 dia
SEMANAL → 7 dias
MENSAL  → 30 dias
ANUAL   → 365 dias
```

A verificação periódica ocorre conforme a configuração:

```python
INTERVALO_VERIFICACAO_SEGUNDOS = 7200
```

Equivalente a duas horas.

## 11.5 Segurança das credenciais

As credenciais SMTP são informações sensíveis.

Em ambientes corporativos, recomenda-se:

- Restringir o acesso às configurações.
- Proteger as credenciais armazenadas.
- Utilizar conexões seguras.
- Evitar exposição de senhas em logs.
- Utilizar contas específicas para automação.
- Aplicar políticas de rotação de credenciais.

---

# 📄 12. Relatórios PDF

**Arquivo:** `extrator_pdf.py`

O projeto contempla a geração de relatórios em PDF utilizando a biblioteca ReportLab.

Os documentos são produzidos a partir das informações registradas no PostgreSQL.

## 12.1 Informações utilizadas

O processo consulta dados relacionados a:

- Colaborador.
- Identificação funcional.
- Departamento.
- Escala.
- Competência.
- Lançamentos.
- Tipo de ocorrência.
- Período de início e término.
- Motivo do acionamento.

## 12.2 Geração dos documentos

A implementação utiliza recursos de formatação, como:

- Tabelas.
- Estilos de texto.
- Alinhamentos.
- Espaçamento.
- Configuração de páginas.
- Formatação de datas.

A biblioteca ReportLab permite gerar documentos estruturados para consulta, arquivamento e distribuição.

## 12.3 Controle de acesso

A interface de extração utiliza funções específicas para consultar os usuários e períodos autorizados.

Essa abordagem permite restringir a geração de relatórios conforme as permissões aplicáveis.

---

# 📊 13. Relatórios Excel

**Arquivo:** `extrator_excel.py`

Além dos relatórios PDF, o sistema disponibiliza a geração de documentos Excel.

A finalidade é permitir que os registros de sobreaviso e acionamento sejam utilizados em análises, conferências e processos administrativos.

## 13.1 Informações disponibilizadas

Os relatórios são construídos a partir de consultas ao PostgreSQL.

Entre as informações consideradas estão:

- Colaborador.
- Departamento.
- Período de competência.
- Escalas.
- Lançamentos.
- Datas e horários.
- Tipo de ocorrência.

## 13.2 Aplicações

Os documentos podem apoiar:

- Conferência de períodos.
- Validação de lançamentos.
- Análise operacional.
- Consolidação administrativa.
- Preparação de informações para processos internos.

A geração de relatórios em diferentes formatos permite atender necessidades distintas de consulta e utilização dos dados.

---

# 🖥️ 14. Interface Web com Streamlit

A aplicação utiliza Streamlit para disponibilizar uma interface administrativa acessível pelo navegador.

## 14.1 Tela principal

**Arquivo:** `front_main.py`

A tela principal contempla:

- Identificação do sistema.
- Autenticação.
- Controle de sessão.
- Navegação entre módulos.
- Recursos relacionados ao cadastro do usuário.

## 14.2 Módulos administrativos

| Arquivo | Funcionalidade |
|---|---|
| `front_main.py` | Interface principal e autenticação. |
| `front_usuarios.py` | Administração de usuários. |
| `front_departamentos.py` | Gerenciamento de departamentos. |
| `front_escalas.py` | Administração de escalas. |
| `front_extrator.py` | Geração de relatórios. |
| `front_config_email.py` | Configuração de envio SMTP. |

## 14.3 Experiência de utilização

A interface utiliza componentes visuais do Streamlit, incluindo:

- Formulários.
- Botões.
- Seletores.
- Mensagens de validação.
- Tabelas.
- Controles de navegação.
- Recursos de download.

O projeto também utiliza estilos CSS para personalizar a apresentação das páginas.

---

# 🗄️ 15. Banco de Dados PostgreSQL

O PostgreSQL é responsável pela persistência das informações utilizadas pelo sistema.

A aplicação utiliza o schema:

```sql
sobreaviso
```

## 15.1 Principais entidades

| Tabela | Responsabilidade |
|---|---|
| `sobreaviso.usuarios` | Cadastro de usuários e informações funcionais. |
| `sobreaviso.empresas` | Cadastro de empresas. |
| `sobreaviso.departamentos` | Estrutura organizacional. |
| `sobreaviso.escalas` | Períodos de sobreaviso. |
| `sobreaviso.escala_competencias` | Relacionamento entre escalas e competências. |
| `sobreaviso.lancamentos` | Registros de sobreaviso e acionamentos. |
| `sobreaviso.configuracao_servicos` | Configuração das rotinas automatizadas. |
| `sobreaviso.logs_servicos` | Histórico de execução dos serviços. |
| `sobreaviso.configuracao_email` | Configurações de comunicação SMTP. |

O projeto também utiliza funções e consultas SQL para autenticação, hierarquia de usuários e validação das operações.

## 15.2 Conexão com PostgreSQL

**Arquivo:** `inicio.py`

A conexão utiliza a biblioteca `psycopg` e variáveis de ambiente.

Exemplo:

```python
import os
import psycopg

from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
```

Essa abordagem permite separar as configurações de conexão do código-fonte.

---

# 🧰 16. Tecnologias Utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Desenvolvimento da aplicação e das rotinas automatizadas. |
| PostgreSQL | Persistência de dados e execução de consultas SQL. |
| psycopg | Integração entre Python e PostgreSQL. |
| Streamlit | Interface web administrativa. |
| ReportLab | Geração de documentos PDF. |
| openpyxl | Manipulação de planilhas Excel. |
| python-dotenv | Carregamento de variáveis de ambiente. |
| SMTP | Envio de comunicações por e-mail. |
| SSL/TLS | Segurança da comunicação com servidores SMTP. |
| subprocess | Execução de processos externos. |
| threading | Suporte a execução concorrente em componentes específicos. |
| SQL recursivo | Consulta de hierarquias organizacionais. |
| Git | Controle de versões. |

---

# 📂 17. Estrutura do Projeto

```text
Sobreaviso-Automate/
│
├── front_main.py
├── front_usuarios.py
├── front_departamentos.py
├── front_escalas.py
├── front_extrator.py
├── front_config_email.py
│
├── autenticacao.py
├── cadastros.py
├── escalas_permissoes.py
│
├── executor.py
├── servico_executor.py
├── servico_email.py
├── replicador_escala.py
│
├── extrator_pdf.py
├── extrator_excel.py
│
├── configurador_email.py
├── inicio.py
│
├── .gitignore
└── README.md
```

## Organização dos componentes

**Frontend**

Arquivos responsáveis pela interface Streamlit.

**Backend**

Módulos que implementam as regras de negócio e operações no banco de dados.

**Serviços**

Componentes responsáveis pela execução periódica de processos.

**Relatórios**

Módulos de geração de documentos PDF e Excel.

**Persistência**

Conexão e consultas ao PostgreSQL.

---

# 🚀 18. Instalação e Configuração

## 18.1 Pré-requisitos

Para executar o sistema, são necessários:

- Python instalado.
- PostgreSQL configurado.
- Banco de dados com o schema `sobreaviso`.
- Tabelas e funções utilizadas pela aplicação.
- Bibliotecas Python necessárias.
- Acesso aos diretórios utilizados pelos serviços.
- Servidor SMTP, caso o envio de e-mails seja utilizado.

## 18.2 Clonar o repositório

```bash
git clone https://github.com/felipenunescardoso/Sobreaviso-Automate.git

cd Sobreaviso-Automate
```

## 18.3 Criar ambiente virtual

No Windows:

```powershell
python -m venv .venv
```

Ativar:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 18.4 Instalar dependências

As principais dependências identificadas no projeto podem ser instaladas com:

```powershell
pip install streamlit "psycopg[binary]" python-dotenv reportlab openpyxl
```

Dependendo da configuração do ambiente, outras dependências podem ser necessárias.

Recomenda-se manter um arquivo `requirements.txt` com as versões utilizadas na implantação.

## 18.5 Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nome_do_banco
DB_USER=usuario
DB_PASSWORD=senha
```

Substitua os valores de exemplo pelas informações do ambiente.

**Importante:** o arquivo `.env` deve permanecer fora do controle de versão.

## 18.6 Preparar o banco de dados

A aplicação depende de tabelas, relacionamentos e funções existentes no schema `sobreaviso`.

O ambiente PostgreSQL deve estar preparado antes da inicialização.

O código-fonte disponibilizado não representa, isoladamente, um instalador completo do banco de dados.

## 18.7 Iniciar a interface

Execute:

```powershell
streamlit run front_main.py
```

Após a inicialização, o Streamlit apresentará o endereço de acesso no terminal.

## 18.8 Executar o replicador de escalas

Para simular:

```powershell
python replicador_escala.py
```

Para aplicar:

```powershell
python replicador_escala.py --aplicar
```

**Atenção:** o modo de aplicação realiza alterações no banco de dados. Recomenda-se validar a simulação antes de executá-lo.

## 18.9 Executar serviços

Os componentes de automação podem ser iniciados individualmente:

```powershell
python servico_executor.py
```

```powershell
python servico_email.py
```

As execuções dependem das configurações registradas no PostgreSQL.

---

# 🔐 19. Segurança e Integridade

O Sobreaviso Automate manipula informações funcionais e registros relacionados à disponibilidade de colaboradores.

Por isso, sua implantação deve considerar controles de segurança e integridade.

## 19.1 Autenticação

O sistema utiliza validação de credenciais por meio do PostgreSQL.

## 19.2 Autorização

As permissões consideram o perfil do usuário e os relacionamentos hierárquicos.

## 19.3 Integridade das escalas

As regras de negócio restringem alterações que possam comprometer o histórico de acionamentos.

## 19.4 Transações

Os módulos de persistência utilizam operações de confirmação e reversão de transações, conforme a rotina executada.

## 19.5 Proteção de credenciais

As credenciais do PostgreSQL devem ser armazenadas em variáveis de ambiente.

As configurações SMTP também devem receber proteção adequada.

## 19.6 Recomendações

- Utilizar conexões seguras.
- Restringir permissões de acesso ao banco.
- Proteger credenciais SMTP.
- Não publicar dados reais de colaboradores.
- Evitar exposição de informações pessoais em logs.
- Realizar backups periódicos.
- Manter o banco de dados atualizado.
- Revisar as permissões antes de disponibilizar o sistema externamente.
- Implementar testes automatizados para as regras de negócio.

---

# 📈 20. Benefícios da Solução

## Centralização das informações

Os registros de escalas, colaboradores e acionamentos são mantidos em uma estrutura centralizada.

## Redução de atividades manuais

A replicação de escalas e os serviços automáticos reduzem a necessidade de execução repetitiva de determinadas tarefas.

## Organização operacional

A aplicação permite estruturar a distribuição de períodos de sobreaviso entre colaboradores.

## Controle por hierarquia

Os gestores podem trabalhar com informações relacionadas à sua estrutura organizacional, respeitando as regras implementadas.

## Rastreabilidade

Os registros operacionais e logs permitem acompanhar as execuções realizadas.

## Padronização dos relatórios

A geração de documentos PDF e Excel facilita a apresentação das informações.

## Flexibilidade de configuração

As periodicidades e parâmetros operacionais podem ser administrados por meio do banco de dados e dos módulos correspondentes.

---

# 🧩 21. Diferenciais Técnicos

O Sobreaviso Automate demonstra a aplicação integrada de diferentes conceitos de desenvolvimento de software e automação.

### Arquitetura modular

Separação entre interface, regras de negócio, banco de dados e serviços.

### Controle de permissões

Aplicação de regras de acesso baseadas em perfis e hierarquias organizacionais.

### Consultas SQL recursivas

Utilização de CTEs recursivas para identificação de subordinados.

### Automação recorrente

Execução de rotinas com periodicidades configuráveis.

### Replicação de escalas

Algoritmo de continuidade de rodízios baseado no histórico de participação.

### Processamento transacional

Utilização de transações para preservar a consistência das alterações.

### Relatórios em múltiplos formatos

Geração de documentos PDF e Excel.

### Integração SMTP

Automação do envio de comunicações e documentos.

### Interface administrativa

Centralização das principais operações em uma aplicação web.

---

# 🔧 22. Evolução do Projeto

A arquitetura permite incorporar novas funcionalidades e melhorias.

Entre as possibilidades de evolução estão:

- Criação de dashboards gerenciais.
- Implementação de indicadores de sobreaviso.
- Ampliação dos controles de auditoria.
- Implementação de notificações em outros canais.
- Criação de APIs para integração com sistemas externos.
- Aprimoramento dos mecanismos de autenticação.
- Implementação de testes automatizados.
- Disponibilização de scripts de implantação.
- Containerização com Docker.
- Monitoramento centralizado dos serviços.
- Integração com sistemas de recursos humanos.
- Integração com soluções de Business Intelligence.

Essas funcionalidades representam possibilidades de evolução, não necessariamente recursos já implementados.

---

# 🎯 23. Aplicações

O Sobreaviso Automate pode ser utilizado como referência para soluções de gestão operacional em diferentes áreas.

Exemplos:

- Tecnologia da Informação.
- Infraestrutura.
- Suporte técnico.
- Operações industriais.
- Manutenção.
- Engenharia.
- Atendimento emergencial.
- Equipes com disponibilidade fora do expediente.

A utilização depende da adequação das regras de negócio às necessidades de cada organização.

---

# 👨‍💻 24. Desenvolvimento

**Desenvolvedor:** Felipe Nunes Cardoso

**Projeto:** Sobreaviso Automate

**Linguagem:** Python

**Banco de dados:** PostgreSQL

**Interface:** Streamlit

**Área de aplicação:** Automação de Processos e Gestão Operacional

O projeto reúne conhecimentos de:

- Desenvolvimento de aplicações Python.
- Modelagem de bancos de dados.
- SQL avançado.
- Consultas recursivas.
- Automação de processos.
- Gerenciamento de tarefas.
- Desenvolvimento de interfaces web.
- Controle de acesso.
- Integração SMTP.
- Geração automatizada de documentos.
- Organização de aplicações modulares.

---

# 📌 25. Considerações Finais

O **Sobreaviso Automate** é uma solução de automação desenvolvida para organizar e centralizar o gerenciamento de escalas de sobreaviso, acionamentos e processos administrativos relacionados.

Sua arquitetura combina uma interface web, regras de negócio, controle de acesso hierárquico, persistência relacional e serviços automatizados.

A utilização de Python, PostgreSQL e Streamlit permite integrar diferentes funcionalidades em uma única aplicação, mantendo uma estrutura modular e preparada para evolução.

O projeto demonstra a aplicação prática de conceitos de engenharia de software, automação operacional e gerenciamento de informações corporativas.

---

**Sobreaviso Automate — Gestão inteligente de escalas, acionamentos e processos operacionais.**
