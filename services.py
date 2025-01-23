from docx import Document
from lxml import etree
from zipfile import ZipFile
import mysql.connector
from fastapi import FastAPI, UploadFile, HTTPException
import os
import json
import re

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

def insert_nota_rodape(associado_a, associado_id, conteudo):
    sql = "INSERT INTO nota_rodapes (associado_a, associado_id, conteudo) VALUES (%s, %s, %s)"
    return execute_insert(sql, (associado_a, associado_id, conteudo))

def insert_remissao(paragrafo_id, conteudo):
    sql = "INSERT INTO remissaos (paragrafo_de_id, conteudo) VALUES (%s, %s)"
    return execute_insert(sql, (paragrafo_id, conteudo))

# Extração de Notas de Rodapé
def extract_notes(docx_path, note_type="footnotes"):
    notes = []
    with ZipFile(docx_path, 'r') as docx:
        xml_path = f"word/{note_type}.xml"
        if xml_path in docx.namelist():
            with docx.open(xml_path) as xml_file:
                xml_content = xml_file.read()
                tree = etree.fromstring(xml_content)
                namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                for note in tree.xpath("//w:footnote | //w:endnote", namespaces=namespace):
                    note_id = note.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id")
                    content = "".join(note.xpath(".//w:t/text()", namespaces=namespace))
                    notes.append({"id": note_id, "content": content})
    return notes

def extract_tables_from_docx(doc):
    tables_data = []
    for table in doc.tables:
        headers = [cell.text.strip() for cell in table.rows[0].cells]
        rows = [
            [cell.text.strip() for cell in row.cells]
            for row in table.rows[1:]
        ]
        tables_data.append({
            "header": headers,
            "rows": rows
        })
    return tables_data

# Processar o Documento com Marcações ###
def process_document(file_path):
    document = Document(file_path)
    estrutura = {"elementos": [], "tabelas": [], "notas_rodape": {}}

    # Extraindo notas de rodapé
    notas = extract_notes(file_path, "footnotes")
    for nota in notas:
        estrutura["notas_rodape"][f"###nota {nota['id']}###"] = nota["content"]

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue

        match = re.match(r"###(.+?)###", text)
        if match:
            tipo = match.group(1).strip()
            estrutura["elementos"].append({"tipo": tipo, "conteudo": ""})
        else:
            if estrutura["elementos"]:
                estrutura["elementos"][-1]["conteudo"] += text + "\n"

    estrutura["tabelas"] = extract_tables_from_docx(document)

    return estrutura

def processar_livro(file_path):
    estrutura = process_document(file_path)
    livro_id = insert_livro("Regimento Interno Comentado")
    print(f"Livro inserido com ID: {livro_id}")
    titulo_id = insert_titulo(livro_id, "Título Geral")
    capitulo_id = insert_capitulo(titulo_id, "Capítulo Geral")
    secao_id = insert_secao(capitulo_id, "Seção Geral")
    artigo_id = insert_artigo(secao_id, "Artigo Geral")
    
    for elemento in estrutura["elementos"]:
        tipo = elemento["tipo"]
        conteudo = elemento["conteudo"].strip()

        if not conteudo:
            continue

        for nota_ref, nota_conteudo in estrutura["notas_rodape"].items():
            if nota_ref in conteudo:
                conteudo = conteudo.replace(nota_ref, "") 
                insert_nota_rodape(tipo, livro_id, nota_conteudo)  # Associa a nota ao elemento
                print(f"Nota de rodapé associada: {nota_ref} -> {nota_conteudo}")

        if tipo == "titulos":
            titulo_id = insert_titulo(livro_id, conteudo)
            print(f"Título inserido: {conteudo}")
        elif tipo == "capitulos":
            capitulo_id = insert_capitulo(titulo_id, conteudo)
            print(f"Capítulo inserido: {conteudo}")
        elif tipo == "secaos":
            secao_id = insert_secao(capitulo_id, conteudo)
            print(f"Seção inserida: {conteudo}")
        elif tipo == "artigos":
            artigo_id = insert_artigo(capitulo_id, conteudo)
            print(f"Artigo inserido: {conteudo}")
        elif tipo.startswith("paragrafo"):
            tipo_paragrafo = re.search(r"tipo: (.+)", tipo)
            tipo_paragrafo = tipo_paragrafo.group(1) if tipo_paragrafo else None
            insert_paragrafo(artigo_id, conteudo, tipo_paragrafo)
            print(f"Parágrafo inserido: {conteudo}")
        elif tipo == "remissaos":
            if 'artigo_id' not in locals():
                artigo_id = insert_artigo(secao_id, "Artigo Geral")
                print(f"Artigo Geral inserido com ID: {artigo_id}")
            insert_remissao(artigo_id, conteudo)
            print(f"Remissão inserida: {conteudo}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)