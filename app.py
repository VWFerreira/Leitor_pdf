import streamlit as st
import os
import pdfplumber
from login import exibir_login
from fpdf import FPDF
import unicodedata
import re
import io
from transformers import pipeline

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
            matches = re.findall(r'(CL[\u00c1A]USULA\s+[A-Z\u00ca\u00c9\u00c3\u00c7\u00c0\u00da\u00cd\u00d3\u00cc\u00c2\u00d4\u00ca\u00d9]+(?:\s+[A-Z\u00ca\u00c9\u00c3\u00c7\u00c0\u00da\u00cd\u00d3\u00cc\u00c2\u00d4\u00ca\u00d9]+)*\s*[-–—]\s*[^\n\.]+)', texto, re.IGNORECASE)
            for match in matches:
                clausulas.append({"titulo": match.strip(), "pagina": i})
    return clausulas

def extrair_corpo_clausula_pagina(pdf, titulo, pagina_inicial):
    texto = ""
    for i in range(pagina_inicial, min(pagina_inicial + 3, len(pdf.pages))):
        texto += pdf.pages[i].extract_text() + "\n"
    padrao = re.compile(rf'({re.escape(titulo)})(.*?)(?=CL[\u00c1A]USULA\s+[A-Z\u00ca\u00c9\u00c3\u00c7]+\s+[A-Z]+\s*[-–—]|\Z)', re.DOTALL | re.IGNORECASE)
    match = padrao.search(texto)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return titulo, "Não foi possível localizar o conteúdo da cláusula."

# Modelo de perguntas e respostas
@st.cache_resource
def carregar_modelo_qa():
    return pipeline("question-answering", model="deepset/roberta-base-squad2")

qa_modelo = carregar_modelo_qa()

def responder_por_bloco(pergunta, texto_completo, tamanho_bloco=1000):
    blocos = [texto_completo[i:i+tamanho_bloco] for i in range(0, len(texto_completo), tamanho_bloco)]
    melhores = []
    for bloco in blocos:
        try:
            resposta = qa_modelo(question=pergunta, context=bloco)
            if resposta["score"] > 0.3 and resposta["answer"].strip():
                melhores.append(resposta)
        except:
            continue
    if melhores:
        melhores.sort(key=lambda x: x["score"], reverse=True)
        return melhores[0]["answer"]
    return "Não foi possível localizar uma resposta confiável no documento."

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

    # Busca por palavra-chave
    st.markdown("---")
    st.subheader("🔍 Buscar por palavra-chave no PDF")

    busca = st.text_input("Digite a palavra ou frase que deseja buscar:")
    if busca:
        resultados = []
        for i, page in enumerate(pdf.pages):
            texto = page.extract_text()
            if texto and re.search(re.escape(busca), texto, re.IGNORECASE):
                trecho = re.findall(rf'(.{{0,60}}{re.escape(busca)}.{{0,60}})', texto, re.IGNORECASE)
                for t in trecho:
                    resultados.append((i + 1, t.strip()))

        if resultados:
            st.success(f"Foram encontrados {len(resultados)} trechos com a palavra '{busca}':")
            for pagina, trecho in resultados:
                st.markdown(f"**Página {pagina}**: {trecho}...")
        else:
            st.warning("Nenhum resultado encontrado.")

    # Pergunta com IA
    st.markdown("---")
    st.subheader("🧐 Fazer uma pergunta sobre o conteúdo do PDF")

    pergunta_usuario = st.text_input("Digite sua pergunta:")
    if pergunta_usuario:
        st.info("Lendo o conteúdo do PDF...")
        texto_pdf_completo = ""
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                texto_pdf_completo += texto.replace("-\n", "").replace("\n", " ") + "\n"

        st.success("Texto carregado. Gerando resposta...")
        resposta_ia = responder_por_bloco(pergunta_usuario, texto_pdf_completo)
        st.markdown(f"**Resposta:** {resposta_ia}")

        if st.button("Salvar resposta em PDF"):
            buffer = salvar_resposta_pdf_memoria(pergunta_usuario, resposta_ia)
            st.download_button("📄 Baixar resposta", buffer, file_name=f"resposta_{usuario}.pdf")

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