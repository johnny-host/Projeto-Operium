"""SQLite com a mesma interface de listas/dicionários usada pelos menus."""
from contextlib import closing
from pathlib import Path
import json
import sqlite3

PASTA = Path(__file__).resolve().parent
ARQUIVO = PASTA / "dados" / "operium.db"
ESQUEMA = PASTA / "schema.sql"


def dados_vazios():
    return {"versao": 1, "admins": [], "funcionarios": [], "regras": []}


def conectar(caminho):
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def json_texto(valor):
    return json.dumps(valor, ensure_ascii=False, allow_nan=False)


def inserir(conexao, tabela, valores):
    # Nomes de tabelas/colunas vêm somente do código; valores usam parâmetros.
    colunas = ', '.join(valores)
    marcadores = ', '.join('?' for _ in valores)
    return conexao.execute(f"INSERT INTO {tabela} ({colunas}) VALUES ({marcadores})", list(valores.values()))


def conferir_banco(conexao):
    if conexao.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise ValueError("Versão do banco não reconhecida. O arquivo foi preservado.")
    if conexao.execute("PRAGMA quick_check").fetchone()[0] != 'ok':
        raise ValueError("O banco apresentou falha de integridade.")
    if conexao.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValueError("O banco contém referências inválidas.")


def gravar_registros(conexao, dados):
    # A transação substitui o retrato em memória sem deixar gravação pela metade.
    for tabela in ('ajustes_escala', 'jornadas', 'marcacoes', 'escalas', 'contratos', 'funcionarios', 'administradores', 'regras'):
        conexao.execute(f"DELETE FROM {tabela}")
    for admin in dados['admins']:
        inserir(conexao, 'administradores', {'usuario': admin['usuario'], 'senha': json_texto(admin['senha'])})
    for funcionario in dados['funcionarios']:
        campos = {chave: funcionario[chave] for chave in ('id', 'nome', 'cpf', 'data_nascimento', 'status')}
        campos['senha'] = json_texto(funcionario['senha']) if funcionario.get('senha') else None
        inserir(conexao, 'funcionarios', campos)
        inserir(conexao, 'contratos', {'funcionario_id': funcionario['id'], **funcionario['contrato']})
        for escala in funcionario.get('escalas', []):
            campos = {chave: escala[chave] for chave in ('inicio', 'fim', 'tipo', 'empresa', 'categoria', 'carga_semanal')}
            configuracao = {chave: escala[chave] for chave in ('dias', 'turno') if chave in escala}
            campos.update(funcionario_id=funcionario['id'], configuracao=json_texto(configuracao))
            escala_id = inserir(conexao, 'escalas', campos).lastrowid
            for ajuste in escala.get('ajustes', []):
                campos = dict(ajuste, escala_id=escala_id, turno=json_texto(ajuste['turno']))
                inserir(conexao, 'ajustes_escala', campos)
        for jornada in funcionario.get('jornadas', []):
            inserir(conexao, 'jornadas', {'funcionario_id': funcionario['id'], **jornada})
        for marcacao in funcionario.get('marcacoes', []):
            inserir(conexao, 'marcacoes', {'funcionario_id': funcionario['id'], **marcacao})
    for regra in dados['regras']:
        campos = {chave: regra[chave] for chave in ('versao', 'empresa', 'categoria', 'inicio', 'fim', 'fonte')}
        parametros = {chave: valor for chave, valor in regra.items() if chave not in campos}
        campos['parametros'] = json_texto(parametros)
        inserir(conexao, 'regras', campos)


