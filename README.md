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

Com o ambiente preparado e ativo, siga as instruções abaixo para executar o protótipo.

### **Opção A: Para um script de linha de comando (CLI)**

Execute o arquivo principal do projeto:

```bash
python3 main.py
```
### **Opção B: Para uma aplicação web (Flask, Django, etc.)**

**1. Configure as variáveis de ambiente (se necessário):**
```bash
# No macOS ou Linux
export FLASK_APP=app.py
export FLASK_ENV=development

# No Windows (CMD)
set FLASK_APP=app.py
set FLASK_ENV=development
```

**2. Inicie o servidor de desenvolvimento:**
```bash
flask run
```
```bash
python manage.py runserver
```

Após iniciar, acesse a aplicação no seu navegador em `http://127.0.0.1:5000` (ou a porta informada no terminal).

### **Opção C: Para executar os testes automatizados**

Para garantir que tudo está funcionando corretamente, você pode rodar a suíte de testes do projeto com o comando:

```bash
# Exemplo usando pytest
pytest
```

---

## (Opcional) Autores

* **[Seu Nome]** - ([seu-email@exemplo.com](mailto:seu-email@exemplo.com))