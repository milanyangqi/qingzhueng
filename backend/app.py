from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
import re
import json

app = Flask(__name__, 
           template_folder='../frontend/templates',
           static_folder='../frontend/static')

# 配置
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qingzhu_english.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 添加模板过滤器
@app.template_filter('from_json')
def from_json(value):
    try:
        return json.loads(value)
    except:
        return []

@app.template_filter('tojson')
def to_json(value):
    return json.dumps(value)

# 数据模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship('UserProfile', backref='user', uselist=False)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    level = db.Column(db.String(20), default='beginner')
    vip_status = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    processed_content = db.Column(db.Text)
    keywords = db.Column(db.Text)  # JSON格式存储关键词
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 路由
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已存在'})
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '邮箱已被注册'})
        
        # 创建新用户
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        
        # 创建用户资料
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '注册成功'})
    
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        return jsonify({'success': True, 'message': '登录成功'})
    
    return jsonify({'success': False, 'message': '用户名或密码错误'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    data = request.get_json()
    user_profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
    
    if user_profile:
        user_profile.full_name = data.get('full_name', user_profile.full_name)
        user_profile.phone = data.get('phone', user_profile.phone)
        user_profile.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': '资料更新成功'})
    
    return jsonify({'success': False, 'message': '更新失败'})

@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/reading')
def reading():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('reading.html')

@app.route('/process_text', methods=['POST'])
def process_text():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'message': '无效的请求数据'})
            
        text = data['text']
        if not text or len(text.strip()) < 10:
            return jsonify({'success': False, 'message': '文本太短，无法处理'})
        
        # 文本处理逻辑
        # 1. 转换为小写
        text_lower = text.lower()
        
        # 2. 分词
        words = re.findall(r'\b[a-zA-Z]+\b', text_lower)
        
        # 3. 过滤停用词和短词
        stop_words = set(['the', 'and', 'a', 'to', 'of', 'in', 'that', 'is', 'it', 'for', 'on', 'with', 'as', 'at', 'by', 'from', 'be', 'was', 'were', 'are', 'have', 'has', 'had', 'this', 'these', 'those', 'they', 'them', 'their', 'we', 'our', 'us', 'you', 'your', 'he', 'his', 'she', 'her', 'i', 'my', 'me', 'an', 'but', 'if', 'or', 'because', 'when', 'where', 'how', 'what', 'which', 'who', 'whom', 'why', 'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must', 'so', 'such', 'than', 'then', 'there', 'here', 'just', 'more', 'most', 'other', 'some', 'such', 'no', 'not', 'only', 'own', 'same', 'too', 'very'])
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # 4. 计算词频
        from collections import Counter
        word_counts = Counter(filtered_words)
        
        # 5. 选择最常见的30个词作为关键词（增加数量）
        top_words = word_counts.most_common(30)
        
        # 构建关键词列表，添加更详细的单词信息
        keywords = []
        
        # 模拟单词库，提供一些常见单词的音标和翻译
        word_dictionary = {
            'test': {'phonetic': '/test/', 'translation': '测试；考验'},
            'hello': {'phonetic': '/həˈloʊ/', 'translation': '你好；问候'},
            'world': {'phonetic': '/wɜːrld/', 'translation': '世界；地球'},
            'computer': {'phonetic': '/kəmˈpjuːtər/', 'translation': '计算机；电脑'},
            'language': {'phonetic': '/ˈlæŋɡwɪdʒ/', 'translation': '语言；表达方式'},
            'english': {'phonetic': '/ˈɪŋɡlɪʃ/', 'translation': '英语；英国人'},
            'learning': {'phonetic': '/ˈlɜːrnɪŋ/', 'translation': '学习；学问'},
            'education': {'phonetic': '/ˌedʒuˈkeɪʃn/', 'translation': '教育；培养'},
            'student': {'phonetic': '/ˈstuːdnt/', 'translation': '学生；研究者'},
            'teacher': {'phonetic': '/ˈtiːtʃər/', 'translation': '教师；导师'},
            'school': {'phonetic': '/skuːl/', 'translation': '学校；校舍'},
            'book': {'phonetic': '/bʊk/', 'translation': '书；书籍'},
            'read': {'phonetic': '/riːd/', 'translation': '阅读；朗读'},
            'write': {'phonetic': '/raɪt/', 'translation': '写；书写'},
            'study': {'phonetic': '/ˈstʌdi/', 'translation': '学习；研究'},
            'knowledge': {'phonetic': '/ˈnɑːlɪdʒ/', 'translation': '知识；学问'},
            'information': {'phonetic': '/ˌɪnfərˈmeɪʃn/', 'translation': '信息；资料'},
            'technology': {'phonetic': '/tekˈnɑːlədʒi/', 'translation': '技术；工艺'},
            'science': {'phonetic': '/ˈsaɪəns/', 'translation': '科学；学科'},
            'research': {'phonetic': '/ˈriːsɜːrtʃ/', 'translation': '研究；调查'}
        }
        
        # 处理关键词
        for word, count in top_words:
            if word in word_dictionary:
                # 如果单词在字典中，使用字典中的信息
                keywords.append({
                    'word': word,
                    'phonetic': word_dictionary[word]['phonetic'],
                    'translation': word_dictionary[word]['translation'],
                    'count': count
                })
            else:
                # 如果单词不在字典中，使用默认格式
                keywords.append({
                    'word': word,
                    'phonetic': f'/{word}/',
                    'translation': f'{word}',
                    'count': count
                })
        
        # 添加一些固定的测试单词，确保功能正常
        if 'test' in text.lower() and not any(k['word'] == 'test' for k in keywords):
            keywords.append({'word': 'test', 'phonetic': '/test/', 'translation': '测试'})
            
        if 'hello' in text.lower() and not any(k['word'] == 'hello' for k in keywords):
            keywords.append({'word': 'hello', 'phonetic': '/həˈloʊ/', 'translation': '你好'})
        
        # 生成标题
        title = ' '.join(text.split()[:8]) + '...' if len(text.split()) > 8 else text
        
        return jsonify({
            'success': True,
            'title': title,
            'words': keywords
        })
        
    except Exception as e:
        print(f"处理文本时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'处理失败: {str(e)}'})

@app.route('/save_article', methods=['POST'])
def save_article():
    try:
        print("收到保存文章请求")
        
        # 检查用户是否登录
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'})
            
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'})
            
        title = data.get('title', '未命名文章')
        content = data.get('content', '')
        processed_content = data.get('processedContent', '')
        keywords_json = json.dumps(data.get('keywords', []))
        
        # 创建新文章
        article = Article(
            title=title,
            content=content,
            processed_content=processed_content,
            keywords=keywords_json,
            user_id=session['user_id']
        )
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '文章保存成功',
            'article_id': article.id
        })
        
    except Exception as e:
        print(f"保存文章时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    try:
        # 检查用户是否登录
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'})
        
        article = Article.query.get(article_id)
        
        if not article:
            return jsonify({'success': False, 'message': '文章不存在'})
            
        # 检查文章是否属于当前用户
        if article.user_id != session['user_id'] and not session.get('is_admin', False):
            return jsonify({'success': False, 'message': '无权访问此文章'})
        
        # 将文章数据转换为字典
        article_data = {
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'processed_content': article.processed_content,
            'keywords': article.keywords,
            'created_at': article.created_at.isoformat()
        }
        
        return jsonify({
            'success': True,
            'article': article_data
        })
        
    except Exception as e:
        print(f"获取文章时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取文章失败: {str(e)}'})

@app.route('/api/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    try:
        # 检查用户是否登录
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'})
        
        article = Article.query.get(article_id)
        
        if not article:
            return jsonify({'success': False, 'message': '文章不存在'})
            
        # 检查文章是否属于当前用户
        if article.user_id != session['user_id'] and not session.get('is_admin', False):
            return jsonify({'success': False, 'message': '无权删除此文章'})
        
        # 删除文章
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '文章已成功删除'
        })
        
    except Exception as e:
        print(f"删除文章时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'删除文章失败: {str(e)}'})

@app.route('/my_articles')
def my_articles():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    articles = Article.query.filter_by(user_id=session['user_id']).order_by(Article.created_at.desc()).all()
    return render_template('my_articles.html', articles=articles)

@app.route('/formatting')
def formatting():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('formatting.html')

@app.route('/reading_comprehension')
def reading_comprehension():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('reading_comprehension.html')

# 添加不同AI模型的API调用函数
import os
import json
import requests

# OpenAI API调用函数
def call_openai_api(title, content, options):
    import openai
    
    # 设置OpenAI API密钥
    openai.api_key = os.environ.get('OPENAI_API_KEY')
    if not openai.api_key:
        raise Exception('OpenAI API密钥未配置')
    
    # 准备生成选项
    generate_vocabulary = options.get('vocabulary', True)
    generate_questions = options.get('questions', True)
    include_translation = options.get('translation', True)
    include_answers = options.get('answers', True)
    
    # 构建提示词
    system_prompt = """你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解材料。"""
    
    user_prompt = f"""基于以下英语文章，请创建一个完整的阅读理解练习：

标题：{title}

内容：{content}

请提供以下内容：
"""
    
    if generate_questions:
        user_prompt += "\n1. 5-8个与文章内容相关的理解问题，由浅入深，包括主旨理解、细节提取、推理判断等不同类型"
    
    if generate_vocabulary:
        user_prompt += "\n2. 文章中10-15个重要词汇，包括单词、词组或习语，并提供英文解释和中文翻译"
    
    if include_answers:
        user_prompt += "\n3. 所有问题的参考答案和解析"
    
    if include_translation:
        user_prompt += "\n4. 文章的中文翻译"
    
    # 调用OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    # 提取生成的内容
    return response.choices[0].message.content

# DeepSeek API调用函数
def call_deepseek_api(title, content, options):
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        raise Exception('DeepSeek API密钥未配置')
    
    # 准备生成选项
    generate_vocabulary = options.get('vocabulary', True)
    generate_questions = options.get('questions', True)
    include_translation = options.get('translation', True)
    include_answers = options.get('answers', True)
    
    # 构建提示词
    system_prompt = "你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解材料。"
    
    user_prompt = f"基于以下英语文章，请创建一个完整的阅读理解练习：\n\n标题：{title}\n\n内容：{content}\n\n请提供以下内容："
    
    if generate_questions:
        user_prompt += "\n1. 5-8个与文章内容相关的理解问题，由浅入深，包括主旨理解、细节提取、推理判断等不同类型"
    
    if generate_vocabulary:
        user_prompt += "\n2. 文章中10-15个重要词汇，包括单词、词组或习语，并提供英文解释和中文翻译"
    
    if include_answers:
        user_prompt += "\n3. 所有问题的参考答案和解析"
    
    if include_translation:
        user_prompt += "\n4. 文章的中文翻译"
    
    # DeepSeek API调用
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()
    
    if 'choices' in response_json and len(response_json['choices']) > 0:
        return response_json['choices'][0]['message']['content']
    else:
        raise Exception(f"DeepSeek API调用失败: {response_json}")

# 豆包API调用函数
def call_doubao_api(title, content, options):
    api_key = os.environ.get('DOUBAO_API_KEY')
    if not api_key:
        raise Exception('豆包API密钥未配置')
    
    # 准备生成选项
    generate_vocabulary = options.get('vocabulary', True)
    generate_questions = options.get('questions', True)
    include_translation = options.get('translation', True)
    include_answers = options.get('answers', True)
    
    # 构建提示词
    system_prompt = "你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解材料。"
    
    user_prompt = f"基于以下英语文章，请创建一个完整的阅读理解练习：\n\n标题：{title}\n\n内容：{content}\n\n请提供以下内容："
    
    if generate_questions:
        user_prompt += "\n1. 5-8个与文章内容相关的理解问题，由浅入深，包括主旨理解、细节提取、推理判断等不同类型"
    
    if generate_vocabulary:
        user_prompt += "\n2. 文章中10-15个重要词汇，包括单词、词组或习语，并提供英文解释和中文翻译"
    
    if include_answers:
        user_prompt += "\n3. 所有问题的参考答案和解析"
    
    if include_translation:
        user_prompt += "\n4. 文章的中文翻译"
    
    # 豆包API调用
    url = "https://api.doubao.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "doubao-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()
    
    if 'choices' in response_json and len(response_json['choices']) > 0:
        return response_json['choices'][0]['message']['content']
    else:
        raise Exception(f"豆包API调用失败: {response_json}")

# 通义千问API调用函数
def call_qianwen_api(title, content, options):
    api_key = os.environ.get('QIANWEN_API_KEY')
    if not api_key:
        raise Exception('通义千问API密钥未配置')
    
    # 准备生成选项
    generate_vocabulary = options.get('vocabulary', True)
    generate_questions = options.get('questions', True)
    include_translation = options.get('translation', True)
    include_answers = options.get('answers', True)
    
    # 构建提示词
    system_prompt = "你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解材料。"
    
    user_prompt = f"基于以下英语文章，请创建一个完整的阅读理解练习：\n\n标题：{title}\n\n内容：{content}\n\n请提供以下内容："
    
    if generate_questions:
        user_prompt += "\n1. 5-8个与文章内容相关的理解问题，由浅入深，包括主旨理解、细节提取、推理判断等不同类型"
    
    if generate_vocabulary:
        user_prompt += "\n2. 文章中10-15个重要词汇，包括单词、词组或习语，并提供英文解释和中文翻译"
    
    if include_answers:
        user_prompt += "\n3. 所有问题的参考答案和解析"
    
    if include_translation:
        user_prompt += "\n4. 文章的中文翻译"
    
    # 通义千问API调用
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        },
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 2000
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()
    
    if 'output' in response_json and 'text' in response_json['output']:
        return response_json['output']['text']
    else:
        raise Exception(f"通义千问API调用失败: {response_json}")

# 硅基流动API调用函数
def call_siliconflow_api(title, content, options):
    api_key = os.environ.get('SILICONFLOW_API_KEY')
    if not api_key:
        raise Exception('硅基流动API密钥未配置')
    
    # 准备生成选项
    generate_vocabulary = options.get('vocabulary', True)
    generate_questions = options.get('questions', True)
    include_translation = options.get('translation', True)
    include_answers = options.get('answers', True)
    
    # 构建提示词
    system_prompt = "你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解材料。"
    
    user_prompt = f"基于以下英语文章，请创建一个完整的阅读理解练习：\n\n标题：{title}\n\n内容：{content}\n\n请提供以下内容："
    
    if generate_questions:
        user_prompt += "\n1. 5-8个与文章内容相关的理解问题，由浅入深，包括主旨理解、细节提取、推理判断等不同类型"
    
    if generate_vocabulary:
        user_prompt += "\n2. 文章中10-15个重要词汇，包括单词、词组或习语，并提供英文解释和中文翻译"
    
    if include_answers:
        user_prompt += "\n3. 所有问题的参考答案和解析"
    
    if include_translation:
        user_prompt += "\n4. 文章的中文翻译"
    
    # 硅基流动API调用
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()
    
    if 'choices' in response_json and len(response_json['choices']) > 0:
        return response_json['choices'][0]['message']['content']
    else:
        raise Exception(f"硅基流动API调用失败: {response_json}")

# 解析AI生成的内容
def parse_generated_content(generated_content, options):
    generate_vocabulary = options.get('vocabulary', True)
    generate_questions = options.get('questions', True)
    include_answers = options.get('answers', True)
    
    sections = generated_content.split('\n\n')
    
    questions = []
    vocabulary = []
    answers = []
    translation = ""
    
    # 简单解析生成的内容
    for section in sections:
        if '问题' in section or 'Question' in section:
            # 提取问题
            question_lines = [line for line in section.split('\n') if line.strip() and ('?' in line or line[0].isdigit())]
            questions.extend(question_lines)
        elif '词汇' in section or 'Vocabulary' in section:
            # 提取词汇
            vocab_lines = section.split('\n')[1:] if section.split('\n') else []
            for line in vocab_lines:
                if ':' in line and line.strip():
                    parts = line.split(':', 1)
                    word = parts[0].strip()
                    if len(parts) > 1 and parts[1].strip():
                        definition_parts = parts[1].split('/')
                        definition = definition_parts[0].strip() if definition_parts else ""
                        translation = definition_parts[1].strip() if len(definition_parts) > 1 else ""
                        vocabulary.append({
                            'word': word,
                            'definition': definition,
                            'translation': translation
                        })
        elif '答案' in section or 'Answer' in section:
            # 提取答案
            answer_lines = [line for line in section.split('\n') if line.strip()]
            answers.extend(answer_lines)
        elif '翻译' in section or 'Translation' in section:
            # 提取翻译
            translation_lines = section.split('\n')[1:] if section.split('\n') else []
            translation = '\n'.join(translation_lines)
    
    # 如果解析失败，使用原始生成内容
    if not questions and generate_questions:
        questions = ["解析问题失败，请查看原始生成内容"]
    
    if not vocabulary and generate_vocabulary:
        vocabulary = [{'word': '解析词汇失败', 'translation': '请查看原始生成内容', 'definition': ''}]
    
    return {
        'questions': questions,
        'vocabulary': vocabulary,
        'answers': answers,
        'translation': translation
    }

@app.route('/generate_comprehension', methods=['POST'])
def generate_comprehension():
    try:
        # 检查用户是否登录
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'})
            
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'})
            
        title = data.get('title', '')
        content = data.get('content', '')
        options = data.get('options', {})
        
        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容不能为空'})
        
        # 获取选择的AI模型
        model = options.get('model', 'openai')
        
        try:
            # 根据选择的模型调用相应的API
            if model == 'openai':
                generated_content = call_openai_api(title, content, options)
            elif model == 'deepseek':
                generated_content = call_deepseek_api(title, content, options)
            elif model == 'doubao':
                generated_content = call_doubao_api(title, content, options)
            elif model == 'qianwen':
                generated_content = call_qianwen_api(title, content, options)
            elif model == 'siliconflow':
                generated_content = call_siliconflow_api(title, content, options)
            else:
                return jsonify({'success': False, 'message': f'不支持的AI模型: {model}'})
            
            # 解析生成的内容
            parsed_content = parse_generated_content(generated_content, options)
            
            return jsonify({
                'success': True,
                'message': '阅读理解生成成功',
                'data': {
                    'title': title,
                    'content': content,
                    'questions': parsed_content['questions'],
                    'vocabulary': parsed_content['vocabulary'],
                    'answers': parsed_content['answers'],
                    'translation': parsed_content['translation'],
                    'raw_generated_content': generated_content,
                    'model': model  # 返回使用的模型信息
                }
            })
            
        except Exception as e:
            print(f"AI API调用失败: {str(e)}")
            return jsonify({'success': False, 'message': f'AI API调用失败: {str(e)}'})
            
        # 如果API调用失败，返回模拟数据作为备份
        return jsonify({
            'success': True,
            'message': '阅读理解生成成功（模拟数据）',
            'data': {
                'title': title,
                'content': content,
                'questions': [
                    '1. What is the main idea of this article?',
                    '2. According to the passage, what are the key points mentioned?',
                    '3. What conclusion can be drawn from the article?',
                    '4. How does the author support their argument?'
                ],
                'vocabulary': [
                    {'word': 'comprehension', 'translation': '理解，领悟', 'definition': 'the ability to understand'},
                    {'word': 'generate', 'translation': '生成，产生', 'definition': 'to produce or create'},
                    {'word': 'article', 'translation': '文章，论文', 'definition': 'a piece of writing'},
                    {'word': 'preview', 'translation': '预览，预视', 'definition': 'an opportunity to view something before it is acquired or becomes generally available'}
                ],
                'model': model
            }
        })
        
    except Exception as e:
        print(f"生成阅读理解时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'})

def create_admin_user():
    """创建默认管理员用户"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@qingzhu.com',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.flush()  # 获取admin.id
        
        # 创建管理员资料
        admin_profile = UserProfile(
            user_id=admin.id,
            full_name='系统管理员'
        )
        db.session.add(admin_profile)
        db.session.commit()
        
        print('默认管理员账户已创建: admin/admin123')

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            create_admin_user()
            db.session.commit()
            print("数据库初始化完成")
        except Exception as e:
            print(f"数据库初始化错误: {e}")
    app.run(host='0.0.0.0', port=5001, debug=True)