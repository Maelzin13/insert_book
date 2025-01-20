from docx import Document
import mysql.connector
from fastapi import FastAPI, UploadFile, HTTPException
import os
import json
import re  # Para trabalhar com marcações ###

# Configuração do Banco de Dados
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="livro_crud"
    )

def execute_insert(sql, params):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(sql, params)
        last_id = cursor.lastrowid
        db.commit()
        return last_id
    except Exception as e:
        print(f"Erro ao executar o SQL: {sql}, Parâmetros: {params}, Erro: {e}")
        raise
    finally:
        cursor.close()
        db.close()

# Funções de Inserção no Banco
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

def insert_paragrafo(artigo_id, conteudo, tipo=None):
    sql = "INSERT INTO paragrafos (artigo_id, conteudo, tipo) VALUES (%s, %s, %s)"
    return execute_insert(sql, (artigo_id, conteudo, tipo))

def insert_quadro(associado_id, tipo, conteudo):
    sql = "INSERT INTO quadros_esquemas (associado_id, tipo, conteudo) VALUES (%s, %s, %s)"
    return execute_insert(sql, (associado_id, tipo, json.dumps(conteudo)))

def insert_nota_rodape(paragrafo_id, conteudo):
    sql = "INSERT INTO nota_rodapes (paragrafo_id, conteudo) VALUES (%s, %s)"
    return execute_insert(sql, (paragrafo_id, conteudo))


def extract_tables_from_docx(doc):
    """
    Extrai as tabelas de um documento do Word (.docx) e as retorna em formato estruturado (JSON).

    :param doc: Documento carregado com python-docx.
    :return: Lista de tabelas, cada uma representada como um dicionário com 'header' e 'rows'.
    """
    tables_data = []

    for table in doc.tables:
        # Extrair cabeçalhos (primeira linha da tabela)
        headers = [cell.text.strip() for cell in table.rows[0].cells]

        # Extrair dados das linhas (exceto a primeira, que é o cabeçalho)
        rows = [
            [cell.text.strip() for cell in row.cells]
            for row in table.rows[1:]  # Ignorar a linha do cabeçalho
        ]

        # Adicionar a tabela ao conjunto de dados
        tables_data.append({
            "header": headers,
            "rows": rows
        })

    return tables_data


# Processar o Documento com Marcações ###
def process_document(file_path):
    document = Document(file_path)
    estrutura = {"paragrafos": [], "tabelas": []}
    current_type = None  # Para armazenar o tipo do parágrafo atual
    buffer = []  # Para agrupar o conteúdo dentro de uma marcação

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue

        # Verificar se a linha é uma marcação ###
        match = re.match(r"###(.+?)###", text)
        if match:
            # Se encontrar uma nova marcação, processar o buffer atual
            if current_type and buffer:
                estrutura["paragrafos"].append({
                    "tipo": current_type,
                    "conteudo": "\n".join(buffer)
                })
                buffer = []

            # Atualizar o tipo atual com a nova marcação
            current_type = match.group(1).strip()
        else:
            # Adicionar o texto ao buffer
            buffer.append(text)

    # Processar o último buffer
    if current_type and buffer:
        estrutura["paragrafos"].append({
            "tipo": current_type,
            "conteudo": "\n".join(buffer)
        })

    # Processar tabelas
    estrutura["tabelas"] = extract_tables_from_docx(document)

    return estrutura

def processar_livro(file_path):
    estrutura = process_document(file_path)
    livro_id = insert_livro("Regimento Interno Comentado")
    print(f"Livro inserido com ID: {livro_id}")

    # Inicializar hierarquia como "Geral"
    titulo_id = insert_titulo(livro_id, "Título Geral")
    capitulo_id = insert_capitulo(titulo_id, "Capítulo Geral")
    secao_id = insert_secao(capitulo_id, "Seção Geral")
    artigo_id = insert_artigo(secao_id, "Artigo Geral")
    print(f"Hierarquia inicial criada: Título Geral > Capítulo Geral > Seção Geral > Artigo Geral")

    for item in estrutura["paragrafos"]:
        tipo = item.get("tipo")
        conteudo = item.get("conteudo")

        try:
            # Processar tipos definidos por marcações ###
            if tipo and tipo.startswith("paragrafo"):
                subtipo = tipo.split(", tipo:")[1].strip() if ", tipo:" in tipo else None
                insert_paragrafo(artigo_id, conteudo, subtipo)
                print(f"Parágrafo inserido: {conteudo} (tipo: {subtipo})")
            elif tipo == "nota_rodapes":
                insert_nota_rodape(artigo_id, conteudo)
                print(f"Nota de rodapé inserida: {conteudo}")
            else:
                # Processar hierarquia padrão sem marcações ###
                if conteudo.startswith("TÍTULO"):
                    titulo_id = insert_titulo(livro_id, conteudo)
                    print(f"Título inserido: {conteudo}")
                    capitulo_id = insert_capitulo(titulo_id, "Capítulo Geral")
                    secao_id = insert_secao(capitulo_id, "Seção Geral")
                    artigo_id = insert_artigo(secao_id, "Artigo Geral")
                elif conteudo.startswith("CAPÍTULO"):
                    capitulo_id = insert_capitulo(titulo_id, conteudo)
                    print(f"Capítulo inserido: {conteudo}")
                    secao_id = insert_secao(capitulo_id, "Seção Geral")
                    artigo_id = insert_artigo(secao_id, "Artigo Geral")
                elif conteudo.startswith("Seção"):
                    secao_id = insert_secao(capitulo_id, conteudo)
                    print(f"Seção inserida: {conteudo}")
                    artigo_id = insert_artigo(secao_id, "Artigo Geral")
                elif conteudo.startswith("Art."):
                    artigo_id = insert_artigo(secao_id, conteudo)
                    print(f"Artigo inserido: {conteudo}")
                else:
                    # Certificar-se de que a hierarquia está completa
                    if artigo_id is None:
                        if secao_id is None:
                            secao_id = insert_secao(capitulo_id, "Seção Geral")
                            print("Seção Geral criada.")
                        if capitulo_id is None:
                            capitulo_id = insert_capitulo(titulo_id, "Capítulo Geral")
                            print("Capítulo Geral criado.")
                        if titulo_id is None:
                            titulo_id = insert_titulo(livro_id, "Título Geral")
                            print("Título Geral criado.")
                        artigo_id = insert_artigo(secao_id, "Artigo Geral")
                        print("Artigo Geral criado.")

                    insert_paragrafo(artigo_id, conteudo)
                    print(f"Parágrafo inserido: {conteudo}")

        except Exception as e:
            print(f"Erro ao processar o item: {conteudo}. Detalhes: {e}")

    # Processar Tabelas
    for tabela in estrutura["tabelas"]:
        insert_quadro(livro_id, "tabela", tabela)
        print(f"Tabela inserida: {tabela['header']}")


# API com FastAPI
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

# Inicialização do Servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
