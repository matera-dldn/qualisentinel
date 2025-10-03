from typing import List, Dict, Any, Optional
from .collector import get_thread_dump, get_httptrace_data


def _run_heuristic_analysis(metrics: dict) -> List[str]:
    """
    Aplica um conjunto de regras heurísticas para diagnosticar problemas de performance
    com base nas métricas coletadas e retorna uma lista de diagnósticos textuais.
    """
    diagnostics = []

    # Heurística 1: Pressão de Memória e Atividade de Garbage Collection
    # Se o GC pausou por mais de 1 segundo no total, é um sinal de alerta.
    if metrics.get('jvm_gc_pause_seconds_sum', 0) > 1.0:
        suggestion = (
            "**Diagnóstico de Pressão de Memória:** A aplicação está gastando tempo excessivo em pausas de "
            "Garbage Collection. Isso é um forte indicativo de consumo ineficiente de memória ou memory leak.\n"
            "*Sugestão de Boas Práticas:* Investigue a criação de objetos pesados (como `new ModelMapper()`) "
            "dentro de loops. Verifique se coleções estáticas (`static List/Map`) estão crescendo indefinidamente."
        )
        diagnostics.append(suggestion)

    # Heurística 2: Gargalo no Acesso ao Banco de Dados + Repositórios mais lentos
    pending = metrics.get('hikaricp_connections_pending', 0)
    repo_timings = metrics.get('repository_timings') or []
    if pending > 0 or repo_timings:
        top_repos = []
        if repo_timings:
            for r in repo_timings[:5]:
                top_repos.append(
                    f"`{r['repository']}.{r['method']}` total={r['total_time_seconds']:.4f}s avg={r['avg_time_seconds']:.4f}s max={r['max_time_seconds']:.4f}s calls={r['invocations']}"
                )
        repos_text = ("\n**Repositórios mais custosos:**\n- " + "\n- ".join(top_repos)) if top_repos else ""
        suggestion = (
            "**Diagnóstico de Gargalo de Acesso a Dados:** "
            + ("Pool de conexões apresenta threads em espera. " if pending > 0 else "")
            + "Foi detectado custo relevante em chamadas de repositórios Spring Data." + repos_text + "\n"
            "*Boas Práticas:* Reduza escopos transacionais, avalie índices e normalize queries. Verifique padrões N+1 e prefira fetch joins adequados."
        )
        diagnostics.append(suggestion)

    # Heurística 3: Contenção de Threads
    # Um número elevado de threads bloqueadas indica gargalo de concorrência.
    if metrics.get('jvm_threads_states_blocked', 0) > 5:
        diagnostics.append("**Sinal de Contenção de Threads:** Threads em estado BLOCKED excedem o limiar.")

    if not diagnostics:
        diagnostics.append("Nenhum padrão de problema crítico foi detectado pelas heurísticas automáticas. O sistema parece operar dentro dos parâmetros normais.")

    return diagnostics

def _enrich_with_thread_dump(target_url: str, diagnostics: List[str]) -> None:
    """Coleta e extrai dados de threads bloqueadas acrescentando contexto ao diagnóstico."""
    td = get_thread_dump(target_url)
    if not td or 'threads' not in td:
        return
    blocked_details = []
    for th in td.get('threads', []):
        try:
            if th.get('threadState') != 'BLOCKED':
                continue
            name = th.get('threadName') or th.get('threadId')
            stack = th.get('stackTrace') or []
            # pega até as 2 primeiras frames significativas
            frames = []
            for fr in stack[:6]:
                cls = fr.get('className')
                meth = fr.get('methodName')
                line = fr.get('lineNumber')
                if cls and not cls.startswith('java.') and not cls.startswith('jdk.'):
                    frames.append(f"{cls}.{meth}:{line}")
                if len(frames) >= 2:
                    break
            if frames:
                blocked_details.append(f"Thread `{name}` bloqueada em: {' | '.join(frames)}")
        except Exception:
            continue
    if blocked_details:
        diagnostics.append("**Detalhes de Contenção (Thread Dump):**\n" + "\n".join(f"- {d}" for d in blocked_details))


def _enrich_with_httptrace(target_url: str, diagnostics: List[str]) -> None:
    traces = get_httptrace_data(target_url)
    if not traces:
        return
    slow_samples = []
    for tr in traces[:10]:
        try:
            req = tr.get('request', {})
            resp = tr.get('response', {})
            time_taken = tr.get('timeTaken') or tr.get('timeTakenMs') or 0
            if time_taken and time_taken > 500:  # >500ms
                slow_samples.append(f"{req.get('method')} {req.get('uri')} -> {resp.get('status')} {time_taken}ms")
        except Exception:
            continue
    if slow_samples:
        diagnostics.append("**HTTP Traces Lentos (amostras):**\n" + "\n".join(f"- {s}" for s in slow_samples))


def analyze_metrics(metrics: dict, target_url: Optional[str] = None) -> str:
    """
    Ponto de entrada do Módulo Analisador.
    Executa a análise heurística e formata um prompt completo e contextualizado
    para ser usado por um engenheiro de software para diagnóstico e refatoração.
    """
    if not metrics:
        return "## Análise QualiSentinel\n\nNão foi possível gerar a análise pois não há métricas disponíveis."

    diagnostics = _run_heuristic_analysis(metrics)

    # Enriquecimento Nível 2: Thread dump se contenção detectada
    if any('Contenção' in d or 'Thread' in d for d in diagnostics) and target_url:
        _enrich_with_thread_dump(target_url, diagnostics)

    # Enriquecimento Nível 3: HTTP trace (se disponível) - apenas se já temos URL
    if target_url:
        _enrich_with_httptrace(target_url, diagnostics)
    
    # Montagem do prompt final para o Gemini
    prompt_header = "## Análise de Performance QualiSentinel\n\n"
    prompt_context = (
        "Você é um engenheiro de software sênior especialista em performance de aplicações Java/Spring. "
        "Com base nas métricas de produção e nos diagnósticos automáticos a seguir, forneça uma análise técnica "
        "detalhada da causa raiz dos problemas e sugira refatorações de código específicas que um desenvolvedor "
        "deveria aplicar para resolver os gargalos.\n\n"
    )
    
    # Formatação das métricas e diagnósticos
    formatted_metrics = (
        "**Métricas de Diagnóstico:**\n"
        f"- Uso de CPU do Sistema: **{metrics.get('system_cpu_usage', 0):.2%}**\n"
        f"- Memória JVM Utilizada: **{metrics.get('jvm_memory_used_bytes', 0) / 1024 / 1024:.2f} MB**\n"
        f"- Tempo Total em Pausas de GC: **{metrics.get('jvm_gc_pause_seconds_sum', 0):.4f} segundos**\n"
        f"- Threads Aguardando Conexão com DB: **{int(metrics.get('hikaricp_connections_pending', 0))}**\n"
        f"- Threads Bloqueadas: **{int(metrics.get('jvm_threads_states_blocked', 0))}**\n\n"
    )
    
    formatted_diagnostics = "**Diagnósticos e Correlações:**\n" + "\n\n".join(diagnostics)
    
    return prompt_header + prompt_context + formatted_metrics + formatted_diagnostics