from docx import Document
import mysql.connector

# Configuração da conexão com o banco de dados
def get_db_connection():
    return mysql.connector.connect(
       host="localhost",
        user="root",
        password="teste",
        database="livro_insert"
    )

# Funções de inserção no banco de dados
def insert_livro(conteudo):
    db = get_db_connection()
    cursor = db.cursor()

    sql = "INSERT INTO livros (conteudo) VALUES (%s)"
    cursor.execute(sql, (conteudo,))
    livro_id = cursor.lastrowid

    db.commit()
    cursor.close()
    db.close()

    return livro_id

def insert_titulo(livro_id, conteudo):
    db = get_db_connection()
    cursor = db.cursor()

    sql = "INSERT INTO titulos (livro_id, conteudo) VALUES (%s, %s)"
    cursor.execute(sql, (livro_id, conteudo))
    titulo_id = cursor.lastrowid

    db.commit()
    cursor.close()
    db.close()

    return titulo_id

def insert_capitulo(titulo_id, conteudo):
    db = get_db_connection()
    cursor = db.cursor()

    sql = "INSERT INTO capitulos (titulo_id, conteudo) VALUES (%s, %s)"
    cursor.execute(sql, (titulo_id, conteudo))
    capitulo_id = cursor.lastrowid

    db.commit()
    cursor.close()
    db.close()

    return capitulo_id

def insert_secao(capitulo_id, conteudo):
    db = get_db_connection()
    cursor = db.cursor()

    sql = "INSERT INTO secaos (capitulo_id, conteudo) VALUES (%s, %s)"
    cursor.execute(sql, (capitulo_id, conteudo))
    secao_id = cursor.lastrowid

    db.commit()
    cursor.close()
    db.close()

    return secao_id

# Função para processar o arquivo .docx
def processar_arquivo(file_path):
    document = Document(file_path)
    conteudo_geral = []
    
    for paragraph in document.paragraphs:
        if paragraph.text.strip():  # Ignorar parágrafos vazios
            conteudo_geral.append(paragraph.text.strip())
    
    return conteudo_geral

# Processar conteúdo do livro e inserir no banco
def processar_livro(file_path):
    # Ler conteúdo do arquivo .docx
    conteudo_geral = processar_arquivo(file_path)
    
    # Criar um novo livro
    livro_id = insert_livro("Regimento Interno Comentado")
    print(f"Livro inserido com ID: {livro_id}")

    # Exemplo de parsing e inserção hierárquica (ajuste conforme necessário)
    titulo_id, capitulo_id = None, None
    for linha in conteudo_geral:
        if linha.startswith("TÍTULO"):
            titulo_id = insert_titulo(livro_id, linha)
            print(f"Título inserido: {linha}")
        elif linha.startswith("CAPÍTULO"):
            capitulo_id = insert_capitulo(titulo_id, linha)
            print(f"Capítulo inserido: {linha}")
        elif linha.startswith("Art."):
            secao_id = insert_secao(capitulo_id, linha)
            print(f"Seção inserida: {linha}")
        else:
            print(f"Conteúdo ignorado ou adicional: {linha}")

# Executar o script
if __name__ == "__main__":
    file_path = "/Users/ismael/Downloads/TEXTO PARCIAL REGIMENTO COMENTADO 10-12-2024.docx"
    processar_livro(file_path)

