import tempfile
import unittest

from btree import BTree
from persistencia import ArmazenamentoTarefas
from tarefas import GerenciadorTarefas


class TesteGerenciadorTarefas(unittest.TestCase):
    def criar_gerenciador(self, pasta):
        armazenamento = ArmazenamentoTarefas(pasta)
        return GerenciadorTarefas(armazenamento)

    def test_insercao_de_tarefa(self):
        with tempfile.TemporaryDirectory() as pasta:
            gerenciador = self.criar_gerenciador(pasta)
            tarefa = gerenciador.cadastrar("Estudar B-Tree", "20/10/2026", "alta")

            self.assertEqual(tarefa.id, 1)
            self.assertEqual(len(gerenciador.listar()), 1)

    def test_busca_por_id_existente(self):
        with tempfile.TemporaryDirectory() as pasta:
            gerenciador = self.criar_gerenciador(pasta)
            tarefa = gerenciador.cadastrar("Fazer README", "21/10/2026", "media")

            encontrada = gerenciador.buscar_por_id(tarefa.id)

            self.assertIsNotNone(encontrada)
            self.assertEqual(encontrada.descricao, "Fazer README")

    def test_busca_por_id_inexistente(self):
        with tempfile.TemporaryDirectory() as pasta:
            gerenciador = self.criar_gerenciador(pasta)

            self.assertIsNone(gerenciador.buscar_por_id(99))

    def test_insercoes_causam_divisao_da_btree(self):
        btree = BTree(grau_minimo=2)

        for chave in range(1, 10):
            btree.inserir(chave, chave * 100)

        self.assertGreater(btree.divisoes, 0)
        self.assertGreater(btree.quantidade_nos(), 1)

    def test_percurso_ordenado_das_chaves(self):
        btree = BTree(grau_minimo=2)
        for chave in [5, 1, 9, 2, 7]:
            btree.inserir(chave, chave)

        self.assertEqual([chave for chave, _ in btree.percurso_ordenado()], [1, 2, 5, 7, 9])

    def test_atualizacao_e_persistencia_da_nova_versao(self):
        with tempfile.TemporaryDirectory() as pasta:
            gerenciador = self.criar_gerenciador(pasta)
            tarefa = gerenciador.cadastrar("Versao antiga", "22/10/2026", "baixa")
            gerenciador.atualizar(tarefa.id, descricao="Versao nova", status="em andamento")

            gerenciador_reiniciado = self.criar_gerenciador(pasta)
            encontrada = gerenciador_reiniciado.buscar_por_id(tarefa.id)

            self.assertEqual(encontrada.descricao, "Versao nova")
            self.assertEqual(encontrada.status, "em andamento")

    def test_exclusao_remove_das_buscas(self):
        with tempfile.TemporaryDirectory() as pasta:
            gerenciador = self.criar_gerenciador(pasta)
            tarefa = gerenciador.cadastrar("Apagar", "23/10/2026", "media")

            self.assertTrue(gerenciador.excluir(tarefa.id))
            self.assertIsNone(gerenciador.buscar_por_id(tarefa.id))
            self.assertEqual(gerenciador.listar(), [])

    def test_carregamento_apos_reiniciar(self):
        with tempfile.TemporaryDirectory() as pasta:
            gerenciador = self.criar_gerenciador(pasta)
            gerenciador.cadastrar("Persistir", "24/10/2026", "alta")

            gerenciador_reiniciado = self.criar_gerenciador(pasta)

            self.assertEqual(len(gerenciador_reiniciado.listar()), 1)
            self.assertEqual(gerenciador_reiniciado.listar()[0].descricao, "Persistir")

    def test_filtros_por_status_e_data(self):
        with tempfile.TemporaryDirectory() as pasta:
            gerenciador = self.criar_gerenciador(pasta)
            tarefa1 = gerenciador.cadastrar("Tarefa A", "25/10/2026", "alta")
            gerenciador.cadastrar("Tarefa B", "26/10/2026", "baixa")
            gerenciador.atualizar(tarefa1.id, status="concluida")

            por_status = gerenciador.filtrar(status="concluida")
            por_data = gerenciador.filtrar(vencimento="26/10/2026")

            self.assertEqual([tarefa.descricao for tarefa in por_status], ["Tarefa A"])
            self.assertEqual([tarefa.descricao for tarefa in por_data], ["Tarefa B"])

    def test_reconstrucao_nao_recupera_excluidas(self):
        with tempfile.TemporaryDirectory() as pasta:
            gerenciador = self.criar_gerenciador(pasta)
            removida = gerenciador.cadastrar("Removida", "27/10/2026", "media")
            ativa = gerenciador.cadastrar("Ativa", "28/10/2026", "alta")
            gerenciador.excluir(removida.id)

            gerenciador_reiniciado = self.criar_gerenciador(pasta)
            gerenciador_reiniciado.armazenamento.reconstruir_indice()

            self.assertIsNone(gerenciador_reiniciado.buscar_por_id(removida.id))
            self.assertEqual(gerenciador_reiniciado.buscar_por_id(ativa.id).descricao, "Ativa")


if __name__ == "__main__":
    unittest.main()
