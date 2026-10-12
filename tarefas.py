from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional


STATUS_VALIDOS = ("pendente", "em andamento", "concluida")
PRIORIDADES_VALIDAS = ("baixa", "media", "alta")
ROTULOS_STATUS = {
    "pendente": "pendente",
    "em andamento": "em andamento",
    "concluida": "concluída",
}
ROTULOS_PRIORIDADES = {
    "baixa": "baixa",
    "media": "média",
    "alta": "alta",
}


@dataclass
class Tarefa:
    id: int
    descricao: str
    vencimento: str
    status: str
    prioridade: str

    def para_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def de_dict(cls, dados: dict) -> "Tarefa":
        return cls(
            id=int(dados["id"]),
            descricao=str(dados["descricao"]),
            vencimento=str(dados["vencimento"]),
            status=str(dados["status"]),
            prioridade=str(dados["prioridade"]),
        )


def normalizar_status(status: str) -> str:
    texto = status.strip().lower()
    texto = texto.replace("í", "i")
    if texto not in STATUS_VALIDOS:
        raise ValueError("Status inválido. Use: pendente, em andamento ou concluída.")
    return texto


def normalizar_prioridade(prioridade: str) -> str:
    texto = prioridade.strip().lower()
    texto = texto.replace("é", "e")
    if texto not in PRIORIDADES_VALIDAS:
        raise ValueError("Prioridade inválida. Use: baixa, média ou alta.")
    return texto


def validar_descricao(descricao: str) -> str:
    texto = descricao.strip()
    if not texto:
        raise ValueError("A descrição não pode ficar vazia.")
    return texto


def validar_data(data: str) -> str:
    texto = data.strip()
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError as erro:
        raise ValueError("Data inválida. Use o formato DD/MM/AAAA.") from erro
    return texto


def formatar_status(status: str) -> str:
    return ROTULOS_STATUS.get(status, status)


def formatar_prioridade(prioridade: str) -> str:
    return ROTULOS_PRIORIDADES.get(prioridade, prioridade)


class GerenciadorTarefas:
    def __init__(self, armazenamento):
        self.armazenamento = armazenamento

    def cadastrar(self, descricao: str, vencimento: str, prioridade: str) -> Tarefa:
        tarefa = Tarefa(
            id=self.armazenamento.proximo_id(),
            descricao=validar_descricao(descricao),
            vencimento=validar_data(vencimento),
            status="pendente",
            prioridade=normalizar_prioridade(prioridade),
        )
        self.armazenamento.salvar_tarefa(tarefa)
        return tarefa

    def buscar_por_id(self, id_tarefa: int) -> Optional[Tarefa]:
        return self.armazenamento.buscar_tarefa(id_tarefa)

    def listar(self) -> list[Tarefa]:
        return self.armazenamento.listar_tarefas()

    def filtrar(self, status: str | None = None, vencimento: str | None = None) -> list[Tarefa]:
        tarefas = self.listar()

        if status:
            status_normalizado = normalizar_status(status)
            tarefas = [tarefa for tarefa in tarefas if tarefa.status == status_normalizado]

        if vencimento:
            data_normalizada = validar_data(vencimento)
            tarefas = [tarefa for tarefa in tarefas if tarefa.vencimento == data_normalizada]

        return tarefas

    def atualizar(
        self,
        id_tarefa: int,
        descricao: str | None = None,
        vencimento: str | None = None,
        prioridade: str | None = None,
        status: str | None = None,
    ) -> Optional[Tarefa]:
        tarefa = self.buscar_por_id(id_tarefa)
        if tarefa is None:
            return None

        if descricao is not None:
            tarefa.descricao = validar_descricao(descricao)
        if vencimento is not None:
            tarefa.vencimento = validar_data(vencimento)
        if prioridade is not None:
            tarefa.prioridade = normalizar_prioridade(prioridade)
        if status is not None:
            tarefa.status = normalizar_status(status)

        self.armazenamento.salvar_tarefa(tarefa)
        return tarefa

    def excluir(self, id_tarefa: int) -> bool:
        if self.buscar_por_id(id_tarefa) is None:
            return False
        self.armazenamento.excluir_tarefa(id_tarefa)
        return True
