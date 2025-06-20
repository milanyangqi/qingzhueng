from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
import json
import re
import requests
import uuid
import time

app = Flask(__name__, 
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

# 用户资料模型
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProfile {self.full_name}>'

# 文章模型
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Article {self.title}>'

# 路由：首页
@app.route('/')
def index():
    return render_template('index.html')

# 路由：用户中心
@app.route('/dashboard')
def dashboard():
    # 检查用户是否登录
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取用户信息
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('index'))
    
    return render_template('dashboard.html', username=user.username)

# 路由：时文阅读页面
@app.route('/reading')
def reading():
    # 检查用户是否登录
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('reading.html')

# 路由：我的文章页面
@app.route('/my_articles')
def my_articles():
    # 检查用户是否登录
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # 获取当前用户的文章
    try:
        # 查询当前用户的所有文章，按创建时间降序排列
        articles = Article.query.filter_by(user_id=session['user_id']).order_by(Article.created_at.desc()).all()
        return render_template('my_articles.html', articles=articles)
    except Exception as e:
        print(f"获取用户文章失败: {str(e)}")
        return render_template('my_articles.html', articles=[])

# 路由：阅读排版页面
@app.route('/formatting')
def formatting():
    # 检查用户是否登录
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('formatting.html')

# 路由：管理员后台
@app.route('/admin')
def admin():
    # 检查用户是否登录且是管理员
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if not session.get('is_admin', False):
        return redirect(url_for('dashboard'))
    
    return render_template('admin.html')

