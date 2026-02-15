import { vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom';

// ============================================
// Firebase Mocks
// ============================================

// Mock Firebase Auth
vi.mock('firebase/auth', () => ({
  signInWithEmailAndPassword: vi.fn(),
  signOut: vi.fn(),
  onAuthStateChanged: vi.fn(),
  getAuth: vi.fn(() => ({})),
}));

// Mock Firebase Database
vi.mock('firebase/database', () => ({
  ref: vi.fn(),
  get: vi.fn(),
  set: vi.fn(),
  update: vi.fn(),
  remove: vi.fn(),
  push: vi.fn(() => ({ key: 'mock-key' })),
  query: vi.fn(),
  orderByChild: vi.fn(),
  equalTo: vi.fn(),
  onValue: vi.fn(),
  getDatabase: vi.fn(() => ({})),
}));

// Mock Firebase App
vi.mock('firebase/app', () => ({
  initializeApp: vi.fn(() => ({})),
  getApps: vi.fn(() => []),
  getApp: vi.fn(() => ({})),
}));

// Mock Firebase Functions
vi.mock('firebase/functions', () => ({
  getFunctions: vi.fn(() => ({})),
  httpsCallable: vi.fn(() => vi.fn()),
}));

// Mock Firebase Config
vi.mock('../config/firebase', () => ({
  auth: {
    currentUser: null,
  },
  database: {},
  functions: {},
}));

// ============================================
// Ant Design Icons Mock
// ============================================

vi.mock('@ant-design/icons', () => {
  const createMockIcon = name => {
    const MockIcon = _props => {
      // Return a span with the icon name for testing
      return `[${name}]`;
    };
    MockIcon.displayName = name;
    return MockIcon;
  };

  return {
    UserOutlined: createMockIcon('UserOutlined'),
    LockOutlined: createMockIcon('LockOutlined'),
    MailOutlined: createMockIcon('MailOutlined'),
    PhoneOutlined: createMockIcon('PhoneOutlined'),
    CheckCircleOutlined: createMockIcon('CheckCircleOutlined'),
    CloseCircleOutlined: createMockIcon('CloseCircleOutlined'),
    LoadingOutlined: createMockIcon('LoadingOutlined'),
    LogoutOutlined: createMockIcon('LogoutOutlined'),
    SettingOutlined: createMockIcon('SettingOutlined'),
    DashboardOutlined: createMockIcon('DashboardOutlined'),
    PrinterOutlined: createMockIcon('PrinterOutlined'),
    ClockCircleOutlined: createMockIcon('ClockCircleOutlined'),
    CrownOutlined: createMockIcon('CrownOutlined'),
    DeleteOutlined: createMockIcon('DeleteOutlined'),
    MoreOutlined: createMockIcon('MoreOutlined'),
    SearchOutlined: createMockIcon('SearchOutlined'),
    EyeOutlined: createMockIcon('EyeOutlined'),
    ReloadOutlined: createMockIcon('ReloadOutlined'),
    EditOutlined: createMockIcon('EditOutlined'),
    MinusCircleOutlined: createMockIcon('MinusCircleOutlined'),
    MessageOutlined: createMockIcon('MessageOutlined'),
    SendOutlined: createMockIcon('SendOutlined'),
    AppstoreOutlined: createMockIcon('AppstoreOutlined'),
    ShoppingCartOutlined: createMockIcon('ShoppingCartOutlined'),
    DollarOutlined: createMockIcon('DollarOutlined'),
    DesktopOutlined: createMockIcon('DesktopOutlined'),
    MenuUnfoldOutlined: createMockIcon('MenuUnfoldOutlined'),
    BankOutlined: createMockIcon('BankOutlined'),
    DownloadOutlined: createMockIcon('DownloadOutlined'),
    TeamOutlined: createMockIcon('TeamOutlined'),
    RocketOutlined: createMockIcon('RocketOutlined'),
    HomeOutlined: createMockIcon('HomeOutlined'),
    BugOutlined: createMockIcon('BugOutlined'),
    PlusOutlined: createMockIcon('PlusOutlined'),
    InfoCircleOutlined: createMockIcon('InfoCircleOutlined'),
    ExclamationCircleOutlined: createMockIcon('ExclamationCircleOutlined'),
    QuestionCircleOutlined: createMockIcon('QuestionCircleOutlined'),
    WarningOutlined: createMockIcon('WarningOutlined'),
    SaveOutlined: createMockIcon('SaveOutlined'),
    SyncOutlined: createMockIcon('SyncOutlined'),
    FilterOutlined: createMockIcon('FilterOutlined'),
    SortAscendingOutlined: createMockIcon('SortAscendingOutlined'),
    CalendarOutlined: createMockIcon('CalendarOutlined'),
    WifiOutlined: createMockIcon('WifiOutlined'),
    ApiOutlined: createMockIcon('ApiOutlined'),
    CloudOutlined: createMockIcon('CloudOutlined'),
    MenuFoldOutlined: createMockIcon('MenuFoldOutlined'),
    BellOutlined: createMockIcon('BellOutlined'),
    InboxOutlined: createMockIcon('InboxOutlined'),
    FileOutlined: createMockIcon('FileOutlined'),
    FolderOutlined: createMockIcon('FolderOutlined'),
    CopyOutlined: createMockIcon('CopyOutlined'),
    HistoryOutlined: createMockIcon('HistoryOutlined'),
    TagOutlined: createMockIcon('TagOutlined'),
    GiftOutlined: createMockIcon('GiftOutlined'),
    PercentageOutlined: createMockIcon('PercentageOutlined'),
    GlobalOutlined: createMockIcon('GlobalOutlined'),
    EnvironmentOutlined: createMockIcon('EnvironmentOutlined'),
    LaptopOutlined: createMockIcon('LaptopOutlined'),
    MobileOutlined: createMockIcon('MobileOutlined'),
    UserAddOutlined: createMockIcon('UserAddOutlined'),
    KeyOutlined: createMockIcon('KeyOutlined'),
    SafetyOutlined: createMockIcon('SafetyOutlined'),
    UpOutlined: createMockIcon('UpOutlined'),
    DownOutlined: createMockIcon('DownOutlined'),
    ThunderboltOutlined: createMockIcon('ThunderboltOutlined'),
    SafetyCertificateOutlined: createMockIcon('SafetyCertificateOutlined'),
    StarOutlined: createMockIcon('StarOutlined'),
    HeartOutlined: createMockIcon('HeartOutlined'),
    FireOutlined: createMockIcon('FireOutlined'),
    ThunderboltFilled: createMockIcon('ThunderboltFilled'),
    StopOutlined: createMockIcon('StopOutlined'),
  };
});

// ============================================
// Animation Libraries Mocks
// ============================================

// Mock framer-motion
vi.mock('framer-motion', () => {
  const React = require('react');

  // Create a mock motion value
  const createMockMotionValue = (initial = 0) => ({
    get: vi.fn(() => initial),
    set: vi.fn(),
    onChange: vi.fn(() => () => {}),
    isAnimating: vi.fn(() => false),
  });

  const createMotionComponent = tag => {
    const MotionComponent = React.forwardRef((props, ref) => {
      const {
        children,
        initial,
        animate,
        exit,
        whileHover,
        whileTap,
        whileInView,
        variants,
        transition,
        onAnimationComplete,
        drag,
        dragConstraints,
        ...rest
      } = props;
      return React.createElement(tag, { ...rest, ref }, children);
    });
    MotionComponent.displayName = `motion.${tag}`;
    return MotionComponent;
  };

  return {
    motion: {
      div: createMotionComponent('div'),
      span: createMotionComponent('span'),
      p: createMotionComponent('p'),
      h1: createMotionComponent('h1'),
      h2: createMotionComponent('h2'),
      h3: createMotionComponent('h3'),
      section: createMotionComponent('section'),
      button: createMotionComponent('button'),
      a: createMotionComponent('a'),
      ul: createMotionComponent('ul'),
      li: createMotionComponent('li'),
      img: createMotionComponent('img'),
      footer: createMotionComponent('footer'),
    },
    useScroll: vi.fn(() => ({
      scrollY: createMockMotionValue(0),
      scrollYProgress: createMockMotionValue(0),
    })),
    useTransform: vi.fn(() => createMockMotionValue(0)),
    useSpring: vi.fn(() => createMockMotionValue(0)),
    useMotionValue: vi.fn((initial = 0) => createMockMotionValue(initial)),
    useInView: vi.fn(() => true),
    AnimatePresence: ({ children }) => children,
  };
});

// Mock GSAP
vi.mock('gsap', () => ({
  gsap: {
    to: vi.fn(),
    from: vi.fn(),
    fromTo: vi.fn(),
    set: vi.fn(),
    timeline: vi.fn(() => ({
      to: vi.fn().mockReturnThis(),
      from: vi.fn().mockReturnThis(),
      fromTo: vi.fn().mockReturnThis(),
      add: vi.fn().mockReturnThis(),
      play: vi.fn(),
      pause: vi.fn(),
      kill: vi.fn(),
    })),
    registerPlugin: vi.fn(),
    context: vi.fn(() => ({
      revert: vi.fn(),
    })),
  },
  default: {
    to: vi.fn(),
    from: vi.fn(),
    fromTo: vi.fn(),
    set: vi.fn(),
    timeline: vi.fn(() => ({
      to: vi.fn().mockReturnThis(),
      from: vi.fn().mockReturnThis(),
      fromTo: vi.fn().mockReturnThis(),
      add: vi.fn().mockReturnThis(),
      play: vi.fn(),
      pause: vi.fn(),
      kill: vi.fn(),
    })),
    registerPlugin: vi.fn(),
    context: vi.fn(() => ({
      revert: vi.fn(),
    })),
  },
}));

// Mock GSAP ScrollTrigger
vi.mock('gsap/ScrollTrigger', () => ({
  ScrollTrigger: {
    create: vi.fn(),
    refresh: vi.fn(),
    getAll: vi.fn(() => []),
    kill: vi.fn(),
  },
  default: {
    create: vi.fn(),
    refresh: vi.fn(),
    getAll: vi.fn(() => []),
    kill: vi.fn(),
  },
}));

// ============================================
// Browser APIs Mocks
// ============================================

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// Mock localStorage
const localStorageMock = {
  store: {},
  getItem: vi.fn(key => localStorageMock.store[key] || null),
  setItem: vi.fn((key, value) => {
    localStorageMock.store[key] = String(value);
  }),
  removeItem: vi.fn(key => {
    delete localStorageMock.store[key];
  }),
  clear: vi.fn(() => {
    localStorageMock.store = {};
  }),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock matchMedia for responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver for Ant Design components
class ResizeObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

window.ResizeObserver = ResizeObserverMock;

// Mock Canvas for animated backgrounds
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  clearRect: vi.fn(),
  beginPath: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  stroke: vi.fn(),
  fillRect: vi.fn(),
  strokeRect: vi.fn(),
  fillText: vi.fn(),
  measureText: vi.fn(() => ({ width: 0 })),
  drawImage: vi.fn(),
  createLinearGradient: vi.fn(() => ({ addColorStop: vi.fn() })),
  createRadialGradient: vi.fn(() => ({ addColorStop: vi.fn() })),
  save: vi.fn(),
  restore: vi.fn(),
  translate: vi.fn(),
  rotate: vi.fn(),
  scale: vi.fn(),
  setTransform: vi.fn(),
}));

