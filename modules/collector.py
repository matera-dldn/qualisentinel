import requests

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
    Busca e parseia as métricas do endpoint /actuator/prometheus de forma robusta.
    Retorna um dicionário com métricas-chave agregadas.
    """
    try:
        response = requests.get(f"{target_url}/actuator/prometheus")
        response.raise_for_status()

        metrics = {
            'jvm_memory_used_bytes': 0.0,  # Inicializamos para poder somar
            'system_cpu_usage': 0.0,
            'http_server_requests_seconds_count': 0,
            'http_server_requests_seconds_max': 0.0,
        }
        lines = response.text.split('\n')

        for line in lines:
            # Ignorar linhas que não são dados de métricas
            if line.startswith('#') or not line.strip():
                continue

            try:
                parts = line.split()
                metric_name = parts[0]
                value = float(parts[-1]) # O valor é SEMPRE o último elemento

                # Agora, verificamos o nome da métrica e agregamos os valores
                if 'jvm_memory_used_bytes' in metric_name:
                    metrics['jvm_memory_used_bytes'] += value

                elif 'system_cpu_usage' in metric_name:
                    metrics['system_cpu_usage'] = value # Este valor é único

                elif 'http_server_requests_seconds_count' in metric_name:
                    metrics['http_server_requests_seconds_count'] += int(value)
                
                elif 'http_server_requests_seconds_max' in metric_name:
                    # Queremos o tempo máximo entre todos os endpoints
                    if value > metrics['http_server_requests_seconds_max']:
                        metrics['http_server_requests_seconds_max'] = value

            except (ValueError, IndexError):
                # Se uma linha não tiver o formato esperado, a ignoramos
                continue
        
        return metrics
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com a aplicação-alvo: {e}")
        return None