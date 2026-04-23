#!/usr/bin/env bash
set -euo pipefail

REPO_OWNER="${REPO_OWNER:-yukkcat}"
REPO_NAME="${REPO_NAME:-gemini-business2api}"

DEFAULT_BRANCH="${BRANCH:-main}"
DEFAULT_INSTALL_DIR="${INSTALL_DIR:-/opt/gemini-business2api}"
DEFAULT_PORT="${PORT:-7860}"
DEFAULT_WITH_REFRESH="${WITH_REFRESH:-0}"
DEFAULT_MODE="${MODE:-}"
DEFAULT_ADMIN_KEY="${ADMIN_KEY:-}"
DEFAULT_DATABASE_URL="${DATABASE_URL:-}"
SHOW_HELP=0

UI_DEV="/dev/tty"

usage() {
  cat <<'EOF'
Gemini Business2API interactive installer

Usage:
  bash deploy/install.sh
  curl -fsSL https://raw.githubusercontent.com/yukkcat/gemini-business2api/main/deploy/install.sh | sudo bash
  curl -fsSL https://raw.githubusercontent.com/yukkcat/gemini-business2api/main/deploy/install.sh | sudo bash -s -- --with-refresh

Optional environment overrides:
  BRANCH=main
  INSTALL_DIR=/opt/gemini-business2api
  PORT=7860
  MODE=docker|python
  WITH_REFRESH=0|1
  ADMIN_KEY=your-admin-key
  DATABASE_URL=postgresql://...

Optional CLI flags:
  --mode docker|python
  --port 7860
  --install-dir /opt/gemini-business2api
  --branch main
  --admin-key your-admin-key
  --database-url postgresql://...
  --with-refresh
  --without-refresh
  --repo-owner yukkcat
  --repo-name gemini-business2api
  -h, --help
EOF
}

normalize_bool() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|y|Y|on|ON) printf '%s' "1" ;;
    0|false|FALSE|no|NO|n|N|off|OFF|"") printf '%s' "0" ;;
    *) return 1 ;;
  esac
}

validate_mode_value() {
  case "${1:-}" in
    docker|python|"") return 0 ;;
    *) return 1 ;;
  esac
}

parse_args() {
  local value=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        SHOW_HELP=1
        shift
        ;;
      --mode)
        value="${2:-}"
        if [[ -z "${value}" ]]; then
          echo "[ERROR] --mode requires a value." >&2
          exit 1
        fi
        DEFAULT_MODE="${value}"
        shift 2
        ;;
      --port)
        value="${2:-}"
        if [[ -z "${value}" ]]; then
          echo "[ERROR] --port requires a value." >&2
          exit 1
        fi
        DEFAULT_PORT="${value}"
        shift 2
        ;;
      --install-dir)
        value="${2:-}"
        if [[ -z "${value}" ]]; then
          echo "[ERROR] --install-dir requires a value." >&2
          exit 1
        fi
        DEFAULT_INSTALL_DIR="${value}"
        shift 2
        ;;
      --branch)
        value="${2:-}"
        if [[ -z "${value}" ]]; then
          echo "[ERROR] --branch requires a value." >&2
          exit 1
        fi
        DEFAULT_BRANCH="${value}"
        shift 2
        ;;
      --admin-key)
        value="${2:-}"
        if [[ -z "${value}" ]]; then
          echo "[ERROR] --admin-key requires a value." >&2
          exit 1
        fi
        DEFAULT_ADMIN_KEY="${value}"
        shift 2
        ;;
      --database-url)
        value="${2:-}"
        if [[ -z "${value}" ]]; then
          echo "[ERROR] --database-url requires a value." >&2
          exit 1
        fi
        DEFAULT_DATABASE_URL="${value}"
        shift 2
        ;;
      --repo-owner)
        value="${2:-}"
        if [[ -z "${value}" ]]; then
          echo "[ERROR] --repo-owner requires a value." >&2
          exit 1
        fi
        REPO_OWNER="${value}"
        shift 2
        ;;
      --repo-name)
        value="${2:-}"
        if [[ -z "${value}" ]]; then
          echo "[ERROR] --repo-name requires a value." >&2
          exit 1
        fi
        REPO_NAME="${value}"
        shift 2
        ;;
      --with-refresh)
        DEFAULT_WITH_REFRESH="1"
        shift
        ;;
      --without-refresh)
        DEFAULT_WITH_REFRESH="0"
        shift
        ;;
      *)
        echo "[ERROR] Unknown argument: $1" >&2
        usage >&2
        exit 1
        ;;
    esac
  done
}

ui_print() {
  printf '%s' "$*" >"${UI_DEV}"
}

ui_println() {
  printf '%s\n' "$*" >"${UI_DEV}"
}

