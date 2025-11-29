# FleetTrack - Sistema de Controle de Frotas 🚛

![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-yellow)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Django](https://img.shields.io/badge/Django-Framework-green)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange)

## 📖 Descrição

O **FleetTrack** é um sistema de gestão de frotas desenvolvido para otimizar o monitoramento e a administração de veículos. Utilizando tecnologia de rastreamento e dados analíticos, o sistema permite que empresas reduzam custos operacionais, melhorem a logística e aumentem a segurança da frota.

Este projeto foi desenvolvido como parte do curso de Engenharia de Software no Centro Universitário Católica de Santa Catarina.

## ⚙️ Funcionalidades

O sistema conta com diversos módulos para gestão completa:

* **Gestão de Veículos:**
    * Cadastro completo de veículos e manutenção.
    * Definição e acompanhamento de rotas.
* **Gestão de Motoristas:**
    * Cadastro e atualização de dados dos condutores.
* **Monitoramento:**
    * Visualização de dados operacionais em tempo real.
    * Integração com serviços de mapas (OpenRouteService/Google Maps) para planejamento de itinerários.
* **Painel Administrativo:**
    * Geração de relatórios de desempenho e custos.
    * Alertas automáticos para eventos críticos.

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python com Framework Django (Arquitetura MVT/MVC).
* **Frontend:** Django Templates, HTML5, CSS3, JavaScript.
* **Banco de Dados:** MySQL.
* **APIs Externas:** OpenRouteService / Google Maps API.
* **Deploy:** Google Cloud Platform (GCP).

## 🏗️ Arquitetura do Projeto

O projeto segue a arquitetura **MVC (Model-View-Controller)** e utiliza o modelo **C4** para documentação arquitetural.

## 🚀 Como executar o projeto

### Pré-requisitos
Antes de começar, precisas de ter instalado na tua máquina:
* [Python 3.x](https://www.python.org/)
* [MySQL](https://www.mysql.com/)

### Passo a passo

1.  **Clone o repositório**
    ```bash
    git clone [https://github.com/gabriel-kramos/fleettrack.git](https://github.com/gabriel-kramos/fleettrack.git)
    cd fleettrack
    ```

2.  **Crie e ative um ambiente virtual**
    ```bash
    # No Windows
    python -m venv venv
    venv\Scripts\activate

    # No Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure o Banco de Dados**
    * Crie um banco de dados no MySQL.
    * Configure as credenciais no arquivo `settings.py`.

5.  **Execute as migrações**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

6.  **Inicie o servidor**
    ```bash
    python manage.py runserver
    ```

7.  **Acesse o projeto**
    * Abra o navegador em: `http://127.0.0.1:8000`

---
