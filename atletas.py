import streamlit as st
import pandas as pd
import time
from datetime import date
import os
from db_manager import DBManager, get_db_manager  # Certifique-se de que esse import esteja correto
import atexit

db_manager = get_db_manager()

@st.dialog("Adicionar Atleta")
def adicionar_atleta_dialog(**kwargs):
    # Se default_clube for passado, já define no selectbox
    default_clube = kwargs.get("default_clube", None)
    nome = st.text_input("Nome") 
    categoria = st.selectbox("Selecione a categoria", ('-48', "-60", "-52", "-66", '-57', '-73', '-63', '-81', '-70', '-90', '-78', '-100', '+78', '+100'))
    ano_nascimento = st.number_input("Ano de nascimento", value=2000)
    if default_clube:
        clube = default_clube
    else:
        clube = st.selectbox("Selecione a equipe", ('Minas', 'Outros', 'Internacional'))

    # Validação e submissão do formulário
    if st.button("Cadastrar", key=f"adicionar_atleta_dialog"):
        if not nome or not categoria or not ano_nascimento:
            st.error("Por favor, preencha todos os campos.")
        else:
            resultado = db_manager.adicionar_atleta(nome, categoria, ano_nascimento, clube)
            if isinstance(resultado, str):  # Se for uma string, é uma mensagem de erro
                st.error(resultado)  # Exibe a mensagem de erro no Streamlit
                db_manager.rollback()
            else:
                st.success("Atleta cadastrado com sucesso!")
                time.sleep(1)  # Pausa para mostrar a mensagem antes de atualizar a página
                st.rerun()

@st.dialog("Editar Atleta")
def editar_atleta_dialog(**kwargs):
    clube = kwargs.get("default_clube", None)
    if not clube:
        st.error("Clube não especificado.")
        return

    # Lista os atletas do clube informado
    lista_atletas = db_manager.listar_atletas_por_clube(clube)
    if not lista_atletas:
        st.error("Nenhum atleta encontrado para este clube.")
        return

    # Cria um dicionário com nome do atleta como chave e os outros dados como valor
    dict_atletas = {atleta[1]: [atleta[0], atleta[2], atleta[3], atleta[4]] for atleta in lista_atletas}
    atleta_escolhido = st.selectbox("Selecione o atleta", options=list(dict_atletas.keys()), index=0)
    
    if atleta_escolhido:
        atleta_id = dict_atletas[atleta_escolhido][0]
        novo_nome = st.text_input("Nome", value=atleta_escolhido)
        categorias_list = ['-48', "-60", "-52", "-66", '-57', '-73', '-63', '-81', '-70', '-90', '-78', '-100', '+78', '+100']
        try:
            idx_categoria = categorias_list.index(dict_atletas[atleta_escolhido][1])
        except ValueError:
            idx_categoria = 0
        nova_categoria = st.selectbox("Selecione a categoria", options=categorias_list, index=idx_categoria)
        # Extrai o ano de nascimento a partir do campo data (data_nasc)
        data_nasc_atual = dict_atletas[atleta_escolhido][2]
        ano_atual = data_nasc_atual.year if isinstance(data_nasc_atual, date) else 2000
        novo_ano = st.number_input("Ano de nascimento", value=ano_atual)
        clubes_list = ['Minas', 'Outros', 'Internacional']
        try:
            idx_clube = clubes_list.index(dict_atletas[atleta_escolhido][3])
        except ValueError:
            idx_clube = 0
        novo_clube = st.selectbox("Selecione o clube", options=clubes_list, index=idx_clube)

        if st.button("Editar", key="editar_atleta_dialog"):
            if not novo_nome or not nova_categoria or not novo_ano or not novo_clube:
                st.error("Por favor, preencha todos os campos.")
            else:
                resultado = db_manager.editar_atleta(atleta_id, novo_nome, nova_categoria, novo_ano, novo_clube)
                if isinstance(resultado, str):
                    st.error(resultado)
                    db_manager.rollback()
                else:
                    st.success("Atleta editado com sucesso!")
                    time.sleep(1)
                    st.rerun()

@st.dialog("Excluir Atleta")
def excluir_atleta_dialog(**kwargs):
    clube = kwargs.get("default_clube", None)
    if not clube:
        st.error("Clube não especificado.")
        return

    # Obtém a lista de atletas do clube informado
    lista_atletas = db_manager.listar_atletas_por_clube(clube)
    
    if not lista_atletas:
        st.error("Nenhum atleta encontrado para este clube.")
        return

    # Cria um dicionário com o nome do atleta como chave e o id como valor
    dict_atletas = {atleta[1]: atleta[0] for atleta in lista_atletas}
    
    # Seleciona o atleta a ser excluído
    atleta = st.selectbox("Selecione o atleta", options=list(dict_atletas.keys()), index=0)
    
    if atleta:
        atleta_id = dict_atletas[atleta]
        st.warning(
            "Isso excluirá permanentemente todos os dados associados a esse atleta. Você tem certeza?", 
            icon="⚠️"
        )
        if st.button("Excluir", key="excluir_atleta_dialog"):
            if db_manager.deletar_atleta(atleta_id):
                st.success("Atleta deletado com sucesso!")
                time.sleep(1)
                st.rerun()    
            else:
                st.error("Erro ao excluir o atleta. Tente novamente.")
                db_manager.rollback()
                time.sleep(1)
                st.rerun()

# Obter a lista de clubes
clubes = ["Minas", "Outros", "Internacional"]

for clube in clubes:
    with st.expander(clube):
        # Listar atletas do clube
        atletas = db_manager.listar_atletas_por_clube(clube)
        colunas = ["Nome", "Categoria", "Ano de Nascimento", "Clube"]
        if not atletas:
            st.write("Nenhum atleta cadastrado")
            df = pd.DataFrame(columns=colunas)
        else:
            df = pd.DataFrame(atletas, columns=["id"] + colunas)
            df = df.drop(columns=["id"])
        
        st.dataframe(df, hide_index=True)
        
        # Criação dos botões para adicionar, excluir e editar atletas
        botao_adicionar_atleta, botao_excluir_atleta, botao_editar_atleta = st.columns([1, 1, 3])
        
        with botao_adicionar_atleta:
            if st.button("Adicionar Atleta", key=f"adicionar_atleta_{clube}"):
                adicionar_atleta_dialog(default_clube=clube)
        
        with botao_excluir_atleta:
            if st.button("Excluir Atleta", key=f"excluir_atleta_{clube}"):
                excluir_atleta_dialog(default_clube=clube)
        
        with botao_editar_atleta:
            if st.button("Editar Atleta", key=f"editar_atleta_{clube}"):
                editar_atleta_dialog(default_clube=clube)
