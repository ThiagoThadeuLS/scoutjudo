import psycopg2
import streamlit as st
from datetime import date

class DBManager:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=st.secrets["DB"]["DB_HOST"],
                port=st.secrets["DB"]["DB_PORT"],
                database=st.secrets["DB"]["DB_NAME"],
                user=st.secrets["DB"]["DB_USER"],
                password=st.secrets["DB"]["DB_PASSWORD"],
                sslmode="require"
            )
            self.cursor = self.conn.cursor()
            print("Conexão bem-sucedida!")
        except psycopg2.OperationalError as e:
            print(f"Erro de conexão: {e}")
            raise

    def check_connection(self):
        if self.conn.closed:
            raise Exception("A conexão com o banco de dados foi fechada.")

    def criar_tabelas(self):
        comandos = [
            """
            CREATE TABLE IF NOT EXISTS atletas (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                categoria TEXT,
                data_nasc DATE,
                clube TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS campeonato (
                id SERIAL PRIMARY KEY,
                nome_competicao TEXT NOT NULL,
                data_competicao DATE NOT NULL,
                classe TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS confrontos (
                id SERIAL PRIMARY KEY,
                campeonato_id INT NOT NULL REFERENCES campeonato(id) ON DELETE CASCADE,
                atleta1_id INT NOT NULL REFERENCES atletas(id) ON DELETE CASCADE,
                atleta2_id INT NOT NULL REFERENCES atletas(id) ON DELETE CASCADE,
                vencedor_id INT REFERENCES atletas(id) ON DELETE SET NULL,
                categoria TEXT,
                tempo_luta INTERVAL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS acoes (
                id SERIAL PRIMARY KEY,
                confronto_id INT NOT NULL REFERENCES confrontos(id) ON DELETE CASCADE,
                atleta_id INT NOT NULL REFERENCES atletas(id) ON DELETE CASCADE,
                quadrante INT,
                grupo_golpe TEXT,
                tempo_ocorrido INTERVAL,
                mao_direita TEXT,
                mao_esquerda TEXT,
                efetividade_golpe TEXT,
                newaza BOOLEAN,
                direcao TEXT,
                partida TEXT,
                efetividade_newaza TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS shido (
            id SERIAL PRIMARY KEY,
            atleta_id INT NOT NULL REFERENCES atletas(id) ON DELETE CASCADE,
            tipo TEXT,
            tempo INTERVAL
            );
            """
        ]
        try:
            for comando in comandos:
                self.cursor.execute(comando)
            self.conn.commit()
            print("Tabelas criadas com sucesso!")
        except Exception as e:
            if not self.conn.closed:
                self.conn.rollback()
            print("Erro ao criar tabelas:", e)
            raise
        
    def rollback(self):
        self.conn.rollback()

    def adicionar_atleta(self, nome, categoria, ano_nascimento, clube):
        """
        Adiciona um novo atleta na tabela atletas.
        O ano de nascimento é convertido para uma data com o dia 01/01.
        Antes de inserir, verifica se já existe um atleta com o mesmo nome, data de nascimento e clube.
        """
        try:
            # Converte o ano para uma data (assumindo 1 de janeiro como data de nascimento)
            data_nasc = date(int(ano_nascimento), 1, 1)
            
            # Verificar se já existe atleta com o mesmo nome, data de nascimento e clube
            check_sql = """
                SELECT id FROM atletas
                WHERE nome = %s AND data_nasc = %s AND clube = %s;
            """
            self.cursor.execute(check_sql, (nome, data_nasc, clube))
            existente = self.cursor.fetchone()
            
            if existente:
                mensagem = "Atleta já cadastrado com este nome, data de nascimento e clube."
                print(mensagem)
                return mensagem
            
            # Se não existir, inserir o novo atleta
            sql = """
                INSERT INTO atletas (nome, categoria, data_nasc, clube)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """
            self.cursor.execute(sql, (nome, categoria, data_nasc, clube))
            id_atleta = self.cursor.fetchone()[0]
            self.conn.commit()
            print(f"Atleta inserido com ID: {id_atleta}")
            return id_atleta
        except Exception as e:
            self.conn.rollback()
            print("Erro ao adicionar atleta:", e)
            return str(e)
        
    def editar_atleta(self, atleta_id, nome, categoria, ano_nascimento, clube):
        """
        Edita os dados de um atleta existente na tabela atletas.
        O ano de nascimento é convertido para uma data com o dia 01/01.
        Verifica se o atleta existe antes da atualização.
        """
        try:
            self.check_connection()
            # Converte o ano para uma data
            data_nasc = date(int(ano_nascimento), 1, 1)
            
            # Verificar se o atleta com o id informado existe
            check_sql = "SELECT id FROM atletas WHERE id = %s;"
            self.cursor.execute(check_sql, (atleta_id,))
            registro = self.cursor.fetchone()
            
            if not registro:
                mensagem = f"Atleta com ID {atleta_id} não encontrado."
                print(mensagem)
                return mensagem

            # Atualiza os dados do atleta
            update_sql = """
                UPDATE atletas
                SET nome = %s, categoria = %s, data_nasc = %s, clube = %s
                WHERE id = %s
                RETURNING id;
            """
            self.cursor.execute(update_sql, (nome, categoria, data_nasc, clube, atleta_id))
            id_atualizado = self.cursor.fetchone()[0]
            self.conn.commit()
            print(f"Atleta com ID {id_atualizado} atualizado com sucesso!")
            return id_atualizado
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception as rollback_error:
                print("Erro no rollback:", rollback_error)
            print("Erro ao editar atleta:", e)
            return str(e)
            
    def listar_atletas_por_clube(self, clube):
        """
        Lista os atletas de um determinado clube.
        Retorna uma lista de tuplas com os campos (id, nome, categoria, data_nasc, clube).
        """
        try:
            self.check_connection()
            sql = "SELECT id, nome, categoria, data_nasc, clube FROM atletas WHERE clube = %s;"
            self.cursor.execute(sql, (clube,))
            return self.cursor.fetchall()
        except Exception as e:
            print("Erro ao listar atletas:", e)
            return []
    
    def adicionar_competicao(self, nome_competicao, data_competicao, classe):
        """
        Adiciona uma nova competição na tabela campeonato.
        
        Parâmetros:
        - nome_competicao: Nome da competição (string, obrigatório)
        - data_competicao: Data da competição (date, obrigatório)
        - classe: Classe ou categoria da competição (string, opcional)
        
        Retorna:
        - O id da competição inserida se a inserção for bem-sucedida,
        ou uma mensagem de erro se a competição já existir.
        """
        try:
            # Verifica se já existe uma competição com o mesmo nome e data
            check_sql = """
                SELECT id FROM campeonato
                WHERE nome_competicao = %s AND data_competicao = %s;
            """
            self.cursor.execute(check_sql, (nome_competicao, data_competicao))
            existente = self.cursor.fetchone()
            if existente:
                mensagem = f"Competição '{nome_competicao}' na data {data_competicao} já cadastrada."
                print(mensagem)
                return None  # ou retorne a mensagem, conforme sua necessidade
            
            # Insere a nova competição
            sql = """
                INSERT INTO campeonato (nome_competicao, data_competicao, classe)
                VALUES (%s, %s, %s)
                RETURNING id;
            """
            self.cursor.execute(sql, (nome_competicao, data_competicao, classe))
            id_competicao = self.cursor.fetchone()[0]
            self.conn.commit()
            print(f"Competição inserida com ID: {id_competicao}")
            return id_competicao
        except Exception as e:
            self.conn.rollback()
            print("Erro ao adicionar competição:", e)
            return str(e)
        
    def listar_competicoes(self):
        """
        Lista todas as competições cadastradas na tabela campeonato.
        Retorna uma lista de tuplas no formato (id, nome_competicao, data_competicao, classe).
        """
        try:
            self.check_connection()
            sql = "SELECT id, nome_competicao, data_competicao, classe FROM campeonato;"
            self.cursor.execute(sql)
            competicoes = self.cursor.fetchall()
            return competicoes
        except Exception as e:
            print("Erro ao listar competições:", e)
            return []
        
    def listar_lutas_por_competicao(self, campeonato_id):
        try:
            self.check_connection()
            sql = """
                SELECT c.id, c.categoria,
                    a1.nome AS atleta1,
                    a2.nome AS atleta2,
                    v.nome AS vencedor,
                    c.tempo_luta
                FROM confrontos c
                JOIN atletas a1 ON c.atleta1_id = a1.id
                JOIN atletas a2 ON c.atleta2_id = a2.id
                LEFT JOIN atletas v ON c.vencedor_id = v.id
                WHERE c.campeonato_id = %s;
            """
            self.cursor.execute(sql, (campeonato_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print("Erro ao listar lutas:", e)
            return []


        
    def listar_todos_atletas(self):
            """
            Lista todos os atletas cadastrados na tabela atletas.
            Retorna uma lista de tuplas no formato (id, nome, categoria, data_nasc, clube).
            """
            try:
                self.check_connection()
                sql = "SELECT id, nome, categoria, data_nasc, clube FROM atletas;"
                self.cursor.execute(sql)
                return self.cursor.fetchall()
            except Exception as e:
                print("Erro ao listar atletas:", e)
                return []
            
    def adicionar_confronto(self, campeonato_id, atleta1_id, atleta2_id, categoria, tempo_luta):
            """
            Adiciona um novo confronto (luta) na tabela confrontos.

            Parâmetros:
            - campeonato_id: ID da competição (int, obrigatório)
            - atleta1_id: ID do primeiro atleta (int, obrigatório)
            - atleta2_id: ID do segundo atleta (int, obrigatório)
            - categoria: Categoria da luta (string, opcional)
            - tempo_luta: Tempo da luta no formato de intervalo (string no formato 'HH:MM:SS', obrigatório)

            Retorna:
            - O id do confronto inserido se a inserção for bem-sucedida,
                ou uma mensagem de erro.
            """
            try:
                # Nota: Se necessário, você pode converter tempo_luta para o formato INTERVAL que seu banco aceita.
                sql = """
                    INSERT INTO confrontos (campeonato_id, atleta1_id, atleta2_id, categoria, tempo_luta)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """
                self.cursor.execute(sql, (campeonato_id, atleta1_id, atleta2_id, categoria, tempo_luta))
                confronto_id = self.cursor.fetchone()[0]
                self.conn.commit()
                print(f"Confronto inserido com ID: {confronto_id}")
                return confronto_id
            except Exception as e:
                self.conn.rollback()
                print("Erro ao adicionar confronto:", e)
                return str(e)
            

    def adicionar_acao(self, confronto_id: int, atleta_id: int, quadrante: int, grupo_golpe: str,
                       tempo_ocorrido: str, mao_direita: str, mao_esquerda: str, efetividade_golpe: str,
                       newaza: bool, direcao: str, partida: str, efetividade_newaza: str):
        """
        Insere uma nova ação na tabela 'acoes'.

        Parâmetros:
          - confronto_id: ID do confronto no qual a ação ocorreu.
          - atleta_id: ID do atleta que realizou a ação.
          - quadrante: Valor do quadrante capturado pela posição da imagem.
          - grupo_golpe: Grupo do golpe (ex: 'Te-Waza', 'Ashi-Waza', etc).
          - tempo_ocorrido: Tempo ocorrido (em formato 'HH:MM:SS' ou outro formato reconhecido pelo banco).
          - mao_direita: Descrição da ação com a mão direita.
          - mao_esquerda: Descrição da ação com a mão esquerda.
          - efetividade_golpe: Efetividade do golpe (ex: 'Yuko', 'Waza-Ari', etc).
          - newaza: Valor booleano indicando se foi realizada ou não a passagem newaza (neste caso, sempre False).
          - direcao: Direção registrada a partir das coordenadas newaza.
          - partida: Origem da passagem (ex: 'Cabeça', 'Costas', etc).
          - efetividade_newaza: Efetividade da passagem newaza.
        
        Retorna:
          - O ID da ação inserida, se a inserção for bem-sucedida.
          - Uma string com a mensagem de erro, caso ocorra alguma exceção.
        """
        try:
            cur = self.conn.cursor()
            insert_query = """
                INSERT INTO acoes (
                    confronto_id, 
                    atleta_id, 
                    quadrante, 
                    grupo_golpe, 
                    tempo_ocorrido, 
                    mao_direita, 
                    mao_esquerda, 
                    efetividade_golpe,
                    newaza, 
                    direcao, 
                    partida, 
                    efetividade_newaza
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            cur.execute(insert_query, (
                confronto_id,
                atleta_id,
                quadrante,
                grupo_golpe,
                tempo_ocorrido,
                mao_direita,
                mao_esquerda,
                efetividade_golpe,
                newaza,
                direcao,
                partida,
                efetividade_newaza
            ))
            acao_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            return acao_id
        except Exception as e:
            self.conn.rollback()
            return str(e)

    def rollback(self):
        """Realiza rollback na transação caso necessário."""
        self.conn.rollback()

    def close(self):
        """Fecha a conexão com o banco de dados."""
        self.conn.close()

    def rollback(self):
        """Realiza rollback na transação caso necessário."""
        self.conn.rollback()

    def close(self):
        """Fecha a conexão com o banco de dados."""
        self.conn.close()
            
    def deletar_confronto(self, confronto_id):
        """
        Exclui um confronto (luta) da tabela confrontos com base no ID informado.
        
        Parâmetros:
        - confronto_id: ID do confronto a ser excluído.

        Retorna:
        - True se a deleção for bem-sucedida, False em caso de erro.
        """
        try:
            self.check_connection()
            sql = "DELETE FROM confrontos WHERE id = %s;"
            self.cursor.execute(sql, (confronto_id,))
            self.conn.commit()
            print(f"Confronto com ID {confronto_id} removido com sucesso!")
            return True
        except Exception as e:
            self.conn.rollback()
            print("Erro ao deletar confronto:", e)
            return False


        
    def fechar_conexao(self):
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()   



def get_db_manager():
    return DBManager()
