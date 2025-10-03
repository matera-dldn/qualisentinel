import streamlit as st
from datetime import datetime
from modules.collector import get_prometheus_metrics
from modules.analyzer import analyze_metrics

st.set_page_config(layout="wide") # Opcional: Deixa o painel mais largo
st.title("QualiSentinel - Painel de Diagnóstico")

# -------------------------------------------------------------
# Controles de Auto Refresh (Sidebar)
# -------------------------------------------------------------
st.sidebar.header("Configurações")
TARGET_APP_HOST = st.sidebar.text_input("Host da Aplicação-Alvo", "http://localhost")
MANAGEMENT_PORT = st.sidebar.number_input("Porta de Gerenciamento (Actuator)", value=8088)

st.sidebar.header("Atualização Automática")
auto_refresh = st.sidebar.checkbox("Habilitar auto refresh", value=True)
intervalo_seg = st.sidebar.slider("Intervalo (segundos)", 5, 120, 60, 5)

if auto_refresh:
    st.markdown(f"<meta http-equiv='refresh' content='{intervalo_seg}'>", unsafe_allow_html=True)

st.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")

# URL completa do Actuator
management_url = f"{TARGET_APP_HOST.strip()}:{MANAGEMENT_PORT}"

st.info(f"Conectando aos endpoints de gerenciamento em: `{management_url}`")

# --- Coleta e Exibição ---
prometheus_data = get_prometheus_metrics(management_url)

if not prometheus_data:
    st.error("Não foi possível coletar as métricas do Prometheus. Verifique se a aplicação-alvo está no ar e as configurações de conexão estão corretas.")
    st.stop() # Interrompe a execução se não houver dados

# --- Dashboard de Métricas ---
st.header("Dashboard de Métricas em Tempo Real")
col1, col2, col3, col4 = st.columns(4)

# Formatação e exibição dos KPIs
cpu_usage = prometheus_data.get('system_cpu_usage', 0) * 100
mem_used_mb = prometheus_data.get('jvm_memory_used_bytes', 0) / 1024 / 1024
threads_blocked = int(prometheus_data.get('jvm_threads_states_blocked', 0))
db_pending = int(prometheus_data.get('hikaricp_connections_pending', 0))

col1.metric("Uso de CPU", f"{cpu_usage:.2f}%")
col2.metric("Memória JVM Utilizada", f"{mem_used_mb:.2f} MB")
col3.metric("Threads Bloqueadas", f"{threads_blocked}", help="Threads esperando por locks")
col4.metric("Threads na Fila do DB", f"{db_pending}", help="Threads esperando por uma conexão com o banco. > 0 é crítico.")

# --- Módulo de Análise ---
st.header("Análise e Diagnóstico QualiSentinel")
with st.spinner('Analisando métricas e aplicando heurísticas...'):
    analysis_result = analyze_metrics(prometheus_data)
    st.markdown(analysis_result, unsafe_allow_html=True)