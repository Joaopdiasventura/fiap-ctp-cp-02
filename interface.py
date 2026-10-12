from __future__ import annotations

from tarefas import (
    GerenciadorTarefas,
    PRIORIDADES_VALIDAS,
    STATUS_VALIDOS,
    Tarefa,
    formatar_prioridade,
    formatar_status,
)


def exibir_menu() -> None:
    print("\n" + "=" * 40)
    print("       GERENCIADOR DE TAREFAS")
    print("=" * 40)
    print("[1] Cadastrar tarefa")
    print("[2] Listar tarefas")
    print("[3] Buscar tarefa por ID")
    print("[4] Atualizar tarefa")
    print("[5] Excluir tarefa")
    print("[6] Filtrar tarefas")
    print("[7] Visualizar índice B-Tree")
    print("[0] Sair")
    print("=" * 40)


def executar_menu(gerenciador: GerenciadorTarefas) -> None:
    while True:
        exibir_menu()
        opcao = input("Escolha uma opção: ").strip()

        try:
            if opcao == "1":
                cadastrar_tarefa(gerenciador)
            elif opcao == "2":
                imprimir_tabela(gerenciador.listar())
            elif opcao == "3":
                buscar_tarefa(gerenciador)
            elif opcao == "4":
                atualizar_tarefa(gerenciador)
            elif opcao == "5":
                excluir_tarefa(gerenciador)
            elif opcao == "6":
                filtrar_tarefas(gerenciador)
            elif opcao == "7":
                visualizar_indice(gerenciador)
            elif opcao == "0":
                print("Programa encerrado. Até mais!")
                break
            else:
                print("Opção inválida. Tente novamente.")
        except ValueError as erro:
            print(f"Erro: {erro}")
        except OSError as erro:
            print(f"Erro ao acessar os arquivos: {erro}")


def cadastrar_tarefa(gerenciador: GerenciadorTarefas) -> None:
    descricao = input("Descrição: ")
    vencimento = input("Data de vencimento (DD/MM/AAAA): ")
    prioridade = escolher_opcao("Prioridade", PRIORIDADES_VALIDAS)
    tarefa = gerenciador.cadastrar(descricao, vencimento, prioridade)
    print(f"Tarefa cadastrada com sucesso. ID gerado: {tarefa.id}")


def buscar_tarefa(gerenciador: GerenciadorTarefas) -> None:
    id_tarefa = ler_id()
    tarefa = gerenciador.buscar_por_id(id_tarefa)
    if tarefa is None:
        print("Tarefa não encontrada.")
        return
    imprimir_tabela([tarefa])


def atualizar_tarefa(gerenciador: GerenciadorTarefas) -> None:
    id_tarefa = ler_id()
    tarefa = gerenciador.buscar_por_id(id_tarefa)
    if tarefa is None:
        print("Tarefa não encontrada.")
        return

    print("Pressione Enter para manter o valor atual.")
    descricao = input(f"Descrição [{tarefa.descricao}]: ").strip()
    vencimento = input(f"Vencimento [{tarefa.vencimento}]: ").strip()
    prioridade = input(
        f"Prioridade {formatar_opcoes(PRIORIDADES_VALIDAS)} [{formatar_prioridade(tarefa.prioridade)}]: "
    ).strip()
    status = input(f"Status {formatar_opcoes(STATUS_VALIDOS)} [{formatar_status(tarefa.status)}]: ").strip()

    atualizada = gerenciador.atualizar(
        id_tarefa,
        descricao=descricao or None,
        vencimento=vencimento or None,
        prioridade=prioridade or None,
        status=status or None,
    )
    print("Tarefa atualizada com sucesso.")
    imprimir_tabela([atualizada])


def excluir_tarefa(gerenciador: GerenciadorTarefas) -> None:
    id_tarefa = ler_id()
    tarefa = gerenciador.buscar_por_id(id_tarefa)
    if tarefa is None:
        print("Tarefa não encontrada.")
        return

    imprimir_tabela([tarefa])
    confirmacao = input("Confirmar exclusão? (s/n): ").strip().lower()
    if confirmacao != "s":
        print("Exclusão cancelada.")
        return

    gerenciador.excluir(id_tarefa)
    print("Tarefa excluída com sucesso.")


