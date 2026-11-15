"""Execute: python -B -m unittest discover -s tests -v"""
from contextlib import redirect_stdout
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import sqlite3

import main as app
import ponto
from armazenamento import carregar_dados, dados_vazios, salvar_dados
from jornada import criar_turno
from ponto import (
    apurar_dia, apurar_periodo, bater_ponto, criar_marcacao, montar_turnos,
    registrar_marcacao, registrar_marcacao_manual, tipos_permitidos,
)
from senhas import proteger_senha
from test_fase3 import escala_exemplo, funcionario_exemplo, regra_exemplo

AGORA = datetime(2026, 11, 10, 12, 0)
TERCA = date(2026, 10, 27)  # escala_exemplo: 08:00-17:00, intervalo de 60 min


def marcar(funcionario, *itens, origem="ponto"):
    """itens: (data, hora, tipo). Usa AGORA como relógio de referência."""
    for data, hora, tipo in itens:
        observacao = "Teste" if origem == "manual" else ""
        registrar_marcacao(funcionario, criar_marcacao(tipo, data, hora, origem, observacao), AGORA)


def dia_completo(funcionario, data, h1, h2, h3, h4):
    marcar(funcionario, (data, h1, "entrada"), (data, h2, "saida_intervalo"),
           (data, h3, "volta_intervalo"), (data, h4, "saida"))


class PontoBase(TestCase):
    def setUp(self):
        self.f = funcionario_exemplo()
        self.f["escalas"] = [escala_exemplo()]
        self.regras = [regra_exemplo()]

    def apurar(self, dia=TERCA):
        return apurar_dia(self.f, dia, self.regras, AGORA)


class MarcacaoTest(PontoBase):
    def test_sequencia_e_tipos_permitidos(self):
        hoje = datetime(2026, 10, 27, 18, 0)
        self.assertEqual(tipos_permitidos(self.f, hoje), ("entrada",))
        marcar(self.f, ("27/10/2026", "08:00", "entrada"))
        self.assertEqual(tipos_permitidos(self.f, hoje), ("saida_intervalo", "saida"))
        marcar(self.f, ("27/10/2026", "12:00", "saida_intervalo"))
        self.assertEqual(tipos_permitidos(self.f, hoje), ("volta_intervalo",))
        marcar(self.f, ("27/10/2026", "13:00", "volta_intervalo"), ("27/10/2026", "17:00", "saida"))
        self.assertEqual(tipos_permitidos(self.f, hoje), ("entrada",))

    def test_marcacoes_invalidas(self):
        casos = [
            ("saida", "27/10/2026", "17:00"),   # sem entrada
            ("entrada", "31/02/2026", "08:00"),  # data inexistente
            ("entrada", "27/10/2026", "25:00"),  # hora inexistente
            ("entrada", "11/11/2026", "08:00"),  # futuro
            ("entrada", "31/12/2025", "08:00"),  # antes da admissão
        ]
        for tipo, data, hora in casos:
            with self.assertRaises(ValueError, msg=(tipo, data, hora)):
                registrar_marcacao(self.f, criar_marcacao(tipo, data, hora), AGORA)
        self.assertNotIn("marcacoes", self.f)

    def test_duplicidade_manual_sem_motivo_e_inativo(self):
        marcar(self.f, ("27/10/2026", "08:00", "entrada"))
        with self.assertRaises(ValueError):
            marcar(self.f, ("27/10/2026", "08:00", "saida"))
        with self.assertRaises(ValueError):
            registrar_marcacao(self.f, criar_marcacao("saida", "27/10/2026", "17:00", "manual", ""), AGORA)
        self.f["status"] = "inativo"
        with self.assertRaises(ValueError):
            marcar(self.f, ("27/10/2026", "17:00", "saida"))

    def test_correcao_fora_de_ordem_mantem_sequencia_valida(self):
        marcar(self.f, ("27/10/2026", "08:00", "entrada"), ("27/10/2026", "17:00", "saida"))
        with self.assertRaises(ValueError):  # volta sem saída para intervalo
            marcar(self.f, ("27/10/2026", "13:00", "volta_intervalo"), origem="manual")
        marcar(self.f, ("27/10/2026", "12:00", "saida_intervalo"), origem="manual")
        self.assertIn("Intervalo iniciado sem retorno registrado", self.apurar()["ocorrencias"])
        with self.assertRaises(ValueError):  # só cabe a volta depois da saída para intervalo
            marcar(self.f, ("27/10/2026", "16:00", "saida_intervalo"), origem="manual")
        marcar(self.f, ("27/10/2026", "13:00", "volta_intervalo"), origem="manual")
        self.assertEqual(self.apurar()["trabalhado_min"], 480)

    def test_turno_esquecido_libera_nova_entrada(self):
        marcar(self.f, ("26/10/2026", "08:00", "entrada"))
        self.assertEqual(tipos_permitidos(self.f, datetime(2026, 10, 26, 20, 0)), ("saida_intervalo", "saida"))
        self.assertEqual(tipos_permitidos(self.f, datetime(2026, 10, 27, 8, 0)), ("entrada",))
        marcar(self.f, ("27/10/2026", "08:00", "entrada"))
        turnos = montar_turnos(self.f["marcacoes"], AGORA)
        self.assertIn("Turno sem saída registrada", turnos[0]["ocorrencias"])


class ApuracaoTest(PontoBase):
    def test_dia_normal_dentro_da_tolerancia(self):
        dia_completo(self.f, "27/10/2026", "08:02", "12:00", "13:00", "17:01")
        r = self.apurar()
        self.assertEqual((r["trabalhado_min"], r["previsto_min"], r["intervalo_min"]), (479, 480, 60))
        self.assertEqual((r["diferenca_min"], r["extra_min"], r["debito_min"]), (-1, 0, 0))
        self.assertEqual(r["ocorrencias"], [])
        self.assertFalse(r["incompleto"])

    def test_atraso_saida_antecipada_e_intervalo_curto(self):
        dia_completo(self.f, "27/10/2026", "08:20", "12:00", "12:30", "16:30")
        r = self.apurar()
        texto = " | ".join(r["ocorrencias"])
        self.assertIn("Atraso de 20 min", texto)
        self.assertIn("Saída antecipada de 30 min", texto)
        self.assertIn("Intervalo de 30 min, menor que o configurado", texto)
        self.assertEqual(r["trabalhado_min"], 460)
        self.assertEqual(r["debito_min"], 20)

    def test_hora_extra_e_limites_da_regra(self):
        dia_completo(self.f, "27/10/2026", "08:00", "12:00", "13:00", "19:30")
        r = self.apurar()
        self.assertEqual(r["extra_min"], 150)
        texto = " | ".join(r["ocorrencias"])
        self.assertIn("Saída 150 min após o previsto", texto)
        self.assertIn("Jornada acima do limite diário", texto)
        self.assertIn("Excedente diário acima do limite", texto)

    def test_ausencia_somente_em_dia_passado_de_trabalho(self):
        r = self.apurar(date(2026, 10, 28))
        self.assertIn("Sem marcação em dia de trabalho previsto", r["ocorrencias"][0])
        self.assertEqual(r["debito_min"], 480)
        self.assertEqual(self.apurar(date(2026, 11, 7))["ocorrencias"], [])    # folga
        self.assertEqual(self.apurar(date(2026, 11, 11))["ocorrencias"], [])   # futuro/sem escala
        self.assertEqual(self.apurar(date(2025, 1, 1))["ocorrencias"], [])     # antes da escala/admissão

    def test_marcacao_em_dsr(self):
        marcar(self.f, ("01/11/2026", "08:00", "entrada"), ("01/11/2026", "12:00", "saida"))
        r = self.apurar(date(2026, 11, 1))
        self.assertIn("Marcação em dia sem trabalho previsto (dsr)", r["ocorrencias"])
        self.assertEqual(r["extra_min"], 240)

    def test_turno_em_andamento_e_intervalo_sem_retorno(self):
        marcar(self.f, ("10/11/2026", "08:00", "entrada"))
        self.f["escalas"][0].update(inicio="09/11/2026", fim="22/11/2026")
        r = self.apurar(date(2026, 11, 10))
        self.assertTrue(r["incompleto"])
        self.assertIsNone(r["diferenca_min"])
        self.assertIn("Turno em andamento", r["ocorrencias"][0])
        marcar(self.f, ("26/10/2026", "08:00", "entrada"), ("26/10/2026", "12:00", "saida_intervalo"))
        antigo = self.apurar(date(2026, 10, 26))["ocorrencias"]  # esquecido: nova entrada veio 15 dias depois
        self.assertIn("Turno sem saída registrada", antigo)
        self.assertIn("Intervalo iniciado sem retorno registrado", antigo)

    def test_turno_noturno_pertence_a_data_da_entrada(self):
        self.f["escalas"][0]["dias"][1] = criar_turno("22:00", "06:00", 60)
        marcar(self.f, ("27/10/2026", "22:00", "entrada"), ("28/10/2026", "01:00", "saida_intervalo"),
               ("28/10/2026", "02:00", "volta_intervalo"), ("28/10/2026", "06:00", "saida"))
        r = self.apurar()
        self.assertEqual((r["trabalhado_min"], r["previsto_min"], r["ocorrencias"]), (420, 420, []))
        self.assertIn("(28/10)", ponto.formatar_marcacoes(r))
        quarta = self.apurar(date(2026, 10, 28))
        self.assertEqual(quarta["trabalhado_min"], 0)
        self.assertIn("Sem marcação", quarta["ocorrencias"][0])

    def test_descanso_entre_jornadas(self):
        self.f["escalas"][0]["dias"][1] = criar_turno("16:00", "23:00", 0)
        self.f["escalas"][0]["dias"][2] = criar_turno("06:00", "17:00", 0)
        marcar(self.f, ("27/10/2026", "16:00", "entrada"), ("27/10/2026", "23:00", "saida"),
               ("28/10/2026", "06:00", "entrada"), ("28/10/2026", "17:00", "saida"))
        self.assertTrue(any("Descanso de 7.0 h" in o for o in self.apurar(date(2026, 10, 28))["ocorrencias"]))

    def test_sem_regra_vigente_e_periodo(self):
        dia_completo(self.f, "27/10/2026", "08:00", "12:00", "13:00", "17:00")
        r = apurar_dia(self.f, TERCA, [], AGORA)
        self.assertEqual(r["ocorrencias"], ["Sem regra vigente; limites não avaliados."])
        resumo = apurar_periodo(self.f, "26/10/2026", "01/11/2026", self.regras, AGORA)
        self.assertEqual(len(resumo["dias"]), 7)
        self.assertEqual(resumo["trabalhado_min"], 480)
        self.assertEqual(resumo["debito_min"], 480 * 4)  # quatro dias úteis sem marcação
        with self.assertRaises(ValueError):
            apurar_periodo(self.f, "02/11/2026", "01/11/2026", self.regras, AGORA)


class MenusTest(PontoBase):
    def test_bater_ponto_confirma_cancela_e_bloqueia_repeticao(self):
        agora = datetime(2026, 10, 27, 8, 0, 30)
        with patch("builtins.input", side_effect=["n"]), redirect_stdout(StringIO()):
            self.assertFalse(bater_ponto(self.f, agora))
        self.assertNotIn("marcacoes", self.f)
        with patch("builtins.input", side_effect=["s"]), redirect_stdout(StringIO()):
            self.assertTrue(bater_ponto(self.f, agora))
        self.assertEqual(self.f["marcacoes"][0]["hora"], "08:00")
        self.assertEqual(self.f["marcacoes"][0]["origem"], "ponto")
        with patch("builtins.input", side_effect=["2", "s"]), redirect_stdout(StringIO()):  # mesma hora: saída
            self.assertFalse(bater_ponto(self.f, agora))
        self.assertEqual(len(self.f["marcacoes"]), 1)

    def test_marcacao_manual_exige_motivo_e_confirmacao(self):
        entradas = ["1", "27/10/2026", "08:00", "1", "Esqueceu de marcar", "s"]
        with patch("builtins.input", side_effect=entradas), redirect_stdout(StringIO()):
            self.assertTrue(registrar_marcacao_manual([self.f], AGORA))
        self.assertEqual(self.f["marcacoes"][0]["observacao"], "Esqueceu de marcar")
        self.assertEqual(self.f["marcacoes"][0]["origem"], "manual")
        entradas = ["1", "27/10/2026", "17:00", "4", "Teste", "n"]
        with patch("builtins.input", side_effect=entradas), redirect_stdout(StringIO()):
            self.assertFalse(registrar_marcacao_manual([self.f], AGORA))
        self.assertEqual(len(self.f["marcacoes"]), 1)

    def test_menus_do_funcionario_e_do_admin_salvam(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "teste.db"
            dados = dados_vazios()
            dados["funcionarios"] = [self.f]
            salvar_dados(dados, arquivo)
            with patch.object(app, "dados", dados), patch.object(app, "funcionarios", dados["funcionarios"]), \
                 patch.object(app, "salvar_dados", side_effect=lambda d: salvar_dados(d, arquivo)), \
                 patch("ponto.datetime") as relogio, redirect_stdout(StringIO()):
                relogio.now.return_value = datetime(2026, 11, 10, 8, 0)
                relogio.strptime.side_effect = datetime.strptime
                relogio.combine.side_effect = datetime.combine
                with patch("builtins.input", side_effect=["6", "s", "4"]):
                    app.menu_funcionario(self.f)
            recuperado = carregar_dados(arquivo)["funcionarios"][0]
            self.assertEqual(recuperado["marcacoes"][0]["tipo"], "entrada")

    def test_consulta_do_funcionario_e_do_admin_mostram_apuracao(self):
        dia_completo(self.f, "27/10/2026", "08:30", "12:00", "13:00", "17:00")
        for chamada in (lambda: ponto.mostrar_ponto(self.f, self.regras, AGORA),
                        lambda: ponto.consultar_ponto([self.f], self.regras)):
            saida = StringIO()
            entradas = ["26/10/2026", "01/11/2026"] if "mostrar" in chamada.__code__.co_names else ["1", "26/10/2026", "01/11/2026"]
            with patch("builtins.input", side_effect=entradas), redirect_stdout(saida):
                chamada()
            self.assertIn("Atraso de 30 min", saida.getvalue())
            self.assertIn("não é folha nem banco de horas", saida.getvalue())


class PersistenciaPontoTest(PontoBase):
    def test_salvar_e_reabrir_com_marcacoes(self):
        dia_completo(self.f, "27/10/2026", "08:00", "12:00", "13:00", "17:00")
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "dados.db"
            dados = dados_vazios()
            dados["admins"] = [{"usuario": "gestor", "senha": proteger_senha("admin1234")}]
            dados["funcionarios"] = [self.f]
            salvar_dados(dados, arquivo)
            self.assertEqual(carregar_dados(arquivo), dados)
            marcacao = dict(self.f["marcacoes"][0], tipo="invalido")
            self.f["marcacoes"].append(marcacao)
            with self.assertRaises(sqlite3.IntegrityError):
                salvar_dados(dados, arquivo)
            self.f["marcacoes"].pop()
            self.assertEqual(len(carregar_dados(arquivo)["funcionarios"][0]["marcacoes"]), 4)

    def test_banco_anterior_a_fase4_recebe_a_tabela(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "dados.db"
            dados = dados_vazios()
            dados["funcionarios"] = [self.f]
            salvar_dados(dados, arquivo)
            con = sqlite3.connect(arquivo)
            con.execute("DROP TABLE marcacoes")
            con.commit()
            con.close()
            self.assertNotIn("marcacoes", carregar_dados(arquivo)["funcionarios"][0])
            dia_completo(self.f, "27/10/2026", "08:00", "12:00", "13:00", "17:00")
            salvar_dados(dados, arquivo)
            self.assertEqual(carregar_dados(arquivo), dados)
