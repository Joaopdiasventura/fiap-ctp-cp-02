from __future__ import annotations

import os
import pickle
import struct
from pathlib import Path
from typing import Optional

from btree import BTree
from tarefas import Tarefa


class ArmazenamentoTarefas:
    """Mini armazenamento binário append-only com índice B-Tree."""

    def __init__(self, pasta_dados: str | Path = "dados"):
        self.pasta_dados = Path(pasta_dados)
        self.arquivo_tarefas = self.pasta_dados / "tarefas.dat"
        self.arquivo_indice = self.pasta_dados / "indice.dat"
        self.indice = BTree(grau_minimo=2)
        self.offsets_ativos: dict[int, int] = {}
        self.maior_id_registrado = 0

        self.pasta_dados.mkdir(parents=True, exist_ok=True)
        self.arquivo_tarefas.touch(exist_ok=True)
        self.carregar()

    def carregar(self) -> None:
        self.offsets_ativos = {}
        self.maior_id_registrado = 0

        for offset, registro in self._iterar_registros():
            id_tarefa = int(registro["id"])
            self.maior_id_registrado = max(self.maior_id_registrado, id_tarefa)
            if registro["tipo"] == "upsert":
                self.offsets_ativos[id_tarefa] = offset
            elif registro["tipo"] == "delete":
                self.offsets_ativos.pop(id_tarefa, None)

        if not self._carregar_indice_salvo():
            self.reconstruir_indice()
        else:
            ids_indice = [chave for chave, _ in self.indice.percurso_ordenado()]
            if ids_indice != sorted(self.offsets_ativos):
                self.reconstruir_indice()

    def proximo_id(self) -> int:
        return self.maior_id_registrado + 1

    def salvar_tarefa(self, tarefa: Tarefa) -> int:
        offset = self._gravar_registro({"tipo": "upsert", "id": tarefa.id, "tarefa": tarefa.para_dict()})
        self.offsets_ativos[tarefa.id] = offset
        self.maior_id_registrado = max(self.maior_id_registrado, tarefa.id)
        self.indice.inserir(tarefa.id, offset)
        self.salvar_indice()
        return offset

    def buscar_tarefa(self, id_tarefa: int) -> Optional[Tarefa]:
        offset = self.indice.buscar(id_tarefa)
        if offset is None:
            return None
        registro = self._ler_registro_offset(offset)
        if registro is None or registro.get("tipo") != "upsert":
            return None
        if int(registro["id"]) not in self.offsets_ativos:
            return None
        return Tarefa.de_dict(registro["tarefa"])

    def listar_tarefas(self) -> list[Tarefa]:
        tarefas = []
        for id_tarefa, offset in sorted(self.offsets_ativos.items()):
            registro = self._ler_registro_offset(offset)
            if registro and registro.get("tipo") == "upsert":
                tarefas.append(Tarefa.de_dict(registro["tarefa"]))
        return tarefas

    def excluir_tarefa(self, id_tarefa: int) -> None:
        if id_tarefa not in self.offsets_ativos:
            return
        self._gravar_registro({"tipo": "delete", "id": id_tarefa})
        self.offsets_ativos.pop(id_tarefa, None)
        self.reconstruir_indice()
        self.salvar_indice()

    def reconstruir_indice(self) -> None:
        self.indice.reconstruir(self.offsets_ativos)

    def salvar_indice(self) -> None:
        temporario = self.arquivo_indice.with_suffix(".tmp")
        dados = {
            "grau_minimo": self.indice.t,
            "pares": self.indice.percurso_ordenado(),
            "maior_id_registrado": self.maior_id_registrado,
        }
        with temporario.open("wb") as arquivo:
            pickle.dump(dados, arquivo)
        os.replace(temporario, self.arquivo_indice)

    def _carregar_indice_salvo(self) -> bool:
        if not self.arquivo_indice.exists() or self.arquivo_indice.stat().st_size == 0:
            return False
        try:
            with self.arquivo_indice.open("rb") as arquivo:
                dados = pickle.load(arquivo)
            self.indice = BTree(grau_minimo=int(dados.get("grau_minimo", 2)))
            self.indice.reconstruir(list(dados.get("pares", [])))
            return True
        except (OSError, pickle.PickleError, EOFError, ValueError, TypeError):
            return False

    def _gravar_registro(self, registro: dict) -> int:
        payload = pickle.dumps(registro)
        cabecalho = struct.pack(">I", len(payload))

        with self.arquivo_tarefas.open("ab") as arquivo:
            offset = arquivo.tell()
            arquivo.write(cabecalho)
            arquivo.write(payload)
            arquivo.flush()
            os.fsync(arquivo.fileno())

        return offset

    def _ler_registro_offset(self, offset: int) -> Optional[dict]:
        try:
            with self.arquivo_tarefas.open("rb") as arquivo:
                arquivo.seek(offset)
                cabecalho = arquivo.read(4)
                if len(cabecalho) != 4:
                    return None
                tamanho = struct.unpack(">I", cabecalho)[0]
                payload = arquivo.read(tamanho)
                if len(payload) != tamanho:
                    return None
                return pickle.loads(payload)
        except (OSError, pickle.PickleError, EOFError):
            return None

    def _iterar_registros(self):
        with self.arquivo_tarefas.open("rb") as arquivo:
            while True:
                offset = arquivo.tell()
                cabecalho = arquivo.read(4)
                if not cabecalho:
                    break
                if len(cabecalho) != 4:
                    break
                tamanho = struct.unpack(">I", cabecalho)[0]
                payload = arquivo.read(tamanho)
                if len(payload) != tamanho:
                    break
                try:
                    yield offset, pickle.loads(payload)
                except (pickle.PickleError, EOFError):
                    break