def filtrar_tarefas(gerenciador: GerenciadorTarefas) -> None:
    print("[1] Filtrar por status")
    print("[2] Filtrar por data de vencimento")
    print("[3] Filtrar por status e data")
    opcao = input("Escolha o filtro: ").strip()

    status = None
    vencimento = None
    if opcao in ("1", "3"):
        status = escolher_opcao("Status", STATUS_VALIDOS)
    if opcao in ("2", "3"):
        vencimento = input("Data de vencimento (DD/MM/AAAA): ")
    if opcao not in ("1", "2", "3"):
        print("Filtro inválido.")
        return

    imprimir_tabela(gerenciador.filtrar(status=status, vencimento=vencimento))


def visualizar_indice(gerenciador: GerenciadorTarefas) -> None:
    indice = gerenciador.armazenamento.indice
    print("\nÍndice B-Tree atual:")
    print(indice.visualizar())
    print("\nEstatísticas:")
    print(f"- Altura: {indice.altura()}")
    print(f"- Nós: {indice.quantidade_nos()}")
    print(f"- Chaves: {indice.total_chaves()}")
    print(f"- Divisões realizadas: {indice.divisoes}")


def escolher_opcao(rotulo: str, opcoes: tuple[str, ...]) -> str:
    while True:
        print(f"{rotulo}:")
        for indice, opcao in enumerate(opcoes, start=1):
            print(f"[{indice}] {formatar_opcao(opcao)}")
        escolha = input("Escolha: ").strip()
        escolha_normalizada = escolha.lower().replace("é", "e").replace("í", "i")
        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            return opcoes[int(escolha) - 1]
        if escolha_normalizada in opcoes:
            return escolha_normalizada
        print("Opção inválida. Tente novamente.")


def formatar_opcao(opcao: str) -> str:
    if opcao in STATUS_VALIDOS:
        return formatar_status(opcao)
    if opcao in PRIORIDADES_VALIDAS:
        return formatar_prioridade(opcao)
    return opcao


def formatar_opcoes(opcoes: tuple[str, ...]) -> str:
    return "(" + ", ".join(formatar_opcao(opcao) for opcao in opcoes) + ")"


def ler_id() -> int:
    texto = input("ID da tarefa: ").strip()
    if not texto.isdigit():
        raise ValueError("Informe um ID numérico.")
    return int(texto)


def imprimir_tabela(tarefas: list[Tarefa]) -> None:
    if not tarefas:
        print("Nenhuma tarefa encontrada.")
        return

    larguras = {
        "id": max(4, max(len(str(tarefa.id)) for tarefa in tarefas)),
        "descricao": max(20, max(len(tarefa.descricao) for tarefa in tarefas)),
        "vencimento": 10,
        "status": max(12, max(len(tarefa.status) for tarefa in tarefas)),
        "prioridade": 10,
    }

    linha = (
        f"+-{'-' * larguras['id']}-+-{'-' * larguras['descricao']}-+-"
        f"{'-' * larguras['vencimento']}-+-{'-' * larguras['status']}-+-"
        f"{'-' * larguras['prioridade']}-+"
    )
    cabecalho = (
        f"| {'ID'.ljust(larguras['id'])} | {'Descrição'.ljust(larguras['descricao'])} | "
        f"{'Vencimento'.ljust(larguras['vencimento'])} | {'Status'.ljust(larguras['status'])} | "
        f"{'Prioridade'.ljust(larguras['prioridade'])} |"
    )

    print(linha)
    print(cabecalho)
    print(linha)
    for tarefa in tarefas:
        print(
            f"| {str(tarefa.id).ljust(larguras['id'])} | "
            f"{tarefa.descricao.ljust(larguras['descricao'])} | "
            f"{tarefa.vencimento.ljust(larguras['vencimento'])} | "
            f"{formatar_status(tarefa.status).ljust(larguras['status'])} | "
            f"{formatar_prioridade(tarefa.prioridade).ljust(larguras['prioridade'])} |"
        )
    print(linha)
