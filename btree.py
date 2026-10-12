from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NoBTree:
    folha: bool = True
    chaves: list[int] = field(default_factory=list)
    valores: list[int] = field(default_factory=list)
    filhos: list["NoBTree"] = field(default_factory=list)


class BTree:
    """B-Tree simples de grau mínimo 2 usada como índice ID -> offset."""

    def __init__(self, grau_minimo: int = 2):
        if grau_minimo < 2:
            raise ValueError("O grau mínimo da B-Tree deve ser pelo menos 2.")
        self.t = grau_minimo
        self.raiz = NoBTree()
        self.divisoes = 0

    def buscar(self, chave: int) -> Optional[int]:
        resultado = self._buscar_no(self.raiz, chave)
        if resultado is None:
            return None
        no, posicao = resultado
        return no.valores[posicao]

    def _buscar_no(self, no: NoBTree, chave: int) -> Optional[tuple[NoBTree, int]]:
        i = 0
        while i < len(no.chaves) and chave > no.chaves[i]:
            i += 1

        if i < len(no.chaves) and chave == no.chaves[i]:
            return no, i

        if no.folha:
            return None

        return self._buscar_no(no.filhos[i], chave)

    def inserir(self, chave: int, valor: int) -> None:
        existente = self._buscar_no(self.raiz, chave)
        if existente is not None:
            no, posicao = existente
            no.valores[posicao] = valor
            return

        raiz = self.raiz
        if len(raiz.chaves) == (2 * self.t) - 1:
            nova_raiz = NoBTree(folha=False, filhos=[raiz])
            self.raiz = nova_raiz
            self._dividir_filho(nova_raiz, 0)
            self._inserir_nao_cheio(nova_raiz, chave, valor)
        else:
            self._inserir_nao_cheio(raiz, chave, valor)

    def _inserir_nao_cheio(self, no: NoBTree, chave: int, valor: int) -> None:
        i = len(no.chaves) - 1

        if no.folha:
            no.chaves.append(0)
            no.valores.append(0)
            while i >= 0 and chave < no.chaves[i]:
                no.chaves[i + 1] = no.chaves[i]
                no.valores[i + 1] = no.valores[i]
                i -= 1
            no.chaves[i + 1] = chave
            no.valores[i + 1] = valor
            return

        while i >= 0 and chave < no.chaves[i]:
            i -= 1
        i += 1

        if len(no.filhos[i].chaves) == (2 * self.t) - 1:
            self._dividir_filho(no, i)
            if chave > no.chaves[i]:
                i += 1

        self._inserir_nao_cheio(no.filhos[i], chave, valor)

    def _dividir_filho(self, pai: NoBTree, indice_filho: int) -> None:
        filho = pai.filhos[indice_filho]
        novo = NoBTree(folha=filho.folha)
        meio = self.t - 1

        chave_meio = filho.chaves[meio]
        valor_meio = filho.valores[meio]

        novo.chaves = filho.chaves[meio + 1 :]
        novo.valores = filho.valores[meio + 1 :]
        filho.chaves = filho.chaves[:meio]
        filho.valores = filho.valores[:meio]

        if not filho.folha:
            novo.filhos = filho.filhos[self.t :]
            filho.filhos = filho.filhos[: self.t]

        pai.chaves.insert(indice_filho, chave_meio)
        pai.valores.insert(indice_filho, valor_meio)
        pai.filhos.insert(indice_filho + 1, novo)
        self.divisoes += 1

    def percurso_ordenado(self) -> list[tuple[int, int]]:
        pares: list[tuple[int, int]] = []
        self._percorrer(self.raiz, pares)
        return pares

    def _percorrer(self, no: NoBTree, pares: list[tuple[int, int]]) -> None:
        for i, chave in enumerate(no.chaves):
            if not no.folha:
                self._percorrer(no.filhos[i], pares)
            pares.append((chave, no.valores[i]))

        if not no.folha:
            self._percorrer(no.filhos[len(no.chaves)], pares)

    def reconstruir(self, pares: dict[int, int] | list[tuple[int, int]]) -> None:
        self.raiz = NoBTree()
        self.divisoes = 0
        itens = pares.items() if isinstance(pares, dict) else pares
        for chave, valor in sorted(itens):
            self.inserir(chave, valor)

    def altura(self) -> int:
        altura = 0
        no = self.raiz
        while True:
            altura += 1
            if no.folha:
                return altura
            no = no.filhos[0]

    def quantidade_nos(self) -> int:
        return self._contar_nos(self.raiz)

    def _contar_nos(self, no: NoBTree) -> int:
        return 1 + sum(self._contar_nos(filho) for filho in no.filhos)

    def total_chaves(self) -> int:
        return len(self.percurso_ordenado())

    def visualizar(self) -> str:
        linhas: list[str] = []
        self._visualizar_no(self.raiz, linhas, nivel=0, nome="raiz")
        return "\n".join(linhas)

    def _visualizar_no(self, no: NoBTree, linhas: list[str], nivel: int, nome: str) -> None:
        indentacao = "    " * nivel
        chaves = ", ".join(str(chave) for chave in no.chaves) or "vazio"
        tipo = "folha" if no.folha else "interno"
        linhas.append(f"{indentacao}{nome}: [{chaves}] ({tipo})")

        for indice, filho in enumerate(no.filhos):
            self._visualizar_no(filho, linhas, nivel + 1, f"filho {indice}")
