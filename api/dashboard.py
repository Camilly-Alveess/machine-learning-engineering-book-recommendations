import streamlit as st
import requests
import pandas as pd
import altair as alt

API_URL = "https://techchalangerapi.onrender.com/api/v1/monitoring/dashboard"

st.set_page_config(page_title="Dashboard de Monitoramento", layout="wide")
st.title("📊 Dashboard de Monitoramento")

try:
    response = requests.get(API_URL)
    data = response.json()
except Exception as e:
    st.error(f"Erro ao conectar a API: {e}")
    st.stop()

st.subheader("🔹 Métricas Atuais")
metrics = data["current_metrics"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Requisições", metrics["total_requests"])
col2.metric("Taxa de Sucesso", f"{metrics['success_rate'] * 100:.2f}%")
col3.metric("Tempo Médio de Resposta", f"{metrics['avg_response_time']:.2f} ms")
col4.metric("Usuários Ativos", metrics["active_users"])

col5, col6, col7 = st.columns(3)
col5.metric("Erro 5xx", f"{metrics['error_rate_5xx'] * 100:.2f}%")
col6.metric("Erro 4xx", f"{metrics['error_rate_4xx'] * 100:.2f}%")
col7.metric("Logins Falhos", f"{metrics['failed_logins_rate'] * 100:.2f}%")

st.caption(f"📅 Última atualização: {metrics['current_timestamp']}")
st.caption(f"Fonte de dados: {metrics['data_source']}")

st.subheader("📈 Requisições por Hora")
requests_df = pd.DataFrame(data["historical_data"]["http_requests_timeline"])
# Garantir que existe uma coluna de timestamp antes de converter
if "timestamp" in requests_df.columns:
    requests_df["timestamp"] = pd.to_datetime(requests_df["timestamp"], errors="coerce")
else:
    # Tenta alternativas comuns
    alt_cols = ["created_at", "date", "datetime"]
    used = None
    for alt in alt_cols:
        if alt in requests_df.columns:
            requests_df["timestamp"] = pd.to_datetime(requests_df[alt], errors="coerce")
            st.warning(f"Coluna 'timestamp' não encontrada. Usando '{alt}' como timestamp.")
            used = alt
            break
    if used is None:
        # Tenta converter o índice para datetime
        try:
            requests_df["timestamp"] = pd.to_datetime(requests_df.index, errors="coerce")
            st.warning("Coluna 'timestamp' não encontrada. Convertendo índice para timestamp (valores inválidos ficarão NaT).")
        except Exception:
            # Cria coluna vazia com NaT para evitar crash e mostrar mensagem
            requests_df["timestamp"] = pd.NaT
            st.error("Coluna 'timestamp' não encontrada e não foi possível inferir; gráficos podem ficar vazios.")

chart = alt.Chart(requests_df).mark_line(point=True).encode(
    x="timestamp:T",
    y="requests_count:Q",
    tooltip=["timestamp", "requests_count"]
).properties(height=300)

st.altair_chart(chart, use_container_width=True)

st.subheader("⏱️ Tempos de Resposta (50, 95, 99)")
response_df = pd.DataFrame(data["historical_data"]["response_times_timeline"])
if "timestamp" in response_df.columns:
    response_df["timestamp"] = pd.to_datetime(response_df["timestamp"], errors="coerce")
else:
    # tenta alternativas e fallback similar ao requests_df
    alt_cols = ["created_at", "date", "datetime"]
    used = None
    for alt in alt_cols:
        if alt in response_df.columns:
            response_df["timestamp"] = pd.to_datetime(response_df[alt], errors="coerce")
            st.warning(f"Coluna 'timestamp' não encontrada em response_times_timeline. Usando '{alt}' como timestamp.")
            used = alt
            break
    if used is None:
        try:
            response_df["timestamp"] = pd.to_datetime(response_df.index, errors="coerce")
            st.warning("Convertendo índice para timestamp no response_df; valores inválidos ficarão NaT.")
        except Exception:
            response_df["timestamp"] = pd.NaT
            st.error("Coluna 'timestamp' não encontrada em response_times_timeline; gráficos podem ficar vazios.")
response_df = response_df.melt(id_vars=["timestamp"], var_name="percentil", value_name="tempo")

chart2 = alt.Chart(response_df).mark_line(point=True).encode(
    x="timestamp:T",
    y="tempo:Q",
    color="percentil:N",
    tooltip=["timestamp", "percentil", "tempo"]
).properties(height=300)

st.altair_chart(chart2, use_container_width=True)

st.subheader("🖥️ Uso de Sistema")
sys_df = pd.DataFrame(data["historical_data"]["system_metrics_timeline"])
if "timestamp" in sys_df.columns:
    sys_df["timestamp"] = pd.to_datetime(sys_df["timestamp"], errors="coerce")
else:
    # tenta conversão por alternativas
    alt_cols = ["created_at", "date", "datetime"]
    used = None
    for alt in alt_cols:
        if alt in sys_df.columns:
            sys_df["timestamp"] = pd.to_datetime(sys_df[alt], errors="coerce")
            st.warning(f"Coluna 'timestamp' não encontrada em system_metrics_timeline. Usando '{alt}' como timestamp.")
            used = alt
            break
    if used is None:
        try:
            sys_df["timestamp"] = pd.to_datetime(sys_df.index, errors="coerce")
            st.warning("Convertendo índice para timestamp no sys_df; valores inválidos ficarão NaT.")
        except Exception:
            sys_df["timestamp"] = pd.NaT
            st.error("Coluna 'timestamp' não encontrada em system_metrics_timeline; gráficos podem ficar vazios.")
sys_df = sys_df.melt(id_vars=["timestamp"], var_name="métrica", value_name="percentual")

sys_df["tempo_metrica"] = sys_df["timestamp"].dt.strftime("%H:%M") + " - " + sys_df["métrica"]

chart3 = alt.Chart(sys_df).mark_bar(size=10).encode(
    x=alt.X("tempo_metrica:N", title=None, axis=None),
    y=alt.Y("percentual:Q", title="Uso (%)"),
    color=alt.Color("métrica:N", title="Métrica"),
    tooltip=["timestamp", "métrica", "percentual"]
).properties(height=300)

st.altair_chart(chart3, use_container_width=True)

st.subheader("⚠️ Eventos de Erro")
errors = data["historical_data"]["error_events"]
if errors:
    st.write(pd.DataFrame(errors))
else:
    st.info("Nenhum evento de erro registrado no último dia.")