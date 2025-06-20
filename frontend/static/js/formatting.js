/**
 * 阅读排版功能的JavaScript文件
 */

// 全局变量
let totalWords = 0;
let totalKeywords = 0;
let isPhoneticVisible = true;
let isMeaningVisible = true;
let isKeywordMeaningVisible = true;

// DOM元素
const textInput = document.getElementById('textInput');
const mainTitleInput = document.getElementById('mainTitle');
const subTitleInput = document.getElementById('subTitle');
const monthInput = document.getElementById('monthInput');
const dayInput = document.getElementById('dayInput');
const processBtn = document.getElementById('processBtn');
const clearBtn = document.getElementById('clearBtn');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const togglePhoneticBtn = document.getElementById('togglePhoneticBtn');
const toggleMeaningBtn = document.getElementById('toggleMeaningBtn');
const toggleKeywordMeaningBtn = document.getElementById('toggleKeywordMeaningBtn');
const articleContent = document.getElementById('articleContent');
const wordList = document.getElementById('wordList');
const previewMonth = document.getElementById('previewMonth');
const previewDay = document.getElementById('previewDay');
const previewMainTitle = document.getElementById('previewMainTitle');
const previewSubTitle = document.getElementById('previewSubTitle');
const totalWordsElement = document.getElementById('totalWords');
const totalKeywordsElement = document.getElementById('totalKeywords');
const wordModal = document.getElementById('wordModal');
const modalWord = document.getElementById('modalWord');
const modalPhonetic = document.getElementById('modalPhonetic');
const modalTranslation = document.getElementById('modalTranslation');
const pronounceBtn = document.getElementById('pronounceBtn');
const closeModalBtn = document.querySelector('.close');
const messageElement = document.getElementById('message');

// 初始化函数
function init() {
    // 设置当前日期
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    
    monthInput.value = month;
    dayInput.value = day;
    previewMonth.textContent = month;
    previewDay.textContent = day;
    
    // 添加事件监听器
    addEventListeners();
}

// 添加事件监听器
function addEventListeners() {
    // 标题输入事件
    mainTitleInput.addEventListener('input', function() {
        previewMainTitle.textContent = this.value || '请输入主标题';
    });
    
    subTitleInput.addEventListener('input', function() {
        previewSubTitle.textContent = this.value || '请输入副标题';
    });
    
    // 日期输入事件
    monthInput.addEventListener('input', function() {
        previewMonth.textContent = this.value || '';
    });
    
    dayInput.addEventListener('input', function() {
        previewDay.textContent = this.value || '';
    });
    
    // 按钮点击事件
    processBtn.addEventListener('click', processText);
    clearBtn.addEventListener('click', clearContent);
    exportPdfBtn.addEventListener('click', exportToPdf);
    
    // 切换显示事件
    togglePhoneticBtn.addEventListener('click', togglePhonetic);
    toggleMeaningBtn.addEventListener('click', toggleMeaning);
    toggleKeywordMeaningBtn.addEventListener('click', toggleKeywordMeaning);
    
    // 模态框事件
    closeModalBtn.addEventListener('click', closeModal);
    pronounceBtn.addEventListener('click', pronounceWord);
    
    // 文本拖放事件
    textInput.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('dragover');
    });
    
    textInput.addEventListener('dragleave', function() {
        this.classList.remove('dragover');
    });
    
    textInput.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'text/plain') {
            const reader = new FileReader();
            reader.onload = function(event) {
                textInput.value = event.target.result;
            };
            reader.readAsText(file);
        } else {
            showMessage('请拖放文本文件', 'error');
        }
    });
}

// 处理文本
async function processText() {
    const text = textInput.value.trim();
    if (!text) {
        showMessage('请输入英文文本', 'error');
        return;
    }
    
    try {
        showMessage('正在处理文本...', 'info');
        
        // 发送文本到后端处理
        const response = await fetch('/process_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 如果没有设置标题，使用生成的标题
            if (!mainTitleInput.value) {
                mainTitleInput.value = data.title;
                previewMainTitle.textContent = data.title;
            }
            
            // 显示处理后的文本和单词列表
            displayProcessedText(text);
            displayWordList(data.words);
            
            // 更新统计信息
            updateStats(text, data.words);
            
            showMessage('文本处理成功', 'success');
        } else {
            showMessage(data.message || '处理失败', 'error');
        }
    } catch (error) {
        console.error('处理文本时出错:', error);
        showMessage('处理文本时出错', 'error');
    }
}