prompt_input() {
  local label="$1"
  local default="${2-}"
  local answer=""

  if [[ -n "${default}" ]]; then
    ui_print "${label} [${default}]: "
  else
    ui_print "${label}: "
  fi

  IFS= read -r answer <"${UI_DEV}" || true
  if [[ -z "${answer}" ]]; then
    answer="${default}"
  fi
  printf '%s' "${answer}"
}

prompt_secret_allow_empty() {
  local label="$1"
  local answer=""

  ui_print "${label}: "
  stty -echo <"${UI_DEV}"
  IFS= read -r answer <"${UI_DEV}" || true
  stty echo <"${UI_DEV}"
  ui_println ""
  printf '%s' "${answer}"
}

confirm() {
  local label="$1"
  local default="${2:-Y}"
  local hint=""
  local answer=""

  case "${default}" in
    Y|y)
      hint="Y/n"
      default="y"
      ;;
    N|n)
      hint="y/N"
      default="n"
      ;;
    *)
      hint="y/n"
      default="n"
      ;;
  esac

  answer="$(prompt_input "${label} (${hint})" "")"
  if [[ -z "${answer}" ]]; then
    answer="${default}"
  fi

  [[ "${answer}" =~ ^[Yy]$ ]]
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    ui_println "[ERROR] Missing command: $1"
    exit 1
  fi
}

ensure_docker_compose() {
  need_cmd docker
  if ! docker compose version >/dev/null 2>&1; then
    ui_println "[ERROR] docker compose plugin not found."
    exit 1
  fi
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi

  need_cmd curl
  ui_println "[INFO] uv not found, installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:${PATH}"

  if ! command -v uv >/dev/null 2>&1; then
    ui_println "[ERROR] uv installation failed."
    exit 1
  fi
}

generate_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 24
  else
    head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n'
  fi
}

validate_port() {
  local port="$1"
  [[ "${port}" =~ ^[0-9]+$ ]] && (( port >= 1 && port <= 65535 ))
}

parse_args "$@"

if [[ "${SHOW_HELP}" == "1" ]]; then
  usage
  exit 0
fi

if ! validate_mode_value "${DEFAULT_MODE}"; then
  echo "[ERROR] MODE must be docker or python." >&2
  exit 1
fi

if ! DEFAULT_WITH_REFRESH="$(normalize_bool "${DEFAULT_WITH_REFRESH}")"; then
  echo "[ERROR] WITH_REFRESH must be 0/1/true/false." >&2
  exit 1
fi

if ! validate_port "${DEFAULT_PORT}"; then
  echo "[ERROR] PORT must be a number between 1 and 65535." >&2
  exit 1
fi

if [[ ! -r "${UI_DEV}" || ! -w "${UI_DEV}" ]]; then
  echo "[ERROR] This installer is interactive and requires a TTY." >&2
  exit 1
fi

port_in_use() {
  local port="$1"

  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]${port}$"
  elif command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
  elif command -v netstat >/dev/null 2>&1; then
    netstat -lnt 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]${port}$"
  else
    return 1
  fi
}

prompt_port() {
  local default="$1"
  local port=""

  while true; do
    port="$(prompt_input "服务端口" "${default}")"
    if ! validate_port "${port}"; then
      ui_println "[WARN] 端口必须是 1-65535 的数字。"
      continue
    fi

    if port_in_use "${port}"; then
      ui_println "[WARN] 检测到端口 ${port} 可能已被占用。"
      if confirm "仍然继续使用这个端口吗" "N"; then
        printf '%s' "${port}"
        return
      fi
      continue
    fi

    printf '%s' "${port}"
    return
  done
}

upsert_env_value() {
  local file="$1"
  local key="$2"
  local value="$3"
  local tmp
  local replaced=0

  tmp="$(mktemp)"
  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${line}" =~ ^[[:space:]#]*${key}= ]]; then
      printf '%s=%s\n' "${key}" "${value}" >>"${tmp}"
      replaced=1
    else
      printf '%s\n' "${line}" >>"${tmp}"
    fi
  done <"${file}"

  if [[ "${replaced}" -eq 0 ]]; then
    printf '\n%s=%s\n' "${key}" "${value}" >>"${tmp}"
  fi

  mv "${tmp}" "${file}"
}

prepare_env_file() {
  local project_root="$1"
  local admin_key="$2"
  local port="$3"
  local database_url="$4"

  if [[ ! -f "${project_root}/.env" ]]; then
    if [[ -f "${project_root}/.env.example" ]]; then
      cp "${project_root}/.env.example" "${project_root}/.env"
      ui_println "[INFO] Created ${project_root}/.env"
    else
      ui_println "[ERROR] Missing .env.example in ${project_root}"
      exit 1
    fi
  fi

  upsert_env_value "${project_root}/.env" "ADMIN_KEY" "${admin_key}"
  upsert_env_value "${project_root}/.env" "PORT" "${port}"
  upsert_env_value "${project_root}/.env" "DATABASE_URL" "${database_url}"
}

