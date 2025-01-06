import pdfplumber
import mysql.connector
from fastapi import FastAPI, UploadFile, HTTPException
import os

# Configuração da conexão com o banco de dados
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="teste",
        database="mysql_biblioteca"
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

def insert_paragrafo(artigo_id, conteudo, tipo=None, paragrafo_id=None):
    sql = "INSERT INTO paragrafos (artigo_id, conteudo, tipo, paragrafo_id) VALUES (%s, %s, %s, %s)"
    return execute_insert(sql, (artigo_id, conteudo, tipo, paragrafo_id))

def insert_tabela(capitulo_id, conteudo):
    sql = "INSERT INTO comentarios (paragrafo_id, conteudo) VALUES (%s, %s)"
    return execute_insert(sql, (capitulo_id, conteudo))

# Função para processar tabelas em Markdown
def processar_tabela_pdf(table):
    if not table:
        return None
    markdown_tabela = []
    for row in table:
        linha = "| " + " | ".join(str(cell).strip() for cell in row) + " |"
        markdown_tabela.append(linha)
    # Adicionar separadores entre cabeçalho e corpo da tabela
    if len(markdown_tabela) > 1:
        cabecalho = markdown_tabela[0]
        separador = "| " + " | ".join("---" for _ in cabecalho.split("|")[1:-1]) + " |"
        markdown_tabela.insert(1, separador)
    return "\n".join(markdown_tabela)

# Função para processar o PDF
def processar_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        livro_id = insert_livro("Regimento Interno Comentado")
        titulo_id = None
        capitulo_id = None
        secao_id = None
        artigo_id = None

        for idx, pagina in enumerate(pdf.pages, start=1):
            texto = pagina.extract_text() or ""
            tabelas = pagina.extract_tables()

            linhas = texto.split("\n")
            for linha in linhas:
                linha = linha.strip()

                if linha.startswith("TÍTULO"):
                    titulo_id = insert_titulo(livro_id, linha)
                    capitulo_id = secao_id = artigo_id = None

                elif linha.startswith("CAPÍTULO"):
                    if not titulo_id:
                        titulo_id = insert_titulo(livro_id, "Título Padrão")
                    capitulo_id = insert_capitulo(titulo_id, linha)
                    secao_id = artigo_id = None

                elif linha.startswith("Seção"):
                    if not capitulo_id:
                        capitulo_id = insert_capitulo(titulo_id or livro_id, "Capítulo Padrão")
                    secao_id = insert_secao(capitulo_id, linha)
                    artigo_id = None

                elif linha.startswith("Art."):
                    if not secao_id:
                        secao_id = insert_secao(capitulo_id or titulo_id or livro_id, "Seção Padrão")
                    artigo_id = insert_artigo(secao_id, linha)

                else:
                    if artigo_id:
                        insert_paragrafo(artigo_id, linha)

            if tabelas:
                for tabela in tabelas:
                    markdown_tabela = processar_tabela_pdf(tabela)
                    if markdown_tabela and capitulo_id:
                        insert_tabela(capitulo_id, markdown_tabela)

# Configuração do FastAPI
app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Formato de arquivo inválido. Somente arquivos .pdf são suportados.")

    temp_file_path = f"./temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Processar o PDF
        processar_pdf(temp_file_path)
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
