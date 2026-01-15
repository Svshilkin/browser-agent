# ========== BROWSER TIMEOUTS (milliseconds) ==========
BROWSER_LAUNCH_TIMEOUT = 30000
BROWSER_CLOSE_TIMEOUT = 10000
PAGE_LOAD_TIMEOUT = 30000
NAVIGATION_TIMEOUT = 30000
NETWORK_IDLE_TIMEOUT = 5000

# ========== ELEMENT INTERACTION TIMEOUTS ==========
ELEMENT_VISIBILITY_TIMEOUT = 10000
ELEMENT_FOCUS_TIMEOUT = 5000
ELEMENT_CLICK_TIMEOUT = 5000
TEXT_INPUT_TIMEOUT = 5000

# ========== LLM SETTINGS ==========
LLM_REQUEST_TIMEOUT = 60  # seconds
LLM_MAX_RETRIES = 3
LLM_RETRY_DELAY = 2  # seconds
LLM_CONTEXT_BUDGET = 4000  # tokens for context management

# ========== AGENT LOOP SETTINGS ==========
MAX_TOOL_USE_ITERATIONS = 20
MIN_ITERATIONS_FOR_SUCCESS = 1
ITERATION_TIMEOUT = 120  # seconds per iteration
TOOL_EXECUTION_TIMEOUT = 60  # seconds

# ========== SCREENSHOT SETTINGS ==========
SCREENSHOT_WIDTH = 1920
SCREENSHOT_HEIGHT = 1080
SCREENSHOT_QUALITY = 80  # percent
SCREENSHOT_FORMAT = "png"  # png or jpeg

# ========== PAGE ANALYSIS SETTINGS ==========
MAX_PAGE_CONTENT_LENGTH = 50000  # characters
MAX_INTERACTIVE_ELEMENTS = 100
ELEMENT_ANALYSIS_BATCH_SIZE = 20
SELECTOR_GENERATION_TIMEOUT = 5000

# ========== LOGGING SETTINGS ==========
LOG_FILE_MAX_SIZE = 10485760  # 10 MB
LOG_FILE_BACKUP_COUNT = 5
LOG_FORMAT_SIMPLE = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FORMAT_DETAILED = "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ========== ERROR HANDLING ==========
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_BASE = 1  # seconds, exponential backoff
RETRY_BACKOFF_MULTIPLIER = 2

# ========== TEXT PROCESSING ==========
TEXT_NORMALIZATION_ENABLED = True
TEXT_MAX_LENGTH = 10000
WORD_SPLIT_THRESHOLD = 50

# ========== API ENDPOINTS ==========
API_VERSION = "2024-01-15"
API_REGION = "global"

# ========== FEATURE FLAGS ==========
FEATURE_VISION_ENABLED = False
FEATURE_REQUEST_INTERCEPTION = False  # XHR/Fetch interception
FEATURE_MULTI_TAB = False  # Multi-tab support
FEATURE_SESSION_PERSISTENCE = False  # Session saving

# ========== DIRECTORY NAMES ==========
DIR_SCREENSHOTS = "screenshots"
DIR_LOGS = "logs"
DIR_CACHE = ".cache"
DIR_TESTS = "tests"
DIR_DOCS = "docs"
DIR_SCRIPTS = "scripts"
DIR_SRC = "src"

# ========== FILE EXTENSIONS ==========
EXT_ENV = ".env"
EXT_LOG = ".log"
EXT_SCREENSHOT = ".png"
EXT_CONFIG = ".toml"
EXT_PYTHON = ".py"

# ========== BROWSER USER AGENTS ==========
USER_AGENT_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

USER_AGENT_FIREFOX = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0)"
    " Gecko/20100101 Firefox/121.0"
)

USER_AGENT_SAFARI = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
    " (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
)

# ========== DEFAULT VALUES ==========
DEFAULT_LANGUAGE = "en"
DEFAULT_ENCODING = "utf-8"
DEFAULT_TIMEZONE = "UTC"

# ========== REGEX PATTERNS ==========
REGEX_URL = r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
REGEX_EMAIL = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
REGEX_PHONE = r"\+?[1-9]\d{1,14}"

# ========== SYSTEM MESSAGES ==========
SYSTEM_PROMPT_VERSION = "1.0"
SYSTEM_PROMPT_LANGUAGE = "en"

# ========== VERSION INFO ==========
APP_VERSION = "0.1.0"
PYTHON_VERSION_REQUIRED = "3.10"

# ========== Browser Type ==========
BROWSER_TYPE = "chromium"  # Options: chromium, firefox, webkit

# ========== Display Settings ==========
BROWSER_HEADLESS = True
BROWSER_VIEWPORT_WIDTH = 1280
BROWSER_VIEWPORT_HEIGHT = 720

# ========== Timeouts ==========
BROWSER_TIMEOUT = 30000  # 30 seconds
BROWSER_NAVIGATION_TIMEOUT_MS = 30000
BROWSER_ACTION_TIMEOUT_MS = 10000

# ========== User Agent ==========
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ========== Retry Settings ==========
BROWSER_MAX_RETRIES = 3
BROWSER_RETRY_DELAY = 2  # seconds, exponential backoff

# ========== Performance ==========
BROWSER_DISABLE_IMAGES = False
BROWSER_DISABLE_CSS = False
BROWSER_OFFLINE_MODE = False

# ========== Launch Arguments ==========
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
]