download_file() {
  local url="$1"
  local target="$2"
  local tmp="${target}.tmp"
  curl -fsSL "${url}" -o "${tmp}"
  mv "${tmp}" "${target}"
}

resolve_local_project_root() {
  local candidates=()
  local script_dir=""

  candidates+=("$(pwd)")

  if script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"; then
    candidates+=("$(cd "${script_dir}/.." >/dev/null 2>&1 && pwd)")
  fi

  for candidate in "${candidates[@]}"; do
    if [[ -f "${candidate}/docker-compose.yml" && -f "${candidate}/main.py" && -d "${candidate}/frontend" ]]; then
      printf '%s' "${candidate}"
      return
    fi
  done

  printf '%s' ""
}

venv_python_path() {
  local project_root="$1"

  if [[ -f "${project_root}/.venv/bin/python" ]]; then
    printf '%s' "${project_root}/.venv/bin/python"
  else
    printf '%s' "${project_root}/.venv/Scripts/python.exe"
  fi
}

print_banner() {
  ui_println ""
  ui_println "=========================================="
  ui_println "Gemini Business2API Interactive Installer"
  ui_println "=========================================="
  ui_println ""
}

choose_mode() {
  local default_mode="$1"
  local answer=""

  while true; do
    ui_println "请选择运行方式："
    ui_println "  1. Docker 部署（推荐）"
    ui_println "  2. Python 启动（开发/调试）"
    ui_println "  0. 退出"
    ui_println ""

    case "${default_mode}" in
      docker) answer="$(prompt_input "输入序号" "1")" ;;
      python) answer="$(prompt_input "输入序号" "2")" ;;
      *) answer="$(prompt_input "输入序号" "")" ;;
    esac

    case "${answer}" in
      1) printf '%s' "docker"; return ;;
      2) printf '%s' "python"; return ;;
      0) exit 0 ;;
      *) ui_println "[WARN] 请输入 0 / 1 / 2"; ui_println "" ;;
    esac
  done
}

run_docker_mode() {
  local local_root="$1"
  local project_root=""
  local branch="${DEFAULT_BRANCH}"
  local port=""
  local admin_key=""
  local database_url=""
  local with_refresh="${DEFAULT_WITH_REFRESH}"
  local install_dir=""
  local raw_base=""

  ui_println ""
  ui_println "== Docker 部署 =="

  if [[ -n "${local_root}" ]] && confirm "检测到当前仓库源码目录：${local_root}。直接使用当前目录部署吗" "Y"; then
    project_root="${local_root}"
  else
    need_cmd curl
    install_dir="$(prompt_input "Docker 安装目录" "${DEFAULT_INSTALL_DIR}")"
    branch="$(prompt_input "GitHub 分支" "${DEFAULT_BRANCH}")"
    raw_base="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${branch}"
    project_root="${install_dir}"

    ui_println "[INFO] 将从 GitHub 下载 compose 文件到：${project_root}"
    mkdir -p "${project_root}" "${project_root}/data"
    download_file "${raw_base}/docker-compose.yml" "${project_root}/docker-compose.yml"
    download_file "${raw_base}/.env.example" "${project_root}/.env.example"
  fi

  port="$(prompt_port "${DEFAULT_PORT}")"
  admin_key="$(prompt_secret_allow_empty "后台 ADMIN_KEY（留空自动生成）")"
  if [[ -z "${admin_key}" ]]; then
    admin_key="${DEFAULT_ADMIN_KEY}"
  fi
  if [[ -z "${admin_key}" ]]; then
    admin_key="$(generate_secret)"
  fi

  database_url="$(prompt_input "DATABASE_URL（留空使用 SQLite）" "${DEFAULT_DATABASE_URL}")"
  if confirm "是否启用 refresh-worker" "$( [[ "${with_refresh}" == "1" ]] && echo "Y" || echo "N" )"; then
    with_refresh="1"
  else
    with_refresh="0"
  fi

  prepare_env_file "${project_root}" "${admin_key}" "${port}" "${database_url}"

  ensure_docker_compose
  cd "${project_root}"

  ui_println "[INFO] Pulling images..."
  docker compose pull

  ui_println "[INFO] Starting services..."
  if [[ "${with_refresh}" == "1" ]]; then
    docker compose --profile refresh up -d
  else
    docker compose up -d
  fi

  ui_println ""
  ui_println "=========================================="
  ui_println "[OK] Docker deployment completed"
  ui_println "=========================================="
  ui_println "目录        : ${project_root}"
  ui_println "后台地址    : http://localhost:${port}/"
  ui_println "API 地址     : http://localhost:${port}/v1/chat/completions"
  ui_println "ADMIN_KEY   : ${admin_key}"
  if [[ -n "${database_url}" ]]; then
    ui_println "数据库      : PostgreSQL"
  else
    ui_println "数据库      : SQLite"
  fi
  if [[ "${with_refresh}" == "1" ]]; then
    ui_println "refresh     : enabled"
  else
    ui_println "refresh     : disabled"
  fi
  ui_println ""
  ui_println "常用命令："
  ui_println "  cd ${project_root}"
  ui_println "  docker compose ps"
  ui_println "  docker compose logs -f gemini-api"
  if [[ "${with_refresh}" == "1" ]]; then
    ui_println "  docker compose --profile refresh ps"
  fi
}