def salvar_dados(dados, caminho=ARQUIVO):
    if dados.get('versao') != 1:
        raise ValueError('Versão dos dados não reconhecida.')
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    novo = not caminho.exists()
    if novo and caminho.with_suffix('.db.bak').exists():
        raise ValueError('Banco ausente, mas existe backup. Restaure antes de continuar.')
    try:
        with closing(conectar(caminho)) as conexao:
            if novo:
                conexao.executescript(ESQUEMA.read_text(encoding='utf-8-sig'))
            else:
                conferir_banco(conexao)
                with closing(sqlite3.connect(caminho.with_suffix('.db.bak'))) as backup:
                    conexao.backup(backup)
                # Bancos criados antes da Fase 4 ganham a tabela de marcações (IF NOT EXISTS).
                conexao.executescript(ESQUEMA.read_text(encoding='utf-8-sig'))
            with conexao:  # commit ao terminar; rollback se ocorrer erro.
                gravar_registros(conexao, dados)
    except Exception:
        if novo and caminho.exists():
            caminho.unlink()  # Só remove o banco novo incompleto, nunca um banco anterior.
        raise


def carregar_dados(caminho=ARQUIVO):
    caminho = Path(caminho)
    if not caminho.exists():
        if caminho.with_suffix('.db.bak').exists():
            raise ValueError('Banco ausente, mas existe backup. Restaure antes de continuar.')
        antigo = caminho.with_suffix('.pkl')
        if antigo.exists() and antigo != caminho:
            from migracao import migrar_pickle
            migrar_pickle(antigo, caminho)
            return carregar_dados(caminho)
        if caminho.with_suffix('.bak').exists():
            raise ValueError('Existe um backup antigo sem banco principal. Confira os arquivos antes de continuar.')
        return dados_vazios()
    dados = dados_vazios()
    with closing(conectar(caminho)) as conexao:
        conferir_banco(conexao)
        tem_marcacoes = conexao.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'marcacoes'").fetchone()
        for linha in conexao.execute('SELECT * FROM administradores ORDER BY rowid'):
            dados['admins'].append({'usuario': linha['usuario'], 'senha': json.loads(linha['senha'])})
        for linha in conexao.execute('SELECT * FROM funcionarios ORDER BY id'):
            funcionario = dict(linha)
            if funcionario['senha'] is None:
                del funcionario['senha']
            else:
                funcionario['senha'] = json.loads(funcionario['senha'])
            contrato = conexao.execute('SELECT * FROM contratos WHERE funcionario_id = ?', (funcionario['id'],)).fetchone()
            if contrato is None:
                raise ValueError('Funcionário sem contrato no banco.')
            funcionario['contrato'] = dict(contrato)
            del funcionario['contrato']['funcionario_id']
            for linha_escala in conexao.execute('SELECT * FROM escalas WHERE funcionario_id = ? ORDER BY id', (funcionario['id'],)):
                escala = dict(linha_escala)
                escala_id = escala.pop('id')
                del escala['funcionario_id']
                escala.update(json.loads(escala.pop('configuracao')))
                for linha_ajuste in conexao.execute('SELECT * FROM ajustes_escala WHERE escala_id = ? ORDER BY id', (escala_id,)):
                    ajuste = dict(linha_ajuste)
                    del ajuste['id'], ajuste['escala_id']
                    ajuste['turno'] = json.loads(ajuste['turno'])
                    escala.setdefault('ajustes', []).append(ajuste)
                funcionario.setdefault('escalas', []).append(escala)
            for linha_jornada in conexao.execute('SELECT * FROM jornadas WHERE funcionario_id = ? ORDER BY id', (funcionario['id'],)):
                jornada = dict(linha_jornada)
                del jornada['id'], jornada['funcionario_id']
                funcionario.setdefault('jornadas', []).append(jornada)
            if tem_marcacoes:
                for linha_marcacao in conexao.execute('SELECT * FROM marcacoes WHERE funcionario_id = ? ORDER BY id', (funcionario['id'],)):
                    marcacao = dict(linha_marcacao)
                    del marcacao['id'], marcacao['funcionario_id']
                    funcionario.setdefault('marcacoes', []).append(marcacao)
            dados['funcionarios'].append(funcionario)
        for linha in conexao.execute('SELECT * FROM regras ORDER BY versao'):
            regra = dict(linha)
            regra.update(json.loads(regra.pop('parametros')))
            dados['regras'].append(regra)
    return dados
