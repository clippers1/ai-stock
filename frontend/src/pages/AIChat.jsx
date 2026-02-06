/**
 * AI对话页面 - 与AI助手交互
 */
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendChatMessage } from '../services/api';
import './AIChat.css';

// 图标组件
const SendIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m22 2-7 20-4-9-9-4Z" />
        <path d="M22 2 11 13" />
    </svg>
);

const MicIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
        <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
);

const BotIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 8V4H8" />
        <rect width="16" height="12" x="4" y="8" rx="2" />
        <path d="M2 14h2" />
        <path d="M20 14h2" />
        <path d="M15 13v2" />
        <path d="M9 13v2" />
    </svg>
);

const UserIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="5" />
        <path d="M20 21a8 8 0 0 0-16 0" />
    </svg>
);

export default function AIChat() {
    // 默认欢迎消息
    const defaultMessages = [
        {
            role: 'assistant',
            content: '您好！我是您的AI投资助手。我可以帮您分析股票、推荐投资机会、解答投资疑问。请问有什么可以帮您的？',
            timestamp: new Date().toISOString()
        }
    ];

    // 从localStorage恢复聊天记录
    const [messages, setMessages] = useState(() => {
        try {
            const saved = localStorage.getItem('ai_chat_messages');
            if (saved) {
                const parsed = JSON.parse(saved);
                return parsed.length > 0 ? parsed : defaultMessages;
            }
        } catch (e) {
            console.error('Failed to load chat history:', e);
        }
        return defaultMessages;
    });
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [suggestions, setSuggestions] = useState([
        '今日有什么推荐？',
        '分析一下NVDA',
        '大盘走势如何？'
    ]);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // 保存聊天记录到localStorage
    useEffect(() => {
        try {
            // 只保留最近50条消息
            const toSave = messages.slice(-50);
            localStorage.setItem('ai_chat_messages', JSON.stringify(toSave));
        } catch (e) {
            console.error('Failed to save chat history:', e);
        }
    }, [messages]);

    // 自动滚动到底部
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage = {
            role: 'user',
            content: input.trim(),
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await sendChatMessage(userMessage.content, messages);

            const assistantMessage = {
                role: 'assistant',
                content: response.reply,
                timestamp: new Date().toISOString()
            };

            setMessages(prev => [...prev, assistantMessage]);
            setSuggestions(response.suggestions || []);
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '抱歉，出现了一些问题。请稍后再试。',
                timestamp: new Date().toISOString()
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setInput(suggestion);
        inputRef.current?.focus();
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="page-container chat-page">
            {/* 顶部栏 */}
            <header className="chat-header">
                <div className="chat-avatar">
                    <BotIcon />
                </div>
                <div className="chat-info">
                    <h1>AI投资助手</h1>
                    <span className="status">在线</span>
                </div>
            </header>

            {/* 消息列表 */}
            <main className="messages-container">
                <div className="messages-list">
                    {messages.map((msg, index) => (
                        <div
                            key={index}
                            className={`message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
                        >
                            <div className="message-avatar">
                                {msg.role === 'user' ? <UserIcon /> : <BotIcon />}
                            </div>
                            <div className="message-content">
                                <div className="markdown-content">
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </div>
                                <span className="message-time">{formatTime(msg.timestamp)}</span>
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div className="message assistant-message">
                            <div className="message-avatar">
                                <BotIcon />
                            </div>
                            <div className="message-content">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </main>

            {/* 快捷建议 */}
            {suggestions.length > 0 && (
                <div className="suggestions-container">
                    <div className="suggestions-scroll">
                        {suggestions.map((suggestion, index) => (
                            <button
                                key={index}
                                className="suggestion-chip"
                                onClick={() => handleSuggestionClick(suggestion)}
                            >
                                {suggestion}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* 输入区域 */}
            <div className="input-container">
                <div className="input-wrapper">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="输入您的问题..."
                        className="chat-input"
                        disabled={loading}
                    />
                    <button
                        className="mic-button"
                        aria-label="语音输入"
                        disabled={loading}
                    >
                        <MicIcon />
                    </button>
                </div>
                <button
                    className={`send-button ${input.trim() ? 'active' : ''}`}
                    onClick={handleSend}
                    disabled={!input.trim() || loading}
                    aria-label="发送"
                >
                    <SendIcon />
                </button>
            </div>
        </div>
    );
}