# 路由：注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已存在'})
        
        # 检查邮箱是否已存在
        existing_email = User.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({'success': False, 'message': '邮箱已被注册'})
        
        # 创建新用户
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.flush()  # 获取new_user.id
            
            # 创建用户资料
            new_profile = UserProfile(user_id=new_user.id, full_name=data.get('full_name', ''))
            db.session.add(new_profile)
            db.session.commit()
            
            return jsonify({'success': True, 'message': '注册成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'注册失败: {str(e)}'})
    
    return render_template('register.html')

# 路由：登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, data['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            
            return jsonify({'success': True, 'message': '登录成功', 'is_admin': user.is_admin})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'})
    
    return render_template('login.html')

# 路由：退出登录
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 路由：用户资料页面
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 获取用户信息
    try:
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('index'))
        
        # 获取用户资料
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        
        # 如果用户资料不存在，创建一个空的资料
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()
        
        # 将用户资料添加到用户对象中
        user.profile = profile
        
        return render_template('profile.html', user=user)
    except Exception as e:
        print(f"获取用户资料失败: {str(e)}")
        return redirect(url_for('dashboard'))

# 路由：获取用户资料
@app.route('/api/profile', methods=['GET'])
def get_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    if not user or not profile:
        return jsonify({'success': False, 'message': '用户资料不存在'})
    
    return jsonify({
        'success': True,
        'data': {
            'username': user.username,
            'email': user.email,
            'full_name': profile.full_name,
            'bio': profile.bio,
            'avatar': profile.avatar
        }
    })

# 路由：更新用户资料
@app.route('/api/profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    data = request.get_json()
    user_id = session['user_id']
    
    try:
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            return jsonify({'success': False, 'message': '用户资料不存在'})
        
        profile.full_name = data.get('full_name', profile.full_name)
        profile.bio = data.get('bio', profile.bio)
        profile.avatar = data.get('avatar', profile.avatar)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '资料更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

# 路由：文章列表页面
@app.route('/articles')
def articles():
    return render_template('articles.html')

# 路由：获取文章列表
@app.route('/api/articles', methods=['GET'])
def get_articles():
    try:
        articles = Article.query.order_by(Article.created_at.desc()).all()
        
        articles_list = []
        for article in articles:
            user = User.query.get(article.user_id)
            username = user.username if user else 'Unknown'
            
            articles_list.append({
                'id': article.id,
                'title': article.title,
                'content': article.content[:200] + '...' if len(article.content) > 200 else article.content,
                'author': username,
                'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({'success': True, 'articles': articles_list})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取文章失败: {str(e)}'})

# 路由：文章详情页面
@app.route('/article/<int:article_id>')
def article_detail(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('article_detail.html', article=article)

# 路由：编辑文章页面
@app.route('/edit_article/<int:article_id>')
def edit_article_page(article_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    article = Article.query.get_or_404(article_id)
    # 仅作者或管理员可编辑
    if article.user_id != session['user_id'] and not session.get('is_admin', False):
        return redirect(url_for('my_articles'))
    return render_template('edit_article.html', article=article)

# 路由：创建文章页面
@app.route('/create_article')
def create_article_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('create_article.html')

# 路由：创建文章API
@app.route('/api/articles', methods=['POST'])
def create_article():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    data = request.get_json()
    
    try:
        new_article = Article(
            title=data['title'],
            content=data['content'],
            user_id=session['user_id']
        )
        
        db.session.add(new_article)
        db.session.commit()
        
        return jsonify({'success': True, 'article_id': new_article.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'})

# 路由：删除文章
@app.route('/api/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    article = Article.query.get(article_id)
    
    if not article:
        return jsonify({'success': False, 'message': '文章不存在'})
    
    if article.user_id != session['user_id'] and not session.get('is_admin', False):
        return jsonify({'success': False, 'message': '没有权限删除此文章'})
    
    try:
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '文章删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

# 路由：阅读理解生成页面
@app.route('/reading_comprehension')
def reading_comprehension():
    return render_template('reading_comprehension.html')

# 路由：基于词汇的文章生成页面
@app.route('/lexile_article')
def lexile_article():
    return render_template('lexile_article.html')

# 调用OpenAI API生成阅读理解
def call_openai_api(title, content, options):
    import openai
    
    # 设置OpenAI API密钥
    openai.api_key = os.environ.get('OPENAI_API_KEY')
    if not openai.api_key:
        raise Exception('OpenAI API密钥未配置')
    
    # 构建提示词
    system_prompt = """你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解练习。
    请根据提供的文章，生成符合要求的阅读理解材料。
    输出格式必须是JSON格式，包含以下字段：
    - vocabulary: 词汇表，包含单词、翻译和定义
    - questions: 阅读理解问题
    - answers: 问题答案和解析
    - translation: 文章的中文翻译
    """
    
    # 根据选项构建用户提示词
    user_prompt = f"""请根据以下英文文章，生成阅读理解练习材料：

标题：{title}

内容：
{content}

请生成以下内容（JSON格式）：
"""
    
    if options.get('vocabulary', True):
        user_prompt += """
1. vocabulary: 词汇表，包含10-15个文章中的重要单词，每个单词包括：
   - word: 单词
   - translation: 中文翻译
   - definition: 英文释义
"""
    
    if options.get('questions', True):
        question_count = options.get('questionCount', 5)
        with_options = options.get('withOptions', False)
        
        user_prompt += f"""
2. questions: {question_count}个阅读理解问题，考察对文章的理解
"""
        
        if with_options:
            user_prompt += """
   每个问题必须包含以下字段：
   - question: 问题内容
   - options: 4个选项，其中一个是正确答案
"""
    
    if options.get('answers', True):
        user_prompt += """
3. answers: 问题的答案和简要解析
"""
    
    if options.get('translation', True):
        user_prompt += """
4. translation: 文章的中文翻译
"""
    
    user_prompt += """

请确保输出是有效的JSON格式，可以直接被解析。
"""
    
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
    generated_content = response.choices[0].message.content
    
    return generated_content

# 调用DeepSeek API生成阅读理解
def call_deepseek_api(title, content, options):
    # 设置DeepSeek API密钥
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        raise Exception('DeepSeek API密钥未配置')
    
    # 构建提示词
    system_prompt = """你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解练习。
    请根据提供的文章，生成符合要求的阅读理解材料。
    输出格式必须是JSON格式，包含以下字段：
    - vocabulary: 词汇表，包含单词、翻译和定义
    - questions: 阅读理解问题
    - answers: 问题答案和解析
    - translation: 文章的中文翻译
    """
    
    # 根据选项构建用户提示词
    user_prompt = f"""请根据以下英文文章，生成阅读理解练习材料：

标题：{title}

内容：
{content}

请生成以下内容（JSON格式）：
"""
    
    if options.get('vocabulary', True):
        user_prompt += """
1. vocabulary: 词汇表，包含10-15个文章中的重要单词，每个单词包括：
   - word: 单词
   - translation: 中文翻译
   - definition: 英文释义
"""
    
    if options.get('questions', True):
        question_count = options.get('questionCount', 5)
        with_options = options.get('withOptions', False)
        
        user_prompt += f"""
2. questions: {question_count}个阅读理解问题，考察对文章的理解
"""
        
        if with_options:
            user_prompt += """
   每个问题必须包含以下字段：
   - question: 问题内容
   - options: 4个选项，其中一个是正确答案
"""
    
    if options.get('answers', True):
        user_prompt += """
3. answers: 问题的答案和简要解析
"""
    
    if options.get('translation', True):
        user_prompt += """
4. translation: 文章的中文翻译
"""
    
    user_prompt += """

请确保输出是有效的JSON格式，可以直接被解析。
"""
    
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
        generated_content = response_json['choices'][0]['message']['content']
    else:
        raise Exception(f"DeepSeek API调用失败: {response_json}")
    
    return generated_content

# 调用豆包API生成阅读理解
def call_doubao_api(title, content, options):
    # 设置豆包API密钥
    api_key = os.environ.get('DOUBAO_API_KEY')
    if not api_key:
        raise Exception('豆包API密钥未配置')
    
    # 构建提示词
    system_prompt = """你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解练习。
    请根据提供的文章，生成符合要求的阅读理解材料。
    输出格式必须是JSON格式，包含以下字段：
    - vocabulary: 词汇表，包含单词、翻译和定义
    - questions: 阅读理解问题
    - answers: 问题答案和解析
    - translation: 文章的中文翻译
    """
    
    # 根据选项构建用户提示词
    user_prompt = f"""请根据以下英文文章，生成阅读理解练习材料：

标题：{title}

内容：
{content}

请生成以下内容（JSON格式）：
"""
    
    if options.get('vocabulary', True):
        user_prompt += """
1. vocabulary: 词汇表，包含10-15个文章中的重要单词，每个单词包括：
   - word: 单词
   - translation: 中文翻译
   - definition: 英文释义
"""
    
    if options.get('questions', True):
        question_count = options.get('questionCount', 5)
        with_options = options.get('withOptions', False)
        
        user_prompt += f"""
2. questions: {question_count}个阅读理解问题，考察对文章的理解
"""
        
        if with_options:
            user_prompt += """
   每个问题必须包含以下字段：
   - question: 问题内容
   - options: 4个选项，其中一个是正确答案
"""
    
    if options.get('answers', True):
        user_prompt += """
3. answers: 问题的答案和简要解析
"""
    
    if options.get('translation', True):
        user_prompt += """
4. translation: 文章的中文翻译
"""
    
    user_prompt += """

请确保输出是有效的JSON格式，可以直接被解析。
"""
    
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
        generated_content = response_json['choices'][0]['message']['content']
    else:
        raise Exception(f"豆包API调用失败: {response_json}")
    
    return generated_content

# 调用通义千问API生成阅读理解
def call_qianwen_api(title, content, options):
    # 设置通义千问API密钥
    api_key = os.environ.get('QIANWEN_API_KEY')
    if not api_key:
        raise Exception('通义千问API密钥未配置')
    
    # 构建提示词
    system_prompt = """你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解练习。
    请根据提供的文章，生成符合要求的阅读理解材料。
    输出格式必须是JSON格式，包含以下字段：
    - vocabulary: 词汇表，包含单词、翻译和定义
    - questions: 阅读理解问题
    - answers: 问题答案和解析
    - translation: 文章的中文翻译
    """
    
    # 根据选项构建用户提示词
    user_prompt = f"""请根据以下英文文章，生成阅读理解练习材料：

标题：{title}

内容：
{content}

请生成以下内容（JSON格式）：
"""
    
    if options.get('vocabulary', True):
        user_prompt += """
1. vocabulary: 词汇表，包含10-15个文章中的重要单词，每个单词包括：
   - word: 单词
   - translation: 中文翻译
   - definition: 英文释义
"""
    
    if options.get('questions', True):
        question_count = options.get('questionCount', 5)
        with_options = options.get('withOptions', False)
        
        user_prompt += f"""
2. questions: {question_count}个阅读理解问题，考察对文章的理解
"""
        
        if with_options:
            user_prompt += """
   每个问题必须包含以下字段：
   - question: 问题内容
   - options: 4个选项，其中一个是正确答案
"""
    
    if options.get('answers', True):
        user_prompt += """
3. answers: 问题的答案和简要解析
"""
    
    if options.get('translation', True):
        user_prompt += """
4. translation: 文章的中文翻译
"""
    
    user_prompt += """

请确保输出是有效的JSON格式，可以直接被解析。
"""
    
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
        generated_content = response_json['output']['text']
    else:
        raise Exception(f"通义千问API调用失败: {response_json}")
    
    return generated_content

# 调用硅基流动API生成阅读理解
def call_siliconflow_api(title, content, options):
    # 设置硅基流动API密钥
    # 直接使用硬编码的API密钥，而不是从环境变量获取
    api_key = 'sk-habqljthapqvkwltxhrhtskvxihotdibjtxmjaxroqtnlorp'
    if not api_key:
        raise Exception('硅基流动API密钥未配置')
    
    # 构建提示词
    system_prompt = """你是一个专业的英语教育助手，擅长创建高质量的英语阅读理解练习。
    请根据提供的文章，生成符合要求的阅读理解材料。
    输出格式必须是JSON格式，包含以下字段：
    - vocabulary: 词汇表，包含单词、翻译和定义
    - questions: 阅读理解问题
    - answers: 问题答案和解析
    - translation: 文章的中文翻译
    """
    
    # 根据选项构建用户提示词
    user_prompt = f"""请根据以下英文文章，生成阅读理解练习材料：

标题：{title}

内容：
{content}

请生成以下内容（JSON格式）：
"""
    
    if options.get('vocabulary', True):
        user_prompt += """
1. vocabulary: 词汇表，包含10-15个文章中的重要单词，每个单词包括：
   - word: 单词
   - translation: 中文翻译
   - definition: 英文释义
"""
    
    if options.get('questions', True):
        question_count = options.get('questionCount', 5)
        with_options = options.get('withOptions', False)
        
        user_prompt += f"""
2. questions: {question_count}个阅读理解问题，考察对文章的理解
"""
        
        if with_options:
            user_prompt += """
   每个问题必须包含以下字段：
   - question: 问题内容
   - options: 4个选项，其中一个是正确答案
"""
    
    if options.get('answers', True):
        user_prompt += """
3. answers: 问题的答案和简要解析
"""
    
    if options.get('translation', True):
        user_prompt += """
4. translation: 文章的中文翻译
"""
    
    user_prompt += """

请确保输出是有效的JSON格式，可以直接被解析。
"""
    
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
        generated_content = response_json['choices'][0]['message']['content']
    else:
        raise Exception(f"硅基流动API调用失败: {response_json}")
    
    return generated_content

# 解析生成的内容
def parse_generated_content(content):
    # 尝试提取JSON部分
    try:
        # 查找可能的JSON开始和结束位置
        json_start = content.find('{')
        json_end = content.rfind('}')
        
        if json_start >= 0 and json_end > json_start:
            json_content = content[json_start:json_end+1]
            data = json.loads(json_content)
            
            # 确保所有必要的字段都存在
            result = {
                'vocabulary': data.get('vocabulary', []),
                'questions': data.get('questions', []),
                'answers': data.get('answers', []),
                'translation': data.get('translation', ''),
                'raw_generated_content': content  # 保存原始生成内容
            }
            
            return result
    except Exception as e:
        print(f"解析JSON失败: {str(e)}")
    
    # 如果无法解析为JSON，尝试使用正则表达式提取信息
    try:
        # 提取词汇表
        vocabulary = []
        vocab_pattern = r'\b([A-Za-z]+)\b\s*(?:\[([^\]]+)\])?[^\n]*?[：:]\s*([^\n]*?)\s*[\-—]\s*([^\n]*)' 
        vocab_matches = re.findall(vocab_pattern, content)
        
        for match in vocab_matches:
            if len(match) >= 3:
                vocabulary.append({
                    'word': match[0].strip(),
                    'phonetic': match[1].strip() if len(match) > 1 and match[1].strip() else '',
                    'translation': match[2].strip() if len(match) > 2 else '',
                    'definition': match[3].strip() if len(match) > 3 else ''
                })
                
        # 如果上面的正则没有匹配到音标，尝试另一种格式的音标提取
        if not any(item.get('phonetic') for item in vocabulary):
            phonetic_pattern = r'\b([A-Za-z]+)\b\s*(/[^/]+/|\[[^\]]+\])[^\n]*?[：:]\s*([^\n]*?)\s*[\-—]\s*([^\n]*)'
            phonetic_matches = re.findall(phonetic_pattern, content)
            
            if phonetic_matches:
                vocabulary = []
                for match in phonetic_matches:
                    if len(match) >= 3:
                        vocabulary.append({
                            'word': match[0].strip(),
                            'phonetic': match[1].strip(),
                            'translation': match[2].strip() if len(match) > 2 else '',
                            'definition': match[3].strip() if len(match) > 3 else ''
                        })
        
        # 提取问题
        questions = []
        question_pattern = r'\d+\.\s*([^\n]+\?)'  # 匹配问题
        question_matches = re.findall(question_pattern, content)
        
        for match in question_matches:
            questions.append(match.strip())
        
        # 提取答案（简单实现）
        answers = []
        answer_section = re.search(r'Answers[:\n]+(.*?)(?=\n\s*\n|$)', content, re.DOTALL)
        if answer_section:
            answer_text = answer_section.group(1)
            answer_items = re.split(r'\d+\.\s*', answer_text)
            for item in answer_items:
                if item.strip():
                    answers.append(item.strip())
        
        # 提取翻译
        translation = ''
        translation_section = re.search(r'Translation[:\n]+(.*?)(?=\n\s*\n|$)', content, re.DOTALL)
        if translation_section:
            translation = translation_section.group(1).strip()
        
        # 如果提取失败，添加错误信息
        if not vocabulary:
            vocabulary = [{'word': '解析失败', 'phonetic': '', 'translation': '请查看原始生成内容', 'definition': ''}]
        if not questions:
            questions = ['解析失败，请查看原始生成内容']
        
        return {
            'vocabulary': vocabulary,
            'questions': questions,
            'answers': answers,
            'translation': translation,
            'raw_generated_content': content  # 保存原始生成内容
        }
    except Exception as e:
        print(f"正则解析失败: {str(e)}")
        
        # 返回错误信息
        return {
            'vocabulary': [{'word': '解析失败', 'phonetic': '', 'translation': '请查看原始生成内容', 'definition': ''}],
            'questions': ['解析失败，请查看原始生成内容'],
            'answers': [],
            'translation': '',
            'raw_generated_content': content  # 保存原始生成内容
        }

# 路由：生成阅读理解
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
        
        # 根据选择的模型调用相应的API
        model = options.get('model', 'openai')
        try:
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
            parsed_data = parse_generated_content(generated_content)
            
            # 添加标题和内容
            parsed_data['title'] = title
            parsed_data['content'] = content
            parsed_data['model'] = model
            
            return jsonify({
                'success': True,
                'message': '阅读理解生成成功',
                'data': parsed_data,
                'model': model
            })
        except Exception as e:
            print(f"AI API调用失败: {str(e)}")
            return jsonify({'success': False, 'message': f'AI API调用失败: {str(e)}'})
            
    except Exception as e:
        print(f"生成阅读理解时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'})

# 生成文章内容的API接口
@app.route('/generate_article_content', methods=['POST'])
def generate_article_content():
    try:
        # 检查用户是否登录
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录'})
            
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'})
            
        title = data.get('title', '')
        model = data.get('model', 'openai')
        
        if not title:
            return jsonify({'success': False, 'message': '文章标题不能为空'})
        
        try:
            # 构建提示词
            system_prompt = "你是一个专业的英语教育助手，擅长创建高质量的英语文章。"
            
            user_prompt = f"请根据以下标题，创建一篇适合英语学习者阅读的文章，文章应该包含丰富的词汇和表达，难度适中，长度在300-500词左右：\n\n标题：{title}\n\n请直接给出文章内容，不要包含其他解释。"
            
            # 根据选择的模型调用相应的API
            if model == 'openai':
                import openai
                
                # 设置OpenAI API密钥
                openai.api_key = os.environ.get('OPENAI_API_KEY')
                if not openai.api_key:
                    raise Exception('OpenAI API密钥未配置')
                
                # 调用OpenAI API
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # 提取生成的内容
                content = response.choices[0].message.content
                
            elif model == 'deepseek':
                api_key = os.environ.get('DEEPSEEK_API_KEY')
                if not api_key:
                    raise Exception('DeepSeek API密钥未配置')
                
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
                    "max_tokens": 1000
                }
                
                response = requests.post(url, headers=headers, json=data)
                response_json = response.json()
                
                if 'choices' in response_json and len(response_json['choices']) > 0:
                    content = response_json['choices'][0]['message']['content']
                else:
                    raise Exception(f"DeepSeek API调用失败: {response_json}")
                
            elif model == 'doubao':
                api_key = os.environ.get('DOUBAO_API_KEY')
                if not api_key:
                    raise Exception('豆包API密钥未配置')
                
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
                    "max_tokens": 1000
                }
                
                response = requests.post(url, headers=headers, json=data)
                response_json = response.json()
                
                if 'choices' in response_json and len(response_json['choices']) > 0:
                    content = response_json['choices'][0]['message']['content']
                else:
                    raise Exception(f"豆包API调用失败: {response_json}")
                
            elif model == 'qianwen':
                api_key = os.environ.get('QIANWEN_API_KEY')
                if not api_key:
                    raise Exception('通义千问API密钥未配置')
                
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
                        "max_tokens": 1000
                    }
                }
                
                response = requests.post(url, headers=headers, json=data)
                response_json = response.json()
                
                if 'output' in response_json and 'text' in response_json['output']:
                    content = response_json['output']['text']
                else:
                    raise Exception(f"通义千问API调用失败: {response_json}")
                
            elif model == 'siliconflow':
                api_key = os.environ.get('SILICONFLOW_API_KEY')
                if not api_key:
                    raise Exception('硅基流动API密钥未配置')
                
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
                    "max_tokens": 1000
                }
                
                response = requests.post(url, headers=headers, json=data)
                response_json = response.json()
                
                if 'choices' in response_json and len(response_json['choices']) > 0:
                    content = response_json['choices'][0]['message']['content']
                else:
                    raise Exception(f"硅基流动API调用失败: {response_json}")
            else:
                return jsonify({'success': False, 'message': f'不支持的AI模型: {model}'})
            
            return jsonify({
                'success': True,
                'message': '文章内容生成成功',
                'content': content,
                'model': model  # 返回使用的模型信息
            })
            
        except Exception as e:
            print(f"AI API调用失败: {str(e)}")
            return jsonify({'success': False, 'message': f'AI API调用失败: {str(e)}'})
        
    except Exception as e:
        print(f"生成文章内容时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'})

# 生成基于词汇和蓝思指数的文章API接口
@app.route('/generate_lexile_article', methods=['POST'])
def generate_lexile_article():
    # 检查用户是否登录
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
        
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'})
        
    topic = data.get('topic', '')
    vocabulary = data.get('vocabulary', '')
    lexile = data.get('lexile', 800)
    word_count = data.get('word_count', 300)
    model = data.get('model', 'openai')
    
    if not topic:
        return jsonify({'success': False, 'message': '文章主题不能为空'})
        
    # 词汇为选填项，不再验证是否为空
    
    try:
        # 处理词汇列表（如果有）
        vocab_list = []
        if vocabulary:
            vocab_list = vocabulary.split('\n') if '\n' in vocabulary else vocabulary.split(',')
            vocab_list = [word.strip() for word in vocab_list if word.strip()]
        
        # 构建提示词
        system_prompt = """你是一个专业的英语教育助手，擅长创建基于特定词汇和蓝思指数的英语文章。
        蓝思指数(Lexile)是衡量文本难度的指标，范围从0到2000，数值越高表示文本越难。
        请根据提供的蓝思指数、主题和词汇列表，创建适合英语学习者的原创文章。
        输出格式必须是JSON格式，包含以下字段：
        - content: 文章内容
        - vocabulary: 词汇表，包含单词、翻译和定义
        - questions: 阅读理解问题
        """
        
        # 构建用户提示词，根据是否有词汇列表调整内容
        if vocab_list:
            user_prompt = f"""请创建一篇英语文章，满足以下要求：

1. 主题：{topic}
2. 蓝思指数(Lexile)：{lexile}
3. 单词数量：大约{word_count}个单词
4. 必须包含以下词汇（尽可能自然地融入文章中）：
   {', '.join(vocab_list)}

请生成以下内容（JSON格式）：
1. content: 文章内容
2. vocabulary: 词汇表，包含文章中使用的所有指定词汇，每个词汇包括：
   - word: 单词
   - translation: 中文翻译
   - definition: 英文释义
3. questions: 5个阅读理解问题，考察对文章的理解

请确保输出是有效的JSON格式，可以直接被解析。
"""
        else:
            user_prompt = f"""请创建一篇英语文章，满足以下要求：

1. 主题：{topic}
2. 蓝思指数(Lexile)：{lexile}
3. 单词数量：大约{word_count}个单词

请生成以下内容（JSON格式）：
1. content: 文章内容
2. vocabulary: 词汇表，包含文章中的重要词汇，每个词汇包括：
   - word: 单词
   - translation: 中文翻译
   - definition: 英文释义
3. questions: 5个阅读理解问题，考察对文章的理解

请确保输出是有效的JSON格式，可以直接被解析。
"""
            
        # 根据选择的模型调用相应的API
        if model == 'openai':
            import openai
            
            # 设置OpenAI API密钥
            openai.api_key = os.environ.get('OPENAI_API_KEY')
            if not openai.api_key:
                raise Exception('OpenAI API密钥未配置')
            
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
            generated_content = response.choices[0].message.content
            
        elif model == 'deepseek':
            api_key = os.environ.get('DEEPSEEK_API_KEY')
            if not api_key:
                raise Exception('DeepSeek API密钥未配置')
            
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
                generated_content = response_json['choices'][0]['message']['content']
            else:
                raise Exception(f"DeepSeek API调用失败: {response_json}")
            
        elif model == 'doubao':
            api_key = os.environ.get('DOUBAO_API_KEY')
            if not api_key:
                raise Exception('豆包API密钥未配置')
            
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
                generated_content = response_json['choices'][0]['message']['content']
            else:
                raise Exception(f"豆包API调用失败: {response_json}")
            
        elif model == 'qianwen':
            api_key = os.environ.get('QIANWEN_API_KEY')
            if not api_key:
                raise Exception('通义千问API密钥未配置')
            
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
                generated_content = response_json['output']['text']
            else:
                raise Exception(f"通义千问API调用失败: {response_json}")
            
        elif model == 'siliconflow':
            api_key = os.environ.get('SILICONFLOW_API_KEY')
            if not api_key:
                raise Exception('硅基流动API密钥未配置')
            
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
                generated_content = response_json['choices'][0]['message']['content']
            else:
                raise Exception(f"硅基流动API调用失败: {response_json}")
        else:
            return jsonify({'success': False, 'message': f'不支持的AI模型: {model}'})
        
        # 解析生成的内容
        try:
            # 查找可能的JSON开始和结束位置
            json_start = generated_content.find('{')
            json_end = generated_content.rfind('}')
            
            if json_start >= 0 and json_end > json_start:
                json_content = generated_content[json_start:json_end+1]
                data = json.loads(json_content)
                
                # 确保所有必要的字段都存在
                result = {
                    'content': data.get('content', ''),
                    'vocabulary': data.get('vocabulary', []),
                    'questions': data.get('questions', []),
                    'topic': topic,
                    'lexile': lexile,
                    'word_count': word_count,
                    'model': model,
                    'raw_generated_content': generated_content  # 保存原始生成内容
                }
                
                return jsonify({
                    'success': True,
                    'message': '文章生成成功',
                    **result
                })
        except Exception as e:
            print(f"解析JSON失败: {str(e)}")
        
        # 如果解析失败，返回原始内容
        return jsonify({
            'success': True,
            'message': '文章生成成功，但解析失败',
            'content': generated_content,
            'vocabulary': [],
            'questions': [],
            'topic': topic,
            'lexile': lexile,
            'word_count': word_count,
            'model': model,
            'raw_generated_content': generated_content
        })
        
    except Exception as e:
        print(f"AI API调用失败: {str(e)}")
        # 如果API调用失败，返回模拟数据作为备份
        sample_content = """# The Solar System

The solar system is a fascinating place. It consists of the Sun and everything that orbits around it. This includes planets, moons, asteroids, comets, and meteoroids.

Mercury is the closest planet to the Sun. It has a rocky surface covered with craters. Venus, the second planet, is similar in size to Earth but has a toxic atmosphere that traps heat, making it the hottest planet.

Earth, our home planet, is the only known place with life. It has one natural satellite, the Moon. Mars, often called the Red Planet, has polar ice caps and evidence of ancient rivers and lakes.

Jupiter is the largest planet in our solar system. It has a Great Red Spot, which is a giant storm. Saturn is famous for its beautiful rings."""
        return jsonify({'success': False, 'message': f'AI API调用失败: {str(e)}'})


# 路由：编辑文章API
@app.route('/api/articles/<int:article_id>', methods=['PUT'])
def edit_article(article_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    data = request.get_json()
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'success': False, 'message': '文章不存在'})
    if article.user_id != session['user_id'] and not session.get('is_admin', False):
        return jsonify({'success': False, 'message': '没有权限编辑此文章'})
    try:
        article.title = data.get('title', article.title)
        article.content = data.get('content', article.content)
        db.session.commit()
        return jsonify({'success': True, 'message': '文章更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

# 路由：检查登录状态
@app.route('/api/check_login', methods=['GET'])
def check_login():
    logged_in = 'user_id' in session
    return jsonify({
        'logged_in': logged_in,
        'user_id': session.get('user_id') if logged_in else None
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5001)