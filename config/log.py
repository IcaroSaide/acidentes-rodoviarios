import logging as log
import warnings

warnings.filterwarnings('ignore')

# Configuração geral
log.basicConfig(
    level=log.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        log.FileHandler('log.log', mode='w', encoding='utf-8'),
        log.StreamHandler()]
)


# Funções personalizadas
def info(msg):
    log.info(f"[INFO] ✅ {msg}")

def warning(msg):
    log.warning(f"[WARNING] ⚠️ {msg}")

def error(msg):
    log.error(f"[ERROR] ❌ {msg}")