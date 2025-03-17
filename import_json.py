import requests
import json

# Configurações da API
ACCESS_TOKEN = 'eyJtaXJvLm9yaWdpbiI6ImV1MDEifQ_WZ3D8WGFN9UIwb0xeG578B6hjOA' 
BASE_URL = 'https://api.miro.com/v2'
BOARD_ID = 'uXjVN--WxHE='  

# Função para buscar todos os itens do board (com paginação)
def get_board_items(board_id, token):
    url = f"{BASE_URL}/boards/{board_id}/items"
    headers = {
        "Authorization": f"Bearer {token}"
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
            print(f"Erro ao acessar o board: {response.status_code} - {response.text}")
            return None
    
    return items

# Função para processar diretamente os dados dos itens
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

#Função para salvar os dados estruturados em JSON
def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"Dados salvos em {filename}")

# Main
if __name__ == "__main__":
    # Obtenha todos os itens do board
    items = get_board_items(BOARD_ID, ACCESS_TOKEN)

    if items:
        # Estruture diretamente a partir dos dados retornados
        board_structure = process_board_items(items)
        
        # Salve a estrutura no arquivo JSON
        save_to_json(board_structure, 'miro_board_structure.json')
