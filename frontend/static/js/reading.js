// 时文阅读模块JavaScript

// 全局变量
let currentText = '';
let processedWords = [];
let isProcessing = false;

// 显示消息
function showMessage(message, type = 'info') {
    const messageEl = document.getElementById('message');
    if (messageEl) {
        messageEl.textContent = message;
        messageEl.className = `message ${type}`;
        messageEl.classList.add('show');
        
        setTimeout(() => {
            messageEl.classList.remove('show');
        }, 3000);
    }
}

// 生成文章标题
function generateTitle(text) {
    // 简单的标题生成逻辑
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length > 0) {
        const firstSentence = sentences[0].trim();
        // 取前8个单词作为标题
        const words = firstSentence.split(/\s+/).slice(0, 8);
        return words.join(' ') + (words.length === 8 ? '...' : '');
    }
    return 'English Reading Article';
}

// 处理文本
async function processText() {
    const textInput = document.getElementById('textInput');
    const text = textInput.value.trim();
    
    if (!text) {
        showMessage('请输入英文文本', 'error');
        return;
    }
    
    if (isProcessing) {
        showMessage('正在处理中，请稍候...', 'warning');
        return;
    }
    
    isProcessing = true;
    const processBtn = document.getElementById('processBtn');
    const originalText = processBtn.innerHTML;
    processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
    processBtn.disabled = true;
    
    // 滚动到页面顶部，确保用户可以看到处理结果
    window.scrollTo(0, 0);
    
    try {
        console.log('发送文本处理请求:', text);
        console.log('请求URL:', '/process_text');
        console.log('请求方法:', 'POST');
        console.log('请求头:', {'Content-Type': 'application/json'});
        console.log('请求体:', JSON.stringify({ text: text }));
        
        const response = await fetch('/process_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        console.log('收到响应状态:', response.status);
        console.log('收到响应状态文本:', response.statusText);
        console.log('收到响应头:', response.headers);
        console.log('收到响应:', response);
        
        const data = await response.json();
        console.log('响应数据:', data);
        
        if (data.success) {
            currentText = text;
            processedWords = data.words || [];
            
            // 使用服务器提供的标题，如果没有则生成标题
            const title = data.title || generateTitle(text);
            document.getElementById('articleTitle').value = title;
            
            console.log('显示处理后的文本');
            // 显示处理后的文本
            displayProcessedText(text, processedWords);
            
            console.log('显示单词列表');
            // 显示单词列表
            displayWordList(processedWords);
            
            console.log('显示结果区域');
            // 显示结果区域
            document.getElementById('resultSection').style.display = 'block';
            
            // 平滑滚动到结果区域
            document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
            
            // 清除草稿（文本已处理完成）
            localStorage.removeItem('reading_draft');
            
            showMessage('文本处理完成！', 'success');
        } else {
            showMessage(data.message || '处理失败', 'error');
        }
    } catch (error) {
        console.error('Process error:', error);
        showMessage('处理失败，请稍后重试', 'error');
    } finally {
        isProcessing = false;
        processBtn.innerHTML = originalText;
        processBtn.disabled = false;
    }
}

// 显示处理后的文本（带单词标注）
function displayProcessedText(text, words) {
    const container = document.getElementById('articleContent'); // 使用正确的 ID
    
    // 创建单词映射
    const wordMap = {};
    words.forEach(word => {
        wordMap[word.word.toLowerCase()] = word;
    });
    
    // 分割文本为单词和标点
    const tokens = text.split(/(\s+|[.,!?;:"'()\[\]{}])/);
    
    let html = '';
    tokens.forEach(token => {
        const cleanToken = token.toLowerCase().replace(/[^a-z]/g, '');
        
        if (wordMap[cleanToken]) {
            const word = wordMap[cleanToken];
            html += `<span class="annotated-word" data-word="${word.word}" data-phonetic="${word.phonetic || ''}" data-translation="${word.translation || ''}" title="${word.phonetic || ''} - ${word.translation || ''}">${token}</span>`;
        } else {
            html += token;
        }
    });
    
    container.innerHTML = html;
    container.style.lineHeight = '1.6';
    container.style.fontSize = '16px';
    container.style.color = '#333';
    container.style.padding = '10px';
    
    // 添加点击事件
    container.querySelectorAll('.annotated-word').forEach(span => {
        span.addEventListener('click', function() {
            showWordDetails(this.dataset.word, this.dataset.phonetic, this.dataset.translation);
        });
    });
    
    // 显示结果区域
    const resultSection = document.getElementById('resultSection');
    resultSection.style.display = 'block';
    
    // 重新组织页面布局
    const inputSection = document.querySelector('.input-section');
    inputSection.style.display = 'none'; // 隐藏输入区域
    
    // 创建两列布局
    const mainContent = document.querySelector('.main-content');
    mainContent.style.display = 'grid';
    mainContent.style.gridTemplateColumns = '1fr 350px';
    mainContent.style.gap = '20px';
    mainContent.style.alignItems = 'start';
    
    // 重新组织卡片布局
    const titleCard = document.querySelector('.title-card');
    const contentCard = document.querySelector('.content-card');
    const keywordsCard = document.querySelector('.keywords-card');
    const saveCard = document.querySelector('.save-card');
    
    // 调整左侧内容区域
    const leftColumn = document.createElement('div');
    leftColumn.className = 'left-column';
    leftColumn.style.display = 'flex';
    leftColumn.style.flexDirection = 'column';
    leftColumn.style.gap = '20px';
    
    // 调整右侧单词区域
    const rightColumn = document.createElement('div');
    rightColumn.className = 'right-column';
    rightColumn.style.position = 'sticky';
    rightColumn.style.top = '20px';
    
    // 移动卡片到新的布局中
    mainContent.innerHTML = '';
    leftColumn.appendChild(titleCard);
    leftColumn.appendChild(contentCard);
    leftColumn.appendChild(saveCard);
    rightColumn.appendChild(keywordsCard);
    
    mainContent.appendChild(leftColumn);
    mainContent.appendChild(rightColumn);
    
    // 调整卡片样式
    contentCard.style.marginBottom = '20px';
    keywordsCard.style.maxHeight = 'calc(100vh - 100px)';
    keywordsCard.style.overflowY = 'auto';
    
    // 自动保存文章
    setTimeout(() => {
        saveArticle();
    }, 1000);
}

// 显示单词列表
function displayWordList(words) {
    const keywordsContainer = document.getElementById('keywordsContainer');
    if (!keywordsContainer) return;
    
    keywordsContainer.innerHTML = '';
    
    if (words.length === 0) {
        keywordsContainer.innerHTML = '<div class="no-words">没有提取到重点单词</div>';
        return;
    }
    
    // 创建单词网格容器
    const wordGrid = document.createElement('div');
    wordGrid.className = 'word-grid';
    wordGrid.style.display = 'grid';
    wordGrid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(200px, 1fr))';
    wordGrid.style.gap = '15px';
    
    // 按字母顺序排序单词
    words.sort((a, b) => a.word.localeCompare(b.word));
    
    // 为每个单词创建卡片
    words.forEach(wordObj => {
        const wordCard = document.createElement('div');
        wordCard.className = 'word-card';
        wordCard.style.background = '#f8f9fa';
        wordCard.style.borderRadius = '8px';
        wordCard.style.padding = '12px';
        wordCard.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
        wordCard.style.cursor = 'pointer';
        wordCard.style.border = '1px solid #e9ecef';
        wordCard.style.transition = 'all 0.3s ease';
        
        const wordText = document.createElement('div');
        wordText.className = 'word-text';
        wordText.textContent = wordObj.word;
        wordText.style.fontWeight = '600';
        wordText.style.fontSize = '1.1rem';
        wordText.style.marginBottom = '5px';
        wordText.style.color = '#333';
        
        const wordPhonetic = document.createElement('div');
        wordPhonetic.className = 'word-phonetic';
        wordPhonetic.textContent = wordObj.phonetic || '暂无音标';
        wordPhonetic.style.fontSize = '0.9rem';
        wordPhonetic.style.color = '#667eea';
        wordPhonetic.style.fontStyle = 'italic';
        wordPhonetic.style.marginBottom = '5px';
        wordPhonetic.style.display = 'block'; // 确保显示
        
        const wordTranslation = document.createElement('div');
        wordTranslation.className = 'word-translation';
        wordTranslation.textContent = wordObj.translation || '暂无翻译';
        wordTranslation.style.fontSize = '0.95rem';
        wordTranslation.style.color = '#666';
        wordTranslation.style.marginBottom = '10px';
        wordTranslation.style.display = 'block'; // 确保显示
        
        const wordActions = document.createElement('div');
        wordActions.className = 'word-actions';
        wordActions.style.display = 'flex';
        wordActions.style.gap = '8px';
        wordActions.style.justifyContent = 'flex-start';
        
        const pronounceBtn = document.createElement('button');
        pronounceBtn.className = 'btn btn-sm btn-outline-primary';
        pronounceBtn.style.padding = '3px 8px';
        pronounceBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
        pronounceBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            playPronunciation(wordObj.word);
        });
        
        const detailsBtn = document.createElement('button');
        detailsBtn.className = 'btn btn-sm btn-outline-info';
        detailsBtn.style.padding = '3px 8px';
        detailsBtn.innerHTML = '<i class="fas fa-info-circle"></i>';
        detailsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            showWordDetails(wordObj.word, wordObj.phonetic, wordObj.translation);
        });
        
        wordActions.appendChild(pronounceBtn);
        wordActions.appendChild(detailsBtn);
        
        wordCard.appendChild(wordText);
        wordCard.appendChild(wordPhonetic);
        wordCard.appendChild(wordTranslation);
        wordCard.appendChild(wordActions);
        
        // 点击单词卡片也可以显示详情
        wordCard.addEventListener('click', () => {
            showWordDetails(wordObj.word, wordObj.phonetic, wordObj.translation);
        });
        
        // 鼠标悬停效果
        wordCard.addEventListener('mouseover', () => {
            wordCard.style.transform = 'translateY(-3px)';
            wordCard.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.1)';
        });
        
        wordCard.addEventListener('mouseout', () => {
            wordCard.style.transform = 'translateY(0)';
            wordCard.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
        });
        
        wordGrid.appendChild(wordCard);
    });
    
    keywordsContainer.appendChild(wordGrid);
    
    // 调整关键词卡片样式
    const keywordsCard = document.querySelector('.keywords-card');
    if (keywordsCard) {
        keywordsCard.style.maxHeight = '100vh';
        keywordsCard.style.overflowY = 'auto';
    }
}

