import requests
import re
from typing import List, Dict, Any, Optional

def get_httptrace_data(target_url: str):
    """
    Tenta coletar dados de traces HTTP a partir de possíveis endpoints do Actuator.
    Tenta, por ordem, /actuator/httptrace e /actuator/http-trace.

    Comportamento:
    - Se o endpoint responde com 200 e retorna JSON, tenta extrair uma lista de traces
      (procura por 'traces' ou aceita diretamente uma lista JSON).
    - Se receber 404, ignora e tenta o próximo endpoint.
    - Se não houver nenhum endpoint disponível retorna uma lista vazia (significando
      que os traces não estão expostos). Se houver erro de conexão/timeout retorna None.
    """
    endpoints = ["/actuator/httptrace", "/actuator/http-trace"]

    for ep in endpoints:
        url = f"{target_url}{ep}"
        try:
            resp = requests.get(url, timeout=5)
        except requests.exceptions.RequestException as e:
            # Erro de conexão/timeout/etc — consideramos falha de coleta
            print(f"Erro ao conectar com a aplicação-alvo em {url}: {e}")
            return None

        # Se não existe, tentamos o próximo endpoint
        if resp.status_code == 404:
            # endpoint não exposto; tentar próxima opção
            continue

        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Para códigos 4xx/5xx diferentes de 404 retornamos None (problema)
            print(f"Resposta inesperada de {url}: {resp.status_code} - {e}")
            return None

        # Tentar parsear JSON — alguns endpoints retornam {'traces': [...]} outros podem
        # retornar diretamente uma lista.
        try:
            data = resp.json()
        except ValueError:
            print(f"Resposta de {url} não é JSON conforme esperado")
            return None

        if isinstance(data, dict) and 'traces' in data:
            return data.get('traces', [])

        if isinstance(data, list):
            return data

        # Caso seja um dicionário com outra forma, tentar heurísticas simples
        # (por exemplo: {'content': [...]})
        if isinstance(data, dict):
            for key in ('content', 'items', 'values'):
                if key in data and isinstance(data[key], list):
                    return data[key]

        # Não reconhecemos o formato — retornar lista vazia (endpoint presente, mas sem traces)
        return []
    

def get_prometheus_metrics(target_url: str):
    """
    Busca e parseia um conjunto expandido de métricas do endpoint /actuator/prometheus,
    focando em dados que permitem um diagnóstico profundo de performance.
    """
    try:
        response = requests.get(f"{target_url}/actuator/prometheus", timeout=5)
        response.raise_for_status()

        # Estrutura de dados expandida para métricas de diagnóstico
        metrics = {
            'jvm_memory_used_bytes': 0.0,
            'system_cpu_usage': 0.0,
            'http_server_requests_seconds_count': 0,
            'http_server_requests_seconds_max': 0.0,
            'jvm_gc_pause_seconds_count': 0,
            'jvm_gc_pause_seconds_sum': 0.0,
            'hikaricp_connections_active': 0.0,
            'hikaricp_connections_pending': 0.0,
            'hikaricp_connections_timeout_total': 0.0,
            'jvm_threads_states_blocked': 0.0,
            'logback_events_error_total': 0.0,
            # Novo: timings de repositórios Spring Data
            'repository_timings': []
        }
        # Acumuladores temporários para métricas de repositório
        repo_acc: Dict[str, Dict[str, float]] = {}
        repo_pattern = re.compile(r'^spring_data_repository_invocations_seconds_(sum|count|max)\{([^}]*)\}')
        lines = response.text.split('\n')

        for line in lines:
            if line.startswith('#') or not line.strip():
                continue

            try:
                parts = line.split()
                metric_name = parts[0]
                value = float(parts[-1])

                # Parsing específico para métricas de repositório Spring Data
                m = repo_pattern.match(metric_name)
                if m:
                    kind = m.group(1)  # sum | count | max
                    labels_raw = m.group(2)
                    labels = {}
                    for pair in labels_raw.split(','):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            labels[k.strip()] = v.strip().strip('"')
                    repo = labels.get('repository') or labels.get('repo') or 'unknown'
                    method = labels.get('method') or 'unknown'
                    key = f"{repo}:{method}"
                    entry = repo_acc.setdefault(key, {
                        'repository': repo,
                        'method': method,
                        'sum': 0.0,
                        'count': 0.0,
                        'max': 0.0,
                    })
                    if kind == 'sum':
                        entry['sum'] += value
                    elif kind == 'count':
                        entry['count'] += value
                    elif kind == 'max' and value > entry['max']:
                        entry['max'] = value
                    # Próxima linha
                    continue

                # Mapeamento robusto de outras métricas-chave para a nossa estrutura
                if 'jvm_memory_used_bytes' in metric_name:
                    metrics['jvm_memory_used_bytes'] += value
                elif 'system_cpu_usage' in metric_name:
                    metrics['system_cpu_usage'] = value
                elif 'http_server_requests_seconds_count' in metric_name:
                    metrics['http_server_requests_seconds_count'] += int(value)
                elif 'http_server_requests_seconds_max' in metric_name and value > metrics['http_server_requests_seconds_max']:
                    metrics['http_server_requests_seconds_max'] = value
                
                # Coleta das novas métricas de diagnóstico
                elif 'jvm_gc_pause_seconds_count' in metric_name:
                    metrics['jvm_gc_pause_seconds_count'] += int(value)
                elif 'jvm_gc_pause_seconds_sum' in metric_name:
                    metrics['jvm_gc_pause_seconds_sum'] += value
                elif 'hikaricp_connections_active' in metric_name:
                    metrics['hikaricp_connections_active'] = value
                elif 'hikaricp_connections_pending' in metric_name:
                    metrics['hikaricp_connections_pending'] = value
                elif 'hikaricp_connections_timeout_total' in metric_name:
                    metrics['hikaricp_connections_timeout_total'] += int(value)
                elif 'jvm_threads_states_threads' in metric_name and 'state="blocked"' in metric_name:
                    metrics['jvm_threads_states_blocked'] = value
                elif 'logback_events_total' in metric_name and 'level="error"' in metric_name:
                    metrics['logback_events_error_total'] += int(value)

            except (ValueError, IndexError):
                continue
        
        # Finaliza lista de repository_timings
        if repo_acc:
            repo_list = []
            for entry in repo_acc.values():
                count = entry['count'] or 0.0
                avg = entry['sum'] / count if count > 0 else 0.0
                repo_list.append({
                    'repository': entry['repository'],
                    'method': entry['method'],
                    'total_time_seconds': entry['sum'],
                    'invocations': int(count),
                    'avg_time_seconds': avg,
                    'max_time_seconds': entry['max'],
                })
            # Ordena por total_time desc para facilitar heurística
            repo_list.sort(key=lambda r: r['total_time_seconds'], reverse=True)
            metrics['repository_timings'] = repo_list

        return metrics
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com a aplicação-alvo: {e}")
        return None


def get_thread_dump(target_url: str) -> Optional[Dict[str, Any]]:
    """Coleta o thread dump via /actuator/threaddump.

    Retorna o JSON (dict) ou None em caso de falha.
    """
    url = f"{target_url}/actuator/threaddump"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Falha ao coletar thread dump: {e}")
        return None
    except ValueError:
        print("Resposta de thread dump não era JSON válido")
        return None