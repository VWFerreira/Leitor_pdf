import streamlit as st
import os
import pdfplumber
from login import exibir_login
from fpdf import FPDF
import unicodedata
import re
import io

# Exibe login antes de tudo
exibir_login()

# Funções auxiliares
def remover_unicode(texto):
    return unicodedata.normalize('NFKD', texto).encode('latin-1', 'ignore').decode('latin-1')

def salvar_resposta_pdf_memoria(pergunta, resposta):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pergunta = remover_unicode(pergunta)
    resposta = remover_unicode(resposta)
    pdf.multi_cell(0, 10, f"Pergunta: {pergunta}\n\nResposta: {resposta}")
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

@st.cache_resource
def carregar_pdf(caminho):
    return pdfplumber.open(caminho)

def mapear_clausulas(pdf):
    clausulas = []
    for i, page in enumerate(pdf.pages):
        texto = page.extract_text()
        if texto:
            matches = re.findall(r'(CL[ÁA]USULA\s+[A-ZÊÉÃÇÀÚÍÓÌÂÔÊÙ]+(?:\s+[A-ZÊÉÃÇÀÚÍÓÌÂÔÊÙ]+)*\s*[-–—]\s*[^\n\.]+)', texto, re.IGNORECASE)
            for match in matches:
                clausulas.append({"titulo": match.strip(), "pagina": i})
    return clausulas

def extrair_corpo_clausula_pagina(pdf, titulo, pagina_inicial):
    texto = ""
    for i in range(pagina_inicial, min(pagina_inicial + 3, len(pdf.pages))):
        texto += pdf.pages[i].extract_text() + "\n"
    padrao = re.compile(rf'({re.escape(titulo)})(.*?)(?=CL[ÁA]USULA\s+[A-ZÊÉÃÇ]+\s+[A-Z]+\s*[-–—]|\Z)', re.DOTALL | re.IGNORECASE)
    match = padrao.search(texto)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return titulo, "Não foi possível localizar o conteúdo da cláusula."

# Interface
st.image("img/logo1.png", width=160)
st.markdown("### CONTRATOS")
st.title("Leitor de Contratos")

pasta_pdfs = "pdfs"
os.makedirs(pasta_pdfs, exist_ok=True)

uploaded_file = st.file_uploader("Envie um arquivo PDF", type="pdf")
if uploaded_file:
    caminho_salvo = os.path.join(pasta_pdfs, uploaded_file.name)
    with open(caminho_salvo, "wb") as f:
        f.write(uploaded_file.read())
    st.success(f"Arquivo '{uploaded_file.name}' salvo com sucesso!")

arquivos_existentes = [f for f in os.listdir(pasta_pdfs) if f.endswith(".pdf")]
pdf_escolhido = st.selectbox("Selecione um PDF da pasta:", sorted(set(arquivos_existentes)))
usuario = st.session_state.get("usuario", "usuário_desconhecido")

if pdf_escolhido:
    caminho_pdf = os.path.join(pasta_pdfs, pdf_escolhido)
    pdf = carregar_pdf(caminho_pdf)
    clausulas_mapeadas = mapear_clausulas(pdf)

    titulos = sorted(set([c["titulo"] for c in clausulas_mapeadas]))
    clausula_escolhida = st.selectbox("Selecione a cláusula para visualizar:", titulos)

    if clausula_escolhida:
        pagina = next(c["pagina"] for c in clausulas_mapeadas if c["titulo"] == clausula_escolhida)
        titulo, corpo = extrair_corpo_clausula_pagina(pdf, clausula_escolhida, pagina)
        st.markdown(f"### {titulo}")
        st.write(corpo)

        if st.button("Salvar cláusula como PDF"):
            buffer = salvar_resposta_pdf_memoria(titulo, corpo)
            st.download_button("📄 Baixar PDF da Cláusula", buffer, file_name=f"resposta_{usuario}.pdf")

    # Busca leve por palavra-chave
    st.markdown("---")
    st.subheader("🔍 Buscar palavra-chave")
    palavra_chave = st.text_input("Digite a palavra-chave:")
    if palavra_chave:
        resultados = []
        for i, page in enumerate(pdf.pages):
            texto = page.extract_text()
            if texto and palavra_chave.lower() in texto.lower():
                resultados.append((i+1, texto.strip()[:200]))

        if resultados:
            st.success(f"Encontrado em {len(resultados)} página(s):")
            for pagina, trecho in resultados:
                st.markdown(f"**Página {pagina}:** {trecho}...")
        else:
            st.warning("Palavra não encontrada no documento.")

# Rodapé
st.markdown(
    """
    <hr style="margin-top: 50px; margin-bottom:10px; border: 1px solid #444;">
    <div style="text-align: center; color: gray; font-size: 14px;">
        By Vilmar William Ferreira • © 2025
    </div>
    """,
    unsafe_allow_html=True
)

