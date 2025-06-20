// 全局变量
let currentArticleId = null;

// 显示消息
function showMessage(text, type = 'info') {
    const message = document.getElementById('message');
    message.textContent = text;
    message.className = `message ${type}`;
    message.style.display = 'block';
    
    setTimeout(() => {
        message.style.display = 'none';
    }, 3000);
}

// 查看文章详情
function viewArticle(articleId) {
    fetch(`/get_article/${articleId}`)
        .then(response => response.json())
        .then(article => {
            document.getElementById('modalTitle').textContent = article.title;
            document.getElementById('modalDate').textContent = new Date(article.created_at).toLocaleDateString();
            
            // 优先使用处理后的内容
            const contentElement = document.getElementById('modalContent');
            if (article.processed_content) {
                contentElement.innerHTML = article.processed_content;
                
                // 为annotated-word元素添加点击事件
                const annotatedWords = contentElement.querySelectorAll('.annotated-word');
                annotatedWords.forEach(word => {
                    word.addEventListener('click', function() {
                        showWordDetails(this);
                    });
                });
            } else {
                contentElement.textContent = article.content;
            }
            
            // 显示关键词
            const keywordsElement = document.getElementById('modalKeywords');
            keywordsElement.innerHTML = '';
            
            if (article.keywords && article.keywords.length > 0) {
                article.keywords.forEach(keyword => {
                    const tag = document.createElement('span');
                    tag.className = 'keyword-tag';
                    tag.textContent = keyword.word;
                    tag.setAttribute('data-phonetic', keyword.phonetic || '');
                    tag.setAttribute('data-translation', keyword.translation || '');
                    tag.addEventListener('click', function() {
                        showWordDetails(this);
                    });
                    keywordsElement.appendChild(tag);
                });
            } else {
                keywordsElement.innerHTML = '<p>无关键词</p>';
            }
            
            // 显示模态框
            document.getElementById('articleModal').style.display = 'block';
        })
        .catch(error => {
            console.error('获取文章失败:', error);
            showMessage('获取文章失败，请重试', 'error');
        });
}

// 显示单词详情
function showWordDetails(element) {
    const word = element.getAttribute('data-word') || element.textContent;
    const phonetic = element.getAttribute('data-phonetic') || '';
    const translation = element.getAttribute('data-translation') || '';
    
    alert(`${word}\n${phonetic}\n${translation}`);
}

// 编辑文章
function editArticle(articleId) {
    window.location.href = `/edit_article/${articleId}`;
}

// 从模态框编辑当前文章
function editCurrentArticle() {
    if (currentArticleId) {
        editArticle(currentArticleId);
    }
}

// 关闭文章详情模态框
function closeArticleModal() {
    document.getElementById('articleModal').style.display = 'none';
}

// 删除文章
function deleteArticle(articleId) {
    currentArticleId = articleId;
    document.getElementById('deleteModal').style.display = 'block';
}

// 关闭删除确认模态框
function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

// 确认删除文章
async function confirmDelete() {
    if (!currentArticleId) return;
    
    try {
        const response = await fetch(`/api/articles/${currentArticleId}`, {
            method: 'DELETE',
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('文章已成功删除', 'success');
            // 关闭模态框
            closeDeleteModal();
            // 刷新页面
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showMessage(data.message || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除文章出错:', error);
        showMessage('删除文章失败', 'error');
    }
}

// 搜索和排序功能
function filterArticles() {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const sortOption = document.getElementById('sortSelect').value;
    const articleCards = document.querySelectorAll('.article-card');
    
    // 过滤和排序文章
    const articlesArray = Array.from(articleCards);
    
    articlesArray.forEach(card => {
        const title = card.getAttribute('data-title');
        // 搜索过滤
        if (title.includes(searchInput)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
    
    // 排序
    const visibleArticles = articlesArray.filter(card => card.style.display !== 'none');
    
    visibleArticles.sort((a, b) => {
        const dateA = new Date(a.getAttribute('data-date'));
        const dateB = new Date(b.getAttribute('data-date'));
        const titleA = a.getAttribute('data-title');
        const titleB = b.getAttribute('data-title');
        
        switch (sortOption) {
            case 'newest':
                return dateB - dateA;
            case 'oldest':
                return dateA - dateB;
            case 'title':
                return titleA.localeCompare(titleB);
            default:
                return 0;
        }
    });
    
    // 重新排列DOM
    const container = document.getElementById('articlesGrid');
    visibleArticles.forEach(card => {
        container.appendChild(card);
    });
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 搜索和排序事件监听
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterArticles);
    }
    
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', filterArticles);
    }
    
    // 模态框关闭按钮
    const closeButtons = document.querySelectorAll('.modal .close');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(e) {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
});