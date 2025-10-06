import streamlit as st
import pandas as pd
import time
from datetime import date
from db_manager import get_db_manager

db_manager = get_db_manager()

# ----- Diálogo para Adicionar Competição -----
@st.dialog("Adicionar Competição")
def adicionar_competicao_dialog():
    nome_competicao = st.text_input("Nome da Competição")
    data_competicao = st.date_input("Data da Competição")
    classe = st.selectbox("Selecione a Classe", ('Cadete', 'Junior', 'Sênior', 'Treino'))
    
    if st.button("Cadastrar", key="adicionar_competicao_dialog"):
        if not nome_competicao or not data_competicao:
            st.error("Por favor, preencha todos os campos obrigatórios.")
        else:
            id_competicao = db_manager.adicionar_competicao(nome_competicao, data_competicao, classe)
            if id_competicao is not None:
                st.success("Competição cadastrada com sucesso!")
                st.rerun()
            else:
                st.error(f"A competição '{nome_competicao}' já está cadastrada ou ocorreu um erro.")
                db_manager.rollback()

# ----- Diálogo para Excluir Competição -----
@st.dialog("Excluir Competição")
def excluir_competicao_dialog():
    lista_competicoes = db_manager.listar_competicoes()
    dict_competicoes = {f"{comp[1]} - {comp[2]}": comp[0] for comp in lista_competicoes}
    competicao_selecionada = st.selectbox("Selecione a Competição", options=list(dict_competicoes.keys()), index=0)
    
    if competicao_selecionada:
        competicao_id = dict_competicoes[competicao_selecionada]
        st.warning("Isso excluirá permanentemente a competição selecionada. Você tem certeza?", icon="⚠️")
        if st.button("Excluir", key="excluir_competicao_dialog"):
            try:
                conn = db_manager.conn
                cursor = conn.cursor()
                query = "DELETE FROM campeonato WHERE id = %s"
                cursor.execute(query, (competicao_id,))
                conn.commit()
                st.success("Competição excluída com sucesso!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error("Erro ao excluir a competição. Tente novamente.")
                db_manager.rollback()
                st.rerun()

# ----- Diálogo para Excluir Luta -----
@st.dialog("Excluir Luta")
def excluir_luta_dialog(default_competicao=None):
    # Seleciona a competição
    if default_competicao:
        comp_id = default_competicao
    else:
        competicoes = db_manager.listar_competicoes()
        if not competicoes:
            st.error("Nenhuma competição encontrada. Cadastre uma competição primeiro.")
            return
        dict_competicoes = {f"{comp[1]} - {comp[2]}": comp[0] for comp in competicoes}
        competicao_selecionada = st.selectbox("Selecione a Competição", options=list(dict_competicoes.keys()), index=0)
        comp_id = dict_competicoes[competicao_selecionada]

    # Listar lutas com o ID (para exclusão) e os dados para exibição
    try:
        db_manager.check_connection()
        sql = """
            SELECT c.id, c.categoria,
                   a1.nome AS "Atleta 1",
                   a2.nome AS "Atleta 2",
                   (SELECT nome FROM atletas WHERE id = c.vencedor_id) AS "Vencedor",
                   c.tempo_luta AS "Tempo de Luta"
            FROM confrontos c
            JOIN atletas a1 ON c.atleta1_id = a1.id
            JOIN atletas a2 ON c.atleta2_id = a2.id
            WHERE c.campeonato_id = %s;
        """
        db_manager.cursor.execute(sql, (comp_id,))
        lutas = db_manager.cursor.fetchall()
    except Exception as e:
        st.error("Erro ao listar lutas.")
        return

    if not lutas:
        st.error("Nenhuma luta cadastrada para essa competição.")
        return

    # Cria um dicionário para mapear uma string de exibição ao ID da luta
    dict_lutas = {
        f"{luta[1]} | {luta[2]} vs {luta[3]} | Vencedor: {luta[4] if luta[4] else 'Sem vencedor'} | Tempo: {luta[5] if luta[5] else 'Sem tempo'}": luta[0]
        for luta in lutas
    }

    luta_selecionada = st.selectbox("Selecione a Luta", options=list(dict_lutas.keys()))
    st.warning("Isso excluirá permanentemente a luta selecionada. Você tem certeza?", icon="⚠️")

    if st.button("Excluir", key="excluir_luta_dialog_button"):
        luta_id = dict_lutas[luta_selecionada]
        if db_manager.deletar_confronto(luta_id):
            st.success("Luta excluída com sucesso!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Erro ao excluir a luta. Tente novamente.")
            db_manager.rollback()
            time.sleep(1)
            st.rerun()

# ----- Layout Principal da Página de Competição usando st.expander -----
competicoes = db_manager.listar_competicoes()
if not competicoes:
    st.error("Nenhuma competição encontrada.")
else:
    for comp in competicoes:
        comp_nome = f"{comp[1]} - {comp[2]}"
        comp_id = comp[0]
        with st.expander(comp_nome):
            try:
                db_manager.check_connection()
                sql = """
                    SELECT c.categoria,
                           a1.nome AS "Atleta 1",
                           a2.nome AS "Atleta 2",
                           (SELECT nome FROM atletas WHERE id = c.vencedor_id) AS "Vencedor",
                           c.tempo_luta AS "Tempo de Luta"
                    FROM confrontos c
                    JOIN atletas a1 ON c.atleta1_id = a1.id
                    JOIN atletas a2 ON c.atleta2_id = a2.id
                    WHERE c.campeonato_id = %s;
                """
                db_manager.cursor.execute(sql, (comp_id,))
                lutas = db_manager.cursor.fetchall()
            except Exception as e:
                st.error("Erro ao listar confrontos.")
                lutas = []

            if not lutas:
                st.write("Nenhum confronto cadastrado para esta competição.")
            else:
                # Cria o DataFrame com as colunas na ordem desejada
                colunas = ["categoria", "Atleta 1", "Atleta 2", "Vencedor", "Tempo de Luta"]
                df = pd.DataFrame(lutas, columns=colunas)
                st.dataframe(df, hide_index=True)
                
                # Botão para excluir uma luta da competição corrente
                if st.button("Excluir Luta", key=f"excluir_luta_{comp_id}"):
                    excluir_luta_dialog(default_competicao=comp_id)

# ----- Colunas para Adicionar ou Excluir Competição -----
col_adicionar, col_excluir = st.columns(2)
with col_adicionar:
    if st.button("Adicionar Competição", key="adicionar_competicao"):
        adicionar_competicao_dialog()
with col_excluir:
    if st.button("Excluir Competição", key="excluir_competicao"):
        excluir_competicao_dialog()
