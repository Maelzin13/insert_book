from docx import Document
import mysql.connector
from fastapi import FastAPI, UploadFile, HTTPException
import os

# Configuração do Banco de Dados
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="teste",
        database="livro_insert"
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

# Funções de Banco de Dados
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
    try:
        sql = "INSERT INTO paragrafos (artigo_id, conteudo, tipo) VALUES (%s, %s, %s)"
        return execute_insert(sql, (artigo_id, conteudo, tipo))
    except Exception as e:
        if "Column 'artigo_id' cannot be null" in str(e):
            raise ValueError("Parágrafo sem 'artigo_id' não pode ser inserido sem um tipo válido.")
        raise

def insert_prefacio():
    print("Inserindo prefácio...")

    # Criar a estrutura geral para o prefácio
    livro_id = insert_livro("Livro Geral")
    titulo_id = insert_titulo(livro_id, "Título do Prefácio")
    capitulo_id = insert_capitulo(titulo_id, "Capítulo do Prefácio")
    secao_id = insert_secao(capitulo_id, "Seção do Prefácio")
    artigo_id = insert_artigo(secao_id, "Artigo do Prefácio")

    # Inserir o conteúdo do prefácio como um parágrafo com o tipo 'prefácio'
    conteudo_prefacio = (
        "CONVENÇÕES\n"
        "▪ As remissões a dispositivos de normas legais diferentes do Regimento são precedidas da respectiva sigla, de acordo com as abreviaturas convencionadas.\n"
        "▪ As remissões a dispositivos não precedidos de sigla se referem ao próprio Regimento.\n\n"
        "ABREVIATURAS\n"
        "Ação Direta de Inconstitucionalidade (ADI)\n"
        "Comissão de Constituição e Justiça e de Cidadania (CCJC)\n"
        "CF- Constituição Federal\n"
        "CN - Congresso Nacional\n"
        "CPI - Comissão Parlamentar de Inquérito\n"
        "CPMI - Comissão Parlamentar Mista de Inquérito\n"
        "DVS - Destaque para Votação em Separado\n"
        "HC - Habeas Corpus\n"
        "INC - Indicação\n"
        "MPV - Medida Provisória\n"
        "MS - Mandado de Segurança\n"
        "MSC - Mensagem\n"
        "PDC - Projeto de Decreto Legislativo (anterior a 2019)\n"
        "PDL - Projeto de Decreto Legislativo (após 2019 (PDL)\n"
        "PEC - Proposta de Emenda à Constituição\n"
        "PL - Projeto de Lei Ordinária\n"
        "PLP - Projeto de Lei Complementar\n"
        "Projeto de Lei de Conversão (PLV)\n"
        "PRC - Projeto de Resolução da Câmara\n"
        "QO - Questão de Ordem\n"
        "REC - Recurso\n"
        "RCCN - Regimento Comum do Congresso Nacional\n"
        "REQ - Requerimento\n"
        "REM - Reclamação\n"
        "RIC - Requerimento de Informação\n"
        "RICD - Regimento Interno da Câmara dos Deputados\n"
        "SGM - Secretaria-Geral da Mesa\n"
        "SDR - Sistema de Deliberação Remota\n"
        "STF - Supremo Tribunal Federal\n"
        "TCU - Tribunal de Contas da União\n"
        "TJDFT - Tribunal de Justiça do Distrito Federal e Territórios\n"
        "TVR – Projeto de Decreto Legislativo relativo a concessão e ou permissão de rádio e televisão"
    )

    insert_paragrafo(artigo_id, conteudo_prefacio, "prefácio")
    print("Prefácio inserido com sucesso.")

def process_document(file_path):
    document = Document(file_path)
    estrutura = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            estrutura.append(text)

    return estrutura

# Processar e inserir o documento no banco
def processar_livro(file_path):
    estrutura = process_document(file_path)
    livro_id = insert_livro("Regimento Interno Comentado")
    print(f"Livro inserido com ID: {livro_id}")

    titulo_id, capitulo_id, secao_id, artigo_id = None, None, None, None

    for linha in estrutura:
        if linha.startswith("TÍTULO"):
            titulo_id = insert_titulo(livro_id, linha)
            print(f"Título inserido: {linha}")
            capitulo_id, secao_id, artigo_id = None, None, None
        elif linha.startswith("CAPÍTULO"):
            if not titulo_id:
                titulo_id = insert_titulo(livro_id, "Título Geral")
                print("Título Geral criado.")
            capitulo_id = insert_capitulo(titulo_id, linha)
            print(f"Capítulo inserido: {linha}")
            secao_id, artigo_id = None, None
        elif linha.startswith("Seção"):
            if not capitulo_id:
                if not titulo_id:
                    titulo_id = insert_titulo(livro_id, "Título Geral")
                    print("Título Geral criado.")
                capitulo_id = insert_capitulo(titulo_id, "Capítulo Geral")
                print("Capítulo Geral criado.")
            secao_id = insert_secao(capitulo_id, linha)
            print(f"Seção inserida: {linha}")
            artigo_id = None
        elif linha.startswith("Art."):
            if not secao_id:
                if not capitulo_id:
                    if not titulo_id:
                        titulo_id = insert_titulo(livro_id, "Título Geral")
                        print("Título Geral criado.")
                    capitulo_id = insert_capitulo(titulo_id, "Capítulo Geral")
                    print("Capítulo Geral criado.")
                secao_id = insert_secao(capitulo_id, "Seção Geral")
                print("Seção Geral criada.")
            artigo_id = insert_artigo(secao_id, linha)
            print(f"Artigo inserido: {linha}")
        else:
            if not artigo_id:
                if not secao_id:
                    if not capitulo_id:
                        if not titulo_id:
                            titulo_id = insert_titulo(livro_id, "Título Geral")
                            print("Título Geral criado.")
                        capitulo_id = insert_capitulo(titulo_id, "Capítulo Geral")
                        print("Capítulo Geral criado.")
                    secao_id = insert_secao(capitulo_id, "Seção Geral")
                    print("Seção Geral criado.")
                artigo_id = insert_artigo(secao_id, "Artigo Geral")
                print("Artigo Geral criado.")
            insert_paragrafo(artigo_id, linha)
            print(f"Parágrafo inserido: {linha}")

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
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar o arquivo: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/insert_prefacio")
async def add_prefacio():
    try:
        insert_prefacio()
        return {"status": "success", "message": "Prefácio inserido com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inserir prefácio: {e}")

# Inicialização do Servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
