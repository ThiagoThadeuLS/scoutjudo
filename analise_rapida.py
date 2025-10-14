import streamlit as st
import time
from datetime import datetime
from db_manager import get_db_manager
from streamlit_image_coordinates import streamlit_image_coordinates



db_manager = get_db_manager()

@st.dialog("Adicionar Luta")
def adicionar_luta_dialog(**kwargs):
    st.header("Adicionar Luta - Análise Rápida")
    
    # Selecione a Competição
    competicoes = db_manager.listar_competicoes()
    if not competicoes:
        st.error("Nenhuma competição encontrada. Cadastre uma competição primeiro.")
        return
    # Cria um dicionário para mapear a exibição da competição com seu ID
    dict_competicoes = { f"{comp[1]} - {comp[2]}": comp[0] for comp in competicoes }
    comp_selecionada = st.selectbox("Selecione a Competição", options=list(dict_competicoes.keys()), index=None)

    # Seleção dos Atletas (Atleta 1 e Atleta 2)
    atletas = db_manager.listar_todos_atletas()
    if not atletas:
        st.error("Nenhum atleta cadastrado.")
        return
    # Cria um dicionário onde a chave é o nome do atleta e o valor é seu ID
    dict_atletas = {atleta[1]: atleta[0] for atleta in atletas}
    atleta1 = st.selectbox("Selecione o Atleta 1", options=list(dict_atletas.keys()), index=None)
    atleta2 = st.selectbox("Selecione o Atleta 2", options=list(dict_atletas.keys()), index=None)

    # Seleção da Categoria
    categorias = ['-48', "-60", "-52", "-66", '-57', '-73', '-63', '-81', '-70', '-90', '-78', '-100', '+78', '+100']
    categoria = st.selectbox("Selecione a Categoria", options=categorias, index=None)

    # Botão para cadastrar a luta
    if st.button("Cadastrar Luta", key="adicionar_luta_dialog"):
        # Recupera os IDs com base nos seletores
        comp_id = dict_competicoes.get(comp_selecionada)
        atleta1_id = dict_atletas.get(atleta1)
        atleta2_id = dict_atletas.get(atleta2)
        # Os campos "vencedor" e "tempo_luta" não são preenchidos no momento (tempo_luta definido como None)
        resultado = db_manager.adicionar_confronto(comp_id, atleta1_id, atleta2_id, categoria, None)
        if isinstance(resultado, str):
            st.error(resultado)
            db_manager.rollback()
        else:
            st.success("Luta adicionada com sucesso!")
            time.sleep(1)
            st.rerun()


@st.dialog("Finalizar Luta")
def finalizar_luta_dialog(finalizar_confronto_id: int = None):
    st.header("Finalizar Luta")
    
    # Recupera o ID do confronto previamente selecionado, ou passado como parâmetro
    confronto_id = finalizar_confronto_id or st.session_state.get("confronto_id")
    if not confronto_id:
        st.error("Nenhum confronto selecionado para finalização.")
        return

    try:
        # Recupera os detalhes do confronto (categoria e IDs dos atletas)
        sql = "SELECT categoria, atleta1_id, atleta2_id FROM confrontos WHERE id = %s"
        db_manager.cursor.execute(sql, (confronto_id,))
        resultado = db_manager.cursor.fetchone()
        if not resultado:
            st.error("Confronto não encontrado.")
            return
        categoria, atleta1_id, atleta2_id = resultado

        # Obtém os nomes dos atletas envolvidos
        db_manager.cursor.execute("SELECT nome FROM atletas WHERE id = %s", (atleta1_id,))
        atleta1_nome = db_manager.cursor.fetchone()[0]
        db_manager.cursor.execute("SELECT nome FROM atletas WHERE id = %s", (atleta2_id,))
        atleta2_nome = db_manager.cursor.fetchone()[0]

        # Exibe as informações do confronto para o usuário
        st.markdown(f"**Confronto:** {atleta1_nome} vs {atleta2_nome}")
        st.markdown(f"**Categoria:** {categoria}")

        # Permite que o usuário escolha o vencedor
        vencedor_selecionado = st.radio("Selecione o Vencedor", options=[atleta1_nome, atleta2_nome])

        # Campo para o usuário informar o tempo total da luta (formato 'HH:MM:SS')
        tempo_total = st.text_input("Tempo Total da Luta (HH:MM:SS)", value="00:00:00")

        if st.button("Finalizar Luta", key="finalizar_luta_button"):
            # Determina o ID do vencedor com base na seleção realizada
            vencedor_id = atleta1_id if vencedor_selecionado == atleta1_nome else atleta2_id

            # Atualiza os campos 'vencedor_id' e 'tempo_luta' na tabela 'confrontos'
            sql_update = "UPDATE confrontos SET vencedor_id = %s, tempo_luta = %s WHERE id = %s"
            db_manager.cursor.execute(sql_update, (vencedor_id, tempo_total, confronto_id))
            db_manager.conn.commit()

            st.success("Luta finalizada com sucesso!")
            st.rerun()

    except Exception as e:
        st.error(f"Erro ao finalizar a luta: {e}")
        db_manager.rollback()




