"""Configuração partilhada derivada do ambiente.

Fonte única da detecção de produção — não recalcular
`os.environ.get("ENVIRONMENT") == "production"` noutros módulos; importar
`IS_PROD` daqui. (Excepção: checks por-request deliberadamente dinâmicos,
como o HSTS no SecurityHeadersMiddleware, que os testes alternam em runtime.)

Carrega o .env aqui também (override=False, idempotente com database.py) para
que IS_PROD seja correcto independentemente da ordem de imports.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env", override=False)

IS_PROD = os.environ.get("ENVIRONMENT") == "production"
