// 认证相关JavaScript

// 显示消息
function showMessage(message, type = 'info') {
    const messageEl = document.getElementById('message');
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
    messageEl.classList.add('show');
    
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, 3000);
}

// 切换到注册表单
function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

// 切换到登录表单
function showLogin() {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
}

// 登录表单处理
document.getElementById('loginFormElement').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showMessage('请填写完整的登录信息', 'error');
        return;
    }
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('登录成功，正在跳转...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
        } else {
            showMessage(data.message, 'error');
        }
    } catch (error) {
        showMessage('登录失败，请稍后重试', 'error');
        console.error('Login error:', error);
    }
});

// 注册表单处理
document.getElementById('registerFormElement').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // 表单验证
    if (!username || !email || !password || !confirmPassword) {
        showMessage('请填写完整的注册信息', 'error');
        return;
    }
    
    if (username.length < 3) {
        showMessage('用户名至少需要3个字符', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage('密码至少需要6个字符', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }
    
    // 邮箱格式验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage('请输入有效的邮箱地址', 'error');
        return;
    }
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('注册成功！请登录', 'success');
            // 清空表单
            document.getElementById('registerFormElement').reset();
            // 切换到登录表单
            setTimeout(() => {
                showLogin();
            }, 1500);
        } else {
            showMessage(data.message, 'error');
        }
    } catch (error) {
        showMessage('注册失败，请稍后重试', 'error');
        console.error('Register error:', error);
    }
});

// 输入框焦点效果
document.querySelectorAll('.input-group input').forEach(input => {
    input.addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
    });
    
    input.addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
    });
});

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查URL参数，如果有register参数则显示注册表单
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'register') {
        showRegister();
    }
    
    // 添加键盘事件监听
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const activeForm = document.querySelector('.form-container:not([style*="display: none"])');
            if (activeForm) {
                const submitBtn = activeForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.click();
                }
            }
        }
    });
});

// 密码强度检查
function checkPasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    return strength;
}

// 实时密码强度显示（可选功能）
document.getElementById('registerPassword').addEventListener('input', function() {
    const password = this.value;
    const strength = checkPasswordStrength(password);
    
    // 这里可以添加密码强度显示逻辑
    // 例如改变输入框边框颜色或显示强度指示器
});

// 防止表单重复提交
let isSubmitting = false;

function preventDoubleSubmit(formElement) {
    if (isSubmitting) {
        return false;
    }
    
    isSubmitting = true;
    
    // 禁用提交按钮
    const submitBtn = formElement.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
        
        // 3秒后重新启用
        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            isSubmitting = false;
        }, 3000);
    }
    
    return true;
}

// 为表单添加防重复提交
document.getElementById('loginFormElement').addEventListener('submit', function(e) {
    if (!preventDoubleSubmit(this)) {
        e.preventDefault();
    }
});

document.getElementById('registerFormElement').addEventListener('submit', function(e) {
    if (!preventDoubleSubmit(this)) {
        e.preventDefault();
    }
});