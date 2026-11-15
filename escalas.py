"""Escalas planejadas por funcionário. Não representam registro de ponto."""
from datetime import datetime, timedelta
from funcionarios import selecionar_funcionario
from jornada import (
    DIAS_SEMANA, converter_data, duracao_turno, formatar_minutos, ler_periodo,
    ler_turno, minutos_horario, minutos_trabalhados, periodos_sobrepostos,
)
from regras import regra_vigente
from validacoes import confirmar, ler_validado, validar_data, validar_nome


def validar_escala(funcionario, escala):
    if funcionario["status"] != "ativo":
        raise ValueError("Reative o funcionário antes de cadastrar uma escala.")
    if converter_data(escala["inicio"]) < converter_data(funcionario["contrato"]["data_admissao"]):
        raise ValueError("A escala não pode começar antes da admissão.")
    if converter_data(escala["fim"]) < converter_data(escala["inicio"]):
        raise ValueError("O fim da escala não pode ser anterior ao início.")
    for outra in funcionario.get("escalas", []):
        if periodos_sobrepostos(escala["inicio"], escala["fim"], outra["inicio"], outra["fim"]):
            raise ValueError("Já existe uma escala neste período. Use um período livre.")
    if escala["tipo"] != "12x36":
        dias = escala["dias"]
        trabalhos = sum(dia["status"] == "trabalho" for dia in dias)
        esperado = {"5x2": 5, "6x1": 6}.get(escala["tipo"])
        if esperado is not None and trabalhos != esperado:
            raise ValueError(f"A jornada {escala['tipo']} precisa de {esperado} dias de trabalho por semana.")
        if trabalhos == 0:
            raise ValueError("Informe pelo menos um dia de trabalho.")
        if not any(dia["status"] == "dsr" for dia in dias):
            raise ValueError("Identifique pelo menos um dia de DSR no modelo semanal.")


def cadastrar_escala(funcionarios):
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is None:
        return
    if funcionario["status"] != "ativo":
        print("Reative o funcionário antes de cadastrar uma escala.")
        return
    tipo = funcionario["contrato"]["jornada"]
    print(f"Jornada: {tipo}. O período terá uma configuração própria.")
    inicio, fim = ler_periodo()
    escala = {
        "inicio": inicio, "fim": fim, "tipo": tipo,
        "empresa": ler_validado("Empresa das regras: ", validar_nome).casefold(),
        "categoria": ler_validado("Categoria das regras: ", validar_nome).casefold(),
        "carga_semanal": funcionario["contrato"]["carga"],
    }
    if tipo == "12x36":
        print("A data inicial será o primeiro plantão; os próximos começarão a cada 48 horas.")
        escala["turno"] = ler_turno(tipo)
    else:
        escala["dias"] = []
        for nome in DIAS_SEMANA:
            while True:
                opcao = input(f"{nome}: 1 - Trabalho, 2 - Folga, 3 - DSR: ").strip()
                if opcao in ("1", "2", "3"):
                    break
                print("Opção inválida.")
            if opcao == "1":
                dia = ler_turno(tipo)
            else:
                dia = {"status": "folga" if opcao == "2" else "dsr"}
            escala["dias"].append(dia)
    try:
        validar_escala(funcionario, escala)
    except ValueError as erro:
        print(erro)
        return
    mostrar_escala(escala)
    if confirmar("Salvar esta escala?"):
        funcionario.setdefault("escalas", []).append(escala)
        print("Escala cadastrada. Os períodos anteriores foram preservados.")


def mostrar_escala(escala):
    print(f"\n{escala['inicio']} a {escala['fim']} | {escala['tipo']} | {escala['empresa']} / {escala['categoria']}")
    dias = [escala["turno"]] if escala["tipo"] == "12x36" else escala["dias"]
    for indice, dia in enumerate(dias):
        nome = "Plantão a cada 48h" if escala["tipo"] == "12x36" else DIAS_SEMANA[indice]
        if dia["status"] == "trabalho":
            print(f"{nome}: {dia['entrada']} às {dia['saida']}, intervalo {dia['intervalo']} min; líquido {formatar_minutos(minutos_trabalhados(dia))}")
        else:
            print(f"{nome}: {dia['status']}")


def planejar_dia(funcionario, dia):
    for escala in funcionario.get("escalas", []):
        if converter_data(escala["inicio"]) <= dia <= converter_data(escala["fim"]):
            # O último ajuste da data prevalece; os anteriores continuam registrados.
            for ajuste in reversed(escala.get("ajustes", [])):
                if converter_data(ajuste["data"]) == dia:
                    return ajuste["turno"], escala
            if escala["tipo"] == "12x36":
                diferenca = (dia - converter_data(escala["inicio"])).days
                turno = escala["turno"] if diferenca % 2 == 0 else {"status": "descanso 12x36"}
            else:
                turno = escala["dias"][dia.weekday()]
            return turno, escala
    return {"status": "sem escala"}, None


def ajustar_dia(funcionarios):
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is None:
        return
    if funcionario["status"] != "ativo":
        print("Reative o funcionário antes de ajustar a escala.")
        return
    data = ler_validado("Data do ajuste (DD/MM/AAAA): ", validar_data)
    anterior, escala = planejar_dia(funcionario, converter_data(data))
    if escala is None:
        print("Cadastre uma escala para este período primeiro.")
        return
    print("Configuração atual:", anterior)
    opcao = input("1 - Trabalho, 2 - Folga, 3 - DSR, 0 - Cancelar: ").strip()
    if opcao == "0":
        return
    if opcao not in ("1", "2", "3"):
        print("Opção inválida.")
        return
    if opcao == "1":
        turno = ler_turno(escala["tipo"])
    else:
        turno = {"status": "folga" if opcao == "2" else "dsr"}
    turno["feriado"] = confirmar("Esta data é feriado na localidade?")
    motivo = ler_validado("Motivo do ajuste: ", validar_nome)
    print("Nova configuração:", turno)
    if confirmar("Salvar ajuste para esta data?"):
        escala.setdefault("ajustes", []).append({
            "data": data, "turno": turno, "motivo": motivo,
            "registrado_em": datetime.now().isoformat(timespec="seconds"),
        })
        print("Ajuste salvo; o padrão dos outros dias foi preservado.")


def gerar_planejamento(funcionario, inicio, fim):
    dia = converter_data(inicio)
    ultimo = converter_data(fim)
    if ultimo < dia or (ultimo - dia).days > 365:
        raise ValueError("Consulte de 1 a 366 dias.")
    linhas = []
    while dia <= ultimo:
        turno, escala = planejar_dia(funcionario, dia)
        linhas.append({"data": dia, "turno": turno, "escala": escala, "minutos": minutos_trabalhados(turno)})
        dia += timedelta(days=1)
    return linhas


def horarios_reais(dia, turno):
    inicio = datetime.combine(dia, datetime.min.time()) + timedelta(minutes=minutos_horario(turno["entrada"]))
    return inicio, inicio + timedelta(minutes=duracao_turno(turno["entrada"], turno["saida"]))


def alertas_planejamento(funcionario, linhas, regras):
    alertas = []
    # Inclui até sete dias anteriores para conferir descanso na borda da consulta.
    fim_anterior = None
    dsr_pendente = False
    for recuo in range(7, 0, -1):
        dia = linhas[0]["data"] - timedelta(days=recuo)
        turno, _ = planejar_dia(funcionario, dia)
        if turno["status"] == "trabalho":
            _, fim_anterior = horarios_reais(dia, turno)
            dsr_pendente = False
        elif turno["status"] == "dsr":
            dsr_pendente = True
    for linha in linhas:
        dia, turno, escala = linha["data"], linha["turno"], linha["escala"]
        data = dia.strftime("%d/%m/%Y")
        if escala is None:
            alertas.append(f"{data}: sem escala cadastrada.")
            continue
        regra = regra_vigente(regras, escala["empresa"], escala["categoria"], dia)
        if regra is None:
            alertas.append(f"{data}: sem regra vigente; limites não avaliados.")
        if turno["status"] == "dsr":
            dsr_pendente = True
        if turno["status"] != "trabalho":
            continue
        inicio, fim = horarios_reais(dia, turno)
        descanso = None if fim_anterior is None else (inicio - fim_anterior).total_seconds() / 3600
        if descanso is not None and descanso < 0:
            alertas.append(f"{data}: turnos sobrepostos.")
        if descanso is not None and escala["tipo"] == "12x36" and descanso < 36:
            alertas.append(f"{data}: descanso menor que 36h na transição para 12x36.")
        if regra:
            horas = linha["minutos"] / 60
            if horas > regra["limite_diario"]:
                alertas.append(f"{data}: jornada acima do limite diário da versão {regra['versao']}.")
            if horas > regra["limite_diario"] + regra["limite_extra"]:
                alertas.append(f"{data}: excedente diário acima do limite de horas extras configurado.")
            if horas > regra["intervalo_acima"] and turno["intervalo"] < regra["intervalo_minimo"]:
                alertas.append(f"{data}: intervalo menor que o configurado.")
            if descanso is not None and descanso < regra["descanso_minimo"]:
                alertas.append(f"{data}: descanso entre jornadas menor que o configurado.")
            if dsr_pendente and descanso is not None and descanso < regra["dsr_minimo"]:
                alertas.append(f"{data}: descanso contínuo do DSR menor que o configurado.")
        fim_anterior = fim
        dsr_pendente = False
    return alertas


def consultar_planejamento(funcionarios, regras):
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is None:
        return
    mostrar_planejamento(funcionario, regras)


def mostrar_planejamento(funcionario, regras):
    """Consulta somente o funcionário recebido, sem permitir selecionar outro ID."""
    inicio, fim = ler_periodo()
    linhas = gerar_planejamento(funcionario, inicio, fim)
    print("\nPREVISÃO — horas atribuídas à data de entrada do turno; não é ponto realizado.")
    if funcionario["status"] != "ativo":
        print("Funcionário inativo: consulta das escalas preservadas.")
    semanas = {}
    for linha in linhas:
        dia, turno = linha["data"], linha["turno"]
        horario = ""
        if turno["status"] == "trabalho":
            horario = f" {turno['entrada']}-{turno['saida']} (intervalo {turno['intervalo']} min)"
        if turno.get("feriado"):
            horario += " [feriado informado]"
        print(f"{dia:%d/%m/%Y} {DIAS_SEMANA[dia.weekday()]} | {turno['status']}{horario} | {formatar_minutos(linha['minutos'])}")
        segunda = dia - timedelta(days=dia.weekday())
        semanas.setdefault(segunda, []).append(linha)
    print("Total previsto:", formatar_minutos(sum(linha["minutos"] for linha in linhas)))
    for segunda, dias in semanas.items():
        total = sum(dia["minutos"] for dia in dias)
        completa = len(dias) == 7 and all(dia["escala"] for dia in dias)
        print(f"Semana de {segunda:%d/%m}: {formatar_minutos(total)} ({'completa' if completa else 'parcial; limites semanais não avaliados'})")
        if completa:
            cargas = {dia["escala"]["carga_semanal"] for dia in dias}
            carga = dias[0]["escala"]["carga_semanal"]
            if len(cargas) == 1 and abs(total / 60 - carga) > 0.01:
                print("  Atenção: total diferente da carga contratual; confira o ciclo e a compensação.")
            if all(dia["escala"]["tipo"] != "12x36" for dia in dias) and not any(dia["turno"]["status"] == "dsr" for dia in dias):
                print("  Atenção: semana sem DSR identificado após os ajustes.")
            versoes = []
            for dia in dias:
                escala = dia["escala"]
                regra = regra_vigente(regras, escala["empresa"], escala["categoria"], dia["data"])
                if regra is not None and regra not in versoes:
                    versoes.append(regra)
            for regra in versoes:
                if total / 60 > regra["limite_semanal"]:
                    print(f"  Atenção: total acima do limite semanal da versão {regra['versao']}; confira a vigência/compensação.")
    for alerta in alertas_planejamento(funcionario, linhas, regras):
        print("Atenção:", alerta)
    print("Alertas auxiliam a conferência; não certificam conformidade trabalhista.")