st.header("Análise Rápida")

tab1, tab2, tab3 = st.tabs(["Treino", "Competição", "Visualização"])
with tab2:
    # Carrega os atletas no escopo da aba "Treino"
    atletas = db_manager.listar_todos_atletas()
    if not atletas:
        st.error("Nenhum atleta cadastrado.")
    else:
        dict_atletas = {atleta[1]: atleta[0] for atleta in atletas}

    if st.button("Adicionar Luta", key="botao_adicionar_luta"):
        adicionar_luta_dialog()

    # Primeiro, selecione a competição
    competicoes = db_manager.listar_competicoes()
    if not competicoes:
        st.error("Nenhuma competição cadastrada.")
    else:
        dict_competicoes = { f"{comp[1]} - {comp[2]}": comp[0] for comp in competicoes }
        competicao_selecionada = st.selectbox("Selecione a Competição para análise", options=list(dict_competicoes.keys()), index=None)
        comp_id = dict_competicoes.get(competicao_selecionada)
        
        # Agora, listamos os confrontos para a competição selecionada
        confrontos = db_manager.listar_lutas_por_competicao(comp_id)
        if not confrontos:
            st.write("Nenhum confronto cadastrado para esta competição.")
        else:
            # Cria um dicionário para exibição: formato "ID: atleta1 vs atleta2 - categoria (tempo_luta)"
            # Exibe os confrontos disponíveis para a competição selecionada
            dict_confrontos = {
                f"{luta[2]} vs {luta[3]} - {luta[1]} ({'Sem tempo' if not luta[5] else luta[5]})": luta[0]
                for luta in confrontos
            }

            confronto_selecionado = st.selectbox("Selecione o Confronto", options=list(dict_confrontos.keys()), index=None)

            if confronto_selecionado:
                # Recupera e armazena o ID do confronto selecionado na session_state
                confronto_id = dict_confrontos.get(confronto_selecionado)
                st.session_state["confronto_id"] = confronto_id
                
                # Inicializa a variável para evitar NameError
                confronto_escolhido = None
                # Encontra o registro de confronto que corresponda ao ID selecionado
                # Considere que os registros em confrontos estão no formato:
                # (id, atleta1, atleta2, categoria, tempo_luta)
                confronto_escolhido = next((luta for luta in confrontos if luta[0] == confronto_id), None)
                
                # Agora verifica se o registro foi encontrado
                if confronto_escolhido:
                    # Desempacota os valores do registro
                    confronto_id, categoria, atleta1, atleta2, vencedor, tempo_luta = confronto_escolhido

                    # Função para extrair somente o primeiro e o último nome
                    def primeiro_e_ultimo_nome(nome_completo: str) -> str:
                        partes = nome_completo.split()
                        if len(partes) >= 2:
                            return partes[0] + " " + partes[-1]
                        return nome_completo

                    atleta1_formatado = primeiro_e_ultimo_nome(atleta1)
                    atleta2_formatado = primeiro_e_ultimo_nome(atleta2)
                    st.markdown(f'<h3 style="text-align: center;">{atleta1_formatado} vs {atleta2_formatado}</h3>', unsafe_allow_html=True)

                    left_div, right_div = st.columns([6, 2])

                    with left_div:

                        seletor_tempo = st.pills(
                        "Tempo", 
                        ['Minuto 3','Minuto 2','Minuto 1','Minuto 0', "Golden Score"], 
                        key="selected_tempo_acao"
                    )
                        
                        if seletor_tempo == "Minuto 0":
                            tempo = "00:00:00"
                        elif seletor_tempo == "Minuto 1":
                            tempo = "00:01:00"
                        elif seletor_tempo == "Minuto 2":
                            tempo = "00:02:00"
                        elif seletor_tempo == "Minuto 3":
                            tempo = "00:03:00"
                        elif seletor_tempo == "Golden Score":
                            tempo = "00:04:00"




                        with st.container():
                            

                            with right_div:
                                st.subheader(" ")
                                st.subheader(" ")
                                # Exibe a imagem e captura as coordenadas clicadas
                                coordinates = streamlit_image_coordinates("assets/tatame.png", key="local", width=250)

                                quadrante = "Não Definida"  # Inicializa a variável

                                if coordinates is not None and "x" in coordinates and "y" in coordinates:
                                    try:
                                        x = float(coordinates["x"])
                                        y = float(coordinates["y"])
                                        if 0 < x < 125 and 0 < y < 125:
                                            quadrante = 1
                                        elif 125 < x < 250 and 0 < y < 125:
                                            quadrante = 2
                                        elif 0 < x < 125 and 125 < y < 250:
                                            quadrante = 3
                                        elif 125 < x < 250 and 125 < y < 250:
                                            quadrante = 4
                                        else:
                                            quadrante = "Desconhecido"
                                    except Exception as e:
                                        st.error(f"Erro ao processar coordenadas: {e}")


                                st.subheader(" ")
                                coordinates_newaza = streamlit_image_coordinates("assets/tatame_newaza.png", key="local_newaza", width=250)

                                # Calcula a direção com base nas coordenadas da imagem newaza
                                direcao_newaza = "Não definida"
                                if coordinates_newaza is not None and "x" in coordinates_newaza and "y" in coordinates_newaza:
                                    try:
                                        x = float(coordinates_newaza["x"])
                                        y = float(coordinates_newaza["y"])
                                        if 0 < x < 83.33 and 0 < y < 83.33:
                                            direcao_newaza = "DEF"
                                        elif 83.33 < x < 166.66 and 0 < y < 83.33:
                                            direcao_newaza = "F"
                                        elif 166.66 < x < 250 and 0 < y < 83.33:
                                            direcao_newaza = "DDF"
                                        elif 0 < x < 83.33 and 83.33 < y < 166.66:
                                            direcao_newaza = "LE"
                                        elif 166.66 < x < 250 and 83.33 < y < 166.66:
                                            direcao_newaza = "LD"
                                        elif 0 < x < 83.33 and 166.66 < y < 250:
                                            direcao_newaza = "DET"
                                        elif 83.33 < x < 166.66 and 166.66 < y < 250:
                                            direcao_newaza = "T"
                                        elif 166.66 < x < 250 and 166.66 < y < 250:
                                            direcao_newaza = "DDT"
                                        else:
                                            direcao_newaza = "Desconhecido"
                                    except Exception as e:
                                        st.error(f"Erro ao processar coordenadas newaza: {e}")


                                if st.button("Finalizar Luta", key="botao_finalizar_luta"):
                                    finalizar_luta_dialog()

                            with left_div:

                                with st.form("forms_evento", clear_on_submit=True):
                                    col_1, col_2, col_3 = st.columns(3)
                                    
                                    with col_1:
                                        st.write("Adicionar Evento")

                                        # Seleciona o atleta que executou a ação
                                        autor = st.pills(
                                            "Selecione o autor da ação",
                                            ["Atleta 1", "Atleta 2"]
                                        )

                                        #Mostrador tachi waza
                                        st.write("Quadrante Tachi-Waza")
                                        st.subheader(quadrante)
                                   
                                    with col_2:
                                        # Seleção da Mão
                                        mao_direita = st.selectbox(
                                            "Mão Direita",
                                            ("Uma Mão (Gola)", "Gola", "Gola Cruzada", "Gola Alta", "Patolada", "Patolada Cruzada", "Arm Drag", "Uma Mão (Manga)", "Manga", "Manga Cruzada", "Cava"),
                                            index=None
                                        )

                                        mao_esquerda = st.selectbox(
                                            "Mão Esquerda",
                                            ("Uma Mão (Gola)", "Gola", "Gola Cruzada", "Gola Alta", "Patolada", "Patolada Cruzada", "Arm Drag", "Uma Mão (Manga)", "Manga", "Manga Cruzada", "Cava"),
                                            index=None
                                        )
                                    
                                    with col_3:
                                        # Grupo do golpe e efetividade do golpe
                                        grupo_golpe = st.pills(
                                            "Selecione o grupo do golpe",
                                            ["Te-Waza", "Ashi-Waza", "Koshi-Waza", "Sutemi-Waza", "Yoko-Sutemi-waza", "Kaeshi Waza", "Tranco"]
                                        )

                                        efetividade_golpe = st.pills(
                                            "Selecione a efetividade do golpe",
                                            ["Yuko", "Waza-Ari", "Ippon", "Golpe Falho", "Golpe Falso", "Irrelevante", "Sofreu contra-golpe", "Transição"]
                                        )   

                                    st.markdown("----")
                                    
                                    col1_ , col2_, col3_ = st.columns(3)

                                    # Dados para a passagem (caso haja passagem, ou newaza)
                                    with col1_:
                                        newaza = False
                                        st.toggle(" ", key="newaza_toggle")
                                        if st.session_state.get("newaza_toggle"):
                                            newaza = True

                                        id_newaza = st.pills(
                                            "Selecione quem fez o ne-waza",
                                            ["Atleta 1", "Atleta 2"]
                                        )

                                        #Mostrador direção newaza
                                        st.write("Direção Ne-Waza")
                                        st.subheader(direcao_newaza)

                                    with col2_:
                                        partida = st.pills(
                                            "Selecione de onde partiu a passagem",
                                            ["Cabeça", "Costas", "Lateral", "Meia-Guarda", "Guarda", "Oportunista"]
                                        )           

                                    with col3_:
                                        efetividade_newaza = st.pills(
                                            "Selecione a efetividade da passagem",
                                            ["Yuko", "Waza-Ari", "Ippon", "Nada", "Sofreu Contra-Ataque"]
                                        )
                                    
                                    

                                    enviar_form = st.form_submit_button("Enviar")

                                    if enviar_form:
                                        # Seleciona o id do atleta com base no valor do autor (usando os nomes dos atletas já carregados anteriormente)
                                        if autor == "Atleta 1":
                                            action_atleta_id = dict_atletas.get(atleta1)
                                        else:
                                            action_atleta_id = dict_atletas.get(atleta2)

                                        # Aqui, assumimos que o tempo_ocorrido foi definido anteriormente conforme o seletor de tempo
                                        tempo_ocorrido = tempo

                                        # Captura o ID do atleta_id_nw com base na seleção do seletor id_newaza
                                        if id_newaza == "Atleta 1":
                                            atleta_id_nw = dict_atletas.get(atleta1)
                                        else:
                                            atleta_id_nw = dict_atletas.get(atleta2)

                                        # Agora, chama o método que adiciona a ação na tabela "acoes"
                                        resultado = db_manager.adicionar_acao(
                                            confronto_id,          # id do confronto selecionado
                                            action_atleta_id,      # atleta que realizou a ação
                                            quadrante,             # quadrante obtido a partir da imagem
                                            grupo_golpe,           # grupo do golpe
                                            tempo_ocorrido,        # tempo ocorrido
                                            mao_direita,           # mão direita
                                            mao_esquerda,          # mão esquerda
                                            efetividade_golpe,     # efetividade do golpe
                                            newaza,                # valor booleano se é newaza
                                            atleta_id_nw,         # ID do atleta relacionado à newaza
                                            direcao_newaza,        # direção da ação em newaza
                                            partida,               # posição de partida da ação
                                            efetividade_newaza     # efetividade da passagem
                                        )


                                        if isinstance(resultado, str):
                                            st.error(resultado)
                                            db_manager.rollback()
                                        else:
                                            st.success("Ação cadastrada com sucesso!")
                                            time.sleep(1)
                                            st.rerun()


                        st.header(" ")
                        
                        # Adicionando o formulário para Shido
                        with st.form("forms_shido", clear_on_submit=True):
                            st.write("Adicionar Shido")

                            # Seleciona quem recebeu shido
                            atleta_recebeu_shido = st.pills(
                                "Selecione quem recebeu shido",
                                ["Atleta 1", "Atleta 2"]
                            )

                            # Seleção do tipo de shido
                            tipo_shido = st.selectbox(
                                "Selecione o shido",
                                ["Golpe Falso", "Falta de Combatividade", "Desligar Kumi-Kata", "Kumi-Kata Irregular", "Pegar na Perna", "Judô Negativo", "Passou a Cabeça"],
                                index=None
                            )

                            # Botão para enviar as informações do shido
                            enviar_form = st.form_submit_button("Enviar")

                            if enviar_form:
                                try:
                                    # Determina qual atleta recebeu shido e captura o ID
                                    atleta_id = ""
                                    if atleta_recebeu_shido == "Atleta 1":
                                        atleta_id = dict_atletas.get(atleta1)  # atleta1 já está definido anteriormente
                                    else:
                                        atleta_id = dict_atletas.get(atleta2)  # atleta2 já está definido anteriormente

                                    # Chama o método que adiciona a shido na tabela "shido"
                                    resultado = db_manager.adicionar_shido(
                                        confronto_id,  # id do confronto selecionado
                                        atleta_id,     # atleta que recebeu shido
                                        tipo_shido,    # tipo de shido selecionado
                                        tempo          # valor do tempo obtido anteriormente
                                    )

                                    if isinstance(resultado, str):
                                        st.error(resultado)
                                        db_manager.rollback()
                                    else:
                                        st.success("Shido cadastrado com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
                                        
                                except Exception as e:
                                    st.error(f"Erro ao adicionar shido: {e}")
                                    db_manager.rollback()
                            
                            

with tab1:
    st.subheader("Análise Treino")  

with tab3:
    st.subheader("Visualização")  






