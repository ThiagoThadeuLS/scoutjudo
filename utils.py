import streamlit as st

def exibir_texto_centralizado(texto, tamanho=20):
    """
    Exibe um texto centralizado com tamanho de fonte customizável no Streamlit.

    Parâmetros:
        texto (str): O texto a ser exibido.
        tamanho (int): O tamanho da fonte em pixels (px). Padrão é 20.
    """
    st.markdown(f"""
        <style>
            .texto-centralizado {{
                text-align: center;
                font-size: {tamanho}px;
                font-weight: bold;
                margin: 30px 0;
            }}
        </style>

        <div class="texto-centralizado">{texto}</div>
        """, unsafe_allow_html=True)