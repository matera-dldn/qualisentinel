import os
from typing import Callable, Dict, Optional, Tuple

"""Módulo de Análise com chaveador estratégico multi-provedor.

Fluxo atual:
1. Coletamos métricas (dict) vindas do collector.
2. Tentamos usar um provedor de IA suportado (Gemini, OpenAI, mock) conforme variáveis de ambiente.
3. Se não houver chave ou ocorrer erro controlado -> geramos um prompt manual reutilizável.

Variáveis de ambiente suportadas:
  AI_PROVIDER            -> "gemini" | "openai" | "mock" | "auto" (default: auto)
  GEMINI_API_KEY         -> chave para Gemini (Google AI)
  OPENAI_API_KEY         -> chave para OpenAI (API pública ou Azure OpenAI *quando compatível*)
  AI_TEMPERATURE         -> (opcional) float (ex: 0.2)
  AI_MODEL               -> (opcional) nome do modelo (ex: "gpt-4o-mini", "gemini-1.5-flash")

Observação sobre GitHub Copilot:
  Copilot não é consumido diretamente por API pública para este tipo de análise runtime; ele atua no editor
  auxiliando geração/edição de código. Aqui estruturamos o código para você facilmente plugar provedores
  que possuam SDK/REST oficial.
"""

# ---------------------------------------------------------------------------
# Prompt base reutilizável (também usado quando chamamos o provedor)
# ---------------------------------------------------------------------------
def _build_base_prompt(metrics: dict) -> str:
    prompt_header = "### Análise de Performance de Aplicação Spring Boot\n\n"
    prompt_context = (
        "Analise as seguintes métricas de uma aplicação Java/Spring e forneça: \n"
        "1. Possíveis gargalos de performance (CPU, memória, IO, concorrência).\n"
        "2. Hipóteses de causa raiz.\n"
        "3. Sugestões de otimização específicas (métodos, padrões, configurações).\n"
        "4. Caso aplicável, refatorações de código ou ajustes de configuração JVM.\n\n"
    )
    # Tratamento robusto para valores ausentes/formatos
    system_cpu = metrics.get('system_cpu_usage')
    if isinstance(system_cpu, (int, float)):
        system_cpu_fmt = f"{system_cpu:.2%}"
    else:
        system_cpu_fmt = "N/A"

    jvm_mem_used = metrics.get('jvm_memory_used_bytes') or 0
    try:
        jvm_mem_fmt = f"{(float(jvm_mem_used) / 1024 / 1024):.2f} MB"
    except Exception:
        jvm_mem_fmt = "N/A"

    total_http = metrics.get('http_server_requests_seconds_count', 'N/A')
    http_max = metrics.get('http_server_requests_seconds_max')
    if isinstance(http_max, (int, float)):
        http_max_fmt = f"{http_max:.4f} s"
    else:
        http_max_fmt = "N/A"

    prompt_metrics = (
        "**Métricas Coletadas:**\n"
        f"- Uso de CPU do Sistema: {system_cpu_fmt}\n"
        f"- Total de Memória JVM Utilizada: {jvm_mem_fmt}\n"
        f"- Total de Requisições HTTP: {total_http}\n"
        f"- Tempo Máximo de Resposta HTTP: {http_max_fmt}\n\n"
    )
    prompt_footer = (
        "Com base nesses dados, qual a causa raiz mais provável para a lentidão? "
        "Liste pontos do código e configurações que deveriam ser investigados primeiro."
    )
    return prompt_header + prompt_context + prompt_metrics + prompt_footer


def _generate_prompt_for_manual_analysis(metrics: dict) -> str:
    """(Plano B) Gera prompt detalhado para uso manual em UI de um provedor."""
    print("Executando Plano B: Gerando prompt para análise manual.")
    return _build_base_prompt(metrics)


# ---------------------------------------------------------------------------
# Implementações de provedores (stubs/simples). Cada função retorna tuple(texto, provider_name)
# Em produção, substituir por chamadas reais ao SDK/REST.
# ---------------------------------------------------------------------------
def _run_with_gemini(metrics: dict) -> Tuple[str, str]:  # provider_name = "gemini"
    print("Executando Plano A (Gemini): Análise direta via API.")
    # TODO: Implementar chamada real quando o SDK estiver disponível.
    # Exemplo (pseudo):
    # import google.generativeai as genai
    # genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    # model = os.getenv('AI_MODEL', 'gemini-1.5-flash')
    # prompt = _build_base_prompt(metrics)
    # response = genai.GenerativeModel(model).generate_content(prompt)
    # return response.text, 'gemini'
    prompt = _build_base_prompt(metrics)
    simulated = (
        "[Gemini Stub] Diagnóstico: Alto consumo de CPU sustentado. Verificar índice de coleções, "
        "uso de paralelismo em `processOrder` e possíveis loops não otimizados."
    )
    return simulated + "\n\nPrompt Base Utilizado:\n" + prompt, 'gemini'


