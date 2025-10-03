# QualiSentinel

Este documento fornece todas as instruções necessárias para configurar o ambiente de desenvolvimento e executar o protótipo.

## Pré-requisitos

Antes de começar, certifique-se de que você tem os seguintes softwares instalados em sua máquina:

* **Python 3.10+** (ou a versão específica que seu projeto usa)
* **Git**

## 1. Preparando o Ambiente

Siga estes passos para configurar o ambiente de desenvolvimento local. Estas instruções garantirão que o projeto rode em um ambiente isolado, sem interferir com outros projetos ou com a sua instalação global do Python.

### Passo 1: Clonar o Repositório

Primeiro, clone este repositório para a sua máquina local usando o seguinte comando no terminal:

```bash
git clone [https://github.com/matera-dldn/qualisentinel.git](https://github.com/matera-dldn/qualisentinel.git)
```

### Passo 2: Acessar a Pasta do Projeto

Navegue para a pasta que acabou de ser criada:

```bash
cd qualisentinel
```

### Passo 3: Criar e Ativar o Ambiente Virtual (`venv`)

Nós usaremos o `venv`, o gerenciador de ambientes virtuais padrão do Python, para isolar as dependências do projeto.

**1. Crie o ambiente:**

```bash
python3 -m venv venv
```

**2. Ative o ambiente:**

* **No macOS ou Linux:**
    ```bash
    source venv/bin/activate
    ```
* **No Windows (CMD ou PowerShell):**
    ```bash
    .\venv\Scripts\activate
    ```

> **Nota:** Após ativar, você verá `(venv)` no início da linha do seu terminal, indicando que o ambiente virtual está ativo.

### Passo 4: Instalar as Dependências

Com o ambiente ativo, instale todas as bibliotecas e pacotes necessários, que estão listados no arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

Pronto! Seu ambiente de desenvolvimento está configurado e pronto para uso.


## 2. Instruções de Execução

Com o ambiente preparado e ativo, rode a interface web baseada em Streamlit com o comando abaixo.

1. Inicie a aplicação Streamlit:

```bash
streamlit run app.py
```

2. (Opcional) Para escolher uma porta diferente ou outras opções do servidor:

```bash
streamlit run app.py --server.port 8501
```

3. Após o comando acima abrir, acesse a interface no seu navegador em `http://localhost:8501` (ou na porta indicada).

Notas:
- Este repositório usa Streamlit para o frontend e exibição de métricas. Os passos acima são suficientes para iniciar a aplicação.
- Se o comando `streamlit` não existir no ambiente, instale o pacote com `pip install streamlit` ou verifique o `requirements.txt`.

Executando com o helper script `run.sh` (opcional):

Se preferir um comando único que ativa o `venv` e inicia o Streamlit, use o script `run.sh` que vem na raiz do projeto.

```bash
# Torna o script executável (apenas na primeira vez):
chmod +x run.sh

# Executa com a porta padrão (8501):
./run.sh

# Executa em outra porta (ex.: 8888):
STREAMLIT_PORT=8888 ./run.sh
```

Observação: o `run.sh` pressupõe que o ambiente virtual está em `./venv`. Se o `venv` não existir, crie com `python3 -m venv venv` e instale as dependências.

---

## Autores

* **[Davi Lima]** - ([davi.neves@matera.com](mailto:davi.neves@matera.com))
* **[Vitor Carvalho]** - ([vitor.carvalho@matera.com](mailto:vitor.carvalho@matera.com))
* **[Arthur Ueta]** - ([arthur.ueta@matera.com](mailto:arthur.ueta@matera.com))