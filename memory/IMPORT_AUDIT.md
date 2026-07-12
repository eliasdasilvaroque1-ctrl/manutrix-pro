# IMPORT AUDIT — MAINTRIX Backend
**Data:** 2026-07-12 | **Escopo:** Todos os arquivos Python em /app/backend

---

## RESUMO

| Métrica | Valor |
|---|---|
| Arquivos Python varridos | 105 |
| Imports third-party encontrados | 20 |
| Cobertos pelo requirements.txt | **20/20 (100%)** |
| Lacunas encontradas | **0** |

---

## IMPORTS DIRETOS vs REQUIREMENTS.TXT

| Import Python | Pacote PyPI | No requirements.txt | Arquivos |
|---|---|---|---|
| `aiofiles` | aiofiles | ✅ | 4 |
| `bcrypt` | bcrypt | ✅ `>=4.3.0` | 1 |
| `docx` | python-docx | ✅ | 2 |
| `dotenv` | python-dotenv | ✅ | 5 |
| `emergentintegrations` | emergentintegrations | ✅ | 1 |
| `fastapi` | fastapi | ✅ | 12 |
| `jwt` | PyJWT | ✅ | 2 |
| `motor` | motor | ✅ | 5 |
| `openpyxl` | openpyxl | ✅ | 18 |
| `passlib` | passlib | ✅ | 1 |
| `pdfplumber` | pdfplumber | ✅ | 1 |
| `PIL` | pillow | ✅ `>=11.0.0` | 1 |
| `pydantic` | pydantic | ✅ | 4 |
| `pymongo` | pymongo | ✅ | 2 |
| `PyPDF2` | PyPDF2 | ✅ | 1 |
| `reportlab` | reportlab | ✅ | 25 |
| `requests` | requests | ✅ | 91 |
| `starlette` | starlette | ✅ | 1 |
| `supabase` | supabase | ✅ | 1 |
| `pytest` | pytest | ✅ `>=8.0.0` | 86 (testes) |

---

## DEPENDÊNCIAS IMPLÍCITAS (não importadas mas obrigatórias)

| Pacote | Motivo | No requirements.txt |
|---|---|---|
| `uvicorn` | Servidor ASGI — usado como CLI (`uvicorn server:app`) | ✅ |
| `python-multipart` | Requerido por FastAPI para `UploadFile`/`Form` | ✅ |
| `email-validator` | Requerido por Pydantic para `EmailStr` | ✅ |
| `dnspython` | Requerido por Motor/PyMongo para URIs `mongodb+srv://` | ✅ |
| `httpx` | Requerido por Supabase como HTTP client | ✅ |

---

## PACOTES REMOVIDOS DO requirements.txt (119 pacotes)

Todos eram dependências transitivas instaladas por `pip freeze`. Serão instalados automaticamente pelo pip ao resolver as dependências diretas.

### Dev Tools (não usados em produção)
| Pacote | Motivo da remoção |
|---|---|
| `black` | Formatador — não usado em runtime |
| `flake8`, `pycodestyle`, `pyflakes`, `mccabe` | Linter — não usado em runtime |
| `mypy`, `mypy_extensions` | Type checker — não usado em runtime |
| `isort` | Import sorter — não usado em runtime |

### AI/LLM (transitivos de emergentintegrations)
| Pacote | Motivo da remoção |
|---|---|
| `openai` | Transitivo de emergentintegrations |
| `litellm` | Transitivo de emergentintegrations |
| `tiktoken`, `tokenizers` | Transitivos de litellm |
| `google-genai`, `google-generativeai` | Transitivos de emergentintegrations |
| `google-api-core`, `google-api-python-client` | Transitivos de google-genai |
| `google-auth`, `google-auth-httplib2` | Transitivos de google-api |
| `googleapis-common-protos`, `grpcio`, `grpcio-status` | Transitivos de google-api |
| `proto-plus`, `protobuf` | Transitivos de grpcio |

### AWS (transitivos de emergentintegrations)
| Pacote | Motivo da remoção |
|---|---|
| `boto3`, `botocore`, `s3transfer`, `s5cmd` | Transitivos — não importados diretamente |