// Mock requestAnimationFrame
window.requestAnimationFrame = vi.fn(cb => setTimeout(cb, 16));
window.cancelAnimationFrame = vi.fn(id => clearTimeout(id));

// Mock scrollTo
window.scrollTo = vi.fn();

// Mock getComputedStyle for Ant Design
window.getComputedStyle = vi.fn(() => ({
  getPropertyValue: vi.fn(() => ''),
}));

// ============================================
// Console Suppression (optional - for cleaner test output)
// ============================================

// Suppress specific console messages during tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

console.error = (...args) => {
  // Suppress React Router future flag warnings
  if (args[0]?.includes?.('React Router Future Flag Warning')) return;
  // Suppress act() warnings that are sometimes false positives
  if (args[0]?.includes?.('not wrapped in act')) return;
  // Suppress Ant Design deprecation warnings
  if (args[0]?.includes?.('[antd:')) return;
  originalConsoleError.apply(console, args);
};

console.warn = (...args) => {
  // Suppress specific warnings if needed
  if (args[0]?.includes?.('componentWillReceiveProps')) return;
  // Suppress Ant Design deprecation warnings
  if (args[0]?.includes?.('[antd:')) return;
  if (args[0]?.includes?.('Warning: [antd')) return;
  originalConsoleWarn.apply(console, args);
};

// ============================================
// Test Utilities - Helper functions for tests
// ============================================

// Reset all mocks between tests
beforeEach(() => {
  vi.clearAllMocks();
  localStorageMock.clear();
});

// Export utilities for use in tests
export { localStorageMock };
