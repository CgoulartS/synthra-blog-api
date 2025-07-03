from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app, origins=["https://synthraia.com.br", "http://localhost:3000"] )

# Diretório para armazenar os posts
POSTS_DIR = 'posts'
POSTS_FILE = 'blog_posts.json'

# Criar diretório se não existir
if not os.path.exists(POSTS_DIR):
    os.makedirs(POSTS_DIR)

def load_posts():
    """Carrega posts existentes do arquivo JSON"""
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_posts(posts):
    """Salva posts no arquivo JSON"""
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

def generate_post_id():
    """Gera ID único para o post"""
    return str(uuid.uuid4())[:8]

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Retorna todos os posts do blog"""
    try:
        posts = load_posts()
        return jsonify({
            'success': True,
            'posts': posts,
            'total': len(posts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts', methods=['POST'])
def create_post():
    """Cria um novo post no blog"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['title', 'content', 'excerpt']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {field}'
                }), 400
        
        # Carregar posts existentes
        posts = load_posts()
        
        # Criar novo post
        new_post = {
            'id': generate_post_id(),
            'title': data['title'],
            'excerpt': data['excerpt'],
            'content': data['content'],
            'author': data.get('author', 'Camila Goulart'),
            'date': datetime.now().strftime('%d de %B, %Y'),
            'readTime': data.get('readTime', '5 min'),
            'category': data.get('category', 'IA'),
            'tags': data.get('tags', ['IA', 'Automação', 'Synthra']),
            'telegramSummary': data.get('telegramSummary', data['excerpt'][:200]),
            'created_at': datetime.now().isoformat()
        }
        
        # Adicionar no início da lista (posts mais recentes primeiro)
        posts.insert(0, new_post)
        
        # Salvar posts
        save_posts(posts)
        
        # Salvar post individual para backup
        post_file = os.path.join(POSTS_DIR, f"{new_post['id']}.json")
        with open(post_file, 'w', encoding='utf-8') as f:
            json.dump(new_post, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Post criado com sucesso!',
            'post': new_post
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """Retorna um post específico"""
    try:
        posts = load_posts()
        post = next((p for p in posts if p['id'] == post_id), None)
        
        if not post:
            return jsonify({
                'success': False,
                'error': 'Post não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'post': post
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Deleta um post específico"""
    try:
        posts = load_posts()
        posts = [p for p in posts if p['id'] != post_id]
        save_posts(posts)
        
        # Deletar arquivo individual
        post_file = os.path.join(POSTS_DIR, f"{post_id}.json")
        if os.path.exists(post_file):
            os.remove(post_file)
        
        return jsonify({
            'success': True,
            'message': 'Post deletado com sucesso!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return jsonify({
        'success': True,
        'message': 'API do Blog Synthra funcionando!',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/webhook/make', methods=['POST'])
def webhook_make():
    """Webhook específico para receber posts do Make.com"""
    try:
        data = request.get_json()
        
        # Log da requisição para debug
        print(f"Webhook recebido: {data}")
        
        # Processar dados do OpenAI (formato JSON)
        if 'choices' in data and len(data['choices']) > 0:
            # Formato da resposta do OpenAI
            content = data['choices'][0]['message']['content']
            
            # Tentar fazer parse do JSON retornado pelo OpenAI
            try:
                post_data = json.loads(content)
            except json.JSONDecodeError:
                # Se não for JSON válido, criar estrutura básica
                post_data = {
                    'title': 'Novo Artigo de IA',
                    'excerpt': 'Artigo gerado automaticamente pela IA.',
                    'content': content,
                    'category': 'IA',
                    'readTime': '5 min'
                }
        else:
            # Formato direto
            post_data = data
        
        # Criar post usando a função existente
        posts = load_posts()
        
        new_post = {
            'id': generate_post_id(),
            'title': post_data.get('title', 'Novo Artigo'),
            'excerpt': post_data.get('excerpt', 'Artigo gerado automaticamente.'),
            'content': post_data.get('content', ''),
            'author': 'Camila Goulart',
            'date': datetime.now().strftime('%d de %B, %Y'),
            'readTime': post_data.get('readTime', '5 min'),
            'category': post_data.get('category', 'IA'),
            'tags': post_data.get('tags', ['IA', 'Automação', 'Synthra']),
            'telegramSummary': post_data.get('telegramSummary', post_data.get('excerpt', '')[:200]),
            'created_at': datetime.now().isoformat()
        }
        
        posts.insert(0, new_post)
        save_posts(posts)
        
        # Salvar backup individual
        post_file = os.path.join(POSTS_DIR, f"{new_post['id']}.json")
        with open(post_file, 'w', encoding='utf-8') as f:
            json.dump(new_post, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Post criado via webhook!',
            'post_id': new_post['id'],
            'title': new_post['title']
        }), 201
        
    except Exception as e:
        print(f"Erro no webhook: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