### Data Science (não importados)
| Pacote | Motivo da remoção |
|---|---|
| `numpy` | Não importado em nenhum arquivo |
| `pandas` | Não importado em nenhum arquivo |
| `lxml` | Não importado — pdfplumber usa internamente |

### Supabase (transitivos de supabase)
| Pacote | Motivo da remoção |
|---|---|
| `postgrest`, `storage3`, `realtime` | Transitivos do pacote supabase |
| `supabase-auth`, `supabase-functions` | Transitivos do pacote supabase |

### HTTP/Network (transitivos)
| Pacote | Motivo da remoção |
|---|---|
| `certifi`, `charset-normalizer`, `idna`, `urllib3` | Transitivos de requests |
| `anyio`, `h11`, `httpcore`, `sniffio` | Transitivos de httpx |
| `aiohttp`, `aiosignal`, `aiohappyeyeballs`, `frozenlist`, `multidict`, `yarl`, `propcache` | Transitivos de supabase/aiohttp |

### Outros transitivos
| Pacote | Motivo da remoção |
|---|---|
| `Jinja2`, `MarkupSafe` | Transitivos (não usados em templates) |
| `PyYAML` | Transitivo de huggingface_hub |
| `cryptography`, `cffi`, `pycparser` | Transitivos de supabase-auth |
| `click` | Transitivo de uvicorn |
| `et_xmlfile` | Transitivo de openpyxl |
| `pydantic_core`, `annotated-types`, `typing_extensions`, `typing-inspection` | Transitivos de pydantic |
| `pdfminer.six`, `pypdfium2` | Transitivos de pdfplumber |
| `stripe` | **NÃO importado** e não é transitivo — removido |
| `python-jose`, `ecdsa`, `rsa`, `pyasn1`, `pyasn1_modules` | Não importados — PyJWT é usado no lugar |
| `jq`, `jsonschema`, `jsonschema-specifications`, `referencing`, `rpds-py` | Transitivos |

---

## VERSÕES ALTERADAS

| Pacote | Antes | Depois | Motivo |
|---|---|---|---|
| `bcrypt` | `==4.1.3` | `>=4.3.0` | 4.1.3 falha no Python 3.13 (PyO3 desatualizado) |
| `pillow` | `==12.3.0` | `>=11.0.0` | Range flexível para compatibilidade cross-platform |
| `pytest` | `==9.0.2` | `>=8.0.0` | Range flexível para CI |

---

## REQUIREMENTS.TXT FINAL (26 pacotes)

```
# Web Framework
fastapi==0.110.1
starlette==0.37.2
uvicorn==0.25.0
python-multipart==0.0.22

# Database
motor==3.3.1
pymongo==4.5.0
dnspython==2.8.0

# Auth & Security
bcrypt>=4.3.0
passlib==1.7.4
PyJWT==2.13.0

# Data Validation
pydantic==2.12.5
email-validator==2.3.0

# HTTP Client
httpx==0.28.1
requests==2.32.5

# File Processing
aiofiles==25.1.0
pillow>=11.0.0
openpyxl==3.1.5
python-docx==1.2.0
PyPDF2==3.0.1
pdfplumber==0.11.10
reportlab==4.4.10

# Environment
python-dotenv==1.2.1

# Supabase
supabase==2.31.0

# Emergent Integrations
emergentintegrations==0.1.0

# Testing
pytest>=8.0.0
```

---

## VERIFICAÇÕES FINAIS

| Teste | Resultado |
|---|---|
| `pip install --dry-run` | ✅ Todas dependências resolvidas |
| Backend startup | ✅ Application startup complete |
| `CI=true yarn build` | ✅ Compiled successfully |
| Imports vs requirements | ✅ 20/20 cobertos (100%) |
| Implicit deps presentes | ✅ 5/5 (uvicorn, python-multipart, email-validator, dnspython, httpx) |

**Cobertura: 100%. Nenhum módulo importado ficou sem pacote correspondente no requirements.txt.**

---
*Auditoria gerada em 2026-07-12*
