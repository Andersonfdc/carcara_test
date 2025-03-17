import streamlit as st
import os
import requests
import json
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF
import io

load_dotenv()

# Configurações
MIRO_ACCESS_TOKEN = os.getenv("MIRO_ACCESS_TOKEN")

# Função para obter elementos do Miro
def get_miro_elements(board_id, access_token):
    url = f"https://api.miro.com/v2/boards/{board_id}/items"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    items = []
    next_page = None

    while True:
        params = {'limit': 50}  # Limite máximo por página
        if next_page:
            params['cursor'] = next_page

        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            items.extend(data.get('data', []))
            next_page = data.get('cursor', None)
            if not next_page:
                break
        else:
            st.error(f"Erro ao acessar o board: {response.status_code} - {response.text}")
            return None
    
    return items

# Função para processar diretamente os dados dos itens (evita chamadas adicionais)
def process_board_items(items):
    structured_data = []

    for item in items:
        item_id = item.get('id')
        item_type = item.get('type')
        item_data = item.get('data', {})
        item_position = item.get('position', {})

        # Captura os textos diretamente se disponíveis
        title = item_data.get('content') or item_data.get('title') or 'N/A'
        description = item_data.get('description') or 'N/A'

        structured_item = {
            'id': item_id,
            'type': item_type,
            'title': title,
            'description': description,
            'position': item_position,
            'metadata': item.get('metadata', {})
        }

        structured_data.append(structured_item)

    return structured_data

# Função para enviar dados ao ChatGPT com prompt aprimorado
def send_to_chatgpt(data):
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Converte os dados para uma string JSON formatada
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    
    prompt = (
        "Você receberá um JSON com os dados completos do fluxo do Miro. "
        "Analise detalhadamente todas as chaves, relações, condições e ramificações presentes nesse JSON. "
        "Com base nessa análise, gere exaustivamente todos os casos de teste possíveis utilizando o formato BDD (Dado, Quando, Então). "
        "Inclua: todos os caminhos e variações do fluxo; cenários de sucesso e de falha; "
        "e casos de não entendimento quando os dados ou interações apresentarem ambiguidades ou inconsistências. "
        "Garanta que nenhum detalhe seja omitido e que cada cenário refletido no JSON seja contemplado no conjunto de testes. "
        f"Segue o JSON:\n\n{json_data}"
    )
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o-mini",
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Erro ao comunicar com o ChatGPT: {e}")
        return ""

# Função para gerar um PDF com os casos de teste
def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    
    # Gera o PDF como string e converte para bytes usando codificação 'latin1'
    pdf_bytes = pdf.output(dest="S").encode("latin1")
    pdf_buffer = io.BytesIO(pdf_bytes)
    return pdf_buffer

# Interface Streamlit
st.title('CARCARA TEST')

# Entrada do ID do quadro
board_id = st.text_input('Insira o ID do quadro Miro:', '')

# Botão de execução
if st.button('Executar'):
    if board_id:
        st.info('Obtendo elementos do Miro...')
        items = get_miro_elements(board_id, MIRO_ACCESS_TOKEN)
        
        if items:
            elements = process_board_items(items)
            st.info('Enviando dados para o ChatGPT...')
            result = send_to_chatgpt(elements)
            
            if result:
                st.success('Análise concluída!')
                # Exibir resultado em tela
                st.text_area('Resultado:', result, height=300)
                
                # Gerar PDF com os casos de teste
                pdf_file = generate_pdf(result)
                
                # Exibir botão para download do PDF
                st.download_button(
                    label="Baixar PDF com casos de teste",
                    data=pdf_file,
                    file_name="casos_de_teste.pdf",
                    mime="application/pdf"
                )
            else:
                st.error('Não foi possível obter uma resposta do ChatGPT.')
        else:
            st.warning('Nenhum elemento encontrado no quadro.')
    else:
        st.error('Por favor, insira um ID de quadro válido.')
