# 🤖 Backend Agente - Sistema de IA para WhatsApp

Sistema completo de agentes de IA especializados para verificação de cobranças e detecção de fraudes via WhatsApp.

## 🎯 **Visão Geral**

Este projeto implementa um sistema multi-agente de IA que utiliza WhatsApp como interface para verificar a autenticidade de boletos, cobranças e transações PIX, detectando possíveis fraudes em tempo real.

## 🧠 **Arquitetura dos Agentes**

### **🔍 Agente Leitor**
- Extrai dados de boletos e documentos usando OCR
- Processa informações de PIX e transações
- Utiliza NLP para entender textos complexos

### **📊 Agente Consultor**
- Verifica dados nos sistemas Bemobi
- Valida beneficiários e valores
- Consulta histórico do cliente

### **🛡️ Agente Detetive**
- Detecta padrões de fraude conhecidos
- Analisa comportamentos suspeitos
- Identifica tentativas de golpe

### **📋 Agente Orquestrador**
- Consolida todas as análises
- Gera pontuação de confiança
- Define status final da verificação

## 🚀 **Funcionalidades**

- ✅ **Verificação Automática** de boletos e PIX
- ✅ **Detecção de Fraudes** em tempo real
- ✅ **Interface WhatsApp** nativa com botões
- ✅ **Respostas Automáticas** para demonstrações
- ✅ **Sistema Multi-Agente** especializado
- ✅ **Análise de Imagens** com OCR
- ✅ **Processamento de Texto** com NLP

## 📁 **Estrutura do Projeto**

```
backend_agente/
├── wpp-bot/                    # Sistema WhatsApp principal
│   ├── app/                    # Código da aplicação
│   │   ├── api/               # Endpoints da API
│   │   ├── services/           # Serviços (IA, WhatsApp, etc.)
│   │   ├── models/             # Modelos de dados
│   │   └── utils/              # Utilitários
│   ├── main.py                 # Servidor principal
│   ├── requirements.txt        # Dependências Python
│   └── docker-compose.yml      # Configuração Docker
├── tests/                      # Arquivos de teste e exemplos
└── README.md                   # Este arquivo
```

## 🛠️ **Tecnologias Utilizadas**

### **Backend**
- **Python 3.9+**
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **PostgreSQL** - Banco de dados
- **Groq API** - Modelos de IA
- **OpenCV** - Processamento de imagens
- **Tesseract** - OCR

### **IA e Machine Learning**
- **Groq API** - Modelos de linguagem
- **OpenCV** - Visão computacional
- **Tesseract** - Reconhecimento óptico
- **NLP** - Processamento de linguagem natural

### **WhatsApp Integration**
- **WhatsApp Business API**
- **Webhooks** para recebimento
- **Botões interativos** nativos
- **Mensagens automáticas**

## 🚀 **Instalação e Configuração**

### **1. Pré-requisitos**
```bash
# Python 3.9+
python --version

# PostgreSQL
# Node.js (para interface web)
```

### **2. Instalação**
```bash
# Clone o repositório
git clone <repository-url>
cd backend_agente

# Instale as dependências
cd wpp-bot
pip install -r requirements.txt
```

### **3. Configuração**
```bash
# Copie o arquivo de exemplo
cp tests/env.example .env

# Configure as variáveis
GROQ_API_KEY=sua_chave_aqui
WHATSAPP_TOKEN=seu_token_aqui
DATABASE_URL=postgresql://user:pass@localhost/db
```

### **4. Execução**
```bash
# Inicie o servidor
cd wpp-bot
python main.py

# Ou com Docker
docker-compose up
```

## 📱 **Como Usar**

### **1. Envie uma mensagem para o WhatsApp**
```
Oi
```

### **2. Escolha uma opção**
- 🎬 **Demo IA** - Demonstração completa
- 🔍 **Verificar** - Verificar cobrança
- 🤖 **Sobre Agentes** - Informações dos agentes

### **3. Envie sua cobrança**
- 📷 **Foto do boleto**
- 📄 **Dados do PIX**
- 📋 **Informações da cobrança**

### **4. Receba a análise**
- ✅ **SEGURO** - Pode pagar
- ⚠️ **SUSPEITO** - Verificar com suporte
- 🚨 **GOLPE** - Não pagar

## 🎬 **Sistema de Demonstração**

O sistema inclui um modo automático para gravação de vídeos:

- **Respostas pré-definidas** para demonstrações
- **Análises simuladas** com dados reais
- **Fluxo completo** para apresentações
- **Resultados aleatórios** (Seguro/Suspeito/Golpe)

## 🔧 **Desenvolvimento**

### **Estrutura dos Serviços**
```
app/services/
├── ai_service.py              # Serviço principal de IA
├── fluxo_bemobi.py            # Fluxo interativo
├── fluxo_bemobi_automatico.py # Fluxo para demonstrações
├── agente_leitor.py           # Agente de leitura
├── agente_consultor.py        # Agente consultor
├── agente_detetive.py         # Agente detetive
├── agente_orquestrador.py     # Agente orquestrador
└── whatsapp.py                # Serviço WhatsApp
```

### **Endpoints da API**
```
/api/v1/
├── /webhook/verify            # Webhook WhatsApp
├── /verificar-cobranca        # Verificar cobrança
├── /processar-resposta        # Processar resposta
├── /mensagem-inicial          # Mensagem inicial
└── /estatisticas              # Estatísticas do sistema
```

## 📊 **Monitoramento**

- **Logs detalhados** de todas as operações
- **Métricas de performance** dos agentes
- **Estatísticas de uso** do sistema
- **Alertas de segurança** em tempo real

## 🤝 **Contribuição**

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 **Suporte**

Para dúvidas ou suporte:
- 📧 Email: suporte@bemobi.com
- 💬 WhatsApp: (21) 98011-2323
- 🌐 Website: www.bemobi.com

---

**Desenvolvido com ❤️ pela equipe Bemobi**