run_python_mode() {
  local local_root="$1"
  local project_root=""
  local port=""
  local admin_key=""
  local database_url=""
  local python_bin=""

  ui_println ""
  ui_println "== Python 启动 =="

  if [[ -z "${local_root}" ]]; then
    ui_println "[ERROR] Python 模式需要在仓库源码目录中运行。"
    ui_println "请先 git clone 仓库，然后执行：bash deploy/install.sh"
    exit 1
  fi

  project_root="${local_root}"
  ui_println "[INFO] 使用当前仓库源码目录：${project_root}"

  port="$(prompt_port "${DEFAULT_PORT}")"
  admin_key="$(prompt_secret_allow_empty "后台 ADMIN_KEY（留空自动生成）")"
  if [[ -z "${admin_key}" ]]; then
    admin_key="${DEFAULT_ADMIN_KEY}"
  fi
  if [[ -z "${admin_key}" ]]; then
    admin_key="$(generate_secret)"
  fi

  database_url="$(prompt_input "DATABASE_URL（留空使用 SQLite）" "${DEFAULT_DATABASE_URL}")"
  prepare_env_file "${project_root}" "${admin_key}" "${port}" "${database_url}"

  if confirm "是否安装 / 检查 uv" "Y"; then
    ensure_uv
    ui_println "[INFO] Ensuring Python 3.11 ..."
    uv python install 3.11
  fi

  if confirm "是否创建或复用 .venv" "Y"; then
    ensure_uv
    (cd "${project_root}" && uv venv --python 3.11 .venv)
  fi

  python_bin="$(venv_python_path "${project_root}")"
  if [[ ! -f "${python_bin}" ]]; then
    ui_println "[ERROR] 未找到虚拟环境 Python：${python_bin}"
    ui_println "请先执行“创建或复用 .venv”。"
    exit 1
  fi

  if confirm "是否安装 Python 依赖" "Y"; then
    ensure_uv
    (cd "${project_root}" && uv pip install --python "${python_bin}" -r requirements.txt)
  fi

  if confirm "是否构建前端" "Y"; then
    need_cmd npm
    (cd "${project_root}/frontend" && npm install && npm run build)
  fi

  ui_println ""
  ui_println "=========================================="
  ui_println "[OK] Python environment is ready"
  ui_println "=========================================="
  ui_println "目录        : ${project_root}"
  ui_println "后台地址    : http://localhost:${port}/"
  ui_println "API 地址     : http://localhost:${port}/v1/chat/completions"
  ui_println "ADMIN_KEY   : ${admin_key}"
  if [[ -n "${database_url}" ]]; then
    ui_println "数据库      : PostgreSQL"
  else
    ui_println "数据库      : SQLite"
  fi
  ui_println "Python      : ${python_bin}"
  ui_println ""

  if confirm "是否立即启动 python main.py" "Y"; then
    cd "${project_root}"
    exec "${python_bin}" main.py
  fi

  ui_println "后续启动命令："
  ui_println "  cd ${project_root}"
  ui_println "  ${python_bin} main.py"
}

main() {
  local local_root=""
  local mode=""

  print_banner
  local_root="$(resolve_local_project_root)"

  if [[ -n "${local_root}" ]]; then
    ui_println "[INFO] 已检测到本地仓库目录：${local_root}"
  else
    ui_println "[INFO] 当前目录未检测到完整仓库源码。"
  fi
  ui_println ""

  mode="$(choose_mode "${DEFAULT_MODE}")"
  case "${mode}" in
    docker) run_docker_mode "${local_root}" ;;
    python) run_python_mode "${local_root}" ;;
    *) ui_println "[ERROR] Unknown mode: ${mode}"; exit 1 ;;
  esac
}

main "$@"
