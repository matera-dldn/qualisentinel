def _run_heuristic_analysis(metrics: dict) -> list[str]:
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

    # Heurística 2: Gargalo no Acesso ao Banco de Dados
    # Se qualquer thread estiver esperando por uma conexão, é um problema crítico.
    if metrics.get('hikaricp_connections_pending', 0) > 0:
        suggestion = (
            "**Diagnóstico de Gargalo Crítico no Banco de Dados:** O pool de conexões com o banco está esgotado! "
            "Existem requisições ativas esperando para poderem executar queries.\n"
            "*Sugestão de Boas Práticas:* Esta é a causa mais provável da lentidão geral. Audite métodos com a anotação "
            "`@Transactional` para garantir que o escopo da transação seja o menor possível. Procure por "
            "consultas que possam estar causando problemas de `N+1`."
        )
        diagnostics.append(suggestion)

    # Heurística 3: Contenção de Threads
    # Um número elevado de threads bloqueadas indica gargalo de concorrência.
    if metrics.get('jvm_threads_states_blocked', 0) > 5:
        suggestion = (
            "**Diagnóstico de Contenção de Threads:** Um número significativo de threads está no estado 'blocked', "
            "indicando que elas estão competindo por recursos compartilhados (locks).\n"
            "*Sugestão de Boas Práticas:* Investigue seções do código que utilizam `synchronized` ou `ReentrantLock`. "
            "Considere usar estruturas de dados do pacote `java.util.concurrent` (ex: `ConcurrentHashMap`) "
            "para reduzir a contenção."
        )
        diagnostics.append(suggestion)

    if not diagnostics:
        diagnostics.append("Nenhum padrão de problema crítico foi detectado pelas heurísticas automáticas. O sistema parece operar dentro dos parâmetros normais.")

    return diagnostics

def analyze_metrics(metrics: dict) -> str:
    """
    Ponto de entrada do Módulo Analisador.
    Executa a análise heurística e formata um prompt completo e contextualizado
    para ser usado por um engenheiro de software para diagnóstico e refatoração.
    """
    if not metrics:
        return "## Análise QualiSentinel\n\nNão foi possível gerar a análise pois não há métricas disponíveis."

    diagnostics = _run_heuristic_analysis(metrics)
    
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
    
    formatted_diagnostics = "**Diagnósticos Automáticos (Heurísticas):**\n" + "\n\n".join(diagnostics)
    
    return prompt_header + prompt_context + formatted_metrics + formatted_diagnostics