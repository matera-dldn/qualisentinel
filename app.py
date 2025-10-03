import streamlit as st
from datetime import datetime
from modules.collector import get_prometheus_metrics
from modules.analyzer import analyze_metrics

st.set_page_config(layout="wide")
st.title("QualiSentinel - Painel de Diagnóstico")

# --- CORREÇÃO DO BUG DO REFRESH: Inicializando o Session State ---
# Se o valor do intervalo ainda não foi definido na sessão, inicializamos com 60.
if 'intervalo_seg' not in st.session_state:
    st.session_state.intervalo_seg = 60

# -------------------------------------------------------------
# Controles (Sidebar)
# -------------------------------------------------------------
st.sidebar.header("Configurações")
TARGET_APP_HOST = st.sidebar.text_input("Host da Aplicação-Alvo", "http://localhost")
MANAGEMENT_PORT = st.sidebar.number_input("Porta de Gerenciamento (Actuator)", value=8088)

st.sidebar.header("Atualização Automática")
auto_refresh = st.sidebar.checkbox("Habilitar auto refresh", value=True)

# --- CORREÇÃO DO BUG DO REFRESH: Usando o 'key' para vincular ao Session State ---
# O 'key' faz com que o valor do slider seja automaticamente salvo em st.session_state.intervalo_seg
st.sidebar.slider(
    "Intervalo (segundos)", 
    min_value=5, 
    max_value=120, 
    key='intervalo_seg', # A chave que conecta ao session_state
    step=5
)

if auto_refresh:
    # Lemos o valor do session_state para garantir que ele persista após o refresh
    st.markdown(f"<meta http-equiv='refresh' content='{st.session_state.intervalo_seg}'>", unsafe_allow_html=True)

st.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')} (intervalo: {st.session_state.intervalo_seg}s)")

# URL completa do Actuator
management_url = f"{TARGET_APP_HOST.strip()}:{MANAGEMENT_PORT}"
st.info(f"Conectando aos endpoints de gerenciamento em: `{management_url}`")

# --- Coleta ---
prometheus_data = get_prometheus_metrics(management_url)
if not prometheus_data:
    st.error("Não foi possível coletar as métricas. Verifique a conexão com a aplicação-alvo.")
    st.stop()

# --- Dashboard de Métricas ---
st.header("Dashboard de Métricas em Tempo Real")
col1, col2, col3, col4 = st.columns(4)

cpu_usage = prometheus_data.get('system_cpu_usage', 0) * 100
mem_used_mb = prometheus_data.get('jvm_memory_used_bytes', 0) / 1024 / 1024
threads_blocked = int(prometheus_data.get('jvm_threads_states_blocked', 0))
db_pending = int(prometheus_data.get('hikaricp_connections_pending', 0))

col1.metric("Uso de CPU", f"{cpu_usage:.2f}%")
col2.metric("Memória JVM Utilizada", f"{mem_used_mb:.2f} MB")
col3.metric("Threads Bloqueadas", f"{threads_blocked}", help="Threads esperando por locks")
col4.metric("Threads na Fila do DB", f"{db_pending}", help="> 0 é crítico.")

# --- INSERÇÃO DO PAINEL DE DETALHES ---
with st.expander("Ver detalhes e evidências coletadas"):
    st.subheader("Timings de Repositórios Spring Data (Top 5 Mais Lentos)")
    repo_data = prometheus_data.get('repository_timings', [])
    if repo_data:
        st.dataframe(repo_data[:5])
    else:
        st.info("Nenhuma métrica de repositório foi coletada.")

    st.subheader("Todas as Métricas (Dados Brutos)")
    st.json(prometheus_data)

# --- Módulo de Análise ---
st.header("Análise e Diagnóstico QualiSentinel")
with st.spinner('Analisando métricas e aplicando heurísticas...'):
    analysis_result = analyze_metrics(prometheus_data, management_url)
    st.markdown(analysis_result, unsafe_allow_html=True)