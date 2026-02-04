/**
 * 主题上下文 - 管理深色/亮色主题切换
 * 支持localStorage持久化和系统偏好检测
 */
import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

// 主题选项
export const THEMES = {
    DARK: 'dark',
    LIGHT: 'light'
};

const STORAGE_KEY = 'ai_stock_theme';

export function ThemeProvider({ children }) {
    // 初始化主题：优先localStorage，其次系统偏好，默认深色
    const [theme, setTheme] = useState(() => {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored && (stored === THEMES.DARK || stored === THEMES.LIGHT)) {
            return stored;
        }
        // 检测系统偏好
        if (window.matchMedia?.('(prefers-color-scheme: light)').matches) {
            return THEMES.LIGHT;
        }
        return THEMES.DARK;
    });

    // 应用主题到DOM
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
    }, [theme]);

    // 监听系统主题变化
    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
        const handleChange = (e) => {
            // 仅在用户未手动设置时跟随系统
            const stored = localStorage.getItem(STORAGE_KEY);
            if (!stored) {
                setTheme(e.matches ? THEMES.LIGHT : THEMES.DARK);
            }
        };
        mediaQuery.addEventListener('change', handleChange);
        return () => mediaQuery.removeEventListener('change', handleChange);
    }, []);

    const toggleTheme = () => {
        setTheme(prev => prev === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK);
    };

    const value = {
        theme,
        setTheme,
        toggleTheme,
        isDark: theme === THEMES.DARK,
        isLight: theme === THEMES.LIGHT
    };

    return (
        <ThemeContext.Provider value={value}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}

export default ThemeContext;