def _run_with_openai(metrics: dict) -> Tuple[str, str]:  # provider_name = "openai"
    print("Executando Plano A (OpenAI): Análise direta via API.")
    # TODO: Implementar chamada real (openai>=1.0). Pseudo-código:
    # from openai import OpenAI
    # client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # model = os.getenv('AI_MODEL', 'gpt-4o-mini')
    # prompt = _build_base_prompt(metrics)
    # completion = client.chat.completions.create(
    #     model=model,
    #     messages=[{"role": "system", "content": "Você é um especialista em performance Java."},
    #               {"role": "user", "content": prompt}],
    #     temperature=float(os.getenv('AI_TEMPERATURE', '0.2'))
    # )
    # text = completion.choices[0].message.content
    prompt = _build_base_prompt(metrics)
    simulated = (
        "[OpenAI Stub] Diagnóstico: Picos de latência correlacionados a GC longo. Considerar ajustar "
        "-Xms/-Xmx e habilitar G1GC se não estiver ativo. Revisar pool de threads do servlet."
    )
    return simulated + "\n\nPrompt Base Utilizado:\n" + prompt, 'openai'


def _run_with_mock(metrics: dict) -> Tuple[str, str]:
    print("Executando Plano A (Mock): Simulação offline.")
    prompt = _build_base_prompt(metrics)
    simulated = (
        "[Mock] Diagnóstico heurístico: CPU elevada possivelmente devido a agregações em memória "
        "e ausência de caching de resultados. Sugerir instrumentar métodos críticos com métricas adicionais."
    )
    return simulated + "\n\nPrompt Base Utilizado:\n" + prompt, 'mock'


ProviderFn = Callable[[dict], Tuple[str, str]]

_PROVIDERS: Dict[str, ProviderFn] = {
    'gemini': _run_with_gemini,
    'openai': _run_with_openai,
    'mock': _run_with_mock,
}


def _select_provider() -> Optional[str]:
    """Resolve qual provedor tentar baseado em AI_PROVIDER e chaves disponíveis."""
    explicit = (os.getenv('AI_PROVIDER') or 'auto').strip().lower()
    if explicit != 'auto':
        return explicit

    # Modo auto: escolher pela ordem de disponibilidade de chave
    if os.getenv('GEMINI_API_KEY'):
        return 'gemini'
    if os.getenv('OPENAI_API_KEY'):
        return 'openai'
    return None  # Sem chave -> prompt manual


def _has_key_for(provider: str) -> bool:
    if provider == 'gemini':
        return bool(os.getenv('GEMINI_API_KEY'))
    if provider == 'openai':
        return bool(os.getenv('OPENAI_API_KEY'))
    if provider == 'mock':
        return True  # mock não precisa de chave
    return False


def analyze_metrics(metrics: dict) -> str:
    """Ponto de entrada principal.

    Estratégia:
    1. Seleciona provedor (ou None) via _select_provider.
    2. Verifica chave (exceto mock); sem chave -> fallback manual.
    3. Executa provedor com tratamento de falhas controladas.
    4. Retorna string final (para manter compatibilidade). Pode embutir metadados.

    Futuro: poder retornar estrutura JSON (dict) com campos: {provider, mode, content}.
    """
    provider = _select_provider()

    if not provider or not _has_key_for(provider):
        return _generate_prompt_for_manual_analysis(metrics)

    fn = _PROVIDERS.get(provider)
    if not fn:
        return _generate_prompt_for_manual_analysis(metrics)

    try:
        content, used_provider = fn(metrics)
        return f"[provider={used_provider}]\n{content}"
    except Exception as ex:  # Robusto contra falhas de rede/SDK
        print(f"[WARN] Falha ao usar provedor '{provider}': {ex}. Fallback para prompt manual.")
        return _generate_prompt_for_manual_analysis(metrics)


# ---------------------------------------------------------------------------
# Helper opcional caso no futuro queiram forma estruturada
# ---------------------------------------------------------------------------
def analyze_metrics_structured(metrics: dict) -> dict:
    """Versão estruturada (não usada ainda pelo restante do app)."""
    provider = _select_provider()
    if not provider or not _has_key_for(provider):
        return {
            'mode': 'manual_prompt',
            'provider': None,
            'content': _generate_prompt_for_manual_analysis(metrics)
        }
    fn = _PROVIDERS.get(provider)
    if not fn:
        return {
            'mode': 'manual_prompt',
            'provider': None,
            'content': _generate_prompt_for_manual_analysis(metrics)
        }
    try:
        content, used = fn(metrics)
        return {'mode': 'ai', 'provider': used, 'content': content}
    except Exception as ex:
        return {
            'mode': 'manual_prompt',
            'provider': None,
            'error': str(ex),
            'content': _generate_prompt_for_manual_analysis(metrics)
        }
