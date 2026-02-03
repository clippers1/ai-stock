/**
 * 底部导航栏组件
 */
import './BottomNav.css';

// 图标组件
const HomeIcon = ({ active }) => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
);

const ChartIcon = ({ active }) => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 3v18h18" />
        <path d="m19 9-5 5-4-4-3 3" />
    </svg>
);

const MessageIcon = ({ active }) => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
    </svg>
);

const navItems = [
    { id: 'recommendations', label: 'AI推荐', Icon: HomeIcon },
    { id: 'analysis', label: '股票分析', Icon: ChartIcon },
    { id: 'chat', label: 'AI对话', Icon: MessageIcon },
];

export default function BottomNav({ currentPage, onNavigate }) {
    return (
        <nav className="bottom-nav">
            {navItems.map(({ id, label, Icon }) => {
                const isActive = currentPage === id;
                return (
                    <button
                        key={id}
                        className={`nav-item ${isActive ? 'active' : ''}`}
                        onClick={() => onNavigate(id)}
                        aria-label={label}
                        aria-current={isActive ? 'page' : undefined}
                    >
                        <Icon active={isActive} />
                        <span className="nav-label">{label}</span>
                    </button>
                );
            })}
        </nav>
    );
}
