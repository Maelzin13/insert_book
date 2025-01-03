from docx import Document
from odf.opendocument import load
from odf.text import P

def read_docx(file_path):
    """Lê arquivos .docx e retorna o texto."""
    doc = Document(file_path)
    content = []
    for paragraph in doc.paragraphs:
        content.append(paragraph.text)
    return "\n".join(content)

def read_odt(file_path):
    """Lê arquivos .odt e retorna o texto."""
    doc = load(file_path)
    content = []
    for paragraph in doc.getElementsByType(P):
        content.append(paragraph.firstChild.data if paragraph.firstChild else "")
    return "\n".join(content)

def process_file(file_path):
    """Identifica o tipo de arquivo e processa seu conteúdo."""
    if file_path.endswith('.docx'):
        return read_docx(file_path)
    elif file_path.endswith('.odt'):
        return read_odt(file_path)
    else:
        raise ValueError("Formato de arquivo não suportado. Use .docx ou .odt.")

# Teste o script
if __name__ == "__main__":
    file_path = input("Digite o caminho completo do arquivo (.docx ou .odt): ")
    try:
        content = process_file(file_path)
        print("\nConteúdo do arquivo:\n")
        print(content)
    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")