// 播放单词发音
function playPronunciation(word) {
    // 使用Web Speech API或第三方TTS服务
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(word);
        utterance.lang = 'en-US';
        utterance.rate = 0.8;
        speechSynthesis.speak(utterance);
    } else {
        showMessage('您的浏览器不支持语音播放', 'warning');
    }
}

// 显示单词详情
function showWordDetails(word, phonetic, translation) {
    const modal = document.getElementById('wordModal');
    const wordElement = document.getElementById('modalWord');
    const phoneticElement = document.getElementById('modalPhonetic');
    const translationElement = document.getElementById('modalTranslation');
    
    // 处理不同的参数情况
    if (typeof word === 'object' && word !== null) {
        // 如果传入的是单词对象
        const wordObj = word;
        wordElement.textContent = wordObj.word;
        phoneticElement.textContent = wordObj.phonetic || '暂无音标';
        translationElement.textContent = wordObj.translation || '暂无翻译';
    } else {
        // 如果传入的是单独的参数
        wordElement.textContent = word;
        phoneticElement.textContent = phonetic || '暂无音标';
        translationElement.textContent = translation || '暂无翻译';
    }
    
    modal.style.display = 'block';
}

// 关闭模态框
function closeModal() {
    document.getElementById('wordModal').style.display = 'none';
}

