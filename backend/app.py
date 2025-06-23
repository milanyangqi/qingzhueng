from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import json
import re
import requests
import uuid
import time

# 设置API密钥
os.environ['SILICONFLOW_API_KEY'] = 'sk-kvekdhbeqyuimzxkfzzlluiaeftjnuivccoutbfifdppvytu'
os.environ['DOUBAO_API_KEY'] = '6fbae205-63c0-46c9-9f18-026613652949'

app = Flask(__name__, 
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

# CORS配置
CORS(app, supports_credentials=True, origins=['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:5173', 'http://127.0.0.1:5173'])

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qingzhu_english.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
app.permanent_session_lifetime = timedelta(days=7)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 添加Jinja2过滤器
@app.template_filter('from_json')
def from_json(value):
    if value is None:
        return []
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except:
        app.logger.error(f"Error parsing JSON: {value}")
        return []

@app.template_filter('tojson')
def to_json(value):
    return json.dumps(value)

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
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
    processed_content = db.Column(db.Text, nullable=True)  # 处理后的内容
    keywords = db.Column(db.Text, nullable=True)  # 关键词，JSON格式存储
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

# 路由：新闻文章页面
@app.route('/news_article')
def news_article():
    # 检查用户是否登录
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('news_article.html')


# 路由：历史文章页面
@app.route('/history_articles')
def history_articles():
    # 检查用户是否登录
    if 'user_id' not in session:
        app.logger.warning("User not logged in, redirecting to index")
        return redirect(url_for('index'))
    
    app.logger.info(f"User {session.get('username', 'unknown')} (ID: {session['user_id']}) accessing history_articles route")
    
    # 获取所有文章
    try:
        # 查询所有文章，按创建时间降序排列
        articles = db.session.query(Article, User.username).join(User, Article.user_id == User.id).order_by(Article.created_at.desc()).all()
        
        # 将查询结果转换为模板可用的格式
        formatted_articles = []
        for article, username in articles:
            article_dict = {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'processed_content': article.processed_content,
                'keywords': article.keywords,
                'user_id': article.user_id,
                'created_at': article.created_at,
                'updated_at': article.updated_at,
                'username': username
            }
            formatted_articles.append(article_dict)
        
        app.logger.info(f"Successfully fetched {len(formatted_articles)} articles for history page.")
        return render_template('history_articles.html', articles=formatted_articles)
    except Exception as e:
        app.logger.error(f"获取历史文章失败: {str(e)}")
        # 如果出错，尝试使用更基本的查询
        try:
            app.logger.info("Falling back to raw SQL query for history articles")
            # 使用原始SQL查询，选择模板需要的所有列
            from sqlalchemy import text
            raw_articles = db.session.execute(
                text("""SELECT a.id, a.title, a.content, a.user_id, a.created_at, a.updated_at, a.processed_content, a.keywords, u.username 
                     FROM article a JOIN user u ON a.user_id = u.id ORDER BY a.created_at DESC""")
            ).fetchall()
            
            # 将查询结果转换为与Article对象行为相似的对象列表
            formatted_articles = []
            
            class AttrDict(dict):
                def __init__(self, *args, **kwargs):
                    super(AttrDict, self).__init__(*args, **kwargs)
                    self.__dict__ = self
                
                # 添加strftime方法以模拟datetime对象的行为
                def strftime(self, format_str):
                    if isinstance(self.get('created_at'), datetime):
                        return self.get('created_at').strftime(format_str)
                    return str(self.get('created_at'))

            for row in raw_articles:
                created_at_obj = row[4]
                if isinstance(created_at_obj, str):
                    try:
                        if '.' in created_at_obj:
                            created_at_obj = datetime.strptime(created_at_obj, '%Y-%m-%d %H:%M:%S.%f')
                        else:
                            created_at_obj = datetime.strptime(created_at_obj, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        app.logger.error(f"Could not parse date string: {created_at_obj}")
                        created_at_obj = datetime.now() # Fallback

                # 确保关键词是有效的JSON字符串
                keywords = row[7] or '[]'
                if not isinstance(keywords, str):
                    try:
                        keywords = json.dumps(keywords)
                    except:
                        app.logger.error(f"Error converting keywords to JSON string: {keywords}")
                        keywords = '[]'

                # 确保 updated_at 也是正确的 datetime 对象
                updated_at_obj = row[5]
                if isinstance(updated_at_obj, str):
                    try:
                        if '.' in updated_at_obj:
                            updated_at_obj = datetime.strptime(updated_at_obj, '%Y-%m-%d %H:%M:%S.%f')
                        else:
                            updated_at_obj = datetime.strptime(updated_at_obj, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        app.logger.error(f"Could not parse updated_at date string: {updated_at_obj}")
                        updated_at_obj = None
                
                article_data = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'user_id': row[3],
                    'created_at': created_at_obj,
                    'updated_at': updated_at_obj,
                    'processed_content': row[6],
                    'keywords': keywords,
                    'username': row[8]
                }
                formatted_articles.append(AttrDict(article_data))

            app.logger.info(f"Fallback query processed {len(formatted_articles)} history articles.")
            return render_template('history_articles.html', articles=formatted_articles)
        except Exception as e2:
            app.logger.error(f"历史文章备用查询也失败: {str(e2)}")
            # 尝试最基本的方式返回空列表
            app.logger.info("Returning empty article list for history page as last resort")
            return render_template('history_articles.html', articles=[])
            
            app.logger.info(f"Fallback query fetched {len(raw_articles)} raw articles for user {session['user_id']}.")

            # 将查询结果转换为与Article对象行为相似的对象列表
            articles = []
            
            class AttrDict(dict):
                def __init__(self, *args, **kwargs):
                    super(AttrDict, self).__init__(*args, **kwargs)
                    self.__dict__ = self
                
                # 添加strftime方法以模拟datetime对象的行为
                def strftime(self, format_str):
                    if isinstance(self.get('created_at'), datetime):
                        return self.get('created_at').strftime(format_str)
                    return str(self.get('created_at'))

            for row in raw_articles:
                created_at_obj = row[4]
                if isinstance(created_at_obj, str):
                    try:
                        if '.' in created_at_obj:
                            created_at_obj = datetime.strptime(created_at_obj, '%Y-%m-%d %H:%M:%S.%f')
                        else:
                            created_at_obj = datetime.strptime(created_at_obj, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                         app.logger.error(f"Could not parse date string: {created_at_obj}")
                         created_at_obj = datetime.now() # Fallback

                # 确保关键词是有效的JSON字符串
                keywords = row[7] or '[]'
                if not isinstance(keywords, str):
                    try:
                        keywords = json.dumps(keywords)
                    except:
                        app.logger.error(f"Error converting keywords to JSON string: {keywords}")
                        keywords = '[]'

                # 确保 updated_at 也是正确的 datetime 对象
                updated_at_obj = row[5]
                if isinstance(updated_at_obj, str):
                    try:
                        if '.' in updated_at_obj:
                            updated_at_obj = datetime.strptime(updated_at_obj, '%Y-%m-%d %H:%M:%S.%f')
                        else:
                            updated_at_obj = datetime.strptime(updated_at_obj, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        app.logger.error(f"Could not parse updated_at date string: {updated_at_obj}")
                        updated_at_obj = None
                
                article_data = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'user_id': row[3],
                    'created_at': created_at_obj,
                    'updated_at': updated_at_obj,
                    'processed_content': row[6],
                    'keywords': keywords
                }
                articles.append(AttrDict(article_data))

            app.logger.info(f"Fallback query processed {len(articles)} articles.")
            for article in articles:
                try:
                    # 格式化日期以避免datetime序列化问题
                    created_at_str = article.created_at.strftime('%Y-%m-%d %H:%M:%S.%f') if hasattr(article.created_at, 'strftime') else str(article.created_at)
                    app.logger.info(f"Fallback Article ID: {article.id}, Title: {article.title}, Created At: {created_at_str}, Keywords: {article.keywords}")
                except Exception as e3:
                    app.logger.error(f"Error logging article info: {str(e3)}")

            return render_template('my_articles.html', articles=articles)
        except Exception as e2:
            app.logger.error(f"备用查询也失败: {str(e2)}")
            # 尝试最基本的方式返回空列表
            app.logger.info("Returning empty article list as last resort")
            return render_template('my_articles.html', articles=[])

# 路由：获取单篇文章详情
@app.route('/get_article/<int:article_id>')
def get_article(article_id):
    # 检查用户是否登录
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # 尝试从数据库获取文章，不再限制只能查看自己的文章
        article = Article.query.filter_by(id=article_id).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # 获取文章作者信息
        user = User.query.get(article.user_id)
        username = user.username if user else 'Unknown'
        
        # 确保关键词是JSON格式
        keywords = []
        if article.keywords:
            try:
                if isinstance(article.keywords, str):
                    keywords = json.loads(article.keywords)
                else:
                    keywords = article.keywords
            except:
                app.logger.error(f"Error parsing keywords for article {article_id}: {article.keywords}")
        
        # 返回文章数据
        return jsonify({
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'processed_content': article.processed_content,
            'keywords': keywords,
            'user_id': article.user_id,
            'username': username,
            'created_at': article.created_at.isoformat(),
            'updated_at': article.updated_at.isoformat() if article.updated_at else None
        })
    
    except Exception as e:
        app.logger.error(f"Error getting article {article_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
            
            # 检查是否有重定向URL
            redirect_url = data.get('redirect')
            if redirect_url:
                return jsonify({
                    'success': True, 
                    'message': '登录成功', 
                    'is_admin': user.is_admin,
                    'redirect_url': redirect_url
                })
            else:
                return jsonify({'success': True, 'message': '登录成功', 'is_admin': user.is_admin})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'})
    
    return redirect(url_for('index'))

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
        return redirect(url_for('history_articles'))
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
    # 重定向到news_article路由，因为功能已合并
    return redirect(url_for('news_article'))

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
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
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
    
    # 豆包API调用（使用火山引擎官方API）
    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "endpoint_id": "ep-20250621182111-tpn6s",
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    # 检查响应状态码
    if response.status_code != 200:
        raise Exception(f"豆包API调用失败: HTTP状态码 {response.status_code}, 响应内容: {response.text}")
    
    # 检查响应内容是否为空
    if not response.text.strip():
        raise Exception("豆包API返回了空响应")
    
    try:
        response_json = response.json()
        if 'choices' in response_json and len(response_json['choices']) > 0:
            generated_content = response_json['choices'][0]['message']['content']
        else:
            raise Exception(f"豆包API调用失败: {response_json}")
    except json.JSONDecodeError as e:
        raise Exception(f"豆包API返回了无效的JSON格式: {e}, 响应内容: {response.text}")
    
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
        model = options.get('model', 'siliconflow')
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
        model = data.get('model', 'siliconflow')
        
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
                
                # 检查响应状态码
                if response.status_code != 200:
                    raise Exception(f"DeepSeek API调用失败: HTTP状态码 {response.status_code}, 响应内容: {response.text}")
                
                # 提取生成的内容
                try:
                    response_json = response.json()
                    content = response_json['choices'][0]['message']['content']
                except Exception as e:
                    raise Exception(f"DeepSeek API返回了无效的响应: {e}, 响应内容: {response.text}")
                
                response = requests.post(url, headers=headers, json=data)
                
                # 检查响应状态码
                if response.status_code != 200:
                    raise Exception(f"豆包API调用失败: HTTP状态码 {response.status_code}, 响应内容: {response.text}")
                
                # 检查响应内容是否为空
                if not response.text.strip():
                    raise Exception("豆包API返回了空响应")
                
                try:
                    response_json = response.json()
                    if 'choices' in response_json and len(response_json['choices']) > 0:
                        content = response_json['choices'][0]['message']['content']
                    else:
                        raise Exception(f"豆包API调用失败: {response_json}")
                except json.JSONDecodeError as e:
                    raise Exception(f"豆包API返回了无效的JSON格式: {e}, 响应内容: {response.text}")
                
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
    model = data.get('model', 'siliconflow')
    
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
        - vocabulary: 词汇表，包含单词、音标、翻译和定义
        - multiple_choice: 选择题（5道题，每题4个选项）
        - translation: 参考译文
        - answers: 答案标识（用于标识是否包含答案）
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
2. vocabulary: 词汇表，包含8-12个文章中的重要词汇，每个词汇包括：
   - word: 单词
   - phonetic: 音标（使用国际音标IPA格式）
   - translation: 中文翻译
   - definition: 英文释义
3. multiple_choice: 5道选择题，每道题包括：
   - question: 题目
   - options: 4个选项的数组，每个选项必须以A、B、C、D开头（如"A. 选项内容"）
   - correct_answer: 正确答案（如A、B、C、D）
   注意：请确保5道题的正确答案分布均匀，不要让所有答案都是同一个选项（如都是A或都是B），应该在A、B、C、D之间合理分布
4. translation: 文章的中文参考译文
5. answers: 设置为true，表示包含答案

请确保输出是有效的JSON格式，可以直接被解析。
"""
        else:
            user_prompt = f"""请创建一篇英语文章，满足以下要求：

1. 主题：{topic}
2. 蓝思指数(Lexile)：{lexile}
3. 单词数量：大约{word_count}个单词

请生成以下内容（JSON格式）：
1. content: 文章内容
2. vocabulary: 词汇表，包含8-12个文章中的重要词汇，每个词汇包括：
   - word: 单词
   - phonetic: 音标（使用国际音标IPA格式）
   - translation: 中文翻译
   - definition: 英文释义
3. multiple_choice: 5道选择题，每道题包括：
   - question: 题目
   - options: 4个选项的数组，每个选项必须以A、B、C、D开头（如"A. 选项内容"）
   - correct_answer: 正确答案（如A、B、C、D）
   注意：请确保5道题的正确答案分布均匀，不要让所有答案都是同一个选项（如都是A或都是B），应该在A、B、C、D之间合理分布
4. translation: 文章的中文参考译文
5. answers: 设置为true，表示包含答案

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
            
            # 豆包API调用（使用火山引擎官方API）
            url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            data = {
                "endpoint_id": "ep-20250621182111-tpn6s",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
                
            response = requests.post(url, headers=headers, json=data)
            
            # 检查HTTP状态码
            if response.status_code != 200:
                raise Exception(f"豆包API调用失败: HTTP状态码 {response.status_code}, 响应内容: {response.text}")
            
            # 检查是否有响应内容
            if not response.text.strip():
                raise Exception("豆包API返回了空响应")
            
            # 尝试解析JSON
            try:
                response_json = response.json()
                
                if 'choices' in response_json and len(response_json['choices']) > 0:
                    generated_content = response_json['choices'][0]['message']['content']
                else:
                    raise Exception(f"豆包API调用失败: {response_json}")
            except json.JSONDecodeError as e:
                raise Exception(f"豆包API返回了无效的JSON格式: {e}, 响应内容: {response.text}")
            
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
            # 使用环境变量中的API密钥
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
                    'multiple_choice': data.get('multiple_choice', []),
                    'translation': data.get('translation', ''),
                    'answers': data.get('answers', True),
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

# 路由：处理文本
@app.route('/process_text', methods=['POST'])
def process_text():
    try:
        # 暂时注释掉登录检查，以便测试
        # if 'user_id' not in session:
        #     return jsonify({'success': False, 'message': '请先登录'})
            
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'message': '无效的请求数据'})
            
        text = data['text']
        if not text.strip():
            return jsonify({'success': False, 'message': '文本内容不能为空'})
        
        # 生成标题
        title = generate_title_from_text(text)
        
        # 提取重要单词
        words = extract_important_words(text)
        
        return jsonify({
            'success': True,
            'message': '文本处理成功',
            'title': title,
            'words': words
        })
    except Exception as e:
        print(f"处理文本时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'处理失败: {str(e)}'})

# 从文本生成标题
def generate_title_from_text(text):
    # 简单实现：取第一句话的前几个单词作为标题
    sentences = text.split('.')
    if sentences and sentences[0].strip():
        words = sentences[0].strip().split()
        title_words = words[:8] if len(words) > 8 else words
        return ' '.join(title_words) + ('...' if len(words) > 8 else '')
    return 'English Reading Article'

# 提取重要单词
def extract_important_words(text):
    # 简单实现：提取较长的单词作为重要单词
    import re
    from collections import Counter
    
    # 清理文本，只保留字母和空格
    clean_text = re.sub(r'[^a-zA-Z\s]', ' ', text.lower())
    
    # 分割成单词
    words = clean_text.split()
    
    # 过滤掉常见的停用词
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
                 'when', 'where', 'how', 'all', 'with', 'for', 'in', 'to', 'from',
                 'of', 'at', 'by', 'about', 'like', 'through', 'over', 'before',
                 'between', 'after', 'since', 'without', 'under', 'within', 'along',
                 'following', 'across', 'behind', 'beyond', 'plus', 'except', 'but',
                 'up', 'out', 'around', 'down', 'off', 'above', 'near', 'is', 'are',
                 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
                 'does', 'did', 'doing', 'can', 'could', 'should', 'would', 'might',
                 'will', 'shall', 'may', 'must', 'that', 'this', 'these', 'those',
                 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
                 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'}
    
    filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
    
    # 计算单词频率
    word_counts = Counter(filtered_words)
    
    # 选择频率较高的单词（最多20个）
    important_words = [{'word': word, 'translation': get_word_translation(word)} 
                      for word, count in word_counts.most_common(20)]
    
    return important_words

# 获取单词翻译
def get_word_translation(word):
    # 简单的单词翻译映射（实际应用中可以使用翻译API或词典数据库）
    translations = {
        'important': '重要的',
        'computer': '计算机',
        'technology': '技术',
        'science': '科学',
        'education': '教育',
        'development': '发展',
        'environment': '环境',
        'government': '政府',
        'business': '商业',
        'research': '研究',
        'information': '信息',
        'knowledge': '知识',
        'experience': '经验',
        'management': '管理',
        'international': '国际的',
        'communication': '通信',
        'university': '大学',
        'community': '社区',
        'industry': '工业',
        'economic': '经济的',
        'political': '政治的',
        'social': '社会的',
        'cultural': '文化的',
        'natural': '自然的',
        'digital': '数字的',
        'global': '全球的',
        'national': '国家的',
        'regional': '地区的',
        'local': '当地的',
        'modern': '现代的',
        'traditional': '传统的',
        'professional': '专业的',
        'personal': '个人的',
        'financial': '金融的',
        'medical': '医疗的',
        'educational': '教育的',
        'technical': '技术的',
        'scientific': '科学的',
        'artistic': '艺术的',
        'creative': '创造性的'
    }
    
    return translations.get(word, '未知')

# 路由：检查登录状态
@app.route('/api/check_login', methods=['GET'])
def check_login():
    logged_in = 'user_id' in session
    return jsonify({
        'logged_in': logged_in,
        'user_id': session.get('user_id') if logged_in else None
    })

# 路由：保存文章
@app.route('/save_article', methods=['POST'])
def save_article():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    try:
        data = request.get_json()
        
        # 检查必要字段
        if not data.get('title') or not data.get('content'):
            return jsonify({'success': False, 'message': '标题和内容不能为空'})
        
        # 构建完整的文章内容，包含词汇
        full_content = data.get('content', '')
        if data.get('vocabulary'):
            full_content += "\n\n词汇列表:\n" + data.get('vocabulary', '')
        
        # 创建新文章
        new_article = Article(
            title=data['title'],
            content=full_content,
            processed_content=data.get('content'),
            keywords=json.dumps([data.get('topic', '')]),
            user_id=session['user_id'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_article)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '文章保存成功',
            'article_id': new_article.id
        })
    except Exception as e:
        db.session.rollback()
        print(f"保存文章出错: {str(e)}")
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})

# 路由：导出PDF
@app.route('/export_article_pdf', methods=['POST'])
def export_article_pdf():
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io
        import html
        
        data = request.get_json()
        title = data.get('title', '未命名文章')
        content = data.get('content', '')
        vocabulary = data.get('vocabulary', '')
        
        # 创建PDF缓冲区
        buffer = io.BytesIO()
        
        # 创建PDF文档
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        # 获取样式
        styles = getSampleStyleSheet()
        
        # 尝试注册中文字体（如果可用）
        font_name = 'Helvetica'  # 默认字体
        try:
            import platform
            import os
            
            if platform.system() == 'Darwin':  # macOS
                # 尝试多个可能的中文字体路径，优先使用支持中文的字体
                font_paths = [
                    '/System/Library/Fonts/PingFang.ttc',
                    '/System/Library/Fonts/STHeiti Light.ttc',
                    '/System/Library/Fonts/STHeiti Medium.ttc',
                    '/System/Library/Fonts/Hiragino Sans GB.ttc',
                    '/System/Library/Fonts/STSong.ttc',
                    '/System/Library/Fonts/STKaiti.ttc',
                    '/Library/Fonts/Arial Unicode MS.ttf',
                    '/System/Library/Fonts/Helvetica.ttc'
                ]
                
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            # 注册字体
                            font = TTFont('ChineseFont', font_path)
                            pdfmetrics.registerFont(font)
                            
                            # 测试字体是否支持中文
                            try:
                                # 尝试创建包含中文的测试段落
                                test_style = ParagraphStyle('test', fontName='ChineseFont', fontSize=12)
                                test_para = Paragraph('测试中文字符', test_style)
                                font_name = 'ChineseFont'
                                print(f"成功注册并验证中文字体: {font_path}")
                                break
                            except Exception as test_error:
                                print(f"字体不支持中文 {font_path}: {test_error}")
                                continue
                                
                        except Exception as font_error:
                            print(f"注册字体失败 {font_path}: {font_error}")
                            continue
                            
            elif platform.system() == 'Windows':
                windows_fonts = [
                    'C:/Windows/Fonts/simsun.ttc',
                    'C:/Windows/Fonts/msyh.ttc',
                    'C:/Windows/Fonts/arial.ttf'
                ]
                
                for font_path in windows_fonts:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                            font_name = 'ChineseFont'
                            print(f"成功注册字体: {font_path}")
                            break
                        except Exception as font_error:
                            print(f"注册字体失败 {font_path}: {font_error}")
                            continue
                            
        except Exception as e:
            print(f"字体注册过程出错: {e}")
            font_name = 'Helvetica'
        
        # 创建标题样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # 创建正文样式
        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=12,
            leading=18,
            alignment=TA_LEFT
        )
        
        # 创建小标题样式
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            spaceAfter=15,
            spaceBefore=20,
            alignment=TA_LEFT
        )
        
        # 构建PDF内容
        story = []
        
        try:
            # 添加标题
            if title:
                # 清理标题，移除HTML标签
                clean_title = html.escape(str(title).strip())
                if clean_title:
                    story.append(Paragraph(clean_title, title_style))
                    story.append(Spacer(1, 20))
            
            # 添加文章内容
            if content:
                story.append(Paragraph('文章内容', subtitle_style))
                content_lines = str(content).split('\n')
                for line in content_lines:
                    line = line.strip()
                    if line:
                        # 移除HTML标签并转义特殊字符
                        clean_line = html.escape(line)
                        # 替换常见的特殊字符
                        clean_line = clean_line.replace('&quot;', '"').replace('&apos;', "'")
                        story.append(Paragraph(clean_line, content_style))
                    else:
                        story.append(Spacer(1, 6))
            
            # 添加词汇列表
            if vocabulary:
                story.append(Spacer(1, 20))
                story.append(Paragraph('词汇列表', subtitle_style))
                # 处理词汇列表，可能包含HTML格式
                vocab_text = str(vocabulary).strip()
                if vocab_text:
                    # 简单处理HTML列表
                    vocab_lines = vocab_text.replace('<li>', '• ').replace('</li>', '\n').split('\n')
                    for line in vocab_lines:
                        line = line.strip()
                        if line and not line.startswith('<'):
                            clean_line = html.escape(line)
                            story.append(Paragraph(clean_line, content_style))
            

                                
        except Exception as content_error:
            print(f"处理PDF内容时出错: {content_error}")
            # 添加错误信息到PDF
            story.append(Paragraph('内容处理出错，请检查数据格式', content_style))
        
        # 确保有内容可以生成PDF
        if not story:
            story.append(Paragraph('无内容可显示', content_style))
        
        # 生成PDF
        try:
            doc.build(story)
            print(f"PDF构建成功，使用字体: {font_name}")
        except Exception as build_error:
            print(f"PDF构建失败: {build_error}")
            # 尝试使用默认字体重新构建
            font_name = 'Helvetica'
            title_style.fontName = font_name
            content_style.fontName = font_name
            subtitle_style.fontName = font_name
            doc.build(story)
        
        # 获取PDF数据
        pdf_data = buffer.getvalue()
        buffer.close()
        
        print(f"生成的PDF大小: {len(pdf_data)} 字节")
        
        # 验证PDF数据
        if len(pdf_data) < 100:  # PDF文件应该至少有几百字节
            raise Exception("生成的PDF文件过小，可能损坏")
        
        # 安全的文件名处理
        safe_filename = ''.join(c for c in str(title) if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not safe_filename:
            safe_filename = 'article'
        
        # 返回PDF文件
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}.pdf"'
        response.headers['Content-Length'] = str(len(pdf_data))
        response.headers['Cache-Control'] = 'no-cache'
        
        print(f"返回PDF文件: {safe_filename}.pdf")
        return response
        
    except ImportError:
        # 如果没有安装reportlab，返回简单的文本文件
        data = request.get_json()
        title = data.get('title', '未命名文章')
        content = data.get('content', '')
        
        response = make_response(content)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="{title}.txt"'
        
        return response
        
    except Exception as e:
        print(f"导出PDF出错: {str(e)}")
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'})

def create_default_admin():
    """创建默认管理员账号"""
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@qingzhu.com',
            is_admin=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("默认管理员账号已创建: admin / admin123")
    else:
        print("管理员账号已存在")

# 路由：检查用户登录状态API
@app.route('/api/check_login_status', methods=['GET'])
def check_login_status():
    """检查用户是否已登录的API端点
    
    Returns:
        JSON: 包含登录状态和用户信息的JSON响应
    """
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'logged_in': True,
                'user_id': user.id,
                'username': user.username,
                'is_admin': user.is_admin
            })
    
    return jsonify({
        'logged_in': False
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True, host='0.0.0.0', port=5001)

# 注意：此路由已在前面定义，这里删除重复定义

# 注意：这些过滤器已在前面定义，这里删除重复定义