from docx import Document
import mysql.connector
from fastapi import FastAPI, UploadFile, HTTPException
import os

# Configuração da conexão com o banco de dados
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="teste",
        database="livro_insert"
    )

# Função genérica para executar inserts e retornar o ID inserido
def execute_insert(sql, params):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(sql, params)
        last_id = cursor.lastrowid
        db.commit()
        return last_id
    except mysql.connector.errors.IntegrityError as e:
        print(f"Erro de integridade: {e}")
        print(f"SQL: {sql}, Parâmetros: {params}")
        raise
    finally:
        cursor.close()
        db.close()

# Funções de inserção específicas
def insert_livro(conteudo):
    sql = "INSERT INTO livros (conteudo) VALUES (%s)"
    return execute_insert(sql, (conteudo,))

def insert_titulo(livro_id, conteudo):
    sql = "INSERT INTO titulos (livro_id, conteudo) VALUES (%s, %s)"
    return execute_insert(sql, (livro_id, conteudo))

def insert_capitulo(titulo_id, conteudo):
    sql = "INSERT INTO capitulos (titulo_id, conteudo) VALUES (%s, %s)"
    return execute_insert(sql, (titulo_id, conteudo))

def insert_secao(capitulo_id, conteudo):
    sql = "INSERT INTO secaos (capitulo_id, conteudo) VALUES (%s, %s)"
    return execute_insert(sql, (capitulo_id, conteudo))

def insert_artigo(secao_id, conteudo):
    sql = "INSERT INTO artigos (secao_id, conteudo) VALUES (%s, %s)"
    return execute_insert(sql, (secao_id, conteudo))

def insert_paragrafo(artigo_id, conteudo):
    sql = "INSERT INTO paragrafos (artigo_id, conteudo) VALUES (%s, %s)"
    return execute_insert(sql, (artigo_id, conteudo))

# Função para processar o arquivo .docx
def processar_arquivo(file_path):
    document = Document(file_path)
    conteudo_geral = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return conteudo_geral

# Função para processar o livro
def processar_livro(file_path):
    conteudo_geral = processar_arquivo(file_path)

    # Criar um novo livro
    livro_id = insert_livro("Regimento Interno Comentado")
    print(f"Livro inserido com ID: {livro_id}")

    # Variáveis para rastrear a hierarquia
    titulo_id, capitulo_id, secao_id, artigo_id = None, None, None, None

    for linha in conteudo_geral:
        linha = linha.strip()

        if linha.startswith("TÍTULO"):
            titulo_id = insert_titulo(livro_id, linha)
            capitulo_id = secao_id = artigo_id = None
            print(f"Título inserido: {linha}")

        elif linha.startswith("CAPÍTULO"):
            if not titulo_id:
                print("ERRO: Título não definido antes do capítulo. Criando título padrão.")
                titulo_id = insert_titulo(livro_id, "Título Padrão")
                print(f"Título padrão criado com ID: {titulo_id}")
            capitulo_id = insert_capitulo(titulo_id, linha)
            secao_id = artigo_id = None
            print(f"Capítulo inserido: {linha}")

        elif linha.startswith("Seção"):
            if not capitulo_id:
                print("ERRO: Capítulo não definido antes da seção. Criando hierarquia padrão.")
                if not titulo_id:
                    titulo_id = insert_titulo(livro_id, "Título Padrão")
                    print(f"Título padrão criado com ID: {titulo_id}")
                capitulo_id = insert_capitulo(titulo_id, "Capítulo Padrão")
                print(f"Capítulo padrão criado com ID: {capitulo_id}")
            secao_id = insert_secao(capitulo_id, linha)
            artigo_id = None
            print(f"Seção inserida: {linha}")

        elif linha.startswith("Art."):
            if not secao_id:
                print("ERRO: Seção não definida antes do artigo. Criando hierarquia padrão.")
                if not capitulo_id:
                    if not titulo_id:
                        titulo_id = insert_titulo(livro_id, "Título Padrão")
                        print(f"Título padrão criado com ID: {titulo_id}")
                    capitulo_id = insert_capitulo(titulo_id, "Capítulo Padrão")
                    print(f"Capítulo padrão criado com ID: {capitulo_id}")
                secao_id = insert_secao(capitulo_id, "Seção Padrão")
                print(f"Seção padrão criada com ID: {secao_id}")
            artigo_id = insert_artigo(secao_id, linha)
            print(f"Artigo inserido: {linha}")

        else:
            if not artigo_id:
                print("ERRO: Nenhum artigo definido. Criando hierarquia padrão.")
                if not secao_id:
                    if not capitulo_id:
                        if not titulo_id:
                            titulo_id = insert_titulo(livro_id, "Título Padrão")
                            print(f"Título padrão criado com ID: {titulo_id}")
                        capitulo_id = insert_capitulo(titulo_id, "Capítulo Padrão")
                        print(f"Capítulo padrão criado com ID: {capitulo_id}")
                    secao_id = insert_secao(capitulo_id, "Seção Padrão")
                    print(f"Seção padrão criada com ID: {secao_id}")
                artigo_id = insert_artigo(secao_id, "Artigo Padrão")
                print(f"Artigo padrão criado com ID: {artigo_id}")
            insert_paragrafo(artigo_id, linha)
            print(f"Parágrafo inserido no Artigo com ID {artigo_id}: {linha}")

# Configuração do FastAPI
app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile):
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Formato de arquivo inválido. Somente arquivos .docx são suportados.")

    temp_file_path = f"./temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        processar_livro(temp_file_path)
        return {"status": "success", "message": f"Arquivo '{file.filename}' processado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar o arquivo: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# Inicialização do servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