// 保存文章
async function saveArticle() {
    const title = document.getElementById('articleTitle').value.trim();
    
    if (!title) {
        showMessage('请输入文章标题', 'error');
        return;
    }
    
    if (!currentText) {
        showMessage('没有可保存的文章内容', 'error');
        return;
    }
    
    try {
        console.log('正在保存文章...');
        console.log('标题:', title);
        console.log('原文:', currentText);
        console.log('处理后内容:', document.getElementById('articleContent').innerHTML);
        console.log('关键词:', processedWords);
        
        const response = await fetch('/save_article', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                content: currentText,
                processedContent: document.getElementById('articleContent').innerHTML,
                keywords: processedWords
            })
        });
        
        console.log('保存文章响应:', response);
        
        const result = await response.json();
        console.log('保存文章响应数据:', result);
        
        if (result.success) {
            // 如果后端返回了特定消息（如图片提醒），则显示该消息
            if (result.message) {
                showMessage(result.message, 'info');
            } else {
                showMessage('文章保存成功！', 'success');
            }
            // 清除本地存储的草稿
            localStorage.removeItem('reading_draft');
            // 不再自动跳转，让用户可以继续查看处理结果
        } else {
            showMessage(`保存失败: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Save error:', error);
        showMessage('保存失败，请稍后重试', 'error');
    }
}

// 清空内容
function clearContent() {
    if (confirm('确定要清空所有内容吗？')) {
        document.getElementById('textInput').value = '';
        document.getElementById('articleTitle').value = '';
        document.getElementById('articleContent').innerHTML = '';
        document.getElementById('keywordsContainer').innerHTML = '';
        document.getElementById('resultSection').style.display = 'none';
        
        currentText = '';
        processedWords = [];
        
        showMessage('内容已清空', 'info');
    }
}

// 调整字体大小
function adjustFontSize(change) {
    const textArea = document.getElementById('articleContent');
    const currentSize = parseInt(window.getComputedStyle(textArea).fontSize);
    const newSize = Math.max(12, Math.min(24, currentSize + change));
    textArea.style.fontSize = newSize + 'px';
}

// 切换主题
function toggleTheme() {
    const body = document.body;
    const isDark = body.classList.contains('dark-theme');
    
    if (isDark) {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }
}

// 导出文章
function exportArticle() {
    if (!currentText) {
        showMessage('没有可导出的内容', 'error');
        return;
    }
    
    const title = document.getElementById('articleTitle').value || 'English Article';
    const content = `# ${title}\n\n${currentText}\n\n## 重点单词\n\n${processedWords.map(w => `- **${w.word}** ${w.phonetic || ''} - ${w.translation || ''}`).join('\n')}`;
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.md`;
    a.click();
    URL.revokeObjectURL(url);
    
    showMessage('文章已导出', 'success');
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 恢复主题设置
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
    
    // 添加键盘快捷键
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'Enter':
                    e.preventDefault();
                    processText();
                    break;
                case 's':
                    e.preventDefault();
                    saveArticle();
                    break;
                case '=':
                case '+':
                    e.preventDefault();
                    adjustFontSize(2);
                    break;
                case '-':
                    e.preventDefault();
                    adjustFontSize(-2);
                    break;
            }
        }
    });
    
    // 模态框点击外部关闭
    window.addEventListener('click', function(e) {
        const modal = document.getElementById('wordModal');
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // 文本输入框自动调整高度
    const textInput = document.getElementById('textInput');
    textInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
    
    // 添加拖拽上传功能
    textInput.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });
    
    textInput.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
    });
    
    textInput.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.type === 'text/plain') {
                const reader = new FileReader();
                reader.onload = function(e) {
                    textInput.value = e.target.result;
                    textInput.style.height = 'auto';
                    textInput.style.height = textInput.scrollHeight + 'px';
                };
                reader.readAsText(file);
            } else {
                showMessage('请上传文本文件', 'error');
            }
        }
    });
    // 表单提交时处理文本
    const textForm = document.getElementById('textForm');
    if (textForm) {
        textForm.addEventListener('submit', function(e) {
            e.preventDefault();
            processText();
        });
    }
    
    // 字体大小输入框
    const fontSizeInput = document.getElementById('fontSizeInput');
    if (fontSizeInput) {
        fontSizeInput.addEventListener('input', function() {
            const articleContent = document.getElementById('articleContent');
            articleContent.style.fontSize = this.value + 'px';
        });
    }
    
    // 行间距输入框
    const lineHeightInput = document.getElementById('lineHeightInput');
    if (lineHeightInput) {
        lineHeightInput.addEventListener('input', function() {
            const articleContent = document.getElementById('articleContent');
            articleContent.style.lineHeight = this.value;
        });
    }
    
    // 字体选择器
    const fontFamilySelect = document.getElementById('fontFamilySelect');
    if (fontFamilySelect) {
        fontFamilySelect.addEventListener('change', function() {
            const articleContent = document.getElementById('articleContent');
            articleContent.style.fontFamily = this.value;
        });
    }
    
    // 颜色选择器
    const colorOptions = document.querySelectorAll('.color-option');
    if (colorOptions.length > 0) {
        colorOptions.forEach(option => {
            option.addEventListener('click', function() {
                // 移除其他选项的选中状态
                document.querySelectorAll('.color-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                
                // 添加当前选项的选中状态
                this.classList.add('selected');
                
                // 设置文本颜色
                const color = this.getAttribute('data-color');
                const articleContent = document.getElementById('articleContent');
                articleContent.style.color = color;
            });
        });
        
        // 默认选中第一个颜色
        colorOptions[0].classList.add('selected');
    }
    
    // 高亮重点词按钮
    const highlightBtn = document.getElementById('highlightBtn');
    if (highlightBtn) {
        highlightBtn.addEventListener('click', function() {
            const annotatedWords = document.querySelectorAll('.annotated-word');
            const isHighlighted = document.querySelector('.annotated-word.highlighted');
            
            annotatedWords.forEach(word => {
                if (isHighlighted) {
                    word.classList.remove('highlighted');
                } else {
                    word.classList.add('highlighted');
                }
            });
            
            // 更新按钮文本
            if (isHighlighted) {
                this.innerHTML = '<i class="fas fa-highlighter"></i> 高亮重点词';
            } else {
                this.innerHTML = '<i class="fas fa-highlighter"></i> 取消高亮';
            }
        });
    }
    
    // 查看我的文章按钮
    const viewArticlesBtn = document.getElementById('viewArticlesBtn');
    if (viewArticlesBtn) {
        viewArticlesBtn.addEventListener('click', function() {
            window.location.href = '/my_articles';
        });
    }
    
    // 清空按钮
    const clearBtn = document.getElementById('clearBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearContent);
    }
    
    // 编辑标题按钮
    const editTitleBtn = document.getElementById('editTitleBtn');
    if (editTitleBtn) {
        editTitleBtn.addEventListener('click', function() {
            const titleInput = document.getElementById('articleTitle');
            titleInput.readOnly = !titleInput.readOnly;
            if (!titleInput.readOnly) {
                titleInput.focus();
                this.innerHTML = '<i class="fas fa-check"></i> 完成编辑';
            } else {
                this.innerHTML = '<i class="fas fa-edit"></i> 编辑标题';
            }
        });
    }
    
    // 处理新文本按钮
    const newArticleBtn = document.getElementById('newArticleBtn');
    if (newArticleBtn) {
        newArticleBtn.addEventListener('click', function() {
            clearContent();
            document.getElementById('textInput').focus();
        });
    }
    
    // 手动保存文章按钮
    const saveArticleBtn = document.getElementById('saveArticleBtn');
    if (saveArticleBtn) {
        saveArticleBtn.addEventListener('click', function() {
            saveArticle();
        });
    }
});

// 工具函数：防抖
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 实时保存草稿（防抖）
const saveDraft = debounce(function() {
    const text = document.getElementById('textInput').value;
    if (text.trim()) {
        localStorage.setItem('reading_draft', text);
    }
}, 1000);

// 恢复草稿
function restoreDraft() {
    const draft = localStorage.getItem('reading_draft');
    if (draft) {
        if (confirm('发现未保存的草稿，是否恢复？')) {
            document.getElementById('textInput').value = draft;
            const textInput = document.getElementById('textInput');
            textInput.style.height = 'auto';
            textInput.style.height = textInput.scrollHeight + 'px';
        } else {
            // 用户选择不恢复草稿，清除localStorage中的草稿
            localStorage.removeItem('reading_draft');
        }
    }
}

// 页面加载时恢复草稿
window.addEventListener('load', restoreDraft);

// 输入时保存草稿
document.getElementById('textInput').addEventListener('input', saveDraft);