// 显示处理后的文本
function displayProcessedText(text) {
    // 简单的文本处理，将文本分成段落并添加到内容区域
    const paragraphs = text.split('\n\n');
    
    let html = '';
    paragraphs.forEach(paragraph => {
        if (paragraph.trim()) {
            // 将段落中的单词用span包裹，以便后续添加样式和交互
            const words = paragraph.split(/\s+/);
            const processedWords = words.map(word => {
                // 提取单词和标点符号
                const match = word.match(/([a-zA-Z]+)([^a-zA-Z]*)/);
                if (match) {
                    const [, wordText, punctuation] = match;
                    return `<span class="article-word-container">
                        <span class="article-word-en">${wordText}</span>
                        ${punctuation ? punctuation : ''}
                    </span>`;
                }
                return `<span class="article-word-container">${word}</span>`;
            });
            
            html += `<p>${processedWords.join(' ')}</p>`;
        }
    });
    
    articleContent.innerHTML = html;
    
    // 为单词添加点击事件
    document.querySelectorAll('.article-word-en').forEach(word => {
        word.addEventListener('click', function() {
            showWordDetails(this.textContent);
        });
    });
}

// 显示单词列表
function displayWordList(words) {
    wordList.innerHTML = '';
    
    words.forEach(wordData => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div class="word-item">
                <div class="word-en">${wordData.word}</div>
                <div class="word-phonetic">${wordData.phonetic}</div>
                <div class="word-meaning">${wordData.translation}</div>
            </div>
        `;
        
        li.addEventListener('click', function() {
            showWordDetails(wordData.word, wordData.phonetic, wordData.translation);
        });
        
        wordList.appendChild(li);
    });
}

// 更新统计信息
function updateStats(text, keywords) {
    // 计算总单词数（简单实现，按空格分割）
    const words = text.match(/\b[a-zA-Z]+\b/g) || [];
    totalWords = words.length;
    totalKeywords = keywords.length;
    
    totalWordsElement.textContent = totalWords;
    totalKeywordsElement.textContent = totalKeywords;
}

// 显示单词详情
function showWordDetails(word, phonetic = '', translation = '') {
    modalWord.textContent = word;
    modalPhonetic.textContent = phonetic || `/${word}/`;
    modalTranslation.textContent = translation || `[${word}的翻译]`;
    
    wordModal.style.display = 'flex';
}

// 关闭模态框
function closeModal() {
    wordModal.style.display = 'none';
}

// 发音功能
function pronounceWord() {
    const word = modalWord.textContent;
    if (!word) return;
    
    const speech = new SpeechSynthesisUtterance(word);
    speech.lang = 'en-US';
    window.speechSynthesis.speak(speech);
}

// 切换音标显示
function togglePhonetic() {
    isPhoneticVisible = !isPhoneticVisible;
    document.body.classList.toggle('hide-phonetic', !isPhoneticVisible);
    togglePhoneticBtn.textContent = isPhoneticVisible ? '隐藏音标' : '显示音标';
    togglePhoneticBtn.classList.toggle('active', isPhoneticVisible);
}

// 切换中文意思显示
function toggleMeaning() {
    isMeaningVisible = !isMeaningVisible;
    document.body.classList.toggle('hide-meaning', !isMeaningVisible);
    toggleMeaningBtn.textContent = isMeaningVisible ? '隐藏中文' : '显示中文';
    toggleMeaningBtn.classList.toggle('active', isMeaningVisible);
}

// 切换正文重点词中文显示
function toggleKeywordMeaning() {
    isKeywordMeaningVisible = !isKeywordMeaningVisible;
    document.body.classList.toggle('hide-keyword-meaning', !isKeywordMeaningVisible);
    toggleKeywordMeaningBtn.textContent = isKeywordMeaningVisible ? '隐藏正文重点词中文' : '显示正文重点词中文';
    toggleKeywordMeaningBtn.classList.toggle('active', isKeywordMeaningVisible);
}

// 清空内容
function clearContent() {
    textInput.value = '';
    articleContent.innerHTML = '';
    wordList.innerHTML = '';
    totalWordsElement.textContent = '0';
    totalKeywordsElement.textContent = '0';
    showMessage('内容已清空', 'info');
}

// 导出为PDF
function exportToPdf() {
    if (!articleContent.innerHTML.trim()) {
        showMessage('没有内容可导出', 'error');
        return;
    }
    
    showMessage('正在准备导出PDF...', 'info');
    
    // 使用window.print()实现简单的PDF导出
    // 在实际应用中，可以使用专业的PDF生成库，如jsPDF或html2pdf
    setTimeout(() => {
        window.print();
    }, 500);
}

// 显示消息
function showMessage(message, type = 'info') {
    messageElement.textContent = message;
    messageElement.className = 'message';
    messageElement.classList.add(type);
    messageElement.classList.add('show');
    
    setTimeout(() => {
        messageElement.classList.remove('show');
    }, 3000);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);