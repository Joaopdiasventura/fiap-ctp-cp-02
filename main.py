from persistencia import ArmazenamentoTarefas
from tarefas import GerenciadorTarefas
from interface import executar_menu


def main() -> None:
    armazenamento = ArmazenamentoTarefas("dados")
    gerenciador = GerenciadorTarefas(armazenamento)
    executar_menu(gerenciador)


if __name__ == "__main__":
    main()
