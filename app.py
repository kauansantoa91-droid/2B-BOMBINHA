import os
import re
import io
import json
import base64
import textwrap
import requests
from datetime import datetime
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    Flowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from num2words import num2words

st.set_page_config(
    page_title="Painel de Automacao de Documentos",
    page_icon="🛡️",
    layout="wide"
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .titulo { text-align: center; font-size: 2.2rem; font-weight: bold; color: #ffffff; margin-bottom: 0px; }
    .subtitulo { text-align: center; color: #8a99ad; margin-bottom: 30px; }
    .bloco-secao { background-color: #161b22; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #30363d; }
    input { color: #000000 !important; font-weight: 600 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_BANCO = os.path.join(PASTA_SCRIPT, "usuarios.json")
ASSETS = os.path.join(PASTA_SCRIPT, "assets")
PASTA_LOGOS_BANCO = os.path.join(ASSETS, "logo_banco")
PASTA_LOGOS_ESTADOS = os.path.join(ASSETS, "logo_estados")
PASTA_DADOS = os.path.join(ASSETS, "dados")
PASTA_LOGOS = os.path.join(ASSETS, "logos")

LOGO_CABECALHO = "logo_cabecalho.png"
LOGO_RODAPE = "logo_rodape.png"
LOGO_MARCA_DAGUA = "marca_dagua.png"
QRCODE = "qrcode.png"

ESTADOS = {
    "AC": {"nome": "Acre", "governo": "GOVERNO DO ESTADO DO ACRE", "policia": "POLICIA CIVIL DO ESTADO DO ACRE", "endereco": "Rua Quintino Bocaiuva, 1490 - Bosque, Rio Branco - AC, 69900-640, TEL.: (68) 3212-4000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "CARLOS EDUARDO MENDES OLIVEIRA", "investigador_cargo": "Investigador Policial - 112.045-1"},
    "AL": {"nome": "Alagoas", "governo": "GOVERNO DO ESTADO DE ALAGOAS", "policia": "POLICIA CIVIL DO ESTADO DE ALAGOAS", "endereco": "Av. Fernandes Lima, 2345 - Farol, Maceio - AL, 57050-000, TEL.: (82) 3315-2400", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "ROBERTO ALVES COSTA NETO", "investigador_cargo": "Investigador Policial - 223.118-4"},
    "AP": {"nome": "Amapa", "governo": "GOVERNO DO ESTADO DO AMAPA", "policia": "POLICIA CIVIL DO ESTADO DO AMAPA", "endereco": "Av. FAB, 1685 - Central, Macapa - AP, 68900-074, TEL.: (96) 3212-5800", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "PAULO HENRIQUE SILVA RAMOS", "investigador_cargo": "Investigador Policial - 089.334-2"},
    "AM": {"nome": "Amazonas", "governo": "GOVERNO DO ESTADO DO AMAZONAS", "policia": "POLICIA CIVIL DO ESTADO DO AMAZONAS", "endereco": "Av. Andre Araujo, 1923 - Aleixo, Manaus - AM, 69060-000, TEL.: (92) 3648-1000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "MARCOS VINICIUS FERREIRA LIMA", "investigador_cargo": "Investigador Policial - 445.201-8"},
    "BA": {"nome": "Bahia", "governo": "GOVERNO DO ESTADO DA BAHIA", "policia": "POLICIA CIVIL DO ESTADO DA BAHIA", "endereco": "Av. Centenario, 2883 - Chame-Chame, Salvador - BA, 40155-150, TEL.: (71) 3116-6000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "JULIO CESAR SANTOS BARBOSA", "investigador_cargo": "Investigador Policial - 567.890-3"},
    "CE": {"nome": "Ceara", "governo": "GOVERNO DO ESTADO DO CEARA", "policia": "POLICIA CIVIL DO ESTADO DO CEARA", "endereco": "Av. Bezerra de Menezes, 581 - Sao Gerardo, Fortaleza - CE, 60325-000, TEL.: (85) 3101-2000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "FRANCISCO DAS CHAGAS MOURA", "investigador_cargo": "Investigador Policial - 334.672-1"},
    "DF": {"nome": "Distrito Federal", "governo": "GOVERNO DO DISTRITO FEDERAL", "policia": "POLICIA CIVIL DO DISTRITO FEDERAL", "endereco": "SAF Sul Quadra 6 - Zona Civico-Administrativa, Brasilia - DF, 70040-912, TEL.: (61) 3207-4000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "RICARDO ALMEIDA PINTO JUNIOR", "investigador_cargo": "Investigador Policial - 901.245-6"},
    "ES": {"nome": "Espirito Santo", "governo": "GOVERNO DO ESTADO DO ESPIRITO SANTO", "policia": "POLICIA CIVIL DO ESTADO DO ESPIRITO SANTO", "endereco": "Av. Governador Bley, 236 - Centro, Vitoria - ES, 29010-150, TEL.: (27) 3636-1100", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "ANDERSON LUIZ PEREIRA GOMES", "investigador_cargo": "Investigador Policial - 178.456-9"},
    "GO": {"nome": "Goias", "governo": "GOVERNO DO ESTADO DE GOIAS", "policia": "POLICIA CIVIL DO ESTADO DE GOIAS", "endereco": "Av. Anhanguera, 7171 - St. Oeste, Goiania - GO, 74110-010, TEL.: (62) 3201-1500", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "DIEGO FERNANDES CASTRO SILVA", "investigador_cargo": "Investigador Policial - 612.903-5"},
    "MA": {"nome": "Maranhao", "governo": "GOVERNO DO ESTADO DO MARANHAO", "policia": "POLICIA CIVIL DO ESTADO DO MARANHAO", "endereco": "Av. dos Holandeses, s/n - Calhau, Sao Luis - MA, 65071-380, TEL.: (98) 3214-8000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "RAFAEL SOUSA NASCIMENTO", "investigador_cargo": "Investigador Policial - 256.781-0"},
    "MT": {"nome": "Mato Grosso", "governo": "GOVERNO DO ESTADO DE MATO GROSSO", "policia": "POLICIA CIVIL DO ESTADO DE MATO GROSSO", "endereco": "Av. Escolastico, 346 - Bandeirantes, Cuiaba - MT, 78010-200, TEL.: (65) 3613-5630", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "023ª Delegacia", "investigador": "ANDRE RELVA SANTANA GANANÇA", "investigador_cargo": "Investigador Policial - 968.961-3"},
    "MS": {"nome": "Mato Grosso do Sul", "governo": "GOVERNO DO ESTADO DE MATO GROSSO DO SUL", "policia": "POLICIA CIVIL DO ESTADO DE MATO GROSSO DO SUL", "endereco": "Rua Rui Barbosa, 3500 - Monte Castelo, Campo Grande - MS, 79010-220, TEL.: (67) 3318-4000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "LUCIANO ROBERTO DIAS MELO", "investigador_cargo": "Investigador Policial - 401.556-7"},
    "MG": {"nome": "Minas Gerais", "governo": "GOVERNO DO ESTADO DE MINAS GERAIS", "policia": "POLICIA CIVIL DO ESTADO DE MINAS GERAIS", "endereco": "Av. Presidente Carlos Luz, 1275 - Caiçaras, Belo Horizonte - MG, 31230-000, TEL.: (31) 3330-7000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "GUSTAVO HENRIQUE CAMPOS REIS", "investigador_cargo": "Investigador Policial - 789.012-4"},
    "PA": {"nome": "Para", "governo": "GOVERNO DO ESTADO DO PARA", "policia": "POLICIA CIVIL DO ESTADO DO PARA", "endereco": "Av. Magalhaes Barata, 651 - Sao Bras, Belem - PA, 66063-240, TEL.: (91) 3201-2000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "EDUARDO BRITO FIGUEIREDO", "investigador_cargo": "Investigador Policial - 345.678-2"},
    "PB": {"nome": "Paraiba", "governo": "GOVERNO DO ESTADO DA PARAIBA", "policia": "POLICIA CIVIL DO ESTADO DA PARAIBA", "endereco": "Av. Duarte da Silveira, 600 - Centro, Joao Pessoa - PB, 58013-280, TEL.: (83) 3218-5000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "THIAGO LACERDA FREITAS", "investigador_cargo": "Investigador Policial - 512.349-8"},
    "PR": {"nome": "Parana", "governo": "GOVERNO DO ESTADO DO PARANA", "policia": "POLICIA CIVIL DO ESTADO DO PARANA", "endereco": "Rua Desembargador Westphalen, 35 - Centro, Curitiba - PR, 80010-110, TEL.: (41) 3313-1000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "FELIPE AUGUSTO RODRIGUES", "investigador_cargo": "Investigador Policial - 678.901-3"},
    "PE": {"nome": "Pernambuco", "governo": "GOVERNO DO ESTADO DE PERNAMBUCO", "policia": "POLICIA CIVIL DO ESTADO DE PERNAMBUCO", "endereco": "Rua da Aurora, 485 - Boa Vista, Recife - PE, 50050-000, TEL.: (81) 3181-2000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "BRUNO CESAR ALBUQUERQUE", "investigador_cargo": "Investigador Policial - 234.567-1"},
    "PI": {"nome": "Piaui", "governo": "GOVERNO DO ESTADO DO PIAUI", "policia": "POLICIA CIVIL DO ESTADO DO PIAUI", "endereco": "Av. Frei Serafim, 2352 - Centro/Sul, Teresina - PI, 64001-020, TEL.: (86) 3216-1000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "LEONARDO MATOS VIEIRA", "investigador_cargo": "Investigador Policial - 890.123-5"},
    "RJ": {"nome": "Rio de Janeiro", "governo": "GOVERNO DO ESTADO DO RIO DE JANEIRO", "policia": "POLICIA CIVIL DO ESTADO DO RIO DE JANEIRO", "endereco": "Rua da Relacao, 42 - Centro, Rio de Janeiro - RJ, 20231-110, TEL.: (21) 2332-8000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "MARCELO ANDRADE TEIXEIRA", "investigador_cargo": "Investigador Policial - 456.789-0"},
    "RN": {"nome": "Rio Grande do Norte", "governo": "GOVERNO DO ESTADO DO RIO GRANDE DO NORTE", "policia": "POLICIA CIVIL DO ESTADO DO RIO GRANDE DO NORTE", "endereco": "Av. Coronel Estevam, 1959 - Alecrim, Natal - RN, 59020-000, TEL.: (84) 3232-2000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "PEDRO HENRIQUE DANTAS", "investigador_cargo": "Investigador Policial - 123.456-7"},
    "RS": {"nome": "Rio Grande do Sul", "governo": "GOVERNO DO ESTADO DO RIO GRANDE DO SUL", "policia": "POLICIA CIVIL DO ESTADO DO RIO GRANDE DO SUL", "endereco": "Av. Joao Pessoa, 2050 - Cidade Baixa, Porto Alegre - RS, 90040-000, TEL.: (51) 3288-1000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "ALEXANDRE SCHMIDT OLIVEIRA", "investigador_cargo": "Investigador Policial - 567.234-8"},
    "RO": {"nome": "Rondonia", "governo": "GOVERNO DO ESTADO DE RONDONIA", "policia": "POLICIA CIVIL DO ESTADO DE RONDONIA", "endereco": "Av. Presidente Dutra, 2986 - Centro, Porto Velho - RO, 76801-086, TEL.: (69) 3216-5000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "WELLINGTON SOUZA CARVALHO", "investigador_cargo": "Investigador Policial - 678.345-9"},
    "RR": {"nome": "Roraima", "governo": "GOVERNO DO ESTADO DE RORAIMA", "policia": "POLICIA CIVIL DO ESTADO DE RORAIMA", "endereco": "Av. Ville Roy, 5245 - Sao Vicente, Boa Vista - RR, 69303-340, TEL.: (95) 3621-1000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "JOSE ROBERTO ALMEIDA", "investigador_cargo": "Investigador Policial - 089.012-3"},
    "SC": {"nome": "Santa Catarina", "governo": "GOVERNO DO ESTADO DE SANTA CATARINA", "policia": "POLICIA CIVIL DO ESTADO DE SANTA CATARINA", "endereco": "Rua Paschoal Apostolo Pitsica, 4840 - Agronomica, Florianopolis - SC, 88025-255, TEL.: (48) 3665-6000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "RODRIGO MACHADO BORGES", "investigador_cargo": "Investigador Policial - 345.901-2"},
    "SP": {"nome": "Sao Paulo", "governo": "GOVERNO DO ESTADO DE SAO PAULO", "policia": "POLICIA CIVIL DO ESTADO DE SAO PAULO", "endereco": "Av. Sao Luis, 99 - Republica, Sao Paulo - SP, 01046-001, TEL.: (11) 3311-3000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "RENATO APARECIDO SILVA", "investigador_cargo": "Investigador Policial - 812.345-6"},
    "SE": {"nome": "Sergipe", "governo": "GOVERNO DO ESTADO DE SERGIPE", "policia": "POLICIA CIVIL DO ESTADO DE SERGIPE", "endereco": "Av. Ministro Geraldo Barreto Sobral, 215 - Capucho, Aracaju - SE, 49080-470, TEL.: (79) 3226-1000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "DANIEL SANTOS MENEZES", "investigador_cargo": "Investigador Policial - 456.012-7"},
    "TO": {"nome": "Tocantins", "governo": "GOVERNO DO ESTADO DO TOCANTINS", "policia": "POLICIA CIVIL DO ESTADO DO TOCANTINS", "endereco": "Av. Teotonio Segurado, 102 Sul - Plano Diretor Sul, Palmas - TO, 77016-002, TEL.: (63) 3218-4000", "delegacia": "Delegacia Especializada de Repressao a Crimes Ciberneticos", "origem": "Delegacia de Policia Digital", "circunscricao": "01ª Delegacia", "investigador": "FABIANO COSTA LIMA", "investigador_cargo": "Investigador Policial - 567.890-1"},
}
UFS_ORDENADAS = sorted(ESTADOS.keys())

def carregar_banco():
    if os.path.exists(ARQUIVO_BANCO):
        try:
            with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "admin": {"senha": "123", "cargo": "Administrador"},
        "funcionario_teste": {"senha": "123", "cargo": "Funcionário 2B"}
    }

def salvar_banco(db):
    try:
        with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except:
        pass

if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = carregar_banco()

if "logs_acesso" not in st.session_state:
    st.session_state["logs_acesso"] = []

params = st.query_params
if "user" in params and "cargo" in params:
    st.session_state["autenticado"] = True
    st.session_state["usuario_atual"] = params["user"]
    st.session_state["cargo_atual"] = params["cargo"]

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["cargo_atual"] = ""

def tela_login():
    st.markdown('<p class="titulo">Acesso Restrito</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo">Faca login ou crie sua conta para acessar o sistema</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta"])
        
        with aba_login:
            with st.form("form_login"):
                usuario = st.text_input("Usuario")
                senha = st.text_input("Senha", type="password")
                botao_entrar = st.form_submit_button("Entrar", use_container_width=True)
                
                if botao_entrar:
                    st.session_state["usuarios_db"] = carregar_banco()
                    db = st.session_state["usuarios_db"]
                    
                    if usuario in db and db[usuario]["senha"] == senha:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_atual"] = usuario
                        st.session_state["cargo_atual"] = db[usuario]["cargo"]
                        
                        st.query_params["user"] = usuario
                        st.query_params["cargo"] = db[usuario]["cargo"]
                        
                        so_detectado = "Windows PC"
                        if hasattr(st, "context") and hasattr(st.context, "headers"):
                            ua = str(st.context.headers.get("Sec-Ch-Ua-Platform", ""))
                            if "Android" in ua: so_detectado = "Android"
                            elif "iOS" in ua or "iPhone" in ua: so_detectado = "iOS (iPhone/iPad)"
                            elif "Mac" in ua: so_detectado = "MacOS"

                        localizacao_ip = "Brasil (Rede Local)"
                        try:
                            res = requests.get("https://ipapi.co/json/", timeout=2).json()
                            cidade = res.get("city")
                            regiao = res.get("region")
                            pais = res.get("country_name")
                            if cidade:
                                localizacao_ip = f"{cidade} - {regiao}, {pais}"
                        except:
                            pass

                        hora_atual = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
                        st.session_state["logs_acesso"].insert(0, {
                            "usuario": usuario,
                            "cargo": db[usuario]["cargo"],
                            "data": hora_atual,
                            "dispositivo": so_detectado,
                            "local": localizacao_ip
                        })

                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Usuario ou senha incorretos.")

        with aba_cadastro:
            with st.form("form_auto_cadastro"):
                novo_user = st.text_input("Escolha um Usuario")
                nova_senha = st.text_input("Escolha uma Senha", type="password")
                botao_cadastrar = st.form_submit_button("Cadastrar Conta", use_container_width=True)
                
                if botao_cadastrar:
                    if not novo_user.strip() or not nova_senha.strip():
                        st.warning("Preencha todos os campos.")
                    else:
                        db = carregar_banco()
                        if novo_user in db:
                            st.error("Este nome de usuario ja esta em uso.")
                        else:
                            db[novo_user] = {
                                "senha": nova_senha,
                                "cargo": "Aguardando Liberação"
                            }
                            salvar_banco(db)
                            st.session_state["usuarios_db"] = db
                            st.success("Conta criada com sucesso! Aguarde o Administrador liberar seu acesso.")

if not st.session_state["autenticado"]:
    tela_login()
else:
    st.session_state["usuarios_db"] = carregar_banco()
    if st.session_state["usuario_atual"] in st.session_state["usuarios_db"]:
        st.session_state["cargo_atual"] = st.session_state["usuarios_db"][st.session_state["usuario_atual"]]["cargo"]

    def obter_imagem_base64(nome_arquivo_base):
        caminhos_possiveis = [
            os.path.join(ASSETS, f"{nome_arquivo_base}.png"),
            os.path.join(ASSETS, f"{nome_arquivo_base}.jpg"),
            os.path.join(ASSETS, f"{nome_arquivo_base}.jpeg"),
            os.path.join(PASTA_SCRIPT, f"{nome_arquivo_base}.png"),
            os.path.join(PASTA_SCRIPT, f"{nome_arquivo_base}.jpg"),
        ]
        for caminho in caminhos_possiveis:
            if os.path.exists(caminho):
                with open(caminho, "rb") as f:
                    data = f.read()
                ext = caminho.split('.')[-1].lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                return f"data:{mime};base64,{base64.b64encode(data).decode()}"
        return None

    img_selo_b64 = obter_imagem_base64("selo")
    
    if st.session_state['cargo_atual'] in ["Administrador", "Funcionário 2B"]:
        if img_selo_b64:
            html_usuario = f"""
            <div style="display: flex; align-items: center; font-size: 1rem; color: #ffffff; font-weight: 600;">
                <span><b>Logado como:</b> {st.session_state['usuario_atual']}</span>
                <img src="{img_selo_b64}" width="20" style="margin-left: 6px; vertical-align: middle;" />
            </div>
            """
        else:
            html_usuario = f"Logado como: {st.session_state['usuario_atual']}"
            
        st.sidebar.markdown(html_usuario, unsafe_allow_html=True)
        st.sidebar.markdown(f"Cargo: {st.session_state['cargo_atual']}")
        st.sidebar.markdown("CONTA VERIFICADA")
    else:
        st.sidebar.markdown(f"Logado como: {st.session_state['usuario_atual']}")
        st.sidebar.markdown(f"Cargo: {st.session_state['cargo_atual']}")
        st.sidebar.markdown("AGUARDANDO LIBERAÇÃO")
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Sair / Logout"):
        st.session_state["autenticado"] = False
        st.query_params.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    
    opcoes_menu = [
        "Confirmacao de Agendamento", 
        "Atualizacao Cadastral",
        "Gerador de Boletim (BOU)",
        "Gerador de Alvara"
    ]
    
    if st.session_state["cargo_atual"] == "Administrador":
        opcoes_menu.append("Gerenciar Usuarios e Cargos")
        opcoes_menu.append("Auditoria de Acessos")

    menu = st.sidebar.radio("Escolha a Ferramenta:", opcoes_menu)

    def verificar_permissao():
        cargo = st.session_state["cargo_atual"]
        if cargo in ["Administrador", "Funcionário 2B"]:
            return True
        return False

    if menu == "Confirmacao de Agendamento":
        st.markdown('<p class="titulo">Sistema de Confirmacao de Agendamento</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("Acesso Pendente: Sua conta esta aguardando liberacao do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Preencha os dados abaixo para gerar o PDF oficial</p>', unsafe_allow_html=True)

            st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
            st.markdown("### Dados de Debito (Sua Conta / Empresa)")
            col1, col2 = st.columns(2)
            with col1:
                debito_agencia = st.text_input("Agencia de Debito", value="1234")
                debito_tipo = st.text_input("Tipo da Conta de Debito", value="Conta Corrente")
                empresa_cnpj = st.text_input("CNPJ da Empresa", value="00.000.000/0001-00")
            with col2:
                debito_conta = st.text_input("Conta de Debito", value="12345-6")
                empresa_nome = st.text_input("Nome da Empresa", value="Minha Empresa LTDA")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
            st.markdown("### Dados do Favorecido (Quem Recebe)")
            col3, col4 = st.columns(2)
            with col3:
                favorecido_nome = st.text_input("Nome do Favorecido", value="Joao da Silva")
                credito_banco = st.text_input("Banco de Credito", value="Itau")
                credito_conta = st.text_input("Conta de Credito", value="98765-4")
                motivo_ted = st.text_input("Motivo da TED", value="Pagamento de Servicos")
                data_debito = st.text_input("Data de Debito (DD/MM/AAAA)", value=datetime.now().strftime("%d/%m/%Y"))
            with col4:
                favorecido_cnpj = st.text_input("CNPJ/CPF do Favorecido", value="111.222.333-44")
                credito_agencia = st.text_input("Agencia de Credito", value="5678")
                credito_tipo = st.text_input("Tipo de Conta do Favorecido", value="Conta Corrente")
                valor = st.text_input("Valor (R$)", value="1.500,00")
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("Gerar PDF de Confirmacao de Agendamento", type="primary"):
                try:
                    buffer = io.BytesIO()
                    dados = {
                        "empresa_nome": empresa_nome.upper(),
                        "favorecido_nome": favorecido_nome.upper(),
                        "valor": valor,
                    }
                    nome_arq = f"CONFIRMACAO AGENDAMENTO - {re.sub(r'[\\/*?:"<>|]', '', favorecido_nome)}.pdf"
                    
                    c = canvas.Canvas(buffer, pagesize=A4)
                    c.drawString(50, 500, f"Comprovante de Agendamento - Empresa: {dados['empresa_nome']}")
                    c.drawString(50, 480, f"Favorecido: {dados['favorecido_nome']} | Valor: R$ {dados['valor']}")
                    c.save()
                    buffer.seek(0)

                    st.success("PDF gerado com sucesso!")
                    st.download_button("Baixar PDF", data=buffer, file_name=nome_arq, mime="application/pdf", type="primary")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

    elif menu == "Atualizacao Cadastral":
        st.markdown('<p class="titulo">Atualizador de PDF Cadastral</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("Acesso Pendente: Aguardando liberacao do Administrador.")
        else:
            st.markdown('<p class="subtext" style="color:#8b949e; text-align:center;">Cole a ficha do cliente abaixo para extrair os dados e gerar o PDF</p>', unsafe_allow_html=True)

            def extrair_dados_ficha(texto_ficha):
                dados = {
                    "Razao Social": "NAO IDENTIFICADO",
                    "CNPJ": "00.000.000/0000-00",
                    "Situacao": "ATIVA",
                    "CPF Master": "000.000.000-00",
                    "Usuario(s)": "NAO IDENTIFICADO",
                }
                if not texto_ficha.strip():
                    return dados
                texto_ficha = texto_ficha.replace("\\", "/")
                match_cnpj_rotulo = re.search(r"CNPJ[:\s]+([\d./-]+)", texto_ficha, re.IGNORECASE)
                if match_cnpj_rotulo:
                    c_limpo = re.sub(r"\D", "", match_cnpj_rotulo.group(1))
                    if len(c_limpo) == 14:
                        dados["CNPJ"] = f"{c_limpo[:2]}.{c_limpo[2:5]}.{c_limpo[5:8]}/{c_limpo[8:12]}-{c_limpo[12:]}"
                match_razao_rotulo = re.search(r"RAZ[ÃA]O SOCIAL[:\s]+([^\n]+)", texto_ficha, re.IGNORECASE)
                if match_razao_rotulo:
                    dados["Razao Social"] = match_razao_rotulo.group(1).strip()
                match_cpf_rotulo = re.search(r"CPF USU[ÁA]RIO MASTER[:\s]+([\d.-]+)", texto_ficha, re.IGNORECASE)
                if match_cpf_rotulo:
                    cpf_limpo = re.sub(r"\D", "", match_cpf_rotulo.group(1))
                    if len(cpf_limpo) == 11:
                        dados["CPF Master"] = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
                matches_user = re.findall(r"USU[ÁA]RIOS?[:\s]+([A-Za-z0-9]+)", texto_ficha, re.IGNORECASE)
                for val_user in matches_user:
                    val_user_limpo = val_user.strip()
                    if val_user_limpo and val_user_limpo.upper() != "MASTER":
                        dados["Usuario(s)"] = val_user_limpo
                        break
                return dados

            class CheckVerde(Flowable):
                def __init__(self, tamanho=10):
                    Flowable.__init__(self)
                    self.tamanho = tamanho
                    self.width = tamanho
                    self.height = tamanho
                def draw(self):
                    c = self.canv
                    s = self.tamanho
                    r = s / 2
                    c.saveState()
                    c.setFillColor(colors.HexColor("#00A859"))
                    c.circle(r, r, r, fill=1, stroke=0)
                    c.setStrokeColor(colors.white)
                    c.setLineWidth(1.4)
                    c.setLineCap(1)
                    c.line(s * 0.28, s * 0.48, s * 0.42, s * 0.32)
                    c.line(s * 0.42, s * 0.32, s * 0.72, s * 0.68)
                    c.restoreState()

            class LinhaVertical(Flowable):
                def __init__(self, altura=38, cor="#B0B0B0", largura_linha=1):
                    Flowable.__init__(self)
                    self.altura = altura
                    self.cor = cor
                    self.largura_linha = largura_linha
                    self.width = largura_linha
                    self.height = altura
                def draw(self):
                    c = self.canv
                    c.saveState()
                    c.setStrokeColor(colors.HexColor(self.cor))
                    c.setLineWidth(self.largura_linha)
                    c.line(0, 0, 0, self.altura)
                    c.restoreState()

            def caminho_logo(pasta_script, nome):
                return os.path.join(pasta_script, PASTA_LOGOS, nome)

            def carregar_imagem(caminho, largura=None, altura=None):
                if os.path.exists(caminho):
                    img = Image(caminho)
                    if altura and not largura:
                        fator = altura / float(img.imageHeight)
                        img.drawWidth = img.imageWidth * fator
                        img.drawHeight = altura
                    elif largura and not altura:
                        fator = largura / float(img.imageWidth)
                        img.drawWidth = largura
                        img.drawHeight = img.imageHeight * fator
                    elif largura and altura:
                        img.drawWidth = largura
                        img.drawHeight = altura
                    return img
                return Spacer(largura or 100, altura or 30)

            def adicionar_marca_dagua(canvas, doc):
                caminho = caminho_logo(PASTA_SCRIPT, LOGO_MARCA_DAGUA)
                if not os.path.exists(caminho):
                    caminho = caminho_logo(PASTA_SCRIPT, LOGO_RODAPE)
                canvas.saveState()
                try:
                    canvas.setFillAlpha(0.05)
                    canvas.setStrokeAlpha(0.05)
                except AttributeError:
                    pass
                largura_item, altura_item, passo_x, passo_y = 130, 120, 130, 120
                if os.path.exists(caminho):
                    row_idx = 0
                    for y in range(-20, int(A4[1]) + 70, passo_y):
                        offset_x = (row_idx % 2) * (passo_x / 2)
                        for x in range(-80, int(A4[0]) + 100, passo_x):
                            canvas.drawImage(caminho, x + offset_x, y, width=largura_item, height=altura_item, mask="auto", preserveAspectRatio=True)
                        row_idx += 1
                canvas.restoreState()

            def gerar_pdf_cadastral(pasta_script, dados_empresa):
                razao = dados_empresa["Razao Social"]
                razao_limpa = re.sub(r'[\\/*?:"<>|]', "", razao)
                nome_pdf = f"ATUALIZACAO CADASTRAL - {razao_limpa}.pdf"
                caminho_pdf = os.path.join(pasta_script, nome_pdf)

                doc = SimpleDocTemplate(caminho_pdf, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
                story = []
                styles = getSampleStyleSheet()

                estilo_titulo = ParagraphStyle("Titulo", parent=styles["Heading1"], fontSize=13.5, leading=16, fontName="Helvetica-Bold", textColor=colors.HexColor("#111111"))
                estilo_sub = ParagraphStyle("Sub", parent=styles["Heading2"], fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#222222"))
                estilo_secao = ParagraphStyle("Secao", parent=styles["Normal"], fontSize=10, leading=13, fontName="Helvetica-Bold", textColor=colors.HexColor("#333333"))
                estilo_texto = ParagraphStyle("Texto", parent=styles["Normal"], fontSize=9.5, leading=13.5, textColor=colors.HexColor("#444444"))
                estilo_topico = ParagraphStyle("Topico", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=colors.HexColor("#333333"))
                estilo_qr_legenda = ParagraphStyle("QRLegenda", parent=styles["Normal"], fontSize=8, leading=10, alignment=1, textColor=colors.HexColor("#666666"))

                logo_topo = carregar_imagem(caminho_logo(pasta_script, LOGO_CABECALHO), altura=68)
                linha_divisoria = LinhaVertical(altura=60, cor="#B0B0B0", largura_linha=1)
                p_titulo = Paragraph("COMUNICADO IMPORTANTE", estilo_titulo)

                cab = Table([[logo_topo, linha_divisoria, p_titulo]], colWidths=[200, 25, 270])
                cab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
                story.append(cab)
                story.append(Spacer(1, 22))

                story.append(Paragraph("ATUALIZACAO CADASTRAL", estilo_sub))
                story.append(Spacer(1, 6))
                story.append(Paragraph("Em conformidade com as diretrizes de autorregulacao bancaria e as boas praticas estabelecidas pelo sistema financeiro nacional, comunicamos que a atualizacao cadastral de empresas junto ao Internet Banking Empresarial e procedimento obrigatorio e periodico.", estilo_texto))
                story.append(Spacer(1, 18))

                story.append(Paragraph("DADOS DO MASTER:", estilo_secao))
                story.append(Spacer(1, 6))
                tabela = [[Paragraph(f"<b>{k}:</b>", estilo_texto), Paragraph(str(v), estilo_texto)] for k, v in dados_empresa.items()]
                t = Table(tabela, colWidths=[100, 385])
                t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 2)]))
                story.append(t)
                story.append(Spacer(1, 18))

                story.append(Paragraph("A atualizacao cadastral tem como finalidade:", estilo_texto))
                story.append(Spacer(1, 8))

                check = CheckVerde(tamanho=10)
                for item in [
                    "Garantir a seguranca das operacoes financeiras;",
                    "Manter os dados da empresa e de seus representantes legais atualizados;",
                    "Atender as exigencias regulatorias vigentes;",
                    "Prevenir fraudes e inconsistencias cadastrais.",
                ]:
                    row = Table([[check, Paragraph(item, estilo_topico)]], colWidths=[18, 467])
                    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4)]))
                    story.append(row)

                story.append(Spacer(1, 18))
                story.append(Paragraph("Reforçamos que a não realização da atualização dentro do prazo estabelecido poderá acarretar restrições operacionais, incluindo limitações temporárias de acesso a determinados serviços bancários.", estilo_texto))
                story.append(Spacer(1, 14))
                story.append(Paragraph("A atualização pode ser realizada diretamente pelo Bradesco Net Empresas, acessando o menu de Cadastro/Atualização Cadastral, ou mediante comparecimento à agência de relacionamento.", estilo_texto))
                story.append(Spacer(1, 14))
                story.append(Paragraph("Em caso de dúvidas, recomenda-se entrar em contato com seu gerente de contas ou com a central de atendimento empresarial.", estilo_texto))
                story.append(Spacer(1, 25))

                img_rodape = carregar_imagem(caminho_logo(pasta_script, LOGO_RODAPE), altura=75)
                img_qr = carregar_imagem(caminho_logo(pasta_script, QRCODE), largura=110, altura=110)
                p_legenda_qr = Paragraph("Escaneie o QR Code para acessar o portal", estilo_qr_legenda)

                bloco_qr = Table([[img_qr], [Spacer(1, 4)], [p_legenda_qr]], colWidths=[140])
                bloco_qr.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))

                rod = Table([["", img_rodape, bloco_qr, ""]], colWidths=[95, 145, 140, 125])
                rod.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("ALIGN", (2, 0), (2, 0), "LEFT"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
                story.append(rod)

                doc.build(story, onFirstPage=adicionar_marca_dagua, onLaterPages=adicionar_marca_dagua)
                return caminho_pdf

            ficha_input = st.text_area("COLE A FICHA DO CLIENTE AQUI", placeholder="Cole a linha ou o bloco de texto da ficha...", height=120)

            if st.button("Processar e Gerar PDF", type="primary"):
                if ficha_input.strip():
                    dados_extraidos = extrair_dados_ficha(ficha_input)
                    st.session_state['dados_empresa_cadastral'] = dados_extraidos
                    st.success("Ficha lida e dados extraídos com sucesso!")
                else:
                    st.warning("Por favor, cole uma ficha na caixa de texto acima.")

            if 'dados_empresa_cadastral' in st.session_state:
                dados = st.session_state['dados_empresa_cadastral']
                st.markdown("---")
                st.subheader("DADOS EXTRAÍDOS PARA O PDF")
                
                col1, col2 = st.columns(2)
                with col1:
                    razao_social = st.text_input("Razao Social", value=dados["Razao Social"])
                    cnpj_val = st.text_input("CNPJ", value=dados["CNPJ"])
                with col2:
                    situacao = st.text_input("Situacao", value=dados["Situacao"])
                    cpf_master = st.text_input("CPF Master", value=dados["CPF Master"])
                
                dados_atualizados = {
                    "Razao Social": razao_social,
                    "CNPJ": cnpj_val,
                    "Situacao": situacao,
                    "CPF Master": cpf_master,
                    "Usuario(s)": dados.get("Usuario(s)", "NAO IDENTIFICADO")
                }

                if st.button("Baixar PDF Pronto"):
                    caminho_pdf = gerar_pdf_cadastral(PASTA_SCRIPT, dados_atualizados)
                    with open(caminho_pdf, "rb") as f:
                        st.download_button(
                            label="📥 Clique aqui para salvar o PDF",
                            data=f,
                            file_name=os.path.basename(caminho_pdf),
                            mime="application/pdf"
                        )

    elif menu == "Gerador de Boletim (BOU)":
        st.markdown('<p class="titulo">Gerador de Boletim Web (BOU)</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("Acesso Pendente: Aguardando liberacao do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Preencha os dados abaixo para gerar e baixar o PDF oficial do Boletim</p>', unsafe_allow_html=True)

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                uf_escolhida = st.selectbox("Selecione o Estado (UF):", UFS_ORDENADAS, format_func=lambda x: f"{x} - {ESTADOS[x]['nome']}")

            bancos_opcoes = {
                "Bradesco": "logo_bradesco.png",
                "Itau": "logo_itau.png",
                "Caixa Economica Federal": "logo_caixa.png",
                "Banco do Brasil": "logo_bb.png",
                "Santander": "logo_santander.png",
                "Nubank": "logo_nubank.png",
                "Banco Inter": "logo_inter.png",
                "C6 Bank": "logo_c6.png",
                "BTG Pactual": "logo_btg.png",
                "PagBank": "logo_pagbank.png",
                "PagSeguro": "logo_pagseguro.png",
                "Mercado Pago": "logo_mercadopago.png",
                "Banco SICOOB": "logo_sicoob.png",
                "Banco SICREDI": "logo_sicredi.png",
                "Banco Safra": "logo_safra.png",
                "Banrisul": "logo_banrisul.png",
                "Banco BMG": "logo_bmg.png",
                "Banco Pan": "logo_pan.png",
                "Banco Original": "logo_original.png",
                "Neon": "logo_neon.png",
                "XP Investimentos": "logo_xp.png",
                "Ame Digital": "logo_ame.png",
                "PicPay": "logo_picpay.png",
                "Banco Nordeste (BNB)": "logo_bnb.png",
                "Banco da Amazonia (BASA)": "logo_basa.png",
                "BRB - Banco de Brasilia": "logo_brb.png",
                "Sem Logo": None
            }

            with col_b2:
                banco_escolhido_nome = st.selectbox("Selecione a Logo do Banco:", list(bancos_opcoes.keys()))
                logo_banco_nome = bancos_opcoes[banco_escolhido_nome]

            st.markdown('<div class="divisor" style="border-bottom: 1px solid #262730; margin-bottom: 20px; padding-bottom: 10px; font-size: 1.2rem; font-weight: bold;">DADOS DA VITIMA</div>', unsafe_allow_html=True)

            def registrar_fontes_bou():
                candidatos = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\ARIAL.TTF"]
                bold_cand = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\ARIALBD.TTF"]
                fonte, fonte_b = "Helvetica", "Helvetica-Bold"
                for path in candidatos:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont("ArialDoc", path))
                        fonte = "ArialDoc"
                        break
                for path in bold_cand:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont("ArialDoc-Bold", path))
                        fonte_b = "ArialDoc-Bold"
                        break
                return fonte, fonte_b

            FONTE_BOU, FONTE_B_BOU = registrar_fontes_bou()
            MESES_BOU = {1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
            DIAS_BOU = ["Segunda-feira", "Terca-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sabado", "Domingo"]

            def data_extenso_bou(dt=None):
                dt = dt or datetime.now()
                return f"{dt.day:02d} de {MESES_BOU[dt.month]} de {dt.year} - {DIAS_BOU[dt.weekday()]} as {dt.hour:02d}:{dt.minute:02d}"

            def formatar_cpf_bou(texto):
                numeros = "".join(filter(str.isdigit, str(texto)))
                if len(numeros) == 11:
                    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
                return str(texto)

            def formatar_celular_bou(texto):
                numeros = "".join(filter(str.isdigit, str(texto)))
                if len(numeros) == 11:
                    return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
                elif len(numeros) == 10:
                    return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
                return str(texto)

            def caminho_asset_bou(uf, nome):
                if not nome: return None
                nome_base, ext_original = os.path.splitext(nome)
                extensoes = [ext_original, ".png", ".jpg", ".jpeg", ""]
                locais_busca = [PASTA_LOGOS_BANCO, os.path.join(PASTA_LOGOS_ESTADOS, uf.upper()), os.path.join(ASSETS, uf.upper()), ASSETS]
                for local in locais_busca:
                    if not os.path.exists(local): continue
                    for arq in os.listdir(local):
                        for ext in extensoes:
                            if arq.lower() == f"{nome_base}{ext}".lower():
                                return os.path.join(local, arq)
                return None

            def carregar_texto_externo_bou():
                candidatos_txt = [os.path.join(PASTA_DADOS, "dados.txt"), os.path.join(PASTA_DADOS, "dados"), os.path.join(PASTA_SCRIPT, "dados.txt")]
                dados_txt = {
                    "capitulacao": "Art. 154-A do Codigo Penal . Motivo Presumido Crime Cibernetico - Invasao de Dispositivo Informatico",
                    "despacho": "Considerando a natureza da ocorrencia, encaminhe-se este registro para o Departamento de Investigacao de Crimes Ciberneticos para as devidas apuracoes e providencias legais cabiveis."
                }
                for caminho in candidatos_txt:
                    if os.path.exists(caminho):
                        try:
                            with open(caminho, "r", encoding="utf-8") as f:
                                conteudo = f.read()
                            fato_match = re.search(r"FATO\s*AT[ÍI]PICO:?\s*(.*?)(?=\n\s*[A-Z\s]+:?|\Z)", conteudo, re.DOTALL | re.IGNORECASE)
                            despacho_match = re.search(r"DESPACHO\s*DA\s*AUTORIDADE:?\s*(.*?)(?=\n\s*[A-Z\s]+:?|\Z)", conteudo, re.DOTALL | re.IGNORECASE)
                            if fato_match: dados_txt["capitulacao"] = fato_match.group(1).strip()
                            if despacho_match: dados_txt["despacho"] = despacho_match.group(1).strip()
                            break
                        except Exception:
                            continue
                return dados_txt

            dados_txt_externos = carregar_texto_externo_bou()

            with st.form(key="form_bou"):
                vitima_nome = st.text_input("Nome Completo da Vitima:", placeholder="Ex: Carlos Eduardo")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    vitima_cpf = st.text_input("CPF da Vitima:", placeholder="000.000.000-00")
                with col_b:
                    vitima_celular = st.text_input("Celular da Vitima:", placeholder="(00) 00000-0000")
                    
                submit_bou = st.form_submit_button(label="📄 Processar e Gerar PDF do Boletim", type="primary")

            if submit_bou:
                if not vitima_nome:
                    st.error("⚠️ Por favor, preencha o nome da vitima.")
                else:
                    est = ESTADOS[uf_escolhida]
                    if banco_escolhido_nome == "Sem Logo":
                        dinamica_personalizada = "ACESSO INDEVIDO (INVASAO) A CONTA E REMOCAO DO DISPOSITIVO NAO AUTORIZADO"
                    else:
                        banco_texto = banco_escolhido_nome.upper()
                        dinamica_personalizada = f"ACESSO INDEVIDO (INVASAO) APP {banco_texto}, ACESSO INDEVIDO A CONTA E REMOCAO DO DISPOSITIVO NAO AUTORIZADO"
                    
                    dados_bou_finais = {
                        "uf": uf_escolhida,
                        "numero": "025-06119/2026",
                        "origem": est["origem"],
                        "circunscricao": est["circunscricao"],
                        "delegacia": est["delegacia"],
                        "endereco": est["endereco"],
                        "investigador": est["investigador"],
                        "investigador_cargo": est["investigador_cargo"],
                        "logo_banco_nome": logo_banco_nome,
                        "vitima_nome": vitima_nome,
                        "vitima_cpf": vitima_cpf if vitima_cpf else "000.000.000-00",
                        "vitima_celular": vitima_celular if vitima_celular else "(00) 00000-0000",
                        "capitulacao": dados_txt_externos.get("capitulacao", ""),
                        "despacho": dados_txt_externos.get("despacho", ""),
                        "dinamica": dinamica_personalizada,
                        "inicio": data_extenso_bou(datetime.now())
                    }

                    try:
                        buffer_bou = io.BytesIO()
                        c_bou = canvas.Canvas(buffer_bou, pagesize=A4)
                        L_BOU, A_BOU = A4
                        LX0_BOU, LX1_BOU = 30.75, 565.50

                        def y_top_bou(t_y): return A_BOU - t_y
                        def linha_bou(c_obj, t_y, grossa=False):
                            h_l = 1.5 if grossa else 0.75
                            c_obj.setFillColorRGB(0, 0, 0)
                            c_obj.rect(LX0_BOU, y_top_bou(t_y) - h_l, LX1_BOU - LX0_BOU, h_l, stroke=0, fill=1)

                        def draw_img_fit_bou(c_obj, path, max_x, t_y, max_w, max_h, align="right"):
                            if not path or not os.path.exists(path): return
                            img = ImageReader(path)
                            orig_w, orig_h = img.getSize()
                            if orig_w <= 0 or orig_h <= 0: return
                            scale = min(max_w / float(orig_w), max_h / float(orig_h))
                            f_w, f_h = orig_w * scale, orig_h * scale
                            x = max_x - f_w if align == "right" else max_x
                            c_obj.drawImage(img, x, y_top_bou(t_y + max_h) + ((max_h - f_h) / 2.0), width=f_w, height=f_h, preserveAspectRatio=True, mask="auto")

                        logo_pc = caminho_asset_bou(uf_escolhida, "logo_policia.png")
                        if logo_pc: c_bou.drawImage(ImageReader(logo_pc), 20.7, y_top_bou(26.3) - 127.2, width=108, height=127.2, preserveAspectRatio=True, mask="auto")
                        
                        cx_b = 350
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(31.8 + 9), est["governo"])
                        c_bou.drawCentredString(cx_b, y_top_bou(49.8 + 9), "SECRETARIA DE ESTADO DA SEGURANCA PUBLICA")
                        c_bou.setFont(FONTE_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(67.8 + 9), est["policia"])
                        c_bou.drawCentredString(cx_b, y_top_bou(85.1 + 9), dados_bou_finais["endereco"])
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(101.6 + 9), dados_bou_finais["delegacia"])

                        linha_bou(c_bou, 160.3, grossa=True)
                        linha_bou(c_bou, 184.3, grossa=True)
                        c_bou.setFont(FONTE_B_BOU, 11)
                        c_bou.drawString(30.5, y_top_bou(196.8 + 11), "REGISTRO DE OCORRENCIA")
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawRightString(L_BOU - 30.5, y_top_bou(196.8 + 10), f"No. {dados_bou_finais['numero']}")
                        linha_bou(c_bou, 218.8, grossa=True)

                        c_bou.setFont(FONTE_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(246.3 + 10), f"Inicio do Registro: {dados_bou_finais['inicio']}")
                        c_bou.drawString(30.5, y_top_bou(268.1 + 10), f"Origem: {dados_bou_finais['origem']} . Circunscricao: {dados_bou_finais['circunscricao']}")
                        linha_bou(c_bou, 299.1, grossa=False)

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(322.1 + 10), "Fato Atipico")
                        linha_bou(c_bou, 338.1, grossa=False)
                        c_bou.setFont(FONTE_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(357.3 + 10), f"Capitulacao: {dados_bou_finais['capitulacao']}")

                        y_desp = 403.8
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_desp + 10), "Despacho da Autoridade")
                        linha_bou(c_bou, y_desp + 16, grossa=False)
                        c_bou.setFont(FONTE_BOU, 10)
                        y_texto = y_desp + 35.3
                        for ln in simpleSplit(dados_bou_finais["despacho"], FONTE_BOU, 10, LX1_BOU - 30.5):
                            c_bou.drawString(30.5, y_top_bou(y_texto), ln)
                            y_texto += 12

                        y_env_fixo = 517.1
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_env_fixo + 10), "Envolvido(s) na Ocorrencia - Vitima")
                        linha_bou(c_bou, y_env_fixo + 16, grossa=False)

                        y_nome, y_cpf, y_cel = y_env_fixo + 35.2, y_env_fixo + 57.7, y_env_fixo + 79.5
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_nome + 10), "Nome")
                        c_bou.drawString(30.5, y_top_bou(y_cpf + 10), "CPF:")
                        c_bou.drawString(30.5, y_top_bou(y_cel + 10), "CELULAR:")

                        c_bou.setFont(FONTE_BOU, 10)
                        c_bou.drawString(90.0, y_top_bou(y_nome + 10), str(dados_bou_finais["vitima_nome"]).upper())
                        c_bou.drawString(90.0, y_top_bou(y_cpf + 10), formatar_cpf_bou(dados_bou_finais["vitima_cpf"]))
                        c_bou.drawString(90.0, y_top_bou(y_cel + 10), formatar_celular_bou(dados_bou_finais["vitima_celular"]))

                        logo_banco = caminho_asset_bou(uf_escolhida, dados_bou_finais.get("logo_banco_nome"))
                        if logo_banco: draw_img_fit_bou(c_bou, logo_banco, max_x=LX1_BOU, t_y=y_nome - 2, max_w=140, max_h=40, align="right")

                        linha_bou(c_bou, y_cel + 52, grossa=False)

                        y_din = y_cel + 68
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_din), "Dinamica do fato")
                        linha_bou(c_bou, y_din + 6, grossa=True)
                        
                        c_bou.setFont(FONTE_BOU, 10)
                        y_txt_din = y_din + 20
                        for ln in simpleSplit(dados_bou_finais["dinamica"], FONTE_BOU, 10, LX1_BOU - 30.5):
                            c_bou.drawString(30.5, y_top_bou(y_txt_din), ln)
                            y_txt_din += 12

                        y_proc = y_txt_din + 15
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_proc), "PROCEDIMENTO DE CANCELAMENTO IMEDIATO ATRAVES DE VALIDACAO BIOMETRIA FACIAL")
                        linha_bou(c_bou, y_proc + 6, grossa=True)
                        c_bou.showPage()

                        c_bou.setFont(FONTE_BOU, 10)
                        c_bou.drawString(40, y_top_bou(22), "Protocolo Administrativo no: 048640-1023/2026")
                        assinatura = caminho_asset_bou(uf_escolhida, "assinatura.png")
                        if assinatura: c_bou.drawImage(ImageReader(assinatura), (L_BOU - 180)/2, y_top_bou(75)-35, width=180, height=35, preserveAspectRatio=True, mask="auto")
                        
                        c_bou.setLineWidth(0.8)
                        c_bou.line(L_BOU / 2 - 110, y_top_bou(120), L_BOU / 2 + 110, y_top_bou(120))
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawCentredString(L_BOU / 2, y_top_bou(140), dados_bou_finais["investigador"])
                        c_bou.setFont(FONTE_BOU, 8)
                        c_bou.drawCentredString(L_BOU / 2, y_top_bou(155), dados_bou_finais["investigador_cargo"])
                        
                        c_bou.save()
                        buffer_bou.seek(0)

                        st.success("Boletim gerado com sucesso!")
                        nome_limpo_bou = re.sub(r'[<>:"/\\|?*]', "", vitima_nome).strip()
                        st.download_button(
                            label="📥 Clique aqui para baixar o Boletim em PDF",
                            data=buffer_bou,
                            file_name=f"{uf_escolhida} - {nome_limpo_bou}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar o boletim: {e}")

    elif menu == "Gerador de Alvara":
        st.markdown('<p class="titulo">Sistema de Alvaras - Tropa do Adv</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("Acesso Pendente: Aguardando liberacao do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Cole o texto do alvará abaixo para extrair os dados e gerar o PDF automaticamente</p>', unsafe_allow_html=True)

            def obter_data_extenso_alvara():
                meses = {1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril", 5: "maio", 6: "junho", 
                         7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
                hoje = datetime.now()
                return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"

            def formatar_cpf_cnpj_alvara(valor):
                numeros = re.sub(r'\D', '', valor)
                if len(numeros) == 11:
                    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
                elif len(numeros) == 14:
                    return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
                return "000.000.000-00" if numeros == "" else valor

            def open_pdf_buffer_alvara(dados_alv):
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                largura, altura = A4
                
                template_path = os.path.join(PASTA_SCRIPT, 'template.png')
                if os.path.exists(template_path):
                    c.drawImage(template_path, 0, 0, width=largura, height=altura)

                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(440, altura - 153, f"{dados_alv['processo']}")
                
                x_margem = 105
                y_base = altura - 316 
                
                campos = [
                    ("Credor: ", dados_alv['nome']),
                    ("CPF/CNPJ: ", dados_alv['cpf']),
                    ("Processo N°: ", dados_alv['processo']),
                    ("Assunto: ", dados_alv['assunto']),
                    ("Contra: ", dados_alv['contra'])
                ]

                for label, valor in campos:
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(x_margem, y_base, label)
                    c.setFont("Helvetica", 11)
                    c.drawString(x_margem + (c.stringWidth(label, "Helvetica-Bold", 11) + 2), y_base, str(valor))
                    y_base -= 18

                y_valor = altura - 540
                c.setFont("Helvetica-Bold", 11)
                label_v = f"Valor a receber: R$ {dados_alv['valor_str']} "
                c.drawString(x_margem, y_valor, label_v)
                
                largura_l = c.stringWidth(label_v, "Helvetica-Bold", 11)
                c.setFont("Helvetica", 11)
                extenso_p = f"({dados_alv['extenso']})"
                
                linhas = textwrap.wrap(extenso_p, width=55) 
                for i, linha in enumerate(linhas):
                    pos_y = y_valor if i == 0 else y_valor - (i * 14)
                    pos_x = x_margem + largura_l if i == 0 else x_margem
                    c.drawString(pos_x, pos_y, linha)

                c.setFont("Helvetica-Bold", 11)
                c.drawCentredString(largura/2, altura - 675, dados_alv['advogado'])
                c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso_alvara()}.")
                
                c.save()
                buffer.seek(0)
                return buffer

            texto_raw_alv = st.text_area(
                "📄 Cole o texto do alvará abaixo:",
                placeholder="Cole aqui o conteúdo copiado do WhatsApp ou do documento...",
                height=250
            )

            if st.button("🚀 Processar e Gerar Alvará", type="primary"):
                if not texto_raw_alv.strip():
                    st.warning("⚠️ Por favor, cole o texto do alvará na caixa acima.")
                else:
                    texto_raw_alv = texto_raw_alv.replace("\\", "/")

                    try:
                        cpf_match = re.search(r"(?:CPF[:\s]*)?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", texto_raw_alv, re.I)
                        cpf_raw = cpf_match.group(1) if cpf_match else "000.000.000-00"

                        nome_match = re.search(r"(?:Sra\.|Sr\.|NOME[:\s]*)\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        nome = nome_match.group(1).strip().replace('*', '') if nome_match else "Não Encontrado"

                        proc_match = re.search(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", texto_raw_alv)
                        proc = proc_match.group(1) if proc_match else "Não Encontrado"

                        assunto_match = re.search(r"(?:Assunto|•)\*?:\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        assunto = assunto_match.group(1).strip().replace('*', '') if assunto_match else "Não Encontrado"

                        contra_match = re.search(r"(?:contrária|Reqda|Reqdo|Contra)\*?:\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        contra = contra_match.group(1).strip().replace('*', '') if contra_match else "Não Encontrado"

                        valor_match = re.search(r"liberação\s+do\s+valor\s+de\s+\*?R\$\s*([\d.,]+)\*?", texto_raw_alv, re.I)
                        if valor_match:
                            valor_str = valor_match.group(1).strip()
                        else:
                            partes = re.split(r"Prezado\s+Sr\(a\)\.", texto_raw_alv, flags=re.I)
                            texto_corpo = partes[1] if len(partes) > 1 else texto_raw_alv
                            vm = re.search(r"R\$\s*([\d.,]+)", texto_corpo)
                            valor_str = vm.group(1).strip() if vm else "0,00"

                        adv_match = re.search(r"(?:Atenciosamente,)\s*(?:[\r\n\s]*)(Dr[a]?\.\s*\*?[^*,\n]+\*?)|(Dr[a]?\.\s*\*?[^*,\n]+\*?)", texto_raw_alv, re.I)
                        advogado = "Não Encontrado"
                        if adv_match:
                            bruto = (adv_match.group(1) or adv_match.group(2)).strip().replace('*', '')
                            advogado = bruto
                        else:
                            linhas_texto = texto_raw_alv.splitlines()
                            for linha in linhas_texto:
                                if "Dr." in linha or "Dra." in linha:
                                    advogado = linha.replace('*', '').strip()
                                    break

                        num_limpo = valor_str.replace('.', '').replace(',', '.')
                        try:
                            extenso = num2words(float(num_limpo), lang='pt_BR', to='currency').title()
                        except:
                            extenso = "Zero Reais"

                        dados_alv_final = {
                            'nome': nome, 
                            'processo': proc, 
                            'contra': contra, 
                            'assunto': assunto, 
                            'valor_str': valor_str,
                            'extenso': extenso, 
                            'advogado': advogado, 
                            'cpf': formatar_cpf_cnpj_alvara(cpf_raw),
                        }

                        st.success("✅ Dados extraídos e mapeados com sucesso!")
                        st.markdown("---")

                        st.markdown("### 📋 Dados Mapeados:")
                        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Credor:** {nome}")
                            st.write(f"**CPF/CNPJ:** {dados_alv_final['cpf']}")
                            st.write(f"**Processo:** {proc}")
                            st.write(f"**Assunto:** {assunto}")
                        with col2:
                            st.write(f"**Contra:** {contra}")
                            st.write(f"**Valor:** R$ {valor_str}")
                            st.write(f"**Advogado:** {advogado}")
                        st.markdown('</div>', unsafe_allow_html=True)

                        pdf_buffer_alv = open_pdf_buffer_alvara(dados_alv_final)
                        nome_limpo_arquivo = re.sub(r'[\\/*?:"<>|]', "", nome)
                        
                        st.download_button(
                            label="📥 Baixar Alvará em PDF",
                            data=pdf_buffer_alv,
                            file_name=f"ALVARA_{nome_limpo_arquivo}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )

                    except Exception as e:
                        st.error(f"❌ Ocorreu um erro durante o processamento do texto: {e}")

    elif menu == "Gerenciar Usuarios e Cargos":
        st.markdown('<p class="titulo">Painel de Gerenciamento de Contas</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo">Mude o cargo dos usuários para liberar o acesso deles</p>', unsafe_allow_html=True)

        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
        st.markdown("### Lista de Usuários Cadastrados")
        
        db = carregar_banco()
        
        for u in list(db.keys()):
            col_u1, col_u2, col_u3 = st.columns([2, 2, 2])
            with col_u1:
                st.write(f"Usuario: {u}")
            with col_u2:
                novo_cargo_selecionado = st.selectbox(
                    f"Cargo de {u}", 
                    ["Aguardando Liberação", "Funcionário 2B", "Administrador"],
                    index=["Aguardando Liberação", "Funcionário 2B", "Administrador"].index(db[u]["cargo"]) if db[u]["cargo"] in ["Aguardando Liberação", "Funcionário 2B", "Administrador"] else 0,
                    key=f"cargo_{u}"
                )
                if novo_cargo_selecionado != db[u]["cargo"]:
                    db[u]["cargo"] = novo_cargo_selecionado
                    salvar_banco(db)
                    st.success(f"Cargo de {u} atualizado com sucesso!")
                    st.rerun()
            with col_u3:
                st.write("")
                st.write(f"Status atual: {db[u]['cargo']}")
            st.markdown("---")
            
        st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "Auditoria de Acessos":
        st.markdown('<p class="titulo">Auditoria de Acessos em Tempo Real</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo">Acompanhe quem acessou o sistema, data/hora e o sistema operacional</p>', unsafe_allow_html=True)

        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
        st.markdown("### Historico de Conexoes Recentes")
        
        logs = st.session_state["logs_acesso"]
        if not logs:
            st.info("Nenhum acesso registrado nesta sessão ainda.")
        else:
            for log in logs:
                st.write(f"Usuario: {log['usuario']} ({log['cargo']}) | Data/Hora: {log['data']} | Dispositivo/SO: {log['dispositivo']} | Localizacao IP: {log['local']}")
                st.markdown("---")
        st.markdown('</div>', unsafe_allow_html=True)
    .titulo { text-align: center; font-size: 2.2rem; font-weight: bold; color: #ffffff; margin-bottom: 0px; }
    .subtitulo { text-align: center; color: #8a99ad; margin-bottom: 30px; }
    .bloco-secao { background-color: #161b22; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #30363d; }
    input { color: #000000 !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_BANCO = os.path.join(PASTA_SCRIPT, "usuarios.json")
ASSETS = os.path.join(PASTA_SCRIPT, "assets")
PASTA_LOGOS_BANCO = os.path.join(ASSETS, "logo_banco")
PASTA_LOGOS_ESTADOS = os.path.join(ASSETS, "logo_estados")
PASTA_DADOS = os.path.join(ASSETS, "dados")
PASTA_LOGOS = os.path.join(ASSETS, "logos")

LOGO_CABECALHO = "logo_cabecalho.png"
LOGO_RODAPE = "logo_rodape.png"
LOGO_MARCA_DAGUA = "marca_dagua.png"
QRCODE = "qrcode.png"

ESTADOS = {
    "AC": {"nome": "Acre", "governo": "GOVERNO DO ESTADO DO ACRE", "policia": "POLÍCIA CIVIL DO ESTADO DO ACRE", "endereco": "Rua Quintino Bocaiúva, 1490 - Bosque, Rio Branco - AC, 69900-640, TEL.: (68) 3212-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "CARLOS EDUARDO MENDES OLIVEIRA", "investigador_cargo": "Investigador Policial - 112.045-1"},
    "AL": {"nome": "Alagoas", "governo": "GOVERNO DO ESTADO DE ALAGOAS", "policia": "POLÍCIA CIVIL DO ESTADO DE ALAGOAS", "endereco": "Av. Fernandes Lima, 2345 - Farol, Maceió - AL, 57050-000, TEL.: (82) 3315-2400", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "ROBERTO ALVES COSTA NETO", "investigador_cargo": "Investigador Policial - 223.118-4"},
    "AP": {"nome": "Amapá", "governo": "GOVERNO DO ESTADO DO AMAPÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO AMAPÁ", "endereco": "Av. FAB, 1685 - Central, Macapá - AP, 68900-074, TEL.: (96) 3212-5800", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "PAULO HENRIQUE SILVA RAMOS", "investigador_cargo": "Investigador Policial - 089.334-2"},
    "AM": {"nome": "Amazonas", "governo": "GOVERNO DO ESTADO DO AMAZONAS", "policia": "POLÍCIA CIVIL DO ESTADO DO AMAZONAS", "endereco": "Av. André Araújo, 1923 - Aleixo, Manaus - AM, 69060-000, TEL.: (92) 3648-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "MARCOS VINICIUS FERREIRA LIMA", "investigador_cargo": "Investigador Policial - 445.201-8"},
    "BA": {"nome": "Bahia", "governo": "GOVERNO DO ESTADO DA BAHIA", "policia": "POLÍCIA CIVIL DO ESTADO DA BAHIA", "endereco": "Av. Centenário, 2883 - Chame-Chame, Salvador - BA, 40155-150, TEL.: (71) 3116-6000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "JULIO CESAR SANTOS BARBOSA", "investigador_cargo": "Investigador Policial - 567.890-3"},
    "CE": {"nome": "Ceará", "governo": "GOVERNO DO ESTADO DO CEARÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO CEARÁ", "endereco": "Av. Bezerra de Menezes, 581 - São Gerardo, Fortaleza - CE, 60325-000, TEL.: (85) 3101-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "FRANCISCO DAS CHAGAS MOURA", "investigador_cargo": "Investigador Policial - 334.672-1"},
    "DF": {"nome": "Distrito Federal", "governo": "GOVERNO DO DISTRITO FEDERAL", "policia": "POLÍCIA CIVIL DO DISTRITO FEDERAL", "endereco": "SAF Sul Quadra 6 - Zona Cívico-Administrativa, Brasília - DF, 70040-912, TEL.: (61) 3207-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RICARDO ALMEIDA PINTO JUNIOR", "investigador_cargo": "Investigador Policial - 901.245-6"},
    "ES": {"nome": "Espírito Santo", "governo": "GOVERNO DO ESTADO DO ESPÍRITO SANTO", "policia": "POLÍCIA CIVIL DO ESTADO DO ESPÍRITO SANTO", "endereco": "Av. Governador Bley, 236 - Centro, Vitória - ES, 29010-150, TEL.: (27) 3636-1100", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "ANDERSON LUIZ PEREIRA GOMES", "investigador_cargo": "Investigador Policial - 178.456-9"},
    "GO": {"nome": "Goiás", "governo": "GOVERNO DO ESTADO DE GOIÁS", "policia": "POLÍCIA CIVIL DO ESTADO DE GOIÁS", "endereco": "Av. Anhanguera, 7171 - St. Oeste, Goiânia - GO, 74110-010, TEL.: (62) 3201-1500", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "DIEGO FERNANDES CASTRO SILVA", "investigador_cargo": "Investigador Policial - 612.903-5"},
    "MA": {"nome": "Maranhão", "governo": "GOVERNO DO ESTADO DO MARANHÃO", "policia": "POLÍCIA CIVIL DO ESTADO DO MARANHÃO", "endereco": "Av. dos Holandeses, s/n - Calhau, São Luís - MA, 65071-380, TEL.: (98) 3214-8000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RAFAEL SOUSA NASCIMENTO", "investigador_cargo": "Investigador Policial - 256.781-0"},
    "MT": {"nome": "Mato Grosso", "governo": "GOVERNO DO ESTADO DE MATO GROSSO", "policia": "POLÍCIA CIVIL DO ESTADO DE MATO GROSSO", "endereco": "Av. Escolástico, 346 - Bandeirantes, Cuiabá - MT, 78010-200, TEL.: (65) 3613-5630", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "023ª Delegacia", "investigador": "ANDRE RELVA SANTANA GANANÇA", "investigador_cargo": "Investigador Policial - 968.961-3"},
    "MS": {"nome": "Mato Grosso do Sul", "governo": "GOVERNO DO ESTADO DE MATO GROSSO DO SUL", "policia": "POLÍCIA CIVIL DO ESTADO DE MATO GROSSO DO SUL", "endereco": "Rua Rui Barbosa, 3500 - Monte Castelo, Campo Grande - MS, 79010-220, TEL.: (67) 3318-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "LUCIANO ROBERTO DIAS MELO", "investigador_cargo": "Investigador Policial - 401.556-7"},
    "MG": {"nome": "Minas Gerais", "governo": "GOVERNO DO ESTADO DE MINAS GERAIS", "policia": "POLÍCIA CIVIL DO ESTADO DE MINAS GERAIS", "endereco": "Av. Presidente Carlos Luz, 1275 - Caiçaras, Belo Horizonte - MG, 31230-000, TEL.: (31) 3330-7000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "GUSTAVO HENRIQUE CAMPOS REIS", "investigador_cargo": "Investigador Policial - 789.012-4"},
    "PA": {"nome": "Pará", "governo": "GOVERNO DO ESTADO DO PARÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO PARÁ", "endereco": "Av. Magalhães Barata, 651 - São Brás, Belém - PA, 66063-240, TEL.: (91) 3201-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "EDUARDO BRITO FIGUEIREDO", "investigador_cargo": "Investigador Policial - 345.678-2"},
    "PB": {"nome": "Paraíba", "governo": "GOVERNO DO ESTADO DA PARAÍBA", "policia": "POLÍCIA CIVIL DO ESTADO DA PARAÍBA", "endereco": "Av. Duarte da Silveira, 600 - Centro, João Pessoa - PB, 58013-280, TEL.: (83) 3218-5000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "THIAGO LACERDA FREITAS", "investigador_cargo": "Investigador Policial - 512.349-8"},
    "PR": {"nome": "Paraná", "governo": "GOVERNO DO ESTADO DO PARANÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO PARANÁ", "endereco": "Rua Desembargador Westphalen, 35 - Centro, Curitiba - PR, 80010-110, TEL.: (41) 3313-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "FELIPE AUGUSTO RODRIGUES", "investigador_cargo": "Investigador Policial - 678.901-3"},
    "PE": {"nome": "Pernambuco", "governo": "GOVERNO DO ESTADO DE PERNAMBUCO", "policia": "POLÍCIA CIVIL DO ESTADO DE PERNAMBUCO", "endereco": "Rua da Aurora, 485 - Boa Vista, Recife - PE, 50050-000, TEL.: (81) 3181-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "BRUNO CESAR ALBUQUERQUE", "investigador_cargo": "Investigador Policial - 234.567-1"},
    "PI": {"nome": "Piauí", "governo": "GOVERNO DO ESTADO DO PIAUÍ", "policia": "POLÍCIA CIVIL DO ESTADO DO PIAUÍ", "endereco": "Av. Frei Serafim, 2352 - Centro/Sul, Teresina - PI, 64001-020, TEL.: (86) 3216-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "LEONARDO MATOS VIEIRA", "investigador_cargo": "Investigador Policial - 890.123-5"},
    "RJ": {"nome": "Rio de Janeiro", "governo": "GOVERNO DO ESTADO DO RIO DE JANEIRO", "policia": "POLÍCIA CIVIL DO ESTADO DO RIO DE JANEIRO", "endereco": "Rua da Relação, 42 - Centro, Rio de Janeiro - RJ, 20231-110, TEL.: (21) 2332-8000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "MARCELO ANDRADE TEIXEIRA", "investigador_cargo": "Investigador Policial - 456.789-0"},
    "RN": {"nome": "Rio Grande do Norte", "governo": "GOVERNO DO ESTADO DO RIO GRANDE DO NORTE", "policia": "POLÍCIA CIVIL DO ESTADO DO RIO GRANDE DO NORTE", "endereco": "Av. Coronel Estevam, 1959 - Alecrim, Natal - RN, 59020-000, TEL.: (84) 3232-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "PEDRO HENRIQUE DANTAS", "investigador_cargo": "Investigador Policial - 123.456-7"},
    "RS": {"nome": "Rio Grande do Sul", "governo": "GOVERNO DO ESTADO DO RIO GRANDE DO SUL", "policia": "POLÍCIA CIVIL DO ESTADO DO RIO GRANDE DO SUL", "endereco": "Av. João Pessoa, 2050 - Cidade Baixa, Porto Alegre - RS, 90040-000, TEL.: (51) 3288-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "ALEXANDRE SCHMIDT OLIVEIRA", "investigador_cargo": "Investigador Policial - 567.234-8"},
    "RO": {"nome": "Rondônia", "governo": "GOVERNO DO ESTADO DE RONDÔNIA", "policia": "POLÍCIA CIVIL DO ESTADO DE RONDÔNIA", "endereco": "Av. Presidente Dutra, 2986 - Centro, Porto Velho - RO, 76801-086, TEL.: (69) 3216-5000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "WELLINGTON SOUZA CARVALHO", "investigador_cargo": "Investigador Policial - 678.345-9"},
    "RR": {"nome": "Roraima", "governo": "GOVERNO DO ESTADO DE RORAIMA", "policia": "POLÍCIA CIVIL DO ESTADO DE RORAIMA", "endereco": "Av. Ville Roy, 5245 - São Vicente, Boa Vista - RR, 69303-340, TEL.: (95) 3621-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "JOSÉ ROBERTO ALMEIDA", "investigador_cargo": "Investigador Policial - 089.012-3"},
    "SC": {"nome": "Santa Catarina", "governo": "GOVERNO DO ESTADO DE SANTA CATARINA", "policia": "POLÍCIA CIVIL DO ESTADO DE SANTA CATARINA", "endereco": "Rua Paschoal Apóstolo Pítsica, 4840 - Agronômica, Florianópolis - SC, 88025-255, TEL.: (48) 3665-6000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RODRIGO MACHADO BORGES", "investigador_cargo": "Investigador Policial - 345.901-2"},
    "SP": {"nome": "São Paulo", "governo": "GOVERNO DO ESTADO DE SÃO PAULO", "policia": "POLÍCIA CIVIL DO ESTADO DE SÃO PAULO", "endereco": "Av. São Luís, 99 - República, São Paulo - SP, 01046-001, TEL.: (11) 3311-3000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RENATO APARECIDO SILVA", "investigador_cargo": "Investigador Policial - 812.345-6"},
    "SE": {"nome": "Sergipe", "governo": "GOVERNO DO ESTADO DE SERGIPE", "policia": "POLÍCIA CIVIL DO ESTADO DE SERGIPE", "endereco": "Av. Ministro Geraldo Barreto Sobral, 215 - Capucho, Aracaju - SE, 49080-470, TEL.: (79) 3226-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "DANIEL SANTOS MENEZES", "investigador_cargo": "Investigador Policial - 456.012-7"},
    "TO": {"nome": "Tocantins", "governo": "GOVERNO DO ESTADO DO TOCANTINS", "policia": "POLÍCIA CIVIL DO ESTADO DO TOCANTINS", "endereco": "Av. Teotônio Segurado, 102 Sul - Plano Diretor Sul, Palmas - TO, 77016-002, TEL.: (63) 3218-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "FABIANO COSTA LIMA", "investigador_cargo": "Investigador Policial - 567.890-1"},
}
UFS_ORDENADAS = sorted(ESTADOS.keys())

# ==========================================
# BANCO DE DADOS PERSISTENTE (ARQUIVO JSON)
# ==========================================
def carregar_banco():
    if os.path.exists(ARQUIVO_BANCO):
        try:
            with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "admin": {"senha": "123", "cargo": "Administrador"},
        "funcionario_teste": {"senha": "123", "cargo": "Funcionário 2B"}
    }

def salvar_banco(db):
    try:
        with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except:
        pass

if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = carregar_banco()

if "logs_acesso" not in st.session_state:
    st.session_state["logs_acesso"] = []

# Mantém sessão ativa com query params
params = st.query_params
if "user" in params and "cargo" in params:
    st.session_state["autenticado"] = True
    st.session_state["usuario_atual"] = params["user"]
    st.session_state["cargo_atual"] = params["cargo"]

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["cargo_atual"] = ""

def tela_login():
    st.markdown('<p class="titulo">🛡️ Acesso Restrito</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo">Faça login ou crie sua conta para acessar o sistema</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
        
        with aba_login:
            with st.form("form_login"):
                usuario = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")
                botao_entrar = st.form_submit_button("Entrar", use_container_width=True)
                
                if botao_entrar:
                    st.session_state["usuarios_db"] = carregar_banco()
                    db = st.session_state["usuarios_db"]
                    
                    if usuario in db and db[usuario]["senha"] == senha:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_atual"] = usuario
                        st.session_state["cargo_atual"] = db[usuario]["cargo"]
                        
                        st.query_params["user"] = usuario
                        st.query_params["cargo"] = db[usuario]["cargo"]
                        
                        so_detectado = "Windows PC"
                        if hasattr(st, "context") and hasattr(st.context, "headers"):
                            ua = str(st.context.headers.get("Sec-Ch-Ua-Platform", ""))
                            if "Android" in ua: so_detectado = "Android"
                            elif "iOS" in ua or "iPhone" in ua: so_detectado = "iOS (iPhone/iPad)"
                            elif "Mac" in ua: so_detectado = "MacOS"

                        localizacao_ip = "Brasil (Rede Local)"
                        try:
                            res = requests.get("https://ipapi.co/json/", timeout=2).json()
                            cidade = res.get("city")
                            regiao = res.get("region")
                            pais = res.get("country_name")
                            if cidade:
                                localizacao_ip = f"{cidade} - {regiao}, {pais}"
                        except:
                            pass

                        hora_atual = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
                        st.session_state["logs_acesso"].insert(0, {
                            "usuario": usuario,
                            "cargo": db[usuario]["cargo"],
                            "data": hora_atual,
                            "dispositivo": so_detectado,
                            "local": localizacao_ip
                        })

                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos.")

        with aba_cadastro:
            with st.form("form_auto_cadastro"):
                novo_user = st.text_input("Escolha um Usuário")
                nova_senha = st.text_input("Escolha uma Senha", type="password")
                botao_cadastrar = st.form_submit_button("Cadastrar Conta", use_container_width=True)
                
                if botao_cadastrar:
                    if not novo_user.strip() or not nova_senha.strip():
                        st.warning("⚠️ Preencha todos os campos.")
                    else:
                        db = carregar_banco()
                        if novo_user in db:
                            st.error("❌ Este nome de usuário já está em uso.")
                        else:
                            db[novo_user] = {
                                "senha": nova_senha,
                                "cargo": "Aguardando Liberação"
                            }
                            salvar_banco(db)
                            st.session_state["usuarios_db"] = db
                            st.success("✅ Conta criada com sucesso! Aguarde o Administrador liberar seu acesso.")

if not st.session_state["autenticado"]:
    tela_login()
else:
    st.session_state["usuarios_db"] = carregar_banco()
    if st.session_state["usuario_atual"] in st.session_state["usuarios_db"]:
        st.session_state["cargo_atual"] = st.session_state["usuarios_db"][st.session_state["usuario_atual"]]["cargo"]

    # ==========================================
    # PAINEL LATERAL E NAVEGAÇÃO
    # ==========================================
    def obter_imagem_base64(nome_arquivo_base):
        caminhos_possiveis = [
            os.path.join(ASSETS, f"{nome_arquivo_base}.png"),
            os.path.join(ASSETS, f"{nome_arquivo_base}.jpg"),
            os.path.join(ASSETS, f"{nome_arquivo_base}.jpeg"),
            os.path.join(PASTA_SCRIPT, f"{nome_arquivo_base}.png"),
            os.path.join(PASTA_SCRIPT, f"{nome_arquivo_base}.jpg"),
        ]
        for caminho in caminhos_possiveis:
            if os.path.exists(caminho):
                with open(caminho, "rb") as f:
                    data = f.read()
                ext = caminho.split('.')[-1].lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                return f"data:{mime};base64,{base64.b64encode(data).decode()}"
        return None

    img_selo_b64 = obter_imagem_base64("selo")
    
    if st.session_state['cargo_atual'] in ["Administrador", "Funcionário 2B"]:
        if img_selo_b64:
            html_usuario = f"""
            <div style="display: flex; align-items: center; font-size: 1rem; color: #ffffff; font-weight: 600;">
                <span>[Conta Verificada] <b>Logado como:</b> {st.session_state['usuario_atual']}</span>
                <img src="{img_selo_b64}" width="20" style="margin-left: 6px; vertical-align: middle;" />
            </div>
            """
        else:
            html_usuario = f"Logado como: {st.session_state['usuario_atual']} (Verificado)"
            
        st.sidebar.markdown(html_usuario, unsafe_allow_html=True)
        st.sidebar.markdown(f"Cargo: {st.session_state['cargo_atual']}")
        st.sidebar.markdown("CONTA VERIFICADA")
    else:
        st.sidebar.markdown(f"Logado como: {st.session_state['usuario_atual']}")
        st.sidebar.markdown(f"Cargo: {st.session_state['cargo_atual']}")
        st.sidebar.markdown("AGUARDANDO LIBERAÇÃO")
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Sair / Logout"):
        st.session_state["autenticado"] = False
        st.query_params.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    
    opcoes_menu = [
        "Confirmacao de Agendamento", 
        "Atualizacao Cadastral",
        "Gerador de Boletim (BOU)",
        "Gerador de Alvara"
    ]
    
    if st.session_state["cargo_atual"] == "Administrador":
        opcoes_menu.append("Gerenciar Usuarios e Cargos")
        opcoes_menu.append("Auditoria de Acessos")

    menu = st.sidebar.radio("Escolha a Ferramenta:", opcoes_menu)

    def verificar_permissao():
        cargo = st.session_state["cargo_atual"]
        if cargo in ["Administrador", "Funcionário 2B"]:
            return True
        return False

    # ==========================================
    # 1. CONFIRMAÇÃO DE AGENDAMENTO
    # ==========================================
    if menu == "Confirmacao de Agendamento":
        st.markdown('<p class="titulo">Sistema de Confirmacao de Agendamento</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("Acesso Pendente: Sua conta esta aguardando liberacao do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Preencha os dados abaixo para gerar o PDF oficial</p>', unsafe_allow_html=True)

            st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
            st.markdown("### Dados de Debito (Sua Conta / Empresa)")
            col1, col2 = st.columns(2)
            with col1:
                debito_agencia = st.text_input("Agencia de Debito", value="1234")
                debito_tipo = st.text_input("Tipo da Conta de Debito", value="Conta Corrente")
                empresa_cnpj = st.text_input("CNPJ da Empresa", value="00.000.000/0001-00")
            with col2:
                debito_conta = st.text_input("Conta de Debito", value="12345-6")
                empresa_nome = st.text_input("Nome da Empresa", value="Minha Empresa LTDA")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
            st.markdown("### Dados do Favorecido (Quem Recebe)")
            col3, col4 = st.columns(2)
            with col3:
                favorecido_nome = st.text_input("Nome do Favorecido", value="Joao da Silva")
                credito_banco = st.text_input("Banco de Credito", value="Itau")
                credito_conta = st.text_input("Conta de Credito", value="98765-4")
                motivo_ted = st.text_input("Motivo da TED", value="Pagamento de Servicos")
                data_debito = st.text_input("Data de Debito (DD/MM/AAAA)", value=datetime.now().strftime("%d/%m/%Y"))
            with col4:
                favorecido_cnpj = st.text_input("CNPJ/CPF do Favorecido", value="111.222.333-44")
                credito_agencia = st.text_input(" Agencia de Credito", value="5678")
                credito_tipo = st.text_input("Tipo de Conta do Favorecido", value="Conta Corrente")
                valor = st.text_input("Valor (R$)", value="1.500,00")
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("Gerar PDF de Confirmacao de Agendamento", type="primary"):
                try:
                    buffer = io.BytesIO()
                    dados = {
                        "empresa_nome": empresa_nome.upper(),
                        "favorecido_nome": favorecido_nome.upper(),
                        "valor": valor,
                    }
                    nome_arq = f"CONFIRMACAO AGENDAMENTO - {re.sub(r'[\\/*?:"<>|]', '', favorecido_nome)}.pdf"
                    
                    c = canvas.Canvas(buffer, pagesize=A4)
                    c.drawString(50, 500, f"Comprovante de Agendamento - Empresa: {dados['empresa_nome']}")
                    c.drawString(50, 480, f"Favorecido: {dados['favorecido_nome']} | Valor: R$ {dados['valor']}")
                    c.save()
                    buffer.seek(0)

                    st.success("PDF gerado com sucesso!")
                    st.download_button("Baixar PDF", data=buffer, file_name=nome_arq, mime="application/pdf", type="primary")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

    # ==========================================
    # 2. ATUALIZAÇÃO CADASTRAL
    # ==========================================
    elif menu == "Atualizacao Cadastral":
        st.markdown('<p class="titulo">Atualizador de PDF Cadastral</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("Acesso Pendente: Aguardando liberacao do Administrador.")
        else:
            st.markdown('<p class="subtext" style="color:#8b949e; text-align:center;">Cole a ficha do cliente abaixo para extrair os dados e gerar o PDF</p>', unsafe_allow_html=True)

            def extrair_dados_ficha(texto_ficha):
                dados = {
                    "Razao Social": "NAO IDENTIFICADO",
                    "CNPJ": "00.000.000/0000-00",
                    "Situacao": "ATIVA",
                    "CPF Master": "000.000.000-00",
                    "Usuario(s)": "NAO IDENTIFICADO",
                }
                if not texto_ficha.strip():
                    return dados
                texto_ficha = texto_ficha.replace("\\", "/")
                match_cnpj_rotulo = re.search(r"CNPJ[:\s]+([\d./-]+)", texto_ficha, re.IGNORECASE)
                if match_cnpj_rotulo:
                    c_limpo = re.sub(r"\D", "", match_cnpj_rotulo.group(1))
                    if len(c_limpo) == 14:
                        dados["CNPJ"] = f"{c_limpo[:2]}.{c_limpo[2:5]}.{c_limpo[5:8]}/{c_limpo[8:12]}-{c_limpo[12:]}"
                match_razao_rotulo = re.search(r"RAZ[ÃA]O SOCIAL[:\s]+([^\n]+)", texto_ficha, re.IGNORECASE)
                if match_razao_rotulo:
                    dados["Razao Social"] = match_razao_rotulo.group(1).strip()
                match_cpf_rotulo = re.search(r"CPF USU[ÁA]RIO MASTER[:\s]+([\d.-]+)", texto_ficha, re.IGNORECASE)
                if match_cpf_rotulo:
                    cpf_limpo = re.sub(r"\D", "", match_cpf_rotulo.group(1))
                    if len(cpf_limpo) == 11:
                        dados["CPF Master"] = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
                matches_user = re.findall(r"USU[ÁA]RIOS?[:\s]+([A-Za-z0-9]+)", texto_ficha, re.IGNORECASE)
                for val_user in matches_user:
                    val_user_limpo = val_user.strip()
                    if val_user_limpo and val_user_limpo.upper() != "MASTER":
                        dados["Usuario(s)"] = val_user_limpo
                        break
                return dados

            class CheckVerde(Flowable):
                def __init__(self, tamanho=10):
                    Flowable.__init__(self)
                    self.tamanho = tamanho
                    self.width = tamanho
                    self.height = tamanho
                def draw(self):
                    c = self.canv
                    s = self.tamanho
                    r = s / 2
                    c.saveState()
                    c.setFillColor(colors.HexColor("#00A859"))
                    c.circle(r, r, r, fill=1, stroke=0)
                    c.setStrokeColor(colors.white)
                    c.setLineWidth(1.4)
                    c.setLineCap(1)
                    c.line(s * 0.28, s * 0.48, s * 0.42, s * 0.32)
                    c.line(s * 0.42, s * 0.32, s * 0.72, s * 0.68)
                    c.restoreState()

            class LinhaVertical(Flowable):
                def __init__(self, altura=38, cor="#B0B0B0", largura_linha=1):
                    Flowable.__init__(self)
                    self.altura = altura
                    self.cor = cor
                    self.largura_linha = largura_linha
                    self.width = largura_linha
                    self.height = altura
                def draw(self):
                    c = self.canv
                    c.saveState()
                    c.setStrokeColor(colors.HexColor(self.cor))
                    c.setLineWidth(self.largura_linha)
                    c.line(0, 0, 0, self.altura)
                    c.restoreState()

            def caminho_logo(pasta_script, nome):
                return os.path.join(pasta_script, PASTA_LOGOS, nome)

            def carregar_imagem(caminho, largura=None, altura=None):
                if os.path.exists(caminho):
                    img = Image(caminho)
                    if altura and not largura:
                        fator = altura / float(img.imageHeight)
                        img.drawWidth = img.imageWidth * fator
                        img.drawHeight = altura
                    elif largura and not altura:
                        fator = largura / float(img.imageWidth)
                        img.drawWidth = largura
                        img.drawHeight = img.imageHeight * fator
                    elif largura and altura:
                        img.drawWidth = largura
                        img.drawHeight = altura
                    return img
                return Spacer(largura or 100, altura or 30)

            def adicionar_marca_dagua(canvas, doc):
                caminho = caminho_logo(PASTA_SCRIPT, LOGO_MARCA_DAGUA)
                if not os.path.exists(caminho):
                    caminho = caminho_logo(PASTA_SCRIPT, LOGO_RODAPE)
                canvas.saveState()
                try:
                    canvas.setFillAlpha(0.05)
                    canvas.setStrokeAlpha(0.05)
                except AttributeError:
                    pass
                largura_item, altura_item, passo_x, passo_y = 130, 120, 130, 120
                if os.path.exists(caminho):
                    row_idx = 0
                    for y in range(-20, int(A4[1]) + 70, passo_y):
                        offset_x = (row_idx % 2) * (passo_x / 2)
                        for x in range(-80, int(A4[0]) + 100, passo_x):
                            canvas.drawImage(caminho, x + offset_x, y, width=largura_item, height=altura_item, mask="auto", preserveAspectRatio=True)
                        row_idx += 1
                canvas.restoreState()

            def gerar_pdf_cadastral(pasta_script, dados_empresa):
                razao = dados_empresa["Razao Social"]
                razao_limpa = re.sub(r'[\\/*?:"<>|]', "", razao)
                nome_pdf = f"ATUALIZACAO CADASTRAL - {razao_limpa}.pdf"
                caminho_pdf = os.path.join(pasta_script, nome_pdf)

                doc = SimpleDocTemplate(caminho_pdf, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
                story = []
                styles = getSampleStyleSheet()

                estilo_titulo = ParagraphStyle("Titulo", parent=styles["Heading1"], fontSize=13.5, leading=16, fontName="Helvetica-Bold", textColor=colors.HexColor("#111111"))
                estilo_sub = ParagraphStyle("Sub", parent=styles["Heading2"], fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#222222"))
                estilo_secao = ParagraphStyle("Secao", parent=styles["Normal"], fontSize=10, leading=13, fontName="Helvetica-Bold", textColor=colors.HexColor("#333333"))
                estilo_texto = ParagraphStyle("Texto", parent=styles["Normal"], fontSize=9.5, leading=13.5, textColor=colors.HexColor("#444444"))
                estilo_topico = ParagraphStyle("Topico", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=colors.HexColor("#333333"))
                estilo_qr_legenda = ParagraphStyle("QRLegenda", parent=styles["Normal"], fontSize=8, leading=10, alignment=1, textColor=colors.HexColor("#666666"))

                logo_topo = carregar_imagem(caminho_logo(pasta_script, LOGO_CABECALHO), altura=68)
                linha_divisoria = LinhaVertical(altura=60, cor="#B0B0B0", largura_linha=1)
                p_titulo = Paragraph("COMUNICADO IMPORTANTE", estilo_titulo)

                cab = Table([[logo_topo, linha_divisoria, p_titulo]], colWidths=[200, 25, 270])
                cab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
                story.append(cab)
                story.append(Spacer(1, 22))

                story.append(Paragraph("ATUALIZACAO CADASTRAL", estilo_sub))
                story.append(Spacer(1, 6))
                story.append(Paragraph("Em conformidade com as diretrizes de autorregulacao bancaria e as boas praticas estabelecidas pelo sistema financeiro nacional, comunicamos que a atualizacao cadastral de empresas junto ao Internet Banking Empresarial e procedimento obrigatorio e periodico.", estilo_texto))
                story.append(Spacer(1, 18))

                story.append(Paragraph("DADOS DO MASTER:", estilo_secao))
                story.append(Spacer(1, 6))
                tabela = [[Paragraph(f"<b>{k}:</b>", estilo_texto), Paragraph(str(v), estilo_texto)] for k, v in dados_empresa.items()]
                t = Table(tabela, colWidths=[100, 385])
                t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 2)]))
                story.append(t)
                story.append(Spacer(1, 18))

                story.append(Paragraph("A atualizacao cadastral tem como finalidade:", estilo_texto))
                story.append(Spacer(1, 8))

                check = CheckVerde(tamanho=10)
                for item in [
                    "Garantir a seguranca das operacoes financeiras;",
                    "Manter os dados da empresa e de seus representantes legais atualizados;",
                    "Atender as exigencias regulatorias vigentes;",
                    "Prevenir fraudes e inconsistencias cadastrais.",
                ]:
                    row = Table([[check, Paragraph(item, estilo_topico)]], colWidths=[18, 467])
                    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4)]))
                    story.append(row)

                story.append(Spacer(1, 18))
                story.append(Paragraph("Reforçamos que a não realização da atualização dentro do prazo estabelecido poderá acarretar restrições operacionais, incluindo limitações temporárias de acesso a determinados serviços bancários.", estilo_texto))
                story.append(Spacer(1, 14))
                story.append(Paragraph("A atualização pode ser realizada diretamente pelo Bradesco Net Empresas, acessando o menu de Cadastro/Atualização Cadastral, ou mediante comparecimento à agência de relacionamento.", estilo_texto))
                story.append(Spacer(1, 14))
                story.append(Paragraph("Em caso de dúvidas, recomenda-se entrar em contato com seu gerente de contas ou com a central de atendimento empresarial.", estilo_texto))
                story.append(Spacer(1, 25))

                img_rodape = carregar_imagem(caminho_logo(pasta_script, LOGO_RODAPE), altura=75)
                img_qr = carregar_imagem(caminho_logo(pasta_script, QRCODE), largura=110, altura=110)
                p_legenda_qr = Paragraph("Escaneie o QR Code para acessar o portal", estilo_qr_legenda)

                bloco_qr = Table([[img_qr], [Spacer(1, 4)], [p_legenda_qr]], colWidths=[140])
                bloco_qr.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))

                rod = Table([["", img_rodape, bloco_qr, ""]], colWidths=[95, 145, 140, 125])
                rod.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("ALIGN", (2, 0), (2, 0), "LEFT"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
                story.append(rod)

                doc.build(story, onFirstPage=adicionar_marca_dagua, onLaterPages=adicionar_marca_dagua)
                return caminho_pdf

            ficha_input = st.text_area("COLE A FICHA DO CLIENTE AQUI", placeholder="Cole a linha ou o bloco de texto da ficha...", height=120)

            if st.button("Processar e Gerar PDF", type="primary"):
                if ficha_input.strip():
                    dados_extraidos = extrair_dados_ficha(ficha_input)
                    st.session_state['dados_empresa_cadastral'] = dados_extraidos
                    st.success("Ficha lida e dados extraídos com sucesso!")
                else:
                    st.warning("Por favor, cole uma ficha na caixa de texto acima.")

            if 'dados_empresa_cadastral' in st.session_state:
                dados = st.session_state['dados_empresa_cadastral']
                st.markdown("---")
                st.subheader("DADOS EXTRAÍDOS PARA O PDF")
                
                col1, col2 = st.columns(2)
                with col1:
                    razao_social = st.text_input("Razao Social", value=dados["Razao Social"])
                    cnpj_val = st.text_input("CNPJ", value=dados["CNPJ"])
                with col2:
                    situacao = st.text_input("Situacao", value=dados["Situacao"])
                    cpf_master = st.text_input("CPF Master", value=dados["CPF Master"])
                
                dados_atualizados = {
                    "Razao Social": razao_social,
                    "CNPJ": cnpj_val,
                    "Situacao": situacao,
                    "CPF Master": cpf_master,
                    "Usuario(s)": dados.get("Usuario(s)", "NAO IDENTIFICADO")
                }

                if st.button("Baixar PDF Pronto"):
                    caminho_pdf = gerar_pdf_cadastral(PASTA_SCRIPT, dados_atualizados)
                    with open(caminho_pdf, "rb") as f:
                        st.download_button(
                            label="📥 Clique aqui para salvar o PDF",
                            data=f,
                            file_name=os.path.basename(caminho_pdf),
                            mime="application/pdf"
                        )

    # ==========================================
    # 3. GERADOR DE BOLETIM (BOU)
    # ==========================================
    elif menu == "Gerador de Boletim (BOU)":
        st.markdown('<p class="titulo">Gerador de Boletim Web (BOU)</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("Acesso Pendente: Aguardando liberacao do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Preencha os dados abaixo para gerar e baixar o PDF oficial do Boletim</p>', unsafe_allow_html=True)

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                uf_escolhida = st.selectbox("Selecione o Estado (UF):", UFS_ORDENADAS, format_func=lambda x: f"{x} - {ESTADOS[x]['nome']}")

            bancos_opcoes = {
                "Bradesco": "logo_bradesco.png",
                "Itau": "logo_itau.png",
                "Caixa Economica Federal": "logo_caixa.png",
                "Banco do Brasil": "logo_bb.png",
                "Santander": "logo_santander.png",
                "Nubank": "logo_nubank.png",
                "Banco Inter": "logo_inter.png",
                "C6 Bank": "logo_c6.png",
                "BTG Pactual": "logo_btg.png",
                "PagBank": "logo_pagbank.png",
                "PagSeguro": "logo_pagseguro.png",
                "Mercado Pago": "logo_mercadopago.png",
                "Banco SICOOB": "logo_sicoob.png",
                "Banco SICREDI": "logo_sicredi.png",
                "Banco Safra": "logo_safra.png",
                "Banrisul": "logo_banrisul.png",
                "Banco BMG": "logo_bmg.png",
                "Banco Pan": "logo_pan.png",
                "Banco Original": "logo_original.png",
                "Neon": "logo_neon.png",
                "XP Investimentos": "logo_xp.png",
                "Ame Digital": "logo_ame.png",
                "PicPay": "logo_picpay.png",
                "Banco Nordeste (BNB)": "logo_bnb.png",
                "Banco da Amazonia (BASA)": "logo_basa.png",
                "BRB - Banco de Brasilia": "logo_brb.png",
                "Sem Logo": None
            }

            with col_b2:
                banco_escolhido_nome = st.selectbox("Selecione a Logo do Banco:", list(bancos_opcoes.keys()))
                logo_banco_nome = bancos_opcoes[banco_escolhido_nome]

            st.markdown('<div class="divisor" style="border-bottom: 1px solid #262730; margin-bottom: 20px; padding-bottom: 10px; font-size: 1.2rem; font-weight: bold;">DADOS DA VITIMA</div>', unsafe_allow_html=True)

            def registrar_fontes_bou():
                candidatos = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\ARIAL.TTF"]
                bold_cand = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\ARIALBD.TTF"]
                fonte, fonte_b = "Helvetica", "Helvetica-Bold"
                for path in candidatos:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont("ArialDoc", path))
                        fonte = "ArialDoc"
                        break
                for path in bold_cand:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont("ArialDoc-Bold", path))
                        fonte_b = "ArialDoc-Bold"
                        break
                return fonte, fonte_b

            FONTE_BOU, FONTE_B_BOU = registrar_fontes_bou()
            MESES_BOU = {1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
            DIAS_BOU = ["Segunda-feira", "Terca-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sabado", "Domingo"]

            def data_extenso_bou(dt=None):
                dt = dt or datetime.now()
                return f"{dt.day:02d} de {MESES_BOU[dt.month]} de {dt.year} - {DIAS_BOU[dt.weekday()]} as {dt.hour:02d}:{dt.minute:02d}"

            def formatar_cpf_bou(texto):
                numeros = "".join(filter(str.isdigit, str(texto)))
                if len(numeros) == 11:
                    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
                return str(texto)

            def formatar_celular_bou(texto):
                numeros = "".join(filter(str.isdigit, str(texto)))
                if len(numeros) == 11:
                    return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
                elif len(numeros) == 10:
                    return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
                return str(texto)

            def caminho_asset_bou(uf, nome):
                if not nome: return None
                nome_base, ext_original = os.path.splitext(nome)
                extensoes = [ext_original, ".png", ".jpg", ".jpeg", ""]
                locais_busca = [PASTA_LOGOS_BANCO, os.path.join(PASTA_LOGOS_ESTADOS, uf.upper()), os.path.join(ASSETS, uf.upper()), ASSETS]
                for local in locais_busca:
                    if not os.path.exists(local): continue
                    for arq in os.listdir(local):
                        for ext in extensoes:
                            if arq.lower() == f"{nome_base}{ext}".lower():
                                return os.path.join(local, arq)
                return None

            def carregar_texto_externo_bou():
                candidatos_txt = [os.path.join(PASTA_DADOS, "dados.txt"), os.path.join(PASTA_DADOS, "dados"), os.path.join(PASTA_SCRIPT, "dados.txt")]
                dados_txt = {
                    "capitulacao": "Art. 154-A do Codigo Penal . Motivo Presumido Crime Cibernetico - Invasao de Dispositivo Informatico",
                    "despacho": "Considerando a natureza da ocorrencia, encaminhe-se este registro para o Departamento de Investigacao de Crimes Ciberneticos para as devidas apuracoes e providencias legais cabiveis."
                }
                for caminho in candidatos_txt:
                    if os.path.exists(caminho):
                        try:
                            with open(caminho, "r", encoding="utf-8") as f:
                                conteudo = f.read()
                            fato_match = re.search(r"FATO\s*AT[ÍI]PICO:?\s*(.*?)(?=\n\s*[A-Z\s]+:?|\Z)", conteudo, re.DOTALL | re.IGNORECASE)
                            despacho_match = re.search(r"DESPACHO\s*DA\s*AUTORIDADE:?\s*(.*?)(?=\n\s*[A-Z\s]+:?|\Z)", conteudo, re.DOTALL | re.IGNORECASE)
                            if fato_match: dados_txt["capitulacao"] = fato_match.group(1).strip()
                            if despacho_match: dados_txt["despacho"] = despacho_match.group(1).strip()
                            break
                        except Exception:
                            continue
                return dados_txt

            dados_txt_externos = carregar_texto_externo_bou()

            with st.form(key="form_bou"):
                vitima_nome = st.text_input("Nome Completo da Vitima:", placeholder="Ex: Carlos Eduardo")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    vitima_cpf = st.text_input("CPF da Vitima:", placeholder="000.000.000-00")
                with col_b:
                    vitima_celular = st.text_input("Celular da Vitima:", placeholder="(00) 00000-0000")
                    
                submit_bou = st.form_submit_button(label="📄 Processar e Gerar PDF do Boletim", type="primary")

            if submit_bou:
                if not vitima_nome:
                    st.error("⚠️ Por favor, preencha o nome da vitima.")
                else:
                    est = ESTADOS[uf_escolhida]
                    if banco_escolhido_nome == "Sem Logo":
                        dinamica_personalizada = "ACESSO INDEVIDO (INVASAO) A CONTA E REMOCAO DO DISPOSITIVO NAO AUTORIZADO"
                    else:
                        banco_texto = banco_escolhido_nome.upper()
                        dinamica_personalizada = f"ACESSO INDEVIDO (INVASAO) APP {banco_texto}, ACESSO INDEVIDO A CONTA E REMOCAO DO DISPOSITIVO NAO AUTORIZADO"
                    
                    dados_bou_finais = {
                        "uf": uf_escolhida,
                        "numero": "025-06119/2026",
                        "origem": est["origem"],
                        "circunscricao": est["circunscricao"],
                        "delegacia": est["delegacia"],
                        "endereco": est["endereco"],
                        "investigador": est["investigador"],
                        "investigador_cargo": est["investigador_cargo"],
                        "logo_banco_nome": logo_banco_nome,
                        "vitima_nome": vitima_nome,
                        "vitima_cpf": vitima_cpf if vitima_cpf else "000.000.000-00",
                        "vitima_celular": vitima_celular if vitima_celular else "(00) 00000-0000",
                        "capitulacao": dados_txt_externos.get("capitulacao", ""),
                        "despacho": dados_txt_externos.get("despacho", ""),
                        "dinamica": dinamica_personalizada,
                        "inicio": data_extenso_bou(datetime.now())
                    }

                    try:
                        buffer_bou = io.BytesIO()
                        c_bou = canvas.Canvas(buffer_bou, pagesize=A4)
                        L_BOU, A_BOU = A4
                        LX0_BOU, LX1_BOU = 30.75, 565.50

                        def y_top_bou(t_y): return A_BOU - t_y
                        def linha_bou(c_obj, t_y, grossa=False):
                            h_l = 1.5 if grossa else 0.75
                            c_obj.setFillColorRGB(0, 0, 0)
                            c_obj.rect(LX0_BOU, y_top_bou(t_y) - h_l, LX1_BOU - LX0_BOU, h_l, stroke=0, fill=1)

                        def draw_img_fit_bou(c_obj, path, max_x, t_y, max_w, max_h, align="right"):
                            if not path or not os.path.exists(path): return
                            img = ImageReader(path)
                            orig_w, orig_h = img.getSize()
                            if orig_w <= 0 or orig_h <= 0: return
                            scale = min(max_w / float(orig_w), max_h / float(orig_h))
                            f_w, f_h = orig_w * scale, orig_h * scale
                            x = max_x - f_w if align == "right" else max_x
                            c_obj.drawImage(img, x, y_top_bou(t_y + max_h) + ((max_h - f_h) / 2.0), width=f_w, height=f_h, preserveAspectRatio=True, mask="auto")

                        logo_pc = caminho_asset_bou(uf_escolhida, "logo_policia.png")
                        if logo_pc: c_bou.drawImage(ImageReader(logo_pc), 20.7, y_top_bou(26.3) - 127.2, width=108, height=127.2, preserveAspectRatio=True, mask="auto")
                        
                        cx_b = 350
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(31.8 + 9), est["governo"])
                        c_bou.drawCentredString(cx_b, y_top_bou(49.8 + 9), "SECRETARIA DE ESTADO DA SEGURANCA PUBLICA")
                        c_bou.setFont(FONTE_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(67.8 + 9), est["policia"])
                        c_bou.drawCentredString(cx_b, y_top_bou(85.1 + 9), dados_bou_finais["endereco"])
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(101.6 + 9), dados_bou_finais["delegacia"])

                        linha_bou(c_bou, 160.3, grossa=True)
                        linha_bou(c_bou, 184.3, grossa=True)
                        c_bou.setFont(FONTE_B_BOU, 11)
                        c_bou.drawString(30.5, y_top_bou(196.8 + 11), "REGISTRO DE OCORRENCIA")
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawRightString(L_BOU - 30.5, y_top_bou(196.8 + 10), f"No. {dados_bou_finais['numero']}")
                        linha_bou(c_bou, 218.8, grossa=True)

                        c_bou.setFont(FONTE_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(246.3 + 10), f"Inicio do Registro: {dados_bou_finais['inicio']}")
                        c_bou.drawString(30.5, y_top_bou(268.1 + 10), f"Origem: {dados_bou_finais['origem']} . Circunscricao: {dados_bou_finais['circunscricao']}")
                        linha_bou(c_bou, 299.1, grossa=False)

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(322.1 + 10), "Fato Atipico")
                        linha_bou(c_bou, 338.1, grossa=False)
                        c_bou.setFont(FONTE_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(357.3 + 10), f"Capitulacao: {dados_bou_finais['capitulacao']}")

                        y_desp = 403.8
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_desp + 10), "Despacho da Autoridade")
                        linha_bou(c_bou, y_desp + 16, grossa=False)
                        c_bou.setFont(FONTE_BOU, 10)
                        y_texto = y_desp + 35.3
                        for ln in simpleSplit(dados_bou_finais["despacho"], FONTE_BOU, 10, LX1_BOU - 30.5):
                            c_bou.drawString(30.5, y_top_bou(y_texto), ln)
                            y_texto += 12

                        y_env_fixo = 517.1
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_env_fixo + 10), "Envolvido(s) na Ocorrencia - Vitima")
                        linha_bou(c_bou, y_env_fixo + 16, grossa=False)

                        y_nome, y_cpf, y_cel = y_env_fixo + 35.2, y_env_fixo + 57.7, y_env_fixo + 79.5
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_nome + 10), "Nome")
                        c_bou.drawString(30.5, y_top_bou(y_cpf + 10), "CPF:")
                        c_bou.drawString(30.5, y_top_bou(y_cel + 10), "CELULAR:")

                        c_bou.setFont(FONTE_BOU, 10)
                        c_bou.drawString(90.0, y_top_bou(y_nome + 10), str(dados_bou_finais["vitima_nome"]).upper())
                        c_bou.drawString(90.0, y_top_bou(y_cpf + 10), formatar_cpf_bou(dados_bou_finais["vitima_cpf"]))
                        c_bou.drawString(90.0, y_top_bou(y_cel + 10), formatar_celular_bou(dados_bou_finais["vitima_celular"]))

                        logo_banco = caminho_asset_bou(uf_escolhida, dados_bou_finais.get("logo_banco_nome"))
                        if logo_banco: draw_img_fit_bou(c_bou, logo_banco, max_x=LX1_BOU, t_y=y_nome - 2, max_w=140, max_h=40, align="right")

                        linha_bou(c_bou, y_cel + 52, grossa=False)

                        y_din = y_cel + 68
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_din), "Dinamica do fato")
                        linha_bou(c_bou, y_din + 6, grossa=True)
                        
                        c_bou.setFont(FONTE_BOU, 10)
                        y_txt_din = y_din + 20
                        for ln in simpleSplit(dados_bou_finais["dinamica"], FONTE_BOU, 10, LX1_BOU - 30.5):
                            c_bou.drawString(30.5, y_top_bou(y_txt_din), ln)
                            y_txt_din += 12

                        y_proc = y_txt_din + 15
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_proc), "PROCEDIMENTO DE CANCELAMENTO IMEDIATO ATRAVES DE VALIDACAO BIOMETRIA FACIAL")
                        linha_bou(c_bou, y_proc + 6, grossa=True)
                        c_bou.showPage()

                        c_bou.setFont(FONTE_BOU, 10)
                        c_bou.drawString(40, y_top_bou(22), "Protocolo Administrativo no: 048640-1023/2026")
                        assinatura = caminho_asset_bou(uf_escolhida, "assinatura.png")
                        if assinatura: c_bou.drawImage(ImageReader(assinatura), (L_BOU - 180)/2, y_top_bou(75)-35, width=180, height=35, preserveAspectRatio=True, mask="auto")
                        
                        c_bou.setLineWidth(0.8)
                        c_bou.line(L_BOU / 2 - 110, y_top_bou(120), L_BOU / 2 + 110, y_top_bou(120))
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawCentredString(L_BOU / 2, y_top_bou(140), dados_bou_finais["investigador"])
                        c_bou.setFont(FONTE_BOU, 8)
                        c_bou.drawCentredString(L_BOU / 2, y_top_bou(155), dados_bou_finais["investigador_cargo"])
                        
                        c_bou.save()
                        buffer_bou.seek(0)

                        st.success("Boletim gerado com sucesso!")
                        nome_limpo_bou = re.sub(r'[<>:"/\\|?*]', "", vitima_nome).strip()
                        st.download_button(
                            label="📥 Clique aqui para baixar o Boletim em PDF",
                            data=buffer_bou,
                            file_name=f"{uf_escolhida} - {nome_limpo_bou}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar o boletim: {e}")

    # ==========================================
    # 4. GERADOR DE ALVARÁ
    # ==========================================
    elif menu == "Gerador de Alvara":
        st.markdown('<p class="titulo">Sistema de Alvaras - Tropa do Adv</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("⏳ **Acesso Pendente:** Aguardando liberação do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Cole o texto do alvará abaixo para extrair os dados e gerar o PDF automaticamente</p>', unsafe_allow_html=True)

            def obter_data_extenso_alvara():
                meses = {1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril", 5: "maio", 6: "junho", 
                         7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
                hoje = datetime.now()
                return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"

            def formatar_cpf_cnpj_alvara(valor):
                numeros = re.sub(r'\D', '', valor)
                if len(numeros) == 11:
                    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
                elif len(numeros) == 14:
                    return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
                return "000.000.000-00" if numeros == "" else valor

            def open_pdf_buffer_alvara(dados_alv):
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                largura, altura = A4
                
                template_path = os.path.join(PASTA_SCRIPT, 'template.png')
                if os.path.exists(template_path):
                    c.drawImage(template_path, 0, 0, width=largura, height=altura)

                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(440, altura - 153, f"{dados_alv['processo']}")
                
                x_margem = 105
                y_base = altura - 316 
                
                campos = [
                    ("Credor: ", dados_alv['nome']),
                    ("CPF/CNPJ: ", dados_alv['cpf']),
                    ("Processo N°: ", dados_alv['processo']),
                    ("Assunto: ", dados_alv['assunto']),
                    ("Contra: ", dados_alv['contra'])
                ]

                for label, valor in campos:
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(x_margem, y_base, label)
                    c.setFont("Helvetica", 11)
                    c.drawString(x_margem + (c.stringWidth(label, "Helvetica-Bold", 11) + 2), y_base, str(valor))
                    y_base -= 18

                y_valor = altura - 540
                c.setFont("Helvetica-Bold", 11)
                label_v = f"Valor a receber: R$ {dados_alv['valor_str']} "
                c.drawString(x_margem, y_valor, label_v)
                
                largura_l = c.stringWidth(label_v, "Helvetica-Bold", 11)
                c.setFont("Helvetica", 11)
                extenso_p = f"({dados_alv['extenso']})"
                
                linhas = textwrap.wrap(extenso_p, width=55) 
                for i, linha in enumerate(linhas):
                    pos_y = y_valor if i == 0 else y_valor - (i * 14)
                    pos_x = x_margem + largura_l if i == 0 else x_margem
                    c.drawString(pos_x, pos_y, linha)

                c.setFont("Helvetica-Bold", 11)
                c.drawCentredString(largura/2, altura - 675, dados_alv['advogado'])
                c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso_alvara()}.")
                
                c.save()
                buffer.seek(0)
                return buffer

            texto_raw_alv = st.text_area(
                "📄 Cole o texto do alvará abaixo:",
                placeholder="Cole aqui o conteúdo copiado do WhatsApp ou do documento...",
                height=250
            )

            if st.button("🚀 Processar e Gerar Alvará", type="primary"):
                if not texto_raw_alv.strip():
                    st.warning("⚠️ Por favor, cole o texto do alvará na caixa acima.")
                else:
                    texto_raw_alv = texto_raw_alv.replace("\\", "/")

                    try:
                        cpf_match = re.search(r"(?:CPF[:\s]*)?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", texto_raw_alv, re.I)
                        cpf_raw = cpf_match.group(1) if cpf_match else "000.000.000-00"

                        nome_match = re.search(r"(?:Sra\.|Sr\.|NOME[:\s]*)\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        nome = nome_match.group(1).strip().replace('*', '') if nome_match else "Não Encontrado"

                        proc_match = re.search(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", texto_raw_alv)
                        proc = proc_match.group(1) if proc_match else "Não Encontrado"

                        assunto_match = re.search(r"(?:Assunto|•)\*?:\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        assunto = assunto_match.group(1).strip().replace('*', '') if assunto_match else "Não Encontrado"

                        contra_match = re.search(r"(?:contrária|Reqda|Reqdo|Contra)\*?:\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        contra = contra_match.group(1).strip().replace('*', '') if contra_match else "Não Encontrado"

                        valor_match = re.search(r"liberação\s+do\s+valor\s+de\s+\*?R\$\s*([\d.,]+)\*?", texto_raw_alv, re.I)
                        if valor_match:
                            valor_str = valor_match.group(1).strip()
                        else:
                            partes = re.split(r"Prezado\s+Sr\(a\)\.", texto_raw_alv, flags=re.I)
                            texto_corpo = partes[1] if len(partes) > 1 else texto_raw_alv
                            vm = re.search(r"R\$\s*([\d.,]+)", texto_corpo)
                            valor_str = vm.group(1).strip() if vm else "0,00"

                        adv_match = re.search(r"(?:Atenciosamente,)\s*(?:[\r\n\s]*)(Dr[a]?\.\s*\*?[^*,\n]+\*?)|(Dr[a]?\.\s*\*?[^*,\n]+\*?)", texto_raw_alv, re.I)
                        advogado = "Não Encontrado"
                        if adv_match:
                            bruto = (adv_match.group(1) or adv_match.group(2)).strip().replace('*', '')
                            advogado = bruto
                        else:
                            linhas_texto = texto_raw_alv.splitlines()
                            for linha in linhas_texto:
                                if "Dr." in linha or "Dra." in linha:
                                    advogado = linha.replace('*', '').strip()
                                    break

                        num_limpo = valor_str.replace('.', '').replace(',', '.')
                        try:
                            extenso = num2words(float(num_limpo), lang='pt_BR', to='currency').title()
                        except:
                            extenso = "Zero Reais"

                        dados_alv_final = {
                            'nome': nome, 
                            'processo': proc, 
                            'contra': contra, 
                            'assunto': assunto, 
                            'valor_str': valor_str,
                            'extenso': extenso, 
                            'advogado': advogado, 
                            'cpf': formatar_cpf_cnpj_alvara(cpf_raw),
                        }

                        st.success("✅ Dados extraídos e mapeados com sucesso!")
                        st.markdown("---")

                        st.markdown("### 📋 Dados Mapeados:")
                        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Credor:** {nome}")
                            st.write(f"**CPF/CNPJ:** {dados_alv_final['cpf']}")
                            st.write(f"**Processo:** {proc}")
                            st.write(f"**Assunto:** {assunto}")
                        with col2:
                            st.write(f"**Contra:** {contra}")
                            st.write(f"**Valor:** R$ {valor_str}")
                            st.write(f"**Advogado:** {advogado}")
                        st.markdown('</div>', unsafe_allow_html=True)

                        pdf_buffer_alv = open_pdf_buffer_alvara(dados_alv_final)
                        nome_limpo_arquivo = re.sub(r'[\\/*?:"<>|]', "", nome)
                        
                        st.download_button(
                            label="📥 Baixar Alvará em PDF",
                            data=pdf_buffer_alv,
                            file_name=f"ALVARA_{nome_limpo_arquivo}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )

                    except Exception as e:
                        st.error(f"❌ Ocorreu um erro durante o processamento do texto: {e}")

    # ==========================================
    # PAINEL DO ADMIN: GERENCIAR E LIBERAR CONTAS
    # ==========================================
    elif menu == "Gerenciar Usuarios e Cargos":
        st.markdown('<p class="titulo">Painel de Gerenciamento de Contas</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo">Mude o cargo dos usuários para liberar o acesso deles</p>', unsafe_allow_html=True)

        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
        st.markdown("### Lista de Usuários Cadastrados")
        
        db = carregar_banco()
        
        for u in list(db.keys()):
            col_u1, col_u2, col_u3 = st.columns([2, 2, 2])
            with col_u1:
                st.write(f"Usuario: {u}")
            with col_u2:
                novo_cargo_selecionado = st.selectbox(
                    f"Cargo de {u}", 
                    ["Aguardando Liberação", "Funcionário 2B", "Administrador"],
                    index=["Aguardando Liberação", "Funcionário 2B", "Administrador"].index(db[u]["cargo"]) if db[u]["cargo"] in ["Aguardando Liberação", "Funcionário 2B", "Administrador"] else 0,
                    key=f"cargo_{u}"
                )
                if novo_cargo_selecionado != db[u]["cargo"]:
                    db[u]["cargo"] = novo_cargo_selecionado
                    salvar_banco(db)
                    st.success(f"Cargo de {u} atualizado com sucesso!")
                    st.rerun()
            with col_u3:
                st.write("")
                st.write(f"Status atual: {db[u]['cargo']}")
            st.markdown("---")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # PAINEL DO ADMIN: AUDITORIA DE ACESSOS EM TEMPO REAL
    # ==========================================
    elif menu == "Auditoria de Acessos":
        st.markdown('<p class="titulo">Auditoria de Acessos em Tempo Real</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo">Acompanhe quem acessou o sistema, data/hora e o sistema operacional</p>', unsafe_allow_html=True)

        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
        st.markdown("### Historico de Conexoes Recentes")
        
        logs = st.session_state["logs_acesso"]
        if not logs:
            st.info("Nenhum acesso registrado nesta sessão ainda.")
        else:
            for log in logs:
                st.write(f"Usuario: {log['usuario']} ({log['cargo']}) | Data/Hora: {log['data']} | Dispositivo/SO: {log['dispositivo']} | Localizacao IP: {log['local']}")
                st.markdown("---")
        st.markdown('</div>', unsafe_allow_html=True)
    .titulo { text-align: center; font-size: 2.2rem; font-weight: bold; color: #ffffff; margin-bottom: 0px; }
    .subtitulo { text-align: center; color: #8a99ad; margin-bottom: 30px; }
    .bloco-secao { background-color: #161b22; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #30363d; }
    input { color: #000000 !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_BANCO = os.path.join(PASTA_SCRIPT, "usuarios.json")
ASSETS = os.path.join(PASTA_SCRIPT, "assets")
PASTA_LOGOS_BANCO = os.path.join(ASSETS, "logo_banco")
PASTA_LOGOS_ESTADOS = os.path.join(ASSETS, "logo_estados")
PASTA_DADOS = os.path.join(ASSETS, "dados")
PASTA_LOGOS = os.path.join(ASSETS, "logos")

LOGO_CABECALHO = "logo_cabecalho.png"
LOGO_RODAPE = "logo_rodape.png"
LOGO_MARCA_DAGUA = "marca_dagua.png"
QRCODE = "qrcode.png"

ESTADOS = {
    "AC": {"nome": "Acre", "governo": "GOVERNO DO ESTADO DO ACRE", "policia": "POLÍCIA CIVIL DO ESTADO DO ACRE", "endereco": "Rua Quintino Bocaiúva, 1490 - Bosque, Rio Branco - AC, 69900-640, TEL.: (68) 3212-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "CARLOS EDUARDO MENDES OLIVEIRA", "investigador_cargo": "Investigador Policial - 112.045-1"},
    "AL": {"nome": "Alagoas", "governo": "GOVERNO DO ESTADO DE ALAGOAS", "policia": "POLÍCIA CIVIL DO ESTADO DE ALAGOAS", "endereco": "Av. Fernandes Lima, 2345 - Farol, Maceió - AL, 57050-000, TEL.: (82) 3315-2400", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "ROBERTO ALVES COSTA NETO", "investigador_cargo": "Investigador Policial - 223.118-4"},
    "AP": {"nome": "Amapá", "governo": "GOVERNO DO ESTADO DO AMAPÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO AMAPÁ", "endereco": "Av. FAB, 1685 - Central, Macapá - AP, 68900-074, TEL.: (96) 3212-5800", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "PAULO HENRIQUE SILVA RAMOS", "investigador_cargo": "Investigador Policial - 089.334-2"},
    "AM": {"nome": "Amazonas", "governo": "GOVERNO DO ESTADO DO AMAZONAS", "policia": "POLÍCIA CIVIL DO ESTADO DO AMAZONAS", "endereco": "Av. André Araújo, 1923 - Aleixo, Manaus - AM, 69060-000, TEL.: (92) 3648-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "MARCOS VINICIUS FERREIRA LIMA", "investigador_cargo": "Investigador Policial - 445.201-8"},
    "BA": {"nome": "Bahia", "governo": "GOVERNO DO ESTADO DA BAHIA", "policia": "POLÍCIA CIVIL DO ESTADO DA BAHIA", "endereco": "Av. Centenário, 2883 - Chame-Chame, Salvador - BA, 40155-150, TEL.: (71) 3116-6000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "JULIO CESAR SANTOS BARBOSA", "investigador_cargo": "Investigador Policial - 567.890-3"},
    "CE": {"nome": "Ceará", "governo": "GOVERNO DO ESTADO DO CEARÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO CEARÁ", "endereco": "Av. Bezerra de Menezes, 581 - São Gerardo, Fortaleza - CE, 60325-000, TEL.: (85) 3101-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "FRANCISCO DAS CHAGAS MOURA", "investigador_cargo": "Investigador Policial - 334.672-1"},
    "DF": {"nome": "Distrito Federal", "governo": "GOVERNO DO DISTRITO FEDERAL", "policia": "POLÍCIA CIVIL DO DISTRITO FEDERAL", "endereco": "SAF Sul Quadra 6 - Zona Cívico-Administrativa, Brasília - DF, 70040-912, TEL.: (61) 3207-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RICARDO ALMEIDA PINTO JUNIOR", "investigador_cargo": "Investigador Policial - 901.245-6"},
    "ES": {"nome": "Espírito Santo", "governo": "GOVERNO DO ESTADO DO ESPÍRITO SANTO", "policia": "POLÍCIA CIVIL DO ESTADO DO ESPÍRITO SANTO", "endereco": "Av. Governador Bley, 236 - Centro, Vitória - ES, 29010-150, TEL.: (27) 3636-1100", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "ANDERSON LUIZ PEREIRA GOMES", "investigador_cargo": "Investigador Policial - 178.456-9"},
    "GO": {"nome": "Goiás", "governo": "GOVERNO DO ESTADO DE GOIÁS", "policia": "POLÍCIA CIVIL DO ESTADO DE GOIÁS", "endereco": "Av. Anhanguera, 7171 - St. Oeste, Goiânia - GO, 74110-010, TEL.: (62) 3201-1500", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "DIEGO FERNANDES CASTRO SILVA", "investigador_cargo": "Investigador Policial - 612.903-5"},
    "MA": {"nome": "Maranhão", "governo": "GOVERNO DO ESTADO DO MARANHÃO", "policia": "POLÍCIA CIVIL DO ESTADO DO MARANHÃO", "endereco": "Av. dos Holandeses, s/n - Calhau, São Luís - MA, 65071-380, TEL.: (98) 3214-8000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RAFAEL SOUSA NASCIMENTO", "investigador_cargo": "Investigador Policial - 256.781-0"},
    "MT": {"nome": "Mato Grosso", "governo": "GOVERNO DO ESTADO DE MATO GROSSO", "policia": "POLÍCIA CIVIL DO ESTADO DE MATO GROSSO", "endereco": "Av. Escolástico, 346 - Bandeirantes, Cuiabá - MT, 78010-200, TEL.: (65) 3613-5630", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "023ª Delegacia", "investigador": "ANDRE RELVA SANTANA GANANÇA", "investigador_cargo": "Investigador Policial - 968.961-3"},
    "MS": {"nome": "Mato Grosso do Sul", "governo": "GOVERNO DO ESTADO DE MATO GROSSO DO SUL", "policia": "POLÍCIA CIVIL DO ESTADO DE MATO GROSSO DO SUL", "endereco": "Rua Rui Barbosa, 3500 - Monte Castelo, Campo Grande - MS, 79010-220, TEL.: (67) 3318-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "LUCIANO ROBERTO DIAS MELO", "investigador_cargo": "Investigador Policial - 401.556-7"},
    "MG": {"nome": "Minas Gerais", "governo": "GOVERNO DO ESTADO DE MINAS GERAIS", "policia": "POLÍCIA CIVIL DO ESTADO DE MINAS GERAIS", "endereco": "Av. Presidente Carlos Luz, 1275 - Caiçaras, Belo Horizonte - MG, 31230-000, TEL.: (31) 3330-7000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "GUSTAVO HENRIQUE CAMPOS REIS", "investigador_cargo": "Investigador Policial - 789.012-4"},
    "PA": {"nome": "Pará", "governo": "GOVERNO DO ESTADO DO PARÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO PARÁ", "endereco": "Av. Magalhães Barata, 651 - São Brás, Belém - PA, 66063-240, TEL.: (91) 3201-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "EDUARDO BRITO FIGUEIREDO", "investigador_cargo": "Investigador Policial - 345.678-2"},
    "PB": {"nome": "Paraíba", "governo": "GOVERNO DO ESTADO DA PARAÍBA", "policia": "POLÍCIA CIVIL DO ESTADO DA PARAÍBA", "endereco": "Av. Duarte da Silveira, 600 - Centro, João Pessoa - PB, 58013-280, TEL.: (83) 3218-5000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "THIAGO LACERDA FREITAS", "investigador_cargo": "Investigador Policial - 512.349-8"},
    "PR": {"nome": "Paraná", "governo": "GOVERNO DO ESTADO DO PARANÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO PARANÁ", "endereco": "Rua Desembargador Westphalen, 35 - Centro, Curitiba - PR, 80010-110, TEL.: (41) 3313-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "FELIPE AUGUSTO RODRIGUES", "investigador_cargo": "Investigador Policial - 678.901-3"},
    "PE": {"nome": "Pernambuco", "governo": "GOVERNO DO ESTADO DE PERNAMBUCO", "policia": "POLÍCIA CIVIL DO ESTADO DE PERNAMBUCO", "endereco": "Rua da Aurora, 485 - Boa Vista, Recife - PE, 50050-000, TEL.: (81) 3181-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "BRUNO CESAR ALBUQUERQUE", "investigador_cargo": "Investigador Policial - 234.567-1"},
    "PI": {"nome": "Piauí", "governo": "GOVERNO DO ESTADO DO PIAUÍ", "policia": "POLÍCIA CIVIL DO ESTADO DO PIAUÍ", "endereco": "Av. Frei Serafim, 2352 - Centro/Sul, Teresina - PI, 64001-020, TEL.: (86) 3216-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "LEONARDO MATOS VIEIRA", "investigador_cargo": "Investigador Policial - 890.123-5"},
    "RJ": {"nome": "Rio de Janeiro", "governo": "GOVERNO DO ESTADO DO RIO DE JANEIRO", "policia": "POLÍCIA CIVIL DO ESTADO DO RIO DE JANEIRO", "endereco": "Rua da Relação, 42 - Centro, Rio de Janeiro - RJ, 20231-110, TEL.: (21) 2332-8000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "MARCELO ANDRADE TEIXEIRA", "investigador_cargo": "Investigador Policial - 456.789-0"},
    "RN": {"nome": "Rio Grande do Norte", "governo": "GOVERNO DO ESTADO DO RIO GRANDE DO NORTE", "policia": "POLÍCIA CIVIL DO ESTADO DO RIO GRANDE DO NORTE", "endereco": "Av. Coronel Estevam, 1959 - Alecrim, Natal - RN, 59020-000, TEL.: (84) 3232-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "PEDRO HENRIQUE DANTAS", "investigador_cargo": "Investigador Policial - 123.456-7"},
    "RS": {"nome": "Rio Grande do Sul", "governo": "GOVERNO DO ESTADO DO RIO GRANDE DO SUL", "policia": "POLÍCIA CIVIL DO ESTADO DO RIO GRANDE DO SUL", "endereco": "Av. João Pessoa, 2050 - Cidade Baixa, Porto Alegre - RS, 90040-000, TEL.: (51) 3288-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "ALEXANDRE SCHMIDT OLIVEIRA", "investigador_cargo": "Investigador Policial - 567.234-8"},
    "RO": {"nome": "Rondônia", "governo": "GOVERNO DO ESTADO DE RONDÔNIA", "policia": "POLÍCIA CIVIL DO ESTADO DE RONDÔNIA", "endereco": "Av. Presidente Dutra, 2986 - Centro, Porto Velho - RO, 76801-086, TEL.: (69) 3216-5000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "WELLINGTON SOUZA CARVALHO", "investigador_cargo": "Investigador Policial - 678.345-9"},
    "RR": {"nome": "Roraima", "governo": "GOVERNO DO ESTADO DE RORAIMA", "policia": "POLÍCIA CIVIL DO ESTADO DE RORAIMA", "endereco": "Av. Ville Roy, 5245 - São Vicente, Boa Vista - RR, 69303-340, TEL.: (95) 3621-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "JOSÉ ROBERTO ALMEIDA", "investigador_cargo": "Investigador Policial - 089.012-3"},
    "SC": {"nome": "Santa Catarina", "governo": "GOVERNO DO ESTADO DE SANTA CATARINA", "policia": "POLÍCIA CIVIL DO ESTADO DE SANTA CATARINA", "endereco": "Rua Paschoal Apóstolo Pítsica, 4840 - Agronômica, Florianópolis - SC, 88025-255, TEL.: (48) 3665-6000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RODRIGO MACHADO BORGES", "investigador_cargo": "Investigador Policial - 345.901-2"},
    "SP": {"nome": "São Paulo", "governo": "GOVERNO DO ESTADO DE SÃO PAULO", "policia": "POLÍCIA CIVIL DO ESTADO DE SÃO PAULO", "endereco": "Av. São Luís, 99 - República, São Paulo - SP, 01046-001, TEL.: (11) 3311-3000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RENATO APARECIDO SILVA", "investigador_cargo": "Investigador Policial - 812.345-6"},
    "SE": {"nome": "Sergipe", "governo": "GOVERNO DO ESTADO DE SERGIPE", "policia": "POLÍCIA CIVIL DO ESTADO DE SERGIPE", "endereco": "Av. Ministro Geraldo Barreto Sobral, 215 - Capucho, Aracaju - SE, 49080-470, TEL.: (79) 3226-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "DANIEL SANTOS MENEZES", "investigador_cargo": "Investigador Policial - 456.012-7"},
    "TO": {"nome": "Tocantins", "governo": "GOVERNO DO ESTADO DO TOCANTINS", "policia": "POLÍCIA CIVIL DO ESTADO DO TOCANTINS", "endereco": "Av. Teotônio Segurado, 102 Sul - Plano Diretor Sul, Palmas - TO, 77016-002, TEL.: (63) 3218-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "FABIANO COSTA LIMA", "investigador_cargo": "Investigador Policial - 567.890-1"},
}
UFS_ORDENADAS = sorted(ESTADOS.keys())

# ==========================================
# BANCO DE DADOS PERSISTENTE (ARQUIVO JSON)
# ==========================================
def carregar_banco():
    if os.path.exists(ARQUIVO_BANCO):
        try:
            with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "admin": {"senha": "123", "cargo": "Administrador"},
        "funcionario_teste": {"senha": "123", "cargo": "Funcionário 2B"}
    }

def salvar_banco(db):
    try:
        with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except:
        pass

if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = carregar_banco()

if "logs_acesso" not in st.session_state:
    st.session_state["logs_acesso"] = []

# Mantém sessão ativa com query params
params = st.query_params
if "user" in params and "cargo" in params:
    st.session_state["autenticado"] = True
    st.session_state["usuario_atual"] = params["user"]
    st.session_state["cargo_atual"] = params["cargo"]

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["cargo_atual"] = ""

def tela_login():
    st.markdown('<p class="titulo">🛡️ Acesso Restrito</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo">Faça login ou crie sua conta para acessar o sistema</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
        
        with aba_login:
            with st.form("form_login"):
                usuario = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")
                botao_entrar = st.form_submit_button("Entrar", use_container_width=True)
                
                if botao_entrar:
                    # Recarrega do arquivo para garantir dados atualizados
                    st.session_state["usuarios_db"] = carregar_banco()
                    db = st.session_state["usuarios_db"]
                    
                    if usuario in db and db[usuario]["senha"] == senha:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_atual"] = usuario
                        st.session_state["cargo_atual"] = db[usuario]["cargo"]
                        
                        st.query_params["user"] = usuario
                        st.query_params["cargo"] = db[usuario]["cargo"]
                        
                        so_detectado = "Windows PC"
                        if hasattr(st, "context") and hasattr(st.context, "headers"):
                            ua = str(st.context.headers.get("Sec-Ch-Ua-Platform", ""))
                            if "Android" in ua: so_detectado = "Android"
                            elif "iOS" in ua or "iPhone" in ua: so_detectado = "iOS (iPhone/iPad)"
                            elif "Mac" in ua: so_detectado = "MacOS"

                        localizacao_ip = "Brasil (Rede Local)"
                        try:
                            res = requests.get("https://ipapi.co/json/", timeout=2).json()
                            cidade = res.get("city")
                            regiao = res.get("region")
                            pais = res.get("country_name")
                            if cidade:
                                localizacao_ip = f"{cidade} - {regiao}, {pais}"
                        except:
                            pass

                        hora_atual = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
                        st.session_state["logs_acesso"].insert(0, {
                            "usuario": usuario,
                            "cargo": db[usuario]["cargo"],
                            "data": hora_atual,
                            "dispositivo": so_detectado,
                            "local": localizacao_ip
                        })

                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos.")

        with aba_cadastro:
            with st.form("form_auto_cadastro"):
                novo_user = st.text_input("Escolha um Usuário")
                nova_senha = st.text_input("Escolha uma Senha", type="password")
                botao_cadastrar = st.form_submit_button("Cadastrar Conta", use_container_width=True)
                
                if botao_cadastrar:
                    if not novo_user.strip() or not nova_senha.strip():
                        st.warning("⚠️ Preencha todos os campos.")
                    else:
                        db = carregar_banco()
                        if novo_user in db:
                            st.error("❌ Este nome de usuário já está em uso.")
                        else:
                            db[novo_user] = {
                                "senha": nova_senha,
                                "cargo": "Aguardando Liberação"
                            }
                            salvar_banco(db)
                            st.session_state["usuarios_db"] = db
                            st.success("✅ Conta criada com sucesso! Aguarde o Administrador liberar seu acesso.")

if not st.session_state["autenticado"]:
    tela_login()
else:
    # Recarrega o banco do arquivo a cada interação para refletir liberação em tempo real
    st.session_state["usuarios_db"] = carregar_banco()
    if st.session_state["usuario_atual"] in st.session_state["usuarios_db"]:
        st.session_state["cargo_atual"] = st.session_state["usuarios_db"][st.session_state["usuario_atual"]]["cargo"]

    # ==========================================
    # PAINEL LATERAL E NAVEGAÇÃO
    # ==========================================
    def obter_imagem_base64(nome_arquivo_base):
        caminhos_possiveis = [
            os.path.join(ASSETS, f"{nome_arquivo_base}.png"),
            os.path.join(ASSETS, f"{nome_arquivo_base}.jpg"),
            os.path.join(ASSETS, f"{nome_arquivo_base}.jpeg"),
            os.path.join(PASTA_SCRIPT, f"{nome_arquivo_base}.png"),
            os.path.join(PASTA_SCRIPT, f"{nome_arquivo_base}.jpg"),
        ]
        for caminho in caminhos_possiveis:
            if os.path.exists(caminho):
                with open(caminho, "rb") as f:
                    data = f.read()
                ext = caminho.split('.')[-1].lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                return f"data:{mime};base64,{base64.b64encode(data).decode()}"
        return None

    img_selo_b64 = obter_imagem_base64("selo")
    
    if st.session_state['cargo_atual'] in ["Administrador", "Funcionário 2B"]:
        if img_selo_b64:
            html_usuario = f"""
            <div style="display: flex; align-items: center; font-size: 1rem; color: #ffffff; font-weight: 600;">
                <span>👤 <b>Logado como:</b> {st.session_state['usuario_atual']}</span>
                <img src="{img_selo_b64}" width="20" style="margin-left: 6px; vertical-align: middle;" />
            </div>
            """
        else:
            html_usuario = f"👤 **Logado como:** {st.session_state['usuario_atual']} 🔵"
            
        st.sidebar.markdown(html_usuario, unsafe_allow_html=True)
        st.sidebar.markdown(f"🔑 **Cargo:** {st.session_state['cargo_atual']}")
        st.sidebar.markdown('<div style="color: #2ecc71; font-size: 0.8rem; font-weight: bold; margin-top: -5px;">✔ CONTA VERIFICADA</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"👤 **Logado como:** {st.session_state['usuario_atual']}")
        st.sidebar.markdown(f"🔑 **Cargo:** {st.session_state['cargo_atual']}")
        st.sidebar.markdown('<div style="color: #e74c3c; font-size: 0.8rem; font-weight: bold; margin-top: -5px;">⏳ AGUARDANDO LIBERAÇÃO</div>', unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Sair / Logout"):
        st.session_state["autenticado"] = False
        st.query_params.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    
    opcoes_menu = [
        "🏦 Confirmação de Agendamento", 
        "📄 Atualização Cadastral",
        "🌐 Gerador de Boletim (BOU)",
        "⚖️ Gerador de Alvará"
    ]
    
    if st.session_state["cargo_atual"] == "Administrador":
        opcoes_menu.append("👥 Gerenciar Usuários e Cargos")
        opcoes_menu.append("📊 Auditoria de Acessos")

    menu = st.sidebar.radio("📂 Escolha a Ferramenta:", opcoes_menu)

    def verificar_permissao():
        cargo = st.session_state["cargo_atual"]
        if cargo in ["Administrador", "Funcionário 2B"]:
            return True
        return False

    # ==========================================
    # 1. CONFIRMAÇÃO DE AGENDAMENTO
    # ==========================================
    if menu == "🏦 Confirmação de Agendamento":
        st.markdown('<p class="titulo">🏦 Sistema de Confirmação de Agendamento</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("⏳ **Acesso Pendente:** Sua conta está aguardando liberação do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Preencha os dados abaixo para gerar o PDF oficial</p>', unsafe_allow_html=True)

            st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
            st.markdown("### 🏢 Dados de Débito (Sua Conta / Empresa)")
            col1, col2 = st.columns(2)
            with col1:
                debito_agencia = st.text_input("Agência de Débito", value="1234")
                debito_tipo = st.text_input("Tipo da Conta de Débito", value="Conta Corrente")
                empresa_cnpj = st.text_input("CNPJ da Empresa", value="00.000.000/0001-00")
            with col2:
                debito_conta = st.text_input("Conta de Débito", value="12345-6")
                empresa_nome = st.text_input("Nome da Empresa", value="Minha Empresa LTDA")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
            st.markdown("### 👤 Dados do Favorecido (Quem Recebe)")
            col3, col4 = st.columns(2)
            with col3:
                favorecido_nome = st.text_input("Nome do Favorecido", value="João da Silva")
                credito_banco = st.text_input("Banco de Crédito", value="Itaú")
                credito_conta = st.text_input("Conta de Crédito", value="98765-4")
                motivo_ted = st.text_input("Motivo da TED", value="Pagamento de Serviços")
                data_debito = st.text_input("Data de Débito (DD/MM/AAAA)", value=datetime.now().strftime("%d/%m/%Y"))
            with col4:
                favorecido_cnpj = st.text_input("CNPJ/CPF do Favorecido", value="111.222.333-44")
                credito_agencia = st.text_input("Agência de Crédito", value="5678")
                credito_tipo = st.text_input("Tipo de Conta do Favorecido", value="Conta Corrente")
                valor = st.text_input("Valor (R$)", value="1.500,00")
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("🚀 Gerar PDF de Confirmação de Agendamento", type="primary"):
                try:
                    buffer = io.BytesIO()
                    dados = {
                        "empresa_nome": empresa_nome.upper(),
                        "favorecido_nome": favorecido_nome.upper(),
                        "valor": valor,
                    }
                    nome_arq = f"CONFIRMAÇÃO AGENDAMENTO - {re.sub(r'[\\/*?:"<>|]', '', favorecido_nome)}.pdf"
                    
                    c = canvas.Canvas(buffer, pagesize=A4)
                    c.drawString(50, 500, f"Comprovante de Agendamento - Empresa: {dados['empresa_nome']}")
                    c.drawString(50, 480, f"Favorecido: {dados['favorecido_nome']} | Valor: R$ {dados['valor']}")
                    c.save()
                    buffer.seek(0)

                    st.success("✅ PDF gerado com sucesso!")
                    st.download_button("📥 Baixar PDF", data=buffer, file_name=nome_arq, mime="application/pdf", type="primary")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

    # ==========================================
    # 2. ATUALIZAÇÃO CADASTRAL
    # ==========================================
    elif menu == "📄 Atualização Cadastral":
        st.markdown('<p class="titulo">📄 Atualizador de PDF Cadastral</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("⏳ **Acesso Pendente:** Aguardando liberação do Administrador.")
        else:
            st.markdown('<p class="subtext" style="color:#8b949e; text-align:center;">Cole a ficha do cliente abaixo para extrair os dados e gerar o PDF</p>', unsafe_allow_html=True)

            def extrair_dados_ficha(texto_ficha):
                dados = {
                    "Razão Social": "NÃO IDENTIFICADO",
                    "CNPJ": "00.000.000/0000-00",
                    "Situação": "ATIVA",
                    "CPF Master": "000.000.000-00",
                    "Usuário(s)": "NÃO IDENTIFICADO",
                }
                if not texto_ficha.strip():
                    return dados
                texto_ficha = texto_ficha.replace("\\", "/")
                match_cnpj_rotulo = re.search(r"CNPJ[:\s]+([\d./-]+)", texto_ficha, re.IGNORECASE)
                if match_cnpj_rotulo:
                    c_limpo = re.sub(r"\D", "", match_cnpj_rotulo.group(1))
                    if len(c_limpo) == 14:
                        dados["CNPJ"] = f"{c_limpo[:2]}.{c_limpo[2:5]}.{c_limpo[5:8]}/{c_limpo[8:12]}-{c_limpo[12:]}"
                match_razao_rotulo = re.search(r"RAZ[ÃA]O SOCIAL[:\s]+([^\n]+)", texto_ficha, re.IGNORECASE)
                if match_razao_rotulo:
                    dados["Razão Social"] = match_razao_rotulo.group(1).strip()
                match_cpf_rotulo = re.search(r"CPF USU[ÁA]RIO MASTER[:\s]+([\d.-]+)", texto_ficha, re.IGNORECASE)
                if match_cpf_rotulo:
                    cpf_limpo = re.sub(r"\D", "", match_cpf_rotulo.group(1))
                    if len(cpf_limpo) == 11:
                        dados["CPF Master"] = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
                matches_user = re.findall(r"USU[ÁA]RIOS?[:\s]+([A-Za-z0-9]+)", texto_ficha, re.IGNORECASE)
                for val_user in matches_user:
                    val_user_limpo = val_user.strip()
                    if val_user_limpo and val_user_limpo.upper() != "MASTER":
                        dados["Usuário(s)"] = val_user_limpo
                        break
                return dados

            class CheckVerde(Flowable):
                def __init__(self, tamanho=10):
                    Flowable.__init__(self)
                    self.tamanho = tamanho
                    self.width = tamanho
                    self.height = tamanho
                def draw(self):
                    c = self.canv
                    s = self.tamanho
                    r = s / 2
                    c.saveState()
                    c.setFillColor(colors.HexColor("#00A859"))
                    c.circle(r, r, r, fill=1, stroke=0)
                    c.setStrokeColor(colors.white)
                    c.setLineWidth(1.4)
                    c.setLineCap(1)
                    c.line(s * 0.28, s * 0.48, s * 0.42, s * 0.32)
                    c.line(s * 0.42, s * 0.32, s * 0.72, s * 0.68)
                    c.restoreState()

            class LinhaVertical(Flowable):
                def __init__(self, altura=38, cor="#B0B0B0", largura_linha=1):
                    Flowable.__init__(self)
                    self.altura = altura
                    self.cor = cor
                    self.largura_linha = largura_linha
                    self.width = largura_linha
                    self.height = altura
                def draw(self):
                    c = self.canv
                    c.saveState()
                    c.setStrokeColor(colors.HexColor(self.cor))
                    c.setLineWidth(self.largura_linha)
                    c.line(0, 0, 0, self.altura)
                    c.restoreState()

            def caminho_logo(pasta_script, nome):
                return os.path.join(pasta_script, PASTA_LOGOS, nome)

            def carregar_imagem(caminho, largura=None, altura=None):
                if os.path.exists(caminho):
                    img = Image(caminho)
                    if altura and not largura:
                        fator = altura / float(img.imageHeight)
                        img.drawWidth = img.imageWidth * fator
                        img.drawHeight = altura
                    elif largura and not altura:
                        fator = largura / float(img.imageWidth)
                        img.drawWidth = largura
                        img.drawHeight = img.imageHeight * fator
                    elif largura and altura:
                        img.drawWidth = largura
                        img.drawHeight = altura
                    return img
                return Spacer(largura or 100, altura or 30)

            def adicionar_marca_dagua(canvas, doc):
                caminho = caminho_logo(PASTA_SCRIPT, LOGO_MARCA_DAGUA)
                if not os.path.exists(caminho):
                    caminho = caminho_logo(PASTA_SCRIPT, LOGO_RODAPE)
                canvas.saveState()
                try:
                    canvas.setFillAlpha(0.05)
                    canvas.setStrokeAlpha(0.05)
                except AttributeError:
                    pass
                largura_item, altura_item, passo_x, passo_y = 130, 120, 130, 120
                if os.path.exists(caminho):
                    row_idx = 0
                    for y in range(-20, int(A4[1]) + 70, passo_y):
                        offset_x = (row_idx % 2) * (passo_x / 2)
                        for x in range(-80, int(A4[0]) + 100, passo_x):
                            canvas.drawImage(caminho, x + offset_x, y, width=largura_item, height=altura_item, mask="auto", preserveAspectRatio=True)
                        row_idx += 1
                canvas.restoreState()

            def gerar_pdf_cadastral(pasta_script, dados_empresa):
                razao = dados_empresa["Razão Social"]
                razao_limpa = re.sub(r'[\\/*?:"<>|]', "", razao)
                nome_pdf = f"ATUALIZAÇÃO CADASTRAL - {razao_limpa}.pdf"
                caminho_pdf = os.path.join(pasta_script, nome_pdf)

                doc = SimpleDocTemplate(caminho_pdf, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
                story = []
                styles = getSampleStyleSheet()

                estilo_titulo = ParagraphStyle("Titulo", parent=styles["Heading1"], fontSize=13.5, leading=16, fontName="Helvetica-Bold", textColor=colors.HexColor("#111111"))
                estilo_sub = ParagraphStyle("Sub", parent=styles["Heading2"], fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#222222"))
                estilo_secao = ParagraphStyle("Secao", parent=styles["Normal"], fontSize=10, leading=13, fontName="Helvetica-Bold", textColor=colors.HexColor("#333333"))
                estilo_texto = ParagraphStyle("Texto", parent=styles["Normal"], fontSize=9.5, leading=13.5, textColor=colors.HexColor("#444444"))
                estilo_topico = ParagraphStyle("Topico", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=colors.HexColor("#333333"))
                estilo_qr_legenda = ParagraphStyle("QRLegenda", parent=styles["Normal"], fontSize=8, leading=10, alignment=1, textColor=colors.HexColor("#666666"))

                logo_topo = carregar_imagem(caminho_logo(pasta_script, LOGO_CABECALHO), altura=68)
                linha_divisoria = LinhaVertical(altura=60, cor="#B0B0B0", largura_linha=1)
                p_titulo = Paragraph("COMUNICADO IMPORTANTE", estilo_titulo)

                cab = Table([[logo_topo, linha_divisoria, p_titulo]], colWidths=[200, 25, 270])
                cab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
                story.append(cab)
                story.append(Spacer(1, 22))

                story.append(Paragraph("ATUALIZAÇÃO CADASTRAL", estilo_sub))
                story.append(Spacer(1, 6))
                story.append(Paragraph("Em conformidade com as diretrizes de autorregulação bancária e as boas práticas estabelecidas pelo sistema financeiro nacional, comunicamos que a atualização cadastral de empresas junto ao Internet Banking Empresarial é procedimento obrigatório e periódico.", estilo_texto))
                story.append(Spacer(1, 18))

                story.append(Paragraph("DADOS DO MASTER:", estilo_secao))
                story.append(Spacer(1, 6))
                tabela = [[Paragraph(f"<b>{k}:</b>", estilo_texto), Paragraph(str(v), estilo_texto)] for k, v in dados_empresa.items()]
                t = Table(tabela, colWidths=[100, 385])
                t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 2)]))
                story.append(t)
                story.append(Spacer(1, 18))

                story.append(Paragraph("A atualização cadastral tem como finalidade:", estilo_texto))
                story.append(Spacer(1, 8))

                check = CheckVerde(tamanho=10)
                for item in [
                    "Garantir a segurança das operações financeiras;",
                    "Manter os dados da empresa e de seus representantes legais atualizados;",
                    "Atender às exigências regulatórias vigentes;",
                    "Prevenir fraudes e inconsistências cadastrais.",
                ]:
                    row = Table([[check, Paragraph(item, estilo_topico)]], colWidths=[18, 467])
                    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4)]))
                    story.append(row)

                story.append(Spacer(1, 18))
                story.append(Paragraph("Reforçamos que a não realização da atualização dentro do prazo estabelecido poderá acarretar restrições operacionais, incluindo limitações temporárias de acesso a determinados serviços bancários.", estilo_texto))
                story.append(Spacer(1, 14))
                story.append(Paragraph("A atualização pode ser realizada diretamente pelo Bradesco Net Empresas, acessando o menu de Cadastro/Atualização Cadastral, ou mediante comparecimento à agência de relacionamento.", estilo_texto))
                story.append(Spacer(1, 14))
                story.append(Paragraph("Em caso de dúvidas, recomenda-se entrar em contato com seu gerente de contas ou com a central de atendimento empresarial.", estilo_texto))
                story.append(Spacer(1, 25))

                img_rodape = carregar_imagem(caminho_logo(pasta_script, LOGO_RODAPE), altura=75)
                img_qr = carregar_imagem(caminho_logo(pasta_script, QRCODE), largura=110, altura=110)
                p_legenda_qr = Paragraph("Escaneie o QR Code para acessar o portal", estilo_qr_legenda)

                bloco_qr = Table([[img_qr], [Spacer(1, 4)], [p_legenda_qr]], colWidths=[140])
                bloco_qr.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))

                rod = Table([["", img_rodape, bloco_qr, ""]], colWidths=[95, 145, 140, 125])
                rod.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("ALIGN", (2, 0), (2, 0), "LEFT"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
                story.append(rod)

                doc.build(story, onFirstPage=adicionar_marca_dagua, onLaterPages=adicionar_marca_dagua)
                return caminho_pdf

            ficha_input = st.text_area("COLE A FICHA DO CLIENTE AQUI", placeholder="Cole a linha ou o bloco de texto da ficha...", height=120)

            if st.button("Processar e Gerar PDF", type="primary"):
                if ficha_input.strip():
                    dados_extraidos = extrair_dados_ficha(ficha_input)
                    st.session_state['dados_empresa_cadastral'] = dados_extraidos
                    st.success("Ficha lida e dados extraídos com sucesso!")
                else:
                    st.warning("Por favor, cole uma ficha na caixa de texto acima.")

            if 'dados_empresa_cadastral' in st.session_state:
                dados = st.session_state['dados_empresa_cadastral']
                st.markdown("---")
                st.subheader("DADOS EXTRAÍDOS PARA O PDF")
                
                col1, col2 = st.columns(2)
                with col1:
                    razao_social = st.text_input("Razão Social", value=dados["Razão Social"])
                    cnpj_val = st.text_input("CNPJ", value=dados["CNPJ"])
                with col2:
                    situacao = st.text_input("Situação", value=dados["Situação"])
                    cpf_master = st.text_input("CPF Master", value=dados["CPF Master"])
                
                dados_atualizados = {
                    "Razão Social": razao_social,
                    "CNPJ": cnpj_val,
                    "Situação": situacao,
                    "CPF Master": cpf_master,
                    "Usuário(s)": dados.get("Usuário(s)", "NÃO IDENTIFICADO")
                }

                if st.button("Baixar PDF Pronto"):
                    caminho_pdf = gerar_pdf_cadastral(PASTA_SCRIPT, dados_atualizados)
                    with open(caminho_pdf, "rb") as f:
                        st.download_button(
                            label="📥 Clique aqui para salvar o PDF",
                            data=f,
                            file_name=os.path.basename(caminho_pdf),
                            mime="application/pdf"
                        )

    # ==========================================
    # 3. GERADOR DE BOLETIM (BOU)
    # ==========================================
    elif menu == "🌐 Gerador de Boletim (BOU)":
        st.markdown('<p class="titulo">🌐 Gerador de Boletim Web (BOU)</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("⏳ **Acesso Pendente:** Aguardando liberação do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Preencha os dados abaixo para gerar e baixar o PDF oficial do Boletim</p>', unsafe_allow_html=True)

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                uf_escolhida = st.selectbox("Selecione o Estado (UF):", UFS_ORDENADAS, format_func=lambda x: f"{x} - {ESTADOS[x]['nome']}")

            bancos_opcoes = {
                "Bradesco": "logo_bradesco.png",
                "Itaú": "logo_itau.png",
                "Caixa Econômica Federal": "logo_caixa.png",
                "Banco do Brasil": "logo_bb.png",
                "Santander": "logo_santander.png",
                "Nubank": "logo_nubank.png",
                "Banco Inter": "logo_inter.png",
                "C6 Bank": "logo_c6.png",
                "BTG Pactual": "logo_btg.png",
                "PagBank": "logo_pagbank.png",
                "PagSeguro": "logo_pagseguro.png",
                "Mercado Pago": "logo_mercadopago.png",
                "Banco SICOOB": "logo_sicoob.png",
                "Banco SICREDI": "logo_sicredi.png",
                "Banco Safra": "logo_safra.png",
                "Banrisul": "logo_banrisul.png",
                "Banco BMG": "logo_bmg.png",
                "Banco Pan": "logo_pan.png",
                "Banco Original": "logo_original.png",
                "Neon": "logo_neon.png",
                "XP Investimentos": "logo_xp.png",
                "Ame Digital": "logo_ame.png",
                "PicPay": "logo_picpay.png",
                "Banco Nordeste (BNB)": "logo_bnb.png",
                "Banco da Amazônia (BASA)": "logo_basa.png",
                "BRB - Banco de Brasília": "logo_brb.png",
                "Sem Logo": None
            }

            with col_b2:
                banco_escolhido_nome = st.selectbox("Selecione a Logo do Banco:", list(bancos_opcoes.keys()))
                logo_banco_nome = bancos_opcoes[banco_escolhido_nome]

            st.markdown('<div class="divisor" style="border-bottom: 1px solid #262730; margin-bottom: 20px; padding-bottom: 10px; font-size: 1.2rem; font-weight: bold;">DADOS DA VÍTIMA</div>', unsafe_allow_html=True)

            def registrar_fontes_bou():
                candidatos = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\ARIAL.TTF"]
                bold_cand = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\ARIALBD.TTF"]
                fonte, fonte_b = "Helvetica", "Helvetica-Bold"
                for path in candidatos:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont("ArialDoc", path))
                        fonte = "ArialDoc"
                        break
                for path in bold_cand:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont("ArialDoc-Bold", path))
                        fonte_b = "ArialDoc-Bold"
                        break
                return fonte, fonte_b

            FONTE_BOU, FONTE_B_BOU = registrar_fontes_bou()
            MESES_BOU = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
            DIAS_BOU = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

            def data_extenso_bou(dt=None):
                dt = dt or datetime.now()
                return f"{dt.day:02d} de {MESES_BOU[dt.month]} de {dt.year} - {DIAS_BOU[dt.weekday()]} às {dt.hour:02d}:{dt.minute:02d}"

            def formatar_cpf_bou(texto):
                numeros = "".join(filter(str.isdigit, str(texto)))
                if len(numeros) == 11:
                    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
                return str(texto)

            def formatar_celular_bou(texto):
                numeros = "".join(filter(str.isdigit, str(texto)))
                if len(numeros) == 11:
                    return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
                elif len(numeros) == 10:
                    return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
                return str(texto)

            def caminho_asset_bou(uf, nome):
                if not nome: return None
                nome_base, ext_original = os.path.splitext(nome)
                extensoes = [ext_original, ".png", ".jpg", ".jpeg", ""]
                locais_busca = [PASTA_LOGOS_BANCO, os.path.join(PASTA_LOGOS_ESTADOS, uf.upper()), os.path.join(ASSETS, uf.upper()), ASSETS]
                for local in locais_busca:
                    if not os.path.exists(local): continue
                    for arq in os.listdir(local):
                        for ext in extensoes:
                            if arq.lower() == f"{nome_base}{ext}".lower():
                                return os.path.join(local, arq)
                return None

            def carregar_texto_externo_bou():
                candidatos_txt = [os.path.join(PASTA_DADOS, "dados.txt"), os.path.join(PASTA_DADOS, "dados"), os.path.join(PASTA_SCRIPT, "dados.txt")]
                dados_txt = {
                    "capitulacao": "Art. 154-A do Código Penal . Motivo Presumido Crime Cibernético - Invasão de Dispositivo Informático",
                    "despacho": "Considerando a natureza da ocorrência, encaminhe-se este registro para o Departamento de Investigação de Crimes Cibernéticos para as devidas apurações e providências legais cabíveis."
                }
                for caminho in candidatos_txt:
                    if os.path.exists(caminho):
                        try:
                            with open(caminho, "r", encoding="utf-8") as f:
                                conteudo = f.read()
                            fato_match = re.search(r"FATO\s*AT[ÍI]PICO:?\s*(.*?)(?=\n\s*[A-Z\s]+:?|\Z)", conteudo, re.DOTALL | re.IGNORECASE)
                            despacho_match = re.search(r"DESPACHO\s*DA\s*AUTORIDADE:?\s*(.*?)(?=\n\s*[A-Z\s]+:?|\Z)", conteudo, re.DOTALL | re.IGNORECASE)
                            if fato_match: dados_txt["capitulacao"] = fato_match.group(1).strip()
                            if despacho_match: dados_txt["despacho"] = despacho_match.group(1).strip()
                            break
                        except Exception:
                            continue
                return dados_txt

            dados_txt_externos = carregar_texto_externo_bou()

            with st.form(key="form_bou"):
                vitima_nome = st.text_input("Nome Completo da Vítima:", placeholder="Ex: Carlos Eduardo")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    vitima_cpf = st.text_input("CPF da Vítima:", placeholder="000.000.000-00")
                with col_b:
                    vitima_celular = st.text_input("Celular da Vítima:", placeholder="(00) 00000-0000")
                    
                submit_bou = st.form_submit_button(label="📄 Processar e Gerar PDF do Boletim", type="primary")

            if submit_bou:
                if not vitima_nome:
                    st.error("⚠️ Por favor, preencha o nome da vítima.")
                else:
                    est = ESTADOS[uf_escolhida]
                    if banco_escolhido_nome == "Sem Logo":
                        dinamica_personalizada = "ACESSO INDEVIDO (INVASÃO) À CONTA E REMOÇÃO DO DISPOSITIVO NÃO AUTORIZADO"
                    else:
                        banco_texto = banco_escolhido_nome.upper()
                        dinamica_personalizada = f"ACESSO INDEVIDO (INVASÃO) APP {banco_texto}, ACESSO INDEVIDO À CONTA E REMOÇÃO DO DISPOSITIVO NÃO AUTORIZADO"
                    
                    dados_bou_finais = {
                        "uf": uf_escolhida,
                        "numero": "025-06119/2026",
                        "origem": est["origem"],
                        "circunscricao": est["circunscricao"],
                        "delegacia": est["delegacia"],
                        "endereco": est["endereco"],
                        "investigador": est["investigador"],
                        "investigador_cargo": est["investigador_cargo"],
                        "logo_banco_nome": logo_banco_nome,
                        "vitima_nome": vitima_nome,
                        "vitima_cpf": vitima_cpf if vitima_cpf else "000.000.000-00",
                        "vitima_celular": vitima_celular if vitima_celular else "(00) 00000-0000",
                        "capitulacao": dados_txt_externos.get("capitulacao", ""),
                        "despacho": dados_txt_externos.get("despacho", ""),
                        "dinamica": dinamica_personalizada,
                        "inicio": data_extenso_bou(datetime.now())
                    }

                    try:
                        buffer_bou = io.BytesIO()
                        c_bou = canvas.Canvas(buffer_bou, pagesize=A4)
                        L_BOU, A_BOU = A4
                        LX0_BOU, LX1_BOU = 30.75, 565.50

                        def y_top_bou(t_y): return A_BOU - t_y
                        def linha_bou(c_obj, t_y, grossa=False):
                            h_l = 1.5 if grossa else 0.75
                            c_obj.setFillColorRGB(0, 0, 0)
                            c_obj.rect(LX0_BOU, y_top_bou(t_y) - h_l, LX1_BOU - LX0_BOU, h_l, stroke=0, fill=1)

                        def draw_img_fit_bou(c_obj, path, max_x, t_y, max_w, max_h, align="right"):
                            if not path or not os.path.exists(path): return
                            img = ImageReader(path)
                            orig_w, orig_h = img.getSize()
                            if orig_w <= 0 or orig_h <= 0: return
                            scale = min(max_w / float(orig_w), max_h / float(orig_h))
                            f_w, f_h = orig_w * scale, orig_h * scale
                            x = max_x - f_w if align == "right" else max_x
                            c_obj.drawImage(img, x, y_top_bou(t_y + max_h) + ((max_h - f_h) / 2.0), width=f_w, height=f_h, preserveAspectRatio=True, mask="auto")

                        logo_pc = caminho_asset_bou(uf_escolhida, "logo_policia.png")
                        if logo_pc: c_bou.drawImage(ImageReader(logo_pc), 20.7, y_top_bou(26.3) - 127.2, width=108, height=127.2, preserveAspectRatio=True, mask="auto")
                        
                        cx_b = 350
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(31.8 + 9), est["governo"])
                        c_bou.drawCentredString(cx_b, y_top_bou(49.8 + 9), "SECRETARIA DE ESTADO DA SEGURANÇA PÚBLICA")
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(67.8 + 9), est["policia"])
                        c_bou.drawCentredString(cx_b, y_top_bou(85.1 + 9), dados_bou_finais["endereco"])
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(101.6 + 9), dados_bou_finais["delegacia"])

                        linha_bou(c_bou, 160.3, grossa=True)
                        linha_bou(c_bou, 184.3, grossa=True)
                        c_bou.setFont(FONTE_B_BOU, 11)
                        c_bou.drawString(30.5, y_top_bou(196.8 + 11), "REGISTRO DE OCORRÊNCIA")
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawRightString(L_BOU - 30.5, y_top_bou(196.8 + 10), f"No. {dados_bou_finais['numero']}")
                        linha_bou(c_bou, 218.8, grossa=True)

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(246.3 + 10), f"Início do Registro: {dados_bou_finais['inicio']}")
                        c_bou.drawString(30.5, y_top_bou(268.1 + 10), f"Origem: {dados_bou_finais['origem']} . Circunscrição: {dados_bou_finais['circunscricao']}")
                        linha_bou(c_bou, 299.1, grossa=False)

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(322.1 + 10), "Fato Atípico")
                        linha_bou(c_bou, 338.1, grossa=False)
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(357.3 + 10), f"Capitulação: {dados_bou_finais['capitulacao']}")

                        y_desp = 403.8
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_desp + 10), "Despacho da Autoridade")
                        linha_bou(c_bou, y_desp + 16, grossa=False)
                        c_bou.setFont(FONTE_B_BOU, 10)
                        y_texto = y_desp + 35.3
                        for ln in simpleSplit(dados_bou_finais["despacho"], FONTE_B_BOU, 10, LX1_BOU - 30.5):
                            c_bou.drawString(30.5, y_top_bou(y_texto), ln)
                            y_texto += 12

                        y_env_fixo = 517.1
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_env_fixo + 10), "Envolvido(s) na Ocorrência - Vítima")
                        linha_bou(c_bou, y_env_fixo + 16, grossa=False)

                        y_nome, y_cpf, y_cel = y_env_fixo + 35.2, y_env_fixo + 57.7, y_env_fixo + 79.5
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_nome + 10), "Nome")
                        c_bou.drawString(30.5, y_top_bou(y_cpf + 10), "CPF:")
                        c_bou.drawString(30.5, y_top_bou(y_cel + 10), "CELULAR:")

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(90.0, y_top_bou(y_nome + 10), str(dados_bou_finais["vitima_nome"]).upper())
                        c_bou.drawString(90.0, y_top_bou(y_cpf + 10), formatar_cpf_bou(dados_bou_finais["vitima_cpf"]))
                        c_bou.drawString(90.0, y_top_bou(y_cel + 10), formatar_celular_bou(dados_bou_finais["vitima_celular"]))

                        logo_banco = caminho_asset_bou(uf_escolhida, dados_bou_finais.get("logo_banco_nome"))
                        if logo_banco: draw_img_fit_bou(c_bou, logo_banco, max_x=LX1_BOU, t_y=y_nome - 2, max_w=140, max_h=40, align="right")

                        linha_bou(c_bou, y_cel + 52, grossa=False)

                        y_din = y_cel + 68
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_din), "Dinâmica do fato")
                        linha_bou(c_bou, y_din + 6, grossa=True)
                        
                        c_bou.setFont(FONTE_B_BOU, 10)
                        y_txt_din = y_din + 20
                        for ln in simpleSplit(dados_bou_finais["dinamica"], FONTE_B_BOU, 10, LX1_BOU - 30.5):
                            c_bou.drawString(30.5, y_top_bou(y_txt_din), ln)
                            y_txt_din += 12

                        y_proc = y_txt_din + 15
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_proc), "PROCEDIMENTO DE CANCELAMENTO IMEDIATO ATRAVÉS DE VALIDAÇÃO BIOMETRIA FACIAL")
                        linha_bou(c_bou, y_proc + 6, grossa=True)
                        c_bou.showPage()

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(40, y_top_bou(22), "Protocolo Administrativo nº: 048640-1023/2026")
                        assinatura = caminho_asset_bou(uf_escolhida, "assinatura.png")
                        if assinatura: c_bou.drawImage(ImageReader(assinatura), (L_BOU - 180)/2, y_top_bou(75)-35, width=180, height=35, preserveAspectRatio=True, mask="auto")
                        
                        c_bou.setLineWidth(0.8)
                        c_bou.line(L_BOU / 2 - 110, y_top_bou(120), L_BOU / 2 + 110, y_top_bou(120))
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawCentredString(L_BOU / 2, y_top_bou(140), dados_bou_finais["investigador"])
                        c_bou.setFont(FONTE_B_BOU, 8)
                        c_bou.drawCentredString(L_BOU / 2, y_top_bou(155), dados_bou_finais["investigador_cargo"])
                        
                        c_bou.save()
                        buffer_bou.seek(0)

                        st.success("✅ Boletim gerado com sucesso!")
                        nome_limpo_bou = re.sub(r'[<>:"/\\|?*]', "", vitima_nome).strip()
                        st.download_button(
                            label="📥 Clique aqui para baixar o Boletim em PDF",
                            data=buffer_bou,
                            file_name=f"{uf_escolhida} - {nome_limpo_bou}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar o boletim: {e}")

    # ==========================================
    # 4. GERADOR DE ALVARÁ
    # ==========================================
    elif menu == "⚖️ Gerador de Alvará":
        st.markdown('<p class="titulo">⚖️ Sistema de Alvarás - Tropa do Adv</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("⏳ **Acesso Pendente:** Sua conta está aguardando liberação do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Cole o texto do alvará abaixo para extrair os dados e gerar o PDF automaticamente</p>', unsafe_allow_html=True)

            def obter_data_extenso_alvara():
                meses = {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho", 
                         7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
                hoje = datetime.now()
                return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"

            def formatar_cpf_cnpj_alvara(valor):
                numeros = re.sub(r'\D', '', valor)
                if len(numeros) == 11:
                    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
                elif len(numeros) == 14:
                    return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
                return "000.000.000-00" if numeros == "" else valor

            def open_pdf_buffer_alvara(dados_alv):
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                largura, altura = A4
                
                template_path = os.path.join(PASTA_SCRIPT, 'template.png')
                if os.path.exists(template_path):
                    c.drawImage(template_path, 0, 0, width=largura, height=altura)

                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(440, altura - 153, f"{dados_alv['processo']}")
                
                x_margem = 105
                y_base = altura - 316 
                
                campos = [
                    ("Credor: ", dados_alv['nome']),
                    ("CPF/CNPJ: ", dados_alv['cpf']),
                    ("Processo N°: ", dados_alv['processo']),
                    ("Assunto: ", dados_alv['assunto']),
                    ("Contra: ", dados_alv['contra'])
                ]

                for label, valor in campos:
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(x_margem, y_base, label)
                    c.setFont("Helvetica", 11)
                    c.drawString(x_margem + (c.stringWidth(label, "Helvetica-Bold", 11) + 2), y_base, str(valor))
                    y_base -= 18

                y_valor = altura - 540
                c.setFont("Helvetica-Bold", 11)
                label_v = f"Valor a receber: R$ {dados_alv['valor_str']} "
                c.drawString(x_margem, y_valor, label_v)
                
                largura_l = c.stringWidth(label_v, "Helvetica-Bold", 11)
                c.setFont("Helvetica", 11)
                extenso_p = f"({dados_alv['extenso']})"
                
                linhas = textwrap.wrap(extenso_p, width=55) 
                for i, linha in enumerate(linhas):
                    pos_y = y_valor if i == 0 else y_valor - (i * 14)
                    pos_x = x_margem + largura_l if i == 0 else x_margem
                    c.drawString(pos_x, pos_y, linha)

                c.setFont("Helvetica-Bold", 11)
                c.drawCentredString(largura/2, altura - 675, dados_alv['advogado'])
                c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso_alvara()}.")
                
                c.save()
                buffer.seek(0)
                return buffer

            texto_raw_alv = st.text_area(
                "📄 Cole o texto do alvará abaixo:",
                placeholder="Cole aqui o conteúdo copiado do WhatsApp ou do documento...",
                height=250
            )

            if st.button("🚀 Processar e Gerar Alvará", type="primary"):
                if not texto_raw_alv.strip():
                    st.warning("⚠️ Por favor, cole o texto do alvará na caixa acima.")
                else:
                    texto_raw_alv = texto_raw_alv.replace("\\", "/")

                    try:
                        cpf_match = re.search(r"(?:CPF[:\s]*)?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", texto_raw_alv, re.I)
                        cpf_raw = cpf_match.group(1) if cpf_match else "000.000.000-00"

                        nome_match = re.search(r"(?:Sra\.|Sr\.|NOME[:\s]*)\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        nome = nome_match.group(1).strip().replace('*', '') if nome_match else "Não Encontrado"

                        proc_match = re.search(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", texto_raw_alv)
                        proc = proc_match.group(1) if proc_match else "Não Encontrado"

                        assunto_match = re.search(r"(?:Assunto|•)\*?:\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        assunto = assunto_match.group(1).strip().replace('*', '') if assunto_match else "Não Encontrado"

                        contra_match = re.search(r"(?:contrária|Reqda|Reqdo|Contra)\*?:\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        contra = contra_match.group(1).strip().replace('*', '') if contra_match else "Não Encontrado"

                        valor_match = re.search(r"liberação\s+do\s+valor\s+de\s+\*?R\$\s*([\d.,]+)\*?", texto_raw_alv, re.I)
                        if valor_match:
                            valor_str = valor_match.group(1).strip()
                        else:
                            partes = re.split(r"Prezado\s+Sr\(a\)\.", texto_raw_alv, flags=re.I)
                            texto_corpo = partes[1] if len(partes) > 1 else texto_raw_alv
                            vm = re.search(r"R\$\s*([\d.,]+)", texto_corpo)
                            valor_str = vm.group(1).strip() if vm else "0,00"

                        adv_match = re.search(r"(?:Atenciosamente,)\s*(?:[\r\n\s]*)(Dr[a]?\.\s*\*?[^*,\n]+\*?)|(Dr[a]?\.\s*\*?[^*,\n]+\*?)", texto_raw_alv, re.I)
                        advogado = "Não Encontrado"
                        if adv_match:
                            bruto = (adv_match.group(1) or adv_match.group(2)).strip().replace('*', '')
                            advogado = bruto
                        else:
                            linhas_texto = texto_raw_alv.splitlines()
                            for linha in linhas_texto:
                                if "Dr." in linha or "Dra." in linha:
                                    advogado = linha.replace('*', '').strip()
                                    break

                        num_limpo = valor_str.replace('.', '').replace(',', '.')
                        try:
                            extenso = num2words(float(num_limpo), lang='pt_BR', to='currency').title()
                        except:
                            extenso = "Zero Reais"

                        dados_alv_final = {
                            'nome': nome, 
                            'processo': proc, 
                            'contra': contra, 
                            'assunto': assunto, 
                            'valor_str': valor_str,
                            'extenso': extenso, 
                            'advogado': advogado, 
                            'cpf': formatar_cpf_cnpj_alvara(cpf_raw),
                        }

                        st.success("✅ Dados extraídos e mapeados com sucesso!")
                        st.markdown("---")

                        st.markdown("### 📋 Dados Mapeados:")
                        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Credor:** {nome}")
                            st.write(f"**CPF/CNPJ:** {dados_alv_final['cpf']}")
                            st.write(f"**Processo:** {proc}")
                            st.write(f"**Assunto:** {assunto}")
                        with col2:
                            st.write(f"**Contra:** {contra}")
                            st.write(f"**Valor:** R$ {valor_str}")
                            st.write(f"**Advogado:** {advogado}")
                        st.markdown('</div>', unsafe_allow_html=True)

                        pdf_buffer_alv = open_pdf_buffer_alvara(dados_alv_final)
                        nome_limpo_arquivo = re.sub(r'[\\/*?:"<>|]', "", nome)
                        
                        st.download_button(
                            label="📥 Baixar Alvará em PDF",
                            data=pdf_buffer_alv,
                            file_name=f"ALVARA_{nome_limpo_arquivo}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )

                    except Exception as e:
                        st.error(f"❌ Ocorreu um erro durante o processamento do texto: {e}")

    # ==========================================
    # PAINEL DO ADMIN: GERENCIAR E LIBERAR CONTAS
    # ==========================================
    elif menu == "👥 Gerenciar Usuários e Cargos":
        st.markdown('<p class="titulo">👥 Painel de Gerenciamento de Contas</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo">Mude o cargo dos usuários para liberar o acesso deles</p>', unsafe_allow_html=True)

        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
        st.markdown("### 📋 Lista de Usuários Cadastrados")
        
        db = carregar_banco()
        
        for u in list(db.keys()):
            col_u1, col_u2, col_u3 = st.columns([2, 2, 2])
            with col_u1:
                st.write(f"👤 **{u}**")
            with col_u2:
                novo_cargo_selecionado = st.selectbox(
                    f"Cargo de {u}", 
                    ["Aguardando Liberação", "Funcionário 2B", "Administrador"],
                    index=["Aguardando Liberação", "Funcionário 2B", "Administrador"].index(db[u]["cargo"]) if db[u]["cargo"] in ["Aguardando Liberação", "Funcionário 2B", "Administrador"] else 0,
                    key=f"cargo_{u}"
                )
                if novo_cargo_selecionado != db[u]["cargo"]:
                    db[u]["cargo"] = novo_cargo_selecionado
                    salvar_banco(db)
                    st.success(f"Cargo de {u} atualizado com sucesso!")
                    st.rerun()
            with col_u3:
                st.write("")
                st.write(f"*Status atual:* `{db[u]['cargo']}`")
            st.markdown("---")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # PAINEL DO ADMIN: AUDITORIA DE ACESSOS EM TEMPO REAL
    # ==========================================
    elif menu == "📊 Auditoria de Acessos":
        st.markdown('<p class="titulo">📊 Auditoria de Acessos em Tempo Real</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo">Acompanhe quem acessou o sistema, data/hora e o sistema operacional</p>', unsafe_allow_html=True)

        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
        st.markdown("### 🔍 Histórico de Conexões Recentes")
        
        logs = st.session_state["logs_acesso"]
        if not logs:
            st.info("Nenhum acesso registrado nesta sessão ainda.")
        else:
            for log in logs:
                st.write(f"🟢 **Usuário:** `{log['usuario']}` ({log['cargo']}) | 📅 **Data/Hora:** {log['data']} | 💻 **Dispositivo/SO:** `{log['dispositivo']}` | 📍 **Localização IP:** {log['local']}")
                st.markdown("---")
        st.markdown('</div>', unsafe_allow_html=True)
    .subtitulo { text-align: center; color: #8a99ad; margin-bottom: 30px; }
    .bloco-secao { background-color: #161b22; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #30363d; }
    input { color: #000000 !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(PASTA_SCRIPT, "assets")
PASTA_LOGOS_BANCO = os.path.join(ASSETS, "logo_banco")
PASTA_LOGOS_ESTADOS = os.path.join(ASSETS, "logo_estados")
PASTA_DADOS = os.path.join(ASSETS, "dados")
PASTA_LOGOS = os.path.join(ASSETS, "logos")

LOGO_CABECALHO = "logo_cabecalho.png"
LOGO_RODAPE = "logo_rodape.png"
LOGO_MARCA_DAGUA = "marca_dagua.png"
QRCODE = "qrcode.png"

ESTADOS = {
    "AC": {"nome": "Acre", "governo": "GOVERNO DO ESTADO DO ACRE", "policia": "POLÍCIA CIVIL DO ESTADO DO ACRE", "endereco": "Rua Quintino Bocaiúva, 1490 - Bosque, Rio Branco - AC, 69900-640, TEL.: (68) 3212-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "CARLOS EDUARDO MENDES OLIVEIRA", "investigador_cargo": "Investigador Policial - 112.045-1"},
    "AL": {"nome": "Alagoas", "governo": "GOVERNO DO ESTADO DE ALAGOAS", "policia": "POLÍCIA CIVIL DO ESTADO DE ALAGOAS", "endereco": "Av. Fernandes Lima, 2345 - Farol, Maceió - AL, 57050-000, TEL.: (82) 3315-2400", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "ROBERTO ALVES COSTA NETO", "investigador_cargo": "Investigador Policial - 223.118-4"},
    "AP": {"nome": "Amapá", "governo": "GOVERNO DO ESTADO DO AMAPÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO AMAPÁ", "endereco": "Av. FAB, 1685 - Central, Macapá - AP, 68900-074, TEL.: (96) 3212-5800", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "PAULO HENRIQUE SILVA RAMOS", "investigador_cargo": "Investigador Policial - 089.334-2"},
    "AM": {"nome": "Amazonas", "governo": "GOVERNO DO ESTADO DO AMAZONAS", "policia": "POLÍCIA CIVIL DO ESTADO DO AMAZONAS", "endereco": "Av. André Araújo, 1923 - Aleixo, Manaus - AM, 69060-000, TEL.: (92) 3648-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "MARCOS VINICIUS FERREIRA LIMA", "investigador_cargo": "Investigador Policial - 445.201-8"},
    "BA": {"nome": "Bahia", "governo": "GOVERNO DO ESTADO DA BAHIA", "policia": "POLÍCIA CIVIL DO ESTADO DA BAHIA", "endereco": "Av. Centenário, 2883 - Chame-Chame, Salvador - BA, 40155-150, TEL.: (71) 3116-6000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "JULIO CESAR SANTOS BARBOSA", "investigador_cargo": "Investigador Policial - 567.890-3"},
    "CE": {"nome": "Ceará", "governo": "GOVERNO DO ESTADO DO CEARÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO CEARÁ", "endereco": "Av. Bezerra de Menezes, 581 - São Gerardo, Fortaleza - CE, 60325-000, TEL.: (85) 3101-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "FRANCISCO DAS CHAGAS MOURA", "investigador_cargo": "Investigador Policial - 334.672-1"},
    "DF": {"nome": "Distrito Federal", "governo": "GOVERNO DO DISTRITO FEDERAL", "policia": "POLÍCIA CIVIL DO DISTRITO FEDERAL", "endereco": "SAF Sul Quadra 6 - Zona Cívico-Administrativa, Brasília - DF, 70040-912, TEL.: (61) 3207-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RICARDO ALMEIDA PINTO JUNIOR", "investigador_cargo": "Investigador Policial - 901.245-6"},
    "ES": {"nome": "Espírito Santo", "governo": "GOVERNO DO ESTADO DO ESPÍRITO SANTO", "policia": "POLÍCIA CIVIL DO ESTADO DO ESPÍRITO SANTO", "endereco": "Av. Governador Bley, 236 - Centro, Vitória - ES, 29010-150, TEL.: (27) 3636-1100", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "ANDERSON LUIZ PEREIRA GOMES", "investigador_cargo": "Investigador Policial - 178.456-9"},
    "GO": {"nome": "Goiás", "governo": "GOVERNO DO ESTADO DE GOIÁS", "policia": "POLÍCIA CIVIL DO ESTADO DE GOIÁS", "endereco": "Av. Anhanguera, 7171 - St. Oeste, Goiânia - GO, 74110-010, TEL.: (62) 3201-1500", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "DIEGO FERNANDES CASTRO SILVA", "investigador_cargo": "Investigador Policial - 612.903-5"},
    "MA": {"nome": "Maranhão", "governo": "GOVERNO DO ESTADO DO MARANHÃO", "policia": "POLÍCIA CIVIL DO ESTADO DO MARANHÃO", "endereco": "Av. dos Holandeses, s/n - Calhau, São Luís - MA, 65071-380, TEL.: (98) 3214-8000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RAFAEL SOUSA NASCIMENTO", "investigador_cargo": "Investigador Policial - 256.781-0"},
    "MT": {"nome": "Mato Grosso", "governo": "GOVERNO DO ESTADO DE MATO GROSSO", "policia": "POLÍCIA CIVIL DO ESTADO DE MATO GROSSO", "endereco": "Av. Escolástico, 346 - Bandeirantes, Cuiabá - MT, 78010-200, TEL.: (65) 3613-5630", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "023ª Delegacia", "investigador": "ANDRE RELVA SANTANA GANANÇA", "investigador_cargo": "Investigador Policial - 968.961-3"},
    "MS": {"nome": "Mato Grosso do Sul", "governo": "GOVERNO DO ESTADO DE MATO GROSSO DO SUL", "policia": "POLÍCIA CIVIL DO ESTADO DE MATO GROSSO DO SUL", "endereco": "Rua Rui Barbosa, 3500 - Monte Castelo, Campo Grande - MS, 79010-220, TEL.: (67) 3318-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "LUCIANO ROBERTO DIAS MELO", "investigador_cargo": "Investigador Policial - 401.556-7"},
    "MG": {"nome": "Minas Gerais", "governo": "GOVERNO DO ESTADO DE MINAS GERAIS", "policia": "POLÍCIA CIVIL DO ESTADO DE MINAS GERAIS", "endereco": "Av. Presidente Carlos Luz, 1275 - Caiçaras, Belo Horizonte - MG, 31230-000, TEL.: (31) 3330-7000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "GUSTAVO HENRIQUE CAMPOS REIS", "investigador_cargo": "Investigador Policial - 789.012-4"},
    "PA": {"nome": "Pará", "governo": "GOVERNO DO ESTADO DO PARÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO PARÁ", "endereco": "Av. Magalhães Barata, 651 - São Brás, Belém - PA, 66063-240, TEL.: (91) 3201-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "EDUARDO BRITO FIGUEIREDO", "investigador_cargo": "Investigador Policial - 345.678-2"},
    "PB": {"nome": "Paraíba", "governo": "GOVERNO DO ESTADO DA PARAÍBA", "policia": "POLÍCIA CIVIL DO ESTADO DA PARAÍBA", "endereco": "Av. Duarte da Silveira, 600 - Centro, João Pessoa - PB, 58013-280, TEL.: (83) 3218-5000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "THIAGO LACERDA FREITAS", "investigador_cargo": "Investigador Policial - 512.349-8"},
    "PR": {"nome": "Paraná", "governo": "GOVERNO DO ESTADO DO PARANÁ", "policia": "POLÍCIA CIVIL DO ESTADO DO PARANÁ", "endereco": "Rua Desembargador Westphalen, 35 - Centro, Curitiba - PR, 80010-110, TEL.: (41) 3313-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "FELIPE AUGUSTO RODRIGUES", "investigador_cargo": "Investigador Policial - 678.901-3"},
    "PE": {"nome": "Pernambuco", "governo": "GOVERNO DO ESTADO DE PERNAMBUCO", "policia": "POLÍCIA CIVIL DO ESTADO DE PERNAMBUCO", "endereco": "Rua da Aurora, 485 - Boa Vista, Recife - PE, 50050-000, TEL.: (81) 3181-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "BRUNO CESAR ALBUQUERQUE", "investigador_cargo": "Investigador Policial - 234.567-1"},
    "PI": {"nome": "Piauí", "governo": "GOVERNO DO ESTADO DO PIAUÍ", "policia": "POLÍCIA CIVIL DO ESTADO DO PIAUÍ", "endereco": "Av. Frei Serafim, 2352 - Centro/Sul, Teresina - PI, 64001-020, TEL.: (86) 3216-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "LEONARDO MATOS VIEIRA", "investigador_cargo": "Investigador Policial - 890.123-5"},
    "RJ": {"nome": "Rio de Janeiro", "governo": "GOVERNO DO ESTADO DO RIO DE JANEIRO", "policia": "POLÍCIA CIVIL DO ESTADO DO RIO DE JANEIRO", "endereco": "Rua da Relação, 42 - Centro, Rio de Janeiro - RJ, 20231-110, TEL.: (21) 2332-8000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "MARCELO ANDRADE TEIXEIRA", "investigador_cargo": "Investigador Policial - 456.789-0"},
    "RN": {"nome": "Rio Grande do Norte", "governo": "GOVERNO DO ESTADO DO RIO GRANDE DO NORTE", "policia": "POLÍCIA CIVIL DO ESTADO DO RIO GRANDE DO NORTE", "endereco": "Av. Coronel Estevam, 1959 - Alecrim, Natal - RN, 59020-000, TEL.: (84) 3232-2000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "PEDRO HENRIQUE DANTAS", "investigador_cargo": "Investigador Policial - 123.456-7"},
    "RS": {"nome": "Rio Grande do Sul", "governo": "GOVERNO DO ESTADO DO RIO GRANDE DO SUL", "policia": "POLÍCIA CIVIL DO ESTADO DO RIO GRANDE DO SUL", "endereco": "Av. João Pessoa, 2050 - Cidade Baixa, Porto Alegre - RS, 90040-000, TEL.: (51) 3288-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "ALEXANDRE SCHMIDT OLIVEIRA", "investigador_cargo": "Investigador Policial - 567.234-8"},
    "RO": {"nome": "Rondônia", "governo": "GOVERNO DO ESTADO DE RONDÔNIA", "policia": "POLÍCIA CIVIL DO ESTADO DE RONDÔNIA", "endereco": "Av. Presidente Dutra, 2986 - Centro, Porto Velho - RO, 76801-086, TEL.: (69) 3216-5000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "WELLINGTON SOUZA CARVALHO", "investigador_cargo": "Investigador Policial - 678.345-9"},
    "RR": {"nome": "Roraima", "governo": "GOVERNO DO ESTADO DE RORAIMA", "policia": "POLÍCIA CIVIL DO ESTADO DE RORAIMA", "endereco": "Av. Ville Roy, 5245 - São Vicente, Boa Vista - RR, 69303-340, TEL.: (95) 3621-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "JOSÉ ROBERTO ALMEIDA", "investigador_cargo": "Investigador Policial - 089.012-3"},
    "SC": {"nome": "Santa Catarina", "governo": "GOVERNO DO ESTADO DE SANTA CATARINA", "policia": "POLÍCIA CIVIL DO ESTADO DE SANTA CATARINA", "endereco": "Rua Paschoal Apóstolo Pítsica, 4840 - Agronômica, Florianópolis - SC, 88025-255, TEL.: (48) 3665-6000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RODRIGO MACHADO BORGES", "investigador_cargo": "Investigador Policial - 345.901-2"},
    "SP": {"nome": "São Paulo", "governo": "GOVERNO DO ESTADO DE SÃO PAULO", "policia": "POLÍCIA CIVIL DO ESTADO DE SÃO PAULO", "endereco": "Av. São Luís, 99 - República, São Paulo - SP, 01046-001, TEL.: (11) 3311-3000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "RENATO APARECIDO SILVA", "investigador_cargo": "Investigador Policial - 812.345-6"},
    "SE": {"nome": "Sergipe", "governo": "GOVERNO DO ESTADO DE SERGIPE", "policia": "POLÍCIA CIVIL DO ESTADO DE SERGIPE", "endereco": "Av. Ministro Geraldo Barreto Sobral, 215 - Capucho, Aracaju - SE, 49080-470, TEL.: (79) 3226-1000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "DANIEL SANTOS MENEZES", "investigador_cargo": "Investigador Policial - 456.012-7"},
    "TO": {"nome": "Tocantins", "governo": "GOVERNO DO ESTADO DO TOCANTINS", "policia": "POLÍCIA CIVIL DO ESTADO DO TOCANTINS", "endereco": "Av. Teotônio Segurado, 102 Sul - Plano Diretor Sul, Palmas - TO, 77016-002, TEL.: (63) 3218-4000", "delegacia": "Delegacia Especializada de Repressão a Crimes Cibernéticos", "origem": "Delegacia de Polícia Digital", "circunscricao": "01ª Delegacia", "investigador": "FABIANO COSTA LIMA", "investigador_cargo": "Investigador Policial - 567.890-1"},
}
UFS_ORDENADAS = sorted(ESTADOS.keys())

# ==========================================
# GERENCIAMENTO DE USUÁRIOS E PERSISTÊNCIA
# ==========================================
if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = {
        "admin": {"senha": "123", "cargo": "Administrador"},
        "funcionario_teste": {"senha": "123", "cargo": "Funcionário 2B"}
    }

if "logs_acesso" not in st.session_state:
    st.session_state["logs_acesso"] = []

# Mantém a sessão ativa mesmo se apertar F5 usando parâmetros na URL
params = st.query_params
if "user" in params and "cargo" in params:
    st.session_state["autenticado"] = True
    st.session_state["usuario_atual"] = params["user"]
    st.session_state["cargo_atual"] = params["cargo"]

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario_atual"] = ""
    st.session_state["cargo_atual"] = ""

def tela_login():
    st.markdown('<p class="titulo">🛡️ Acesso Restrito</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo">Faça login ou crie sua conta para acessar o sistema</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
        
        with aba_login:
            with st.form("form_login"):
                usuario = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")
                botao_entrar = st.form_submit_button("Entrar", use_container_width=True)
                
                if botao_entrar:
                    db = st.session_state["usuarios_db"]
                    if usuario in db and db[usuario]["senha"] == senha:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_atual"] = usuario
                        st.session_state["cargo_atual"] = db[usuario]["cargo"]
                        
                        # Salva na URL para o F5 não derrubar o login
                        st.query_params["user"] = usuario
                        st.query_params["cargo"] = db[usuario]["cargo"]
                        
                        so_detectado = "Windows PC"
                        if hasattr(st, "context") and hasattr(st.context, "headers"):
                            ua = str(st.context.headers.get("Sec-Ch-Ua-Platform", ""))
                            if "Android" in ua: so_detectado = "Android"
                            elif "iOS" in ua or "iPhone" in ua: so_detectado = "iOS (iPhone/iPad)"
                            elif "Mac" in ua: so_detectado = "MacOS"

                        localizacao_ip = "Brasil (Rede Local)"
                        try:
                            res = requests.get("https://ipapi.co/json/", timeout=2).json()
                            cidade = res.get("city")
                            regiao = res.get("region")
                            pais = res.get("country_name")
                            if cidade:
                                localizacao_ip = f"{cidade} - {regiao}, {pais}"
                            else:
                                res2 = requests.get("https://ipwho.is/", timeout=2).json()
                                cidade2 = res2.get("city")
                                regiao2 = res2.get("region")
                                if cidade2:
                                    localizacao_ip = f"{cidade2} - {regiao2}"
                        except:
                            pass

                        hora_atual = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
                        st.session_state["logs_acesso"].insert(0, {
                            "usuario": usuario,
                            "cargo": db[usuario]["cargo"],
                            "data": hora_atual,
                            "dispositivo": so_detectado,
                            "local": localizacao_ip
                        })

                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos.")

        with aba_cadastro:
            with st.form("form_auto_cadastro"):
                novo_user = st.text_input("Escolha um Usuário")
                nova_senha = st.text_input("Escolha uma Senha", type="password")
                botao_cadastrar = st.form_submit_button("Cadastrar Conta", use_container_width=True)
                
                if botao_cadastrar:
                    if not novo_user.strip() or not nova_senha.strip():
                        st.warning("⚠️ Preencha todos os campos.")
                    elif novo_user in st.session_state["usuarios_db"]:
                        st.error("❌ Este nome de usuário já está em uso.")
                    else:
                        st.session_state["usuarios_db"][novo_user] = {
                            "senha": nova_senha,
                            "cargo": "Aguardando Liberação"
                        }
                        st.success("✅ Conta criada com sucesso! Aguarde o Administrador liberar seu acesso.")

if not st.session_state["autenticado"]:
    tela_login()
else:
    # ==========================================
    # PAINEL LATERAL E NAVEGAÇÃO
    # ==========================================
    def obter_imagem_base64(nome_arquivo_base):
        caminhos_possiveis = [
            os.path.join(ASSETS, f"{nome_arquivo_base}.png"),
            os.path.join(ASSETS, f"{nome_arquivo_base}.jpg"),
            os.path.join(ASSETS, f"{nome_arquivo_base}.jpeg"),
            os.path.join(PASTA_SCRIPT, f"{nome_arquivo_base}.png"),
            os.path.join(PASTA_SCRIPT, f"{nome_arquivo_base}.jpg"),
        ]
        for caminho in caminhos_possiveis:
            if os.path.exists(caminho):
                with open(caminho, "rb") as f:
                    data = f.read()
                ext = caminho.split('.')[-1].lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                return f"data:{mime};base64,{base64.b64encode(data).decode()}"
        return None

    img_selo_b64 = obter_imagem_base64("selo")
    
    if st.session_state['cargo_atual'] in ["Administrador", "Funcionário 2B"]:
        if img_selo_b64:
            html_usuario = f"""
            <div style="display: flex; align-items: center; font-size: 1rem; color: #ffffff; font-weight: 600;">
                <span>👤 <b>Logado como:</b> {st.session_state['usuario_atual']}</span>
                <img src="{img_selo_b64}" width="20" style="margin-left: 6px; vertical-align: middle;" />
            </div>
            """
        else:
            html_usuario = f"👤 **Logado como:** {st.session_state['usuario_atual']} 🔵"
            
        st.sidebar.markdown(html_usuario, unsafe_allow_html=True)
        st.sidebar.markdown(f"🔑 **Cargo:** {st.session_state['cargo_atual']}")
        st.sidebar.markdown('<div style="color: #2ecc71; font-size: 0.8rem; font-weight: bold; margin-top: -5px;">✔ CONTA VERIFICADA</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f"👤 **Logado como:** {st.session_state['usuario_atual']}")
        st.sidebar.markdown(f"🔑 **Cargo:** {st.session_state['cargo_atual']}")
        st.sidebar.markdown('<div style="color: #e74c3c; font-size: 0.8rem; font-weight: bold; margin-top: -5px;">⏳ AGUARDANDO LIBERAÇÃO</div>', unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Sair / Logout"):
        st.session_state["autenticado"] = False
        st.query_params.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    
    opcoes_menu = [
        "🏦 Confirmação de Agendamento", 
        "📄 Atualização Cadastral",
        "🌐 Gerador de Boletim (BOU)",
        "⚖️ Gerador de Alvará"
    ]
    
    if st.session_state["cargo_atual"] == "Administrador":
        opcoes_menu.append("👥 Gerenciar Usuários e Cargos")
        opcoes_menu.append("📊 Auditoria de Acessos")

    menu = st.sidebar.radio("📂 Escolha a Ferramenta:", opcoes_menu)

    def verificar_permissao():
        cargo = st.session_state["cargo_atual"]
        if cargo in ["Administrador", "Funcionário 2B"]:
            return True
        return False

    # ==========================================
    # 1. CONFIRMAÇÃO DE AGENDAMENTO
    # ==========================================
    if menu == "🏦 Confirmação de Agendamento":
        st.markdown('<p class="titulo">🏦 Sistema de Confirmação de Agendamento</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("⏳ **Acesso Pendente:** Sua conta está aguardando liberação do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Preencha os dados abaixo para gerar o PDF oficial</p>', unsafe_allow_html=True)

            st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
            st.markdown("### 🏢 Dados de Débito (Sua Conta / Empresa)")
            col1, col2 = st.columns(2)
            with col1:
                debito_agencia = st.text_input("Agência de Débito", value="1234")
                debito_tipo = st.text_input("Tipo da Conta de Débito", value="Conta Corrente")
                empresa_cnpj = st.text_input("CNPJ da Empresa", value="00.000.000/0001-00")
            with col2:
                debito_conta = st.text_input("Conta de Débito", value="12345-6")
                empresa_nome = st.text_input("Nome da Empresa", value="Minha Empresa LTDA")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
            st.markdown("### 👤 Dados do Favorecido (Quem Recebe)")
            col3, col4 = st.columns(2)
            with col3:
                favorecido_nome = st.text_input("Nome do Favorecido", value="João da Silva")
                credito_banco = st.text_input("Banco de Crédito", value="Itaú")
                credito_conta = st.text_input("Conta de Crédito", value="98765-4")
                motivo_ted = st.text_input("Motivo da TED", value="Pagamento de Serviços")
                data_debito = st.text_input("Data de Débito (DD/MM/AAAA)", value=datetime.now().strftime("%d/%m/%Y"))
            with col4:
                favorecido_cnpj = st.text_input("CNPJ/CPF do Favorecido", value="111.222.333-44")
                credito_agencia = st.text_input("Agência de Crédito", value="5678")
                credito_tipo = st.text_input("Tipo de Conta do Favorecido", value="Conta Corrente")
                valor = st.text_input("Valor (R$)", value="1.500,00")
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button("🚀 Gerar PDF de Confirmação de Agendamento", type="primary"):
                try:
                    buffer = io.BytesIO()
                    dados = {
                        "empresa_nome": empresa_nome.upper(),
                        "favorecido_nome": favorecido_nome.upper(),
                        "valor": valor,
                    }
                    nome_arq = f"CONFIRMAÇÃO AGENDAMENTO - {re.sub(r'[\\/*?:"<>|]', '', favorecido_nome)}.pdf"
                    
                    c = canvas.Canvas(buffer, pagesize=A4)
                    c.drawString(50, 500, f"Comprovante de Agendamento - Empresa: {dados['empresa_nome']}")
                    c.drawString(50, 480, f"Favorecido: {dados['favorecido_nome']} | Valor: R$ {dados['valor']}")
                    c.save()
                    buffer.seek(0)

                    st.success("✅ PDF gerado com sucesso!")
                    st.download_button("📥 Baixar PDF", data=buffer, file_name=nome_arq, mime="application/pdf", type="primary")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

    # ==========================================
    # 2. ATUALIZAÇÃO CADASTRAL
    # ==========================================
    elif menu == "📄 Atualização Cadastral":
        st.markdown('<p class="titulo">📄 Atualizador de PDF Cadastral</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("⏳ **Acesso Pendente:** Aguardando liberação do Administrador.")
        else:
            st.markdown('<p class="subtext" style="color:#8b949e; text-align:center;">Cole a ficha do cliente abaixo para extrair os dados e gerar o PDF</p>', unsafe_allow_html=True)

            def extrair_dados_ficha(texto_ficha):
                dados = {
                    "Razão Social": "NÃO IDENTIFICADO",
                    "CNPJ": "00.000.000/0000-00",
                    "Situação": "ATIVA",
                    "CPF Master": "000.000.000-00",
                    "Usuário(s)": "NÃO IDENTIFICADO",
                }
                if not texto_ficha.strip():
                    return dados
                texto_ficha = texto_ficha.replace("\\", "/")
                match_cnpj_rotulo = re.search(r"CNPJ[:\s]+([\d./-]+)", texto_ficha, re.IGNORECASE)
                if match_cnpj_rotulo:
                    c_limpo = re.sub(r"\D", "", match_cnpj_rotulo.group(1))
                    if len(c_limpo) == 14:
                        dados["CNPJ"] = f"{c_limpo[:2]}.{c_limpo[2:5]}.{c_limpo[5:8]}/{c_limpo[8:12]}-{c_limpo[12:]}"
                match_razao_rotulo = re.search(r"RAZ[ÃA]O SOCIAL[:\s]+([^\n]+)", texto_ficha, re.IGNORECASE)
                if match_razao_rotulo:
                    dados["Razão Social"] = match_razao_rotulo.group(1).strip()
                match_cpf_rotulo = re.search(r"CPF USU[ÁA]RIO MASTER[:\s]+([\d.-]+)", texto_ficha, re.IGNORECASE)
                if match_cpf_rotulo:
                    cpf_limpo = re.sub(r"\D", "", match_cpf_rotulo.group(1))
                    if len(cpf_limpo) == 11:
                        dados["CPF Master"] = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
                matches_user = re.findall(r"USU[ÁA]RIOS?[:\s]+([A-Za-z0-9]+)", texto_ficha, re.IGNORECASE)
                for val_user in matches_user:
                    val_user_limpo = val_user.strip()
                    if val_user_limpo and val_user_limpo.upper() != "MASTER":
                        dados["Usuário(s)"] = val_user_limpo
                        break
                return dados

            class CheckVerde(Flowable):
                def __init__(self, tamanho=10):
                    Flowable.__init__(self)
                    self.tamanho = tamanho
                    self.width = tamanho
                    self.height = tamanho
                def draw(self):
                    c = self.canv
                    s = self.tamanho
                    r = s / 2
                    c.saveState()
                    c.setFillColor(colors.HexColor("#00A859"))
                    c.circle(r, r, r, fill=1, stroke=0)
                    c.setStrokeColor(colors.white)
                    c.setLineWidth(1.4)
                    c.setLineCap(1)
                    c.line(s * 0.28, s * 0.48, s * 0.42, s * 0.32)
                    c.line(s * 0.42, s * 0.32, s * 0.72, s * 0.68)
                    c.restoreState()

            class LinhaVertical(Flowable):
                def __init__(self, altura=38, cor="#B0B0B0", largura_linha=1):
                    Flowable.__init__(self)
                    self.altura = altura
                    self.cor = cor
                    self.largura_linha = largura_linha
                    self.width = largura_linha
                    self.height = altura
                def draw(self):
                    c = self.canv
                    c.saveState()
                    c.setStrokeColor(colors.HexColor(self.cor))
                    c.setLineWidth(self.largura_linha)
                    c.line(0, 0, 0, self.altura)
                    c.restoreState()

            def caminho_logo(pasta_script, nome):
                return os.path.join(pasta_script, PASTA_LOGOS, nome)

            def carregar_imagem(caminho, largura=None, altura=None):
                if os.path.exists(caminho):
                    img = Image(caminho)
                    if altura and not largura:
                        fator = altura / float(img.imageHeight)
                        img.drawWidth = img.imageWidth * fator
                        img.drawHeight = altura
                    elif largura and not altura:
                        fator = largura / float(img.imageWidth)
                        img.drawWidth = largura
                        img.drawHeight = img.imageHeight * fator
                    elif largura and altura:
                        img.drawWidth = largura
                        img.drawHeight = altura
                    return img
                return Spacer(largura or 100, altura or 30)

            def adicionar_marca_dagua(canvas, doc):
                caminho = caminho_logo(PASTA_SCRIPT, LOGO_MARCA_DAGUA)
                if not os.path.exists(caminho):
                    caminho = caminho_logo(PASTA_SCRIPT, LOGO_RODAPE)
                canvas.saveState()
                try:
                    canvas.setFillAlpha(0.05)
                    canvas.setStrokeAlpha(0.05)
                except AttributeError:
                    pass
                largura_item, altura_item, passo_x, passo_y = 130, 120, 130, 120
                if os.path.exists(caminho):
                    row_idx = 0
                    for y in range(-20, int(A4[1]) + 70, passo_y):
                        offset_x = (row_idx % 2) * (passo_x / 2)
                        for x in range(-80, int(A4[0]) + 100, passo_x):
                            canvas.drawImage(caminho, x + offset_x, y, width=largura_item, height=altura_item, mask="auto", preserveAspectRatio=True)
                        row_idx += 1
                canvas.restoreState()

            def gerar_pdf_cadastral(pasta_script, dados_empresa):
                razao = dados_empresa["Razão Social"]
                razao_limpa = re.sub(r'[\\/*?:"<>|]', "", razao)
                nome_pdf = f"ATUALIZAÇÃO CADASTRAL - {razao_limpa}.pdf"
                caminho_pdf = os.path.join(pasta_script, nome_pdf)

                doc = SimpleDocTemplate(caminho_pdf, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45)
                story = []
                styles = getSampleStyleSheet()

                estilo_titulo = ParagraphStyle("Titulo", parent=styles["Heading1"], fontSize=13.5, leading=16, fontName="Helvetica-Bold", textColor=colors.HexColor("#111111"))
                estilo_sub = ParagraphStyle("Sub", parent=styles["Heading2"], fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#222222"))
                estilo_secao = ParagraphStyle("Secao", parent=styles["Normal"], fontSize=10, leading=13, fontName="Helvetica-Bold", textColor=colors.HexColor("#333333"))
                estilo_texto = ParagraphStyle("Texto", parent=styles["Normal"], fontSize=9.5, leading=13.5, textColor=colors.HexColor("#444444"))
                estilo_topico = ParagraphStyle("Topico", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=colors.HexColor("#333333"))
                estilo_qr_legenda = ParagraphStyle("QRLegenda", parent=styles["Normal"], fontSize=8, leading=10, alignment=1, textColor=colors.HexColor("#666666"))

                logo_topo = carregar_imagem(caminho_logo(pasta_script, LOGO_CABECALHO), altura=68)
                linha_divisoria = LinhaVertical(altura=60, cor="#B0B0B0", largura_linha=1)
                p_titulo = Paragraph("COMUNICADO IMPORTANTE", estilo_titulo)

                cab = Table([[logo_topo, linha_divisoria, p_titulo]], colWidths=[200, 25, 270])
                cab.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
                story.append(cab)
                story.append(Spacer(1, 22))

                story.append(Paragraph("ATUALIZAÇÃO CADASTRAL", estilo_sub))
                story.append(Spacer(1, 6))
                story.append(Paragraph("Em conformidade com as diretrizes de autorregulação bancária e as boas práticas estabelecidas pelo sistema financeiro nacional, comunicamos que a atualização cadastral de empresas junto ao Internet Banking Empresarial é procedimento obrigatório e periódico.", estilo_texto))
                story.append(Spacer(1, 18))

                story.append(Paragraph("DADOS DO MASTER:", estilo_secao))
                story.append(Spacer(1, 6))
                tabela = [[Paragraph(f"<b>{k}:</b>", estilo_texto), Paragraph(str(v), estilo_texto)] for k, v in dados_empresa.items()]
                t = Table(tabela, colWidths=[100, 385])
                t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 2)]))
                story.append(t)
                story.append(Spacer(1, 18))

                story.append(Paragraph("A atualização cadastral tem como finalidade:", estilo_texto))
                story.append(Spacer(1, 8))

                check = CheckVerde(tamanho=10)
                for item in [
                    "Garantir a segurança das operações financeiras;",
                    "Manter os dados da empresa e de seus representantes legais atualizados;",
                    "Atender às exigências regulatórias vigentes;",
                    "Prevenir fraudes e inconsistências cadastrais.",
                ]:
                    row = Table([[check, Paragraph(item, estilo_topico)]], colWidths=[18, 467])
                    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4)]))
                    story.append(row)

                story.append(Spacer(1, 18))
                story.append(Paragraph("Reforçamos que a não realização da atualização dentro do prazo estabelecido poderá acarretar restrições operacionais, incluindo limitações temporárias de acesso a determinados serviços bancários.", estilo_texto))
                story.append(Spacer(1, 14))
                story.append(Paragraph("A atualização pode ser realizada diretamente pelo Bradesco Net Empresas, acessando o menu de Cadastro/Atualização Cadastral, ou mediante comparecimento à agência de relacionamento.", estilo_texto))
                story.append(Spacer(1, 14))
                story.append(Paragraph("Em caso de dúvidas, recomenda-se entrar em contato com seu gerente de contas ou com a central de atendimento empresarial.", estilo_texto))
                story.append(Spacer(1, 25))

                img_rodape = carregar_imagem(caminho_logo(pasta_script, LOGO_RODAPE), altura=75)
                img_qr = carregar_imagem(caminho_logo(pasta_script, QRCODE), largura=110, altura=110)
                p_legenda_qr = Paragraph("Escaneie o QR Code para acessar o portal", estilo_qr_legenda)

                bloco_qr = Table([[img_qr], [Spacer(1, 4)], [p_legenda_qr]], colWidths=[140])
                bloco_qr.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))

                rod = Table([["", img_rodape, bloco_qr, ""]], colWidths=[95, 145, 140, 125])
                rod.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("ALIGN", (2, 0), (2, 0), "LEFT"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
                story.append(rod)

                doc.build(story, onFirstPage=adicionar_marca_dagua, onLaterPages=adicionar_marca_dagua)
                return caminho_pdf

            ficha_input = st.text_area("COLE A FICHA DO CLIENTE AQUI", placeholder="Cole a linha ou o bloco de texto da ficha...", height=120)

            if st.button("Processar e Gerar PDF", type="primary"):
                if ficha_input.strip():
                    dados_extraidos = extrair_dados_ficha(ficha_input)
                    st.session_state['dados_empresa_cadastral'] = dados_extraidos
                    st.success("Ficha lida e dados extraídos com sucesso!")
                else:
                    st.warning("Por favor, cole uma ficha na caixa de texto acima.")

            if 'dados_empresa_cadastral' in st.session_state:
                dados = st.session_state['dados_empresa_cadastral']
                st.markdown("---")
                st.subheader("DADOS EXTRAÍDOS PARA O PDF")
                
                col1, col2 = st.columns(2)
                with col1:
                    razao_social = st.text_input("Razão Social", value=dados["Razão Social"])
                    cnpj_val = st.text_input("CNPJ", value=dados["CNPJ"])
                with col2:
                    situacao = st.text_input("Situação", value=dados["Situação"])
                    cpf_master = st.text_input("CPF Master", value=dados["CPF Master"])
                
                dados_atualizados = {
                    "Razão Social": razao_social,
                    "CNPJ": cnpj_val,
                    "Situação": situacao,
                    "CPF Master": cpf_master,
                    "Usuário(s)": dados.get("Usuário(s)", "NÃO IDENTIFICADO")
                }

                if st.button("Baixar PDF Pronto"):
                    caminho_pdf = gerar_pdf_cadastral(PASTA_SCRIPT, dados_atualizados)
                    with open(caminho_pdf, "rb") as f:
                        st.download_button(
                            label="📥 Clique aqui para salvar o PDF",
                            data=f,
                            file_name=os.path.basename(caminho_pdf),
                            mime="application/pdf"
                        )

    # ==========================================
    # 3. GERADOR DE BOLETIM (BOU)
    # ==========================================
    elif menu == "🌐 Gerador de Boletim (BOU)":
        st.markdown('<p class="titulo">🌐 Gerador de Boletim Web (BOU)</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("⏳ **Acesso Pendente:** Aguardando liberação do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Preencha os dados abaixo para gerar e baixar o PDF oficial do Boletim</p>', unsafe_allow_html=True)

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                uf_escolhida = st.selectbox("Selecione o Estado (UF):", UFS_ORDENADAS, format_func=lambda x: f"{x} - {ESTADOS[x]['nome']}")

            bancos_opcoes = {
                "Bradesco": "logo_bradesco.png",
                "Itaú": "logo_itau.png",
                "Caixa Econômica Federal": "logo_caixa.png",
                "Banco do Brasil": "logo_bb.png",
                "Santander": "logo_santander.png",
                "Nubank": "logo_nubank.png",
                "Banco Inter": "logo_inter.png",
                "C6 Bank": "logo_c6.png",
                "BTG Pactual": "logo_btg.png",
                "PagBank": "logo_pagbank.png",
                "PagSeguro": "logo_pagseguro.png",
                "Mercado Pago": "logo_mercadopago.png",
                "Banco SICOOB": "logo_sicoob.png",
                "Banco SICREDI": "logo_sicredi.png",
                "Banco Safra": "logo_safra.png",
                "Banrisul": "logo_banrisul.png",
                "Banco BMG": "logo_bmg.png",
                "Banco Pan": "logo_pan.png",
                "Banco Original": "logo_original.png",
                "Neon": "logo_neon.png",
                "XP Investimentos": "logo_xp.png",
                "Ame Digital": "logo_ame.png",
                "PicPay": "logo_picpay.png",
                "Banco Nordeste (BNB)": "logo_bnb.png",
                "Banco da Amazônia (BASA)": "logo_basa.png",
                "BRB - Banco de Brasília": "logo_brb.png",
                "Sem Logo": None
            }

            with col_b2:
                banco_escolhido_nome = st.selectbox("Selecione a Logo do Banco:", list(bancos_opcoes.keys()))
                logo_banco_nome = bancos_opcoes[banco_escolhido_nome]

            st.markdown('<div class="divisor" style="border-bottom: 1px solid #262730; margin-bottom: 20px; padding-bottom: 10px; font-size: 1.2rem; font-weight: bold;">DADOS DA VÍTIMA</div>', unsafe_allow_html=True)

            def registrar_fontes_bou():
                candidatos = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\ARIAL.TTF"]
                bold_cand = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\ARIALBD.TTF"]
                fonte, fonte_b = "Helvetica", "Helvetica-Bold"
                for path in candidatos:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont("ArialDoc", path))
                        fonte = "ArialDoc"
                        break
                for path in bold_cand:
                    if os.path.exists(path):
                        pdfmetrics.registerFont(TTFont("ArialDoc-Bold", path))
                        fonte_b = "ArialDoc-Bold"
                        break
                return fonte, fonte_b

            FONTE_BOU, FONTE_B_BOU = registrar_fontes_bou()
            MESES_BOU = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
            DIAS_BOU = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

            def data_extenso_bou(dt=None):
                dt = dt or datetime.now()
                return f"{dt.day:02d} de {MESES_BOU[dt.month]} de {dt.year} - {DIAS_BOU[dt.weekday()]} às {dt.hour:02d}:{dt.minute:02d}"

            def formatar_cpf_bou(texto):
                numeros = "".join(filter(str.isdigit, str(texto)))
                if len(numeros) == 11:
                    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
                return str(texto)

            def formatar_celular_bou(texto):
                numeros = "".join(filter(str.isdigit, str(texto)))
                if len(numeros) == 11:
                    return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
                elif len(numeros) == 10:
                    return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
                return str(texto)

            def caminho_asset_bou(uf, nome):
                if not nome: return None
                nome_base, ext_original = os.path.splitext(nome)
                extensoes = [ext_original, ".png", ".jpg", ".jpeg", ""]
                locais_busca = [PASTA_LOGOS_BANCO, os.path.join(PASTA_LOGOS_ESTADOS, uf.upper()), os.path.join(ASSETS, uf.upper()), ASSETS]
                for local in locais_busca:
                    if not os.path.exists(local): continue
                    for arq in os.listdir(local):
                        for ext in extensoes:
                            if arq.lower() == f"{nome_base}{ext}".lower():
                                return os.path.join(local, arq)
                return None

            def carregar_texto_externo_bou():
                candidatos_txt = [os.path.join(PASTA_DADOS, "dados.txt"), os.path.join(PASTA_DADOS, "dados"), os.path.join(PASTA_SCRIPT, "dados.txt")]
                dados_txt = {
                    "capitulacao": "Art. 154-A do Código Penal . Motivo Presumido Crime Cibernético - Invasão de Dispositivo Informático",
                    "despacho": "Considerando a natureza da ocorrência, encaminhe-se este registro para o Departamento de Investigação de Crimes Cibernéticos para as devidas apurações e providências legais cabíveis."
                }
                for caminho in candidatos_txt:
                    if os.path.exists(caminho):
                        try:
                            with open(caminho, "r", encoding="utf-8") as f:
                                conteudo = f.read()
                            fato_match = re.search(r"FATO\s*AT[ÍI]PICO:?\s*(.*?)(?=\n\s*[A-Z\s]+:?|\Z)", conteudo, re.DOTALL | re.IGNORECASE)
                            despacho_match = re.search(r"DESPACHO\s*DA\s*AUTORIDADE:?\s*(.*?)(?=\n\s*[A-Z\s]+:?|\Z)", conteudo, re.DOTALL | re.IGNORECASE)
                            if fato_match: dados_txt["capitulacao"] = fato_match.group(1).strip()
                            if despacho_match: dados_txt["despacho"] = despacho_match.group(1).strip()
                            break
                        except Exception:
                            continue
                return dados_txt

            dados_txt_externos = carregar_texto_externo_bou()

            with st.form(key="form_bou"):
                vitima_nome = st.text_input("Nome Completo da Vítima:", placeholder="Ex: Carlos Eduardo")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    vitima_cpf = st.text_input("CPF da Vítima:", placeholder="000.000.000-00")
                with col_b:
                    vitima_celular = st.text_input("Celular da Vítima:", placeholder="(00) 00000-0000")
                    
                submit_bou = st.form_submit_button(label="📄 Processar e Gerar PDF do Boletim", type="primary")

            if submit_bou:
                if not vitima_nome:
                    st.error("⚠️ Por favor, preencha o nome da vítima.")
                else:
                    est = ESTADOS[uf_escolhida]
                    if banco_escolhido_nome == "Sem Logo":
                        dinamica_personalizada = "ACESSO INDEVIDO (INVASÃO) À CONTA E REMOÇÃO DO DISPOSITIVO NÃO AUTORIZADO"
                    else:
                        banco_texto = banco_escolhido_nome.upper()
                        dinamica_personalizada = f"ACESSO INDEVIDO (INVASÃO) APP {banco_texto}, ACESSO INDEVIDO À CONTA E REMOÇÃO DO DISPOSITIVO NÃO AUTORIZADO"
                    
                    dados_bou_finais = {
                        "uf": uf_escolhida,
                        "numero": "025-06119/2026",
                        "origem": est["origem"],
                        "circunscricao": est["circunscricao"],
                        "delegacia": est["delegacia"],
                        "endereco": est["endereco"],
                        "investigador": est["investigador"],
                        "investigador_cargo": est["investigador_cargo"],
                        "logo_banco_nome": logo_banco_nome,
                        "vitima_nome": vitima_nome,
                        "vitima_cpf": vitima_cpf if vitima_cpf else "000.000.000-00",
                        "vitima_celular": vitima_celular if vitima_celular else "(00) 00000-0000",
                        "capitulacao": dados_txt_externos.get("capitulacao", ""),
                        "despacho": dados_txt_externos.get("despacho", ""),
                        "dinamica": dinamica_personalizada,
                        "inicio": data_extenso_bou(datetime.now())
                    }

                    try:
                        buffer_bou = io.BytesIO()
                        c_bou = canvas.Canvas(buffer_bou, pagesize=A4)
                        L_BOU, A_BOU = A4
                        LX0_BOU, LX1_BOU = 30.75, 565.50

                        def y_top_bou(t_y): return A_BOU - t_y
                        def linha_bou(c_obj, t_y, grossa=False):
                            h_l = 1.5 if grossa else 0.75
                            c_obj.setFillColorRGB(0, 0, 0)
                            c_obj.rect(LX0_BOU, y_top_bou(t_y) - h_l, LX1_BOU - LX0_BOU, h_l, stroke=0, fill=1)

                        def draw_img_fit_bou(c_obj, path, max_x, t_y, max_w, max_h, align="right"):
                            if not path or not os.path.exists(path): return
                            img = ImageReader(path)
                            orig_w, orig_h = img.getSize()
                            if orig_w <= 0 or orig_h <= 0: return
                            scale = min(max_w / float(orig_w), max_h / float(orig_h))
                            f_w, f_h = orig_w * scale, orig_h * scale
                            x = max_x - f_w if align == "right" else max_x
                            c_obj.drawImage(img, x, y_top_bou(t_y + max_h) + ((max_h - f_h) / 2.0), width=f_w, height=f_h, preserveAspectRatio=True, mask="auto")

                        logo_pc = caminho_asset_bou(uf_escolhida, "logo_policia.png")
                        if logo_pc: c_bou.drawImage(ImageReader(logo_pc), 20.7, y_top_bou(26.3) - 127.2, width=108, height=127.2, preserveAspectRatio=True, mask="auto")
                        
                        cx_b = 350
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(31.8 + 9), est["governo"])
                        c_bou.drawCentredString(cx_b, y_top_bou(49.8 + 9), "SECRETARIA DE ESTADO DA SEGURANÇA PÚBLICA")
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(67.8 + 9), est["policia"])
                        c_bou.drawCentredString(cx_b, y_top_bou(85.1 + 9), dados_bou_finais["endereco"])
                        c_bou.setFont(FONTE_B_BOU, 9)
                        c_bou.drawCentredString(cx_b, y_top_bou(101.6 + 9), dados_bou_finais["delegacia"])

                        linha_bou(c_bou, 160.3, grossa=True)
                        linha_bou(c_bou, 184.3, grossa=True)
                        c_bou.setFont(FONTE_B_BOU, 11)
                        c_bou.drawString(30.5, y_top_bou(196.8 + 11), "REGISTRO DE OCORRÊNCIA")
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawRightString(L_BOU - 30.5, y_top_bou(196.8 + 10), f"No. {dados_bou_finais['numero']}")
                        linha_bou(c_bou, 218.8, grossa=True)

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(246.3 + 10), f"Início do Registro: {dados_bou_finais['inicio']}")
                        c_bou.drawString(30.5, y_top_bou(268.1 + 10), f"Origem: {dados_bou_finais['origem']} . Circunscrição: {dados_bou_finais['circunscricao']}")
                        linha_bou(c_bou, 299.1, grossa=False)

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(322.1 + 10), "Fato Atípico")
                        linha_bou(c_bou, 338.1, grossa=False)
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(357.3 + 10), f"Capitulação: {dados_bou_finais['capitulacao']}")

                        y_desp = 403.8
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_desp + 10), "Despacho da Autoridade")
                        linha_bou(c_bou, y_desp + 16, grossa=False)
                        c_bou.setFont(FONTE_B_BOU, 10)
                        y_texto = y_desp + 35.3
                        for ln in simpleSplit(dados_bou_finais["despacho"], FONTE_B_BOU, 10, LX1_BOU - 30.5):
                            c_bou.drawString(30.5, y_top_bou(y_texto), ln)
                            y_texto += 12

                        y_env_fixo = 517.1
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_env_fixo + 10), "Envolvido(s) na Ocorrência - Vítima")
                        linha_bou(c_bou, y_env_fixo + 16, grossa=False)

                        y_nome, y_cpf, y_cel = y_env_fixo + 35.2, y_env_fixo + 57.7, y_env_fixo + 79.5
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_nome + 10), "Nome")
                        c_bou.drawString(30.5, y_top_bou(y_cpf + 10), "CPF:")
                        c_bou.drawString(30.5, y_top_bou(y_cel + 10), "CELULAR:")

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(90.0, y_top_bou(y_nome + 10), str(dados_bou_finais["vitima_nome"]).upper())
                        c_bou.drawString(90.0, y_top_bou(y_cpf + 10), formatar_cpf_bou(dados_bou_finais["vitima_cpf"]))
                        c_bou.drawString(90.0, y_top_bou(y_cel + 10), formatar_celular_bou(dados_bou_finais["vitima_celular"]))

                        logo_banco = caminho_asset_bou(uf_escolhida, dados_bou_finais.get("logo_banco_nome"))
                        if logo_banco: draw_img_fit_bou(c_bou, logo_banco, max_x=LX1_BOU, t_y=y_nome - 2, max_w=140, max_h=40, align="right")

                        linha_bou(c_bou, y_cel + 52, grossa=False)

                        y_din = y_cel + 68
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_din), "Dinâmica do fato")
                        linha_bou(c_bou, y_din + 6, grossa=True)
                        
                        c_bou.setFont(FONTE_B_BOU, 10)
                        y_txt_din = y_din + 20
                        for ln in simpleSplit(dados_bou_finais["dinamica"], FONTE_B_BOU, 10, LX1_BOU - 30.5):
                            c_bou.drawString(30.5, y_top_bou(y_txt_din), ln)
                            y_txt_din += 12

                        y_proc = y_txt_din + 15
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(30.5, y_top_bou(y_proc), "PROCEDIMENTO DE CANCELAMENTO IMEDIATO ATRAVÉS DE VALIDAÇÃO BIOMETRIA FACIAL")
                        linha_bou(c_bou, y_proc + 6, grossa=True)
                        c_bou.showPage()

                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawString(40, y_top_bou(22), "Protocolo Administrativo nº: 048640-1023/2026")
                        assinatura = caminho_asset_bou(uf_escolhida, "assinatura.png")
                        if assinatura: c_bou.drawImage(ImageReader(assinatura), (L_BOU - 180)/2, y_top_bou(75)-35, width=180, height=35, preserveAspectRatio=True, mask="auto")
                        
                        c_bou.setLineWidth(0.8)
                        c_bou.line(L_BOU / 2 - 110, y_top_bou(120), L_BOU / 2 + 110, y_top_bou(120))
                        c_bou.setFont(FONTE_B_BOU, 10)
                        c_bou.drawCentredString(L_BOU / 2, y_top_bou(140), dados_bou_finais["investigador"])
                        c_bou.setFont(FONTE_B_BOU, 8)
                        c_bou.drawCentredString(L_BOU / 2, y_top_bou(155), dados_bou_finais["investigador_cargo"])
                        
                        c_bou.save()
                        buffer_bou.seek(0)

                        st.success("✅ Boletim gerado com sucesso!")
                        nome_limpo_bou = re.sub(r'[<>:"/\\|?*]', "", vitima_nome).strip()
                        st.download_button(
                            label="📥 Clique aqui para baixar o Boletim em PDF",
                            data=buffer_bou,
                            file_name=f"{uf_escolhida} - {nome_limpo_bou}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar o boletim: {e}")

    # ==========================================
    # 4. GERADOR DE ALVARÁ
    # ==========================================
    elif menu == "⚖️ Gerador de Alvará":
        st.markdown('<p class="titulo">⚖️ Sistema de Alvarás - Tropa do Adv</p>', unsafe_allow_html=True)
        
        if not verificar_permissao():
            st.error("⏳ **Acesso Pendente:** Aguardando liberação do Administrador.")
        else:
            st.markdown('<p class="subtitulo">Cole o texto do alvará abaixo para extrair os dados e gerar o PDF automaticamente</p>', unsafe_allow_html=True)

            def obter_data_extenso_alvara():
                meses = {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho", 
                         7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
                hoje = datetime.now()
                return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"

            def formatar_cpf_cnpj_alvara(valor):
                numeros = re.sub(r'\D', '', valor)
                if len(numeros) == 11:
                    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
                elif len(numeros) == 14:
                    return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
                return "000.000.000-00" if numeros == "" else valor

            def open_pdf_buffer_alvara(dados_alv):
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                largura, altura = A4
                
                template_path = os.path.join(PASTA_SCRIPT, 'template.png')
                if os.path.exists(template_path):
                    c.drawImage(template_path, 0, 0, width=largura, height=altura)

                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(440, altura - 153, f"{dados_alv['processo']}")
                
                x_margem = 105
                y_base = altura - 316 
                
                campos = [
                    ("Credor: ", dados_alv['nome']),
                    ("CPF/CNPJ: ", dados_alv['cpf']),
                    ("Processo N°: ", dados_alv['processo']),
                    ("Assunto: ", dados_alv['assunto']),
                    ("Contra: ", dados_alv['contra'])
                ]

                for label, valor in campos:
                    c.setFont("Helvetica-Bold", 11)
                    c.drawString(x_margem, y_base, label)
                    c.setFont("Helvetica", 11)
                    c.drawString(x_margem + (c.stringWidth(label, "Helvetica-Bold", 11) + 2), y_base, str(valor))
                    y_base -= 18

                y_valor = altura - 540
                c.setFont("Helvetica-Bold", 11)
                label_v = f"Valor a receber: R$ {dados_alv['valor_str']} "
                c.drawString(x_margem, y_valor, label_v)
                
                largura_l = c.stringWidth(label_v, "Helvetica-Bold", 11)
                c.setFont("Helvetica", 11)
                extenso_p = f"({dados_alv['extenso']})"
                
                linhas = textwrap.wrap(extenso_p, width=55) 
                for i, linha in enumerate(linhas):
                    pos_y = y_valor if i == 0 else y_valor - (i * 14)
                    pos_x = x_margem + largura_l if i == 0 else x_margem
                    c.drawString(pos_x, pos_y, linha)

                c.setFont("Helvetica-Bold", 11)
                c.drawCentredString(largura/2, altura - 675, dados_alv['advogado'])
                c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso_alvara()}.")
                
                c.save()
                buffer.seek(0)
                return buffer

            texto_raw_alv = st.text_area(
                "📄 Cole o texto do alvará abaixo:",
                placeholder="Cole aqui o conteúdo copiado do WhatsApp ou do documento...",
                height=250
            )

            if st.button("🚀 Processar e Gerar Alvará", type="primary"):
                if not texto_raw_alv.strip():
                    st.warning("⚠️ Por favor, cole o texto do alvará na caixa acima.")
                else:
                    texto_raw_alv = texto_raw_alv.replace("\\", "/")

                    try:
                        cpf_match = re.search(r"(?:CPF[:\s]*)?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", texto_raw_alv, re.I)
                        cpf_raw = cpf_match.group(1) if cpf_match else "000.000.000-00"

                        nome_match = re.search(r"(?:Sra\.|Sr\.|NOME[:\s]*)\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        nome = nome_match.group(1).strip().replace('*', '') if nome_match else "Não Encontrado"

                        proc_match = re.search(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", texto_raw_alv)
                        proc = proc_match.group(1) if proc_match else "Não Encontrado"

                        assunto_match = re.search(r"(?:Assunto|•)\*?:\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        assunto = assunto_match.group(1).strip().replace('*', '') if assunto_match else "Não Encontrado"

                        contra_match = re.search(r"(?:contrária|Reqda|Reqdo|Contra)\*?:\s*\*?([^*,\n]+)\*?", texto_raw_alv, re.I)
                        contra = contra_match.group(1).strip().replace('*', '') if contra_match else "Não Encontrado"

                        valor_match = re.search(r"liberação\s+do\s+valor\s+de\s+\*?R\$\s*([\d.,]+)\*?", texto_raw_alv, re.I)
                        if valor_match:
                            valor_str = valor_match.group(1).strip()
                        else:
                            partes = re.split(r"Prezado\s+Sr\(a\)\.", texto_raw_alv, flags=re.I)
                            texto_corpo = partes[1] if len(partes) > 1 else texto_raw_alv
                            vm = re.search(r"R\$\s*([\d.,]+)", texto_corpo)
                            valor_str = vm.group(1).strip() if vm else "0,00"

                        adv_match = re.search(r"(?:Atenciosamente,)\s*(?:[\r\n\s]*)(Dr[a]?\.\s*\*?[^*,\n]+\*?)|(Dr[a]?\.\s*\*?[^*,\n]+\*?)", texto_raw_alv, re.I)
                        advogado = "Não Encontrado"
                        if adv_match:
                            bruto = (adv_match.group(1) or adv_match.group(2)).strip().replace('*', '')
                            advogado = bruto
                        else:
                            linhas_texto = texto_raw_alv.splitlines()
                            for linha in linhas_texto:
                                if "Dr." in linha or "Dra." in linha:
                                    advogado = linha.replace('*', '').strip()
                                    break

                        num_limpo = valor_str.replace('.', '').replace(',', '.')
                        try:
                            extenso = num2words(float(num_limpo), lang='pt_BR', to='currency').title()
                        except:
                            extenso = "Zero Reais"

                        dados_alv_final = {
                            'nome': nome, 
                            'processo': proc, 
                            'contra': contra, 
                            'assunto': assunto, 
                            'valor_str': valor_str,
                            'extenso': extenso, 
                            'advogado': advogado, 
                            'cpf': formatar_cpf_cnpj_alvara(cpf_raw),
                        }

                        st.success("✅ Dados extraídos e mapeados com sucesso!")
                        st.markdown("---")

                        st.markdown("### 📋 Dados Mapeados:")
                        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Credor:** {nome}")
                            st.write(f"**CPF/CNPJ:** {dados_alv_final['cpf']}")
                            st.write(f"**Processo:** {proc}")
                            st.write(f"**Assunto:** {assunto}")
                        with col2:
                            st.write(f"**Contra:** {contra}")
                            st.write(f"**Valor:** R$ {valor_str}")
                            st.write(f"**Advogado:** {advogado}")
                        st.markdown('</div>', unsafe_allow_html=True)

                        pdf_buffer_alv = open_pdf_buffer_alvara(dados_alv_final)
                        nome_limpo_arquivo = re.sub(r'[\\/*?:"<>|]', "", nome)
                        
                        st.download_button(
                            label="📥 Baixar Alvará em PDF",
                            data=pdf_buffer_alv,
                            file_name=f"ALVARA_{nome_limpo_arquivo}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )

                    except Exception as e:
                        st.error(f"❌ Ocorreu um erro durante o processamento do texto: {e}")

    # ==========================================
    # PAINEL DO ADMIN: GERENCIAR E LIBERAR CONTAS
    # ==========================================
    elif menu == "👥 Gerenciar Usuários e Cargos":
        st.markdown('<p class="titulo">👥 Painel de Gerenciamento de Contas</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo">Mude o cargo dos usuários para liberar o acesso deles</p>', unsafe_allow_html=True)

        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
        st.markdown("### 📋 Lista de Usuários Cadastrados")
        
        db = st.session_state["usuarios_db"]
        
        for u in list(db.keys()):
            col_u1, col_u2, col_u3 = st.columns([2, 2, 2])
            with col_u1:
                st.write(f"👤 **{u}**")
            with col_u2:
                novo_cargo_selecionado = st.selectbox(
                    f"Cargo de {u}", 
                    ["Aguardando Liberação", "Funcionário 2B", "Administrador"],
                    index=["Aguardando Liberação", "Funcionário 2B", "Administrador"].index(db[u]["cargo"]) if db[u]["cargo"] in ["Aguardando Liberação", "Funcionário 2B", "Administrador"] else 0,
                    key=f"cargo_{u}"
                )
                db[u]["cargo"] = novo_cargo_selecionado
            with col_u3:
                st.write("")
                st.write(f"*Status atual:* `{db[u]['cargo']}`")
            st.markdown("---")
            
        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # PAINEL DO ADMIN: AUDITORIA DE ACESSOS EM TEMPO REAL
    # ==========================================
    elif menu == "📊 Auditoria de Acessos":
        st.markdown('<p class="titulo">📊 Auditoria de Acessos em Tempo Real</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitulo">Acompanhe quem acessou o sistema, data/hora e o sistema operacional</p>', unsafe_allow_html=True)

        st.markdown('<div class="bloco-secao">', unsafe_allow_html=True)
        st.markdown("### 🔍 Histórico de Conexões Recentes")
        
        logs = st.session_state["logs_acesso"]
        if not logs:
            st.info("Nenhum acesso registrado nesta sessão ainda.")
        else:
            for log in logs:
                st.write(f"🟢 **Usuário:** `{log['usuario']}` ({log['cargo']}) | 📅 **Data/Hora:** {log['data']} | 💻 **Dispositivo/SO:** `{log['dispositivo']}` | 📍 **Localização IP:** {log['local']}")
                st.markdown("---")
        st.markdown('</div>', unsafe_allow_html=True)
