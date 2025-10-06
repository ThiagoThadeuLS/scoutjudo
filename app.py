import streamlit as st
from db_manager import DBManager, get_db_manager

# Configuração da página
st.set_page_config(page_title="Análise Judô", layout="wide")

# Inicialização do banco de dados
db_manager = get_db_manager()
db_manager.criar_tabelas()


# Definição das páginas
home_page = st.Page("home.py", title= "Home")
atletas_page = st.Page("atletas.py", title="Atletas")
competicao_page = st.Page("competicao.py", title="Competição")
analise_rapida_page = st.Page("analise_rapida.py", title="Análise Rápida")
analise_detalhada_page = st.Page("analise_detalhada.py", title="Análise Detalhada")
vizu_analise_page = st.Page("vizu_analise.py", title="Vizualização Análise")

pg = st.navigation([home_page, atletas_page, competicao_page, analise_rapida_page, analise_detalhada_page, vizu_analise_page])
pg.run()