import streamlit as st
from modules.collector import get_httptrace_data, get_prometheus_metrics
from modules.analyzer import analyze_metrics

st.title("QualiSentinel - Painel de Diagnóstico")

# URL base da aplicação-alvo
TARGET_APP_HOST = "http://localhost"
# Porta de gerenciamento do Actuator
MANAGEMENT_PORT = 8088

# URL completa do Actuator
management_url = f"{TARGET_APP_HOST}:{MANAGEMENT_PORT}"

st.info(f"Conectando aos endpoints de gerenciamento em: {management_url}")

st.header("Métricas do Prometheus")
prometheus_data = get_prometheus_metrics(management_url)
if prometheus_data:
    st.json(prometheus_data)
else:
    st.error("Não foi possível coletar as métricas do Prometheus. Verifique se a aplicação-alvo está no ar e o endpoint está acessível.")

st.header("HTTP Traces")
httptrace_data = get_httptrace_data(management_url)
if httptrace_data:
    st.dataframe(httptrace_data)
else:
    st.error("Não foi possível coletar os HTTP traces. Verifique se o endpoint '/actuator/httptrace' está exposto na configuração da aplicação-alvo.")


st.header("Análise e Diagnóstico QualiSentinel")
if prometheus_data:
    with st.spinner('Analisando métricas...'):
        analysis_result = analyze_metrics(prometheus_data)
        st.markdown(analysis_result)
else:
    st.warning("Análise não pode ser executada pois não há dados de métricas.")