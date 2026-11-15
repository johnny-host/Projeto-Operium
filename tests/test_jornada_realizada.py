from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from test_fase3 import funcionario_exemplo
from registros_jornada import criar_registro, validar_registro, registrar_jornada
from jornada import minutos_trabalhados
from armazenamento import salvar_dados, carregar_dados, dados_vazios
import main as app


class JornadaRealizadaTest(TestCase):
    def test_diurna_noturna_e_sem_intervalo(self):
        for horarios, esperado in [(('08:00','17:00','12:00','13:00'),480),
                                   (('22:00','06:00','01:00','02:00'),420),
                                   (('20:00','04:00','23:30','00:30'),420),
                                   (('08:00','12:00','',''),240)]:
            self.assertEqual(minutos_trabalhados(criar_registro('26/10/2026', *horarios)), esperado)

    def test_horarios_e_intervalos_invalidos(self):
        for horarios in [('25:00','17:00','',''), ('08:00','08:00','',''),
                         ('08:00','17:00','13:00','12:00'), ('22:00','06:00','07:00','08:00'),
                         ('08:00','17:00','12:00','')]:
            with self.assertRaises(ValueError):
                criar_registro('26/10/2026', *horarios)

    def test_admissao_futuro_inativo_e_sobreposicao(self):
        f = funcionario_exemplo()
        for data in ['01/01/2025', '01/01/2999']:
            with self.assertRaises(ValueError):
                validar_registro(f, criar_registro(data,'08:00','12:00'))
        f['status'] = 'inativo'
        with self.assertRaises(ValueError):
            validar_registro(f, criar_registro('26/10/2026','08:00','12:00'))
        f['status'] = 'ativo'
        f['jornadas'] = [criar_registro('26/10/2026','22:00','06:00')]
        with self.assertRaises(ValueError):
            validar_registro(f, criar_registro('27/10/2026','05:00','12:00'))
        validar_registro(f, criar_registro('27/10/2026','06:00','12:00'))

    def test_confirmacao_cancelamento_e_correcao_sem_duplicar(self):
        f = funcionario_exemplo()
        entradas = ['1','26/10/2026','08:00','17:00','s','12:00','13:00','','s']
        with patch('builtins.input', side_effect=entradas), redirect_stdout(StringIO()):
            self.assertTrue(registrar_jornada([f]))
        with patch('builtins.input', side_effect=['1','26/10/2026','n']), redirect_stdout(StringIO()):
            self.assertFalse(registrar_jornada([f]))
        entradas = ['1','26/10/2026','s','08:00','12:00','n','Correção','s']
        with patch('builtins.input', side_effect=entradas), redirect_stdout(StringIO()):
            self.assertTrue(registrar_jornada([f]))
        self.assertEqual(len(f['jornadas']), 1)
        self.assertEqual(minutos_trabalhados(f['jornadas'][0]),240)
        entradas = ['1','27/10/2026','08:00','12:00','n','','n']
        with patch('builtins.input', side_effect=entradas), redirect_stdout(StringIO()):
            self.assertFalse(registrar_jornada([f]))
        self.assertEqual(len(f['jornadas']),1)

    def test_menu_salva_e_reabre(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'teste.db'
            dados = dados_vazios()
            dados['funcionarios'] = [funcionario_exemplo()]
            entradas = ['14','1','26/10/2026','08:00','12:00','n','','s','6']
            with patch.object(app, 'dados', dados), patch.object(app,'funcionarios',dados['funcionarios']), \
                 patch.object(app,'salvar_dados',side_effect=lambda d: salvar_dados(d,caminho)), \
                 patch('builtins.input',side_effect=entradas), redirect_stdout(StringIO()):
                app.menu_sistema({'usuario':'teste'})
            f = carregar_dados(caminho)['funcionarios'][0]
            self.assertEqual(minutos_trabalhados(f['jornadas'][0]),240)

    def test_funcionario_consulta_somente_proprio_registro(self):
        f = funcionario_exemplo()
        with patch('builtins.input',side_effect=['5','4']), patch.object(app,'mostrar_jornadas') as consulta, redirect_stdout(StringIO()):
            app.menu_funcionario(f)
        consulta.assert_called_once_with(f)
