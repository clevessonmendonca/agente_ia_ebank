# 🤖 CALVIN - Agente de IA Contextual para Hackathon Bemobi 2025

## 🎯 Visão Geral

**CALVIN** é um agente único de IA que se especializa através de **contextos**, não múltiplos agentes separados. Utiliza **AWS Bedrock** como motor de IA e integra com as tecnologias da Bemobi.

### ✅ **Arquitetura Modular:**
```
CALVIN AGENT (Único)
├── 🧭 Onboarding → Smart Checkout + MCPS  
├── 💳 Payments → Smart Checkout + Simulações
├── 🛡️ Security → BeTrusty + Auth Adaptativa
├── 🤝 Relationship → Grace + Retenção
└── 💝 Assisted → Modalidade Inclusiva
```

## 📁 Estrutura do Backend

```
backend/
├── calvin_agent.py      # Agente principal com especialidades
├── calvin_api.py        # Servidor Flask com endpoints
├── requirements.txt     # Dependências Python
├── env.example         # Configurações de exemplo
└── README.md          # Este arquivo
```

## 🚀 Instalação e Execução

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar AWS
```bash
# Configurar credenciais AWS
aws configure

# Ou exportar variáveis
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### 3. Iniciar Servidor
```bash
python calvin_api.py
```

### 4. Testar API
```bash
# Health check
curl http://localhost:8000/health

# Chat inteligente
curl -X POST http://localhost:8000/calvin/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, preciso de ajuda com pagamentos", "user_context": {"country": "Brazil"}}'
```

## 📡 Endpoints Principais

### Chat Inteligente (Detecção Automática)
```bash
POST /calvin/chat
Body: {
  "message": "Sua mensagem aqui",
  "user_context": {
    "country": "Brazil",
    "age": 30,
    "assisted_mode": false
  }
}
```

### Especialidades Específicas
```bash
POST /calvin/onboarding     # Boas-vindas
POST /calvin/payments       # Pagamentos  
POST /calvin/security       # Segurança
POST /calvin/relationship   # Relacionamento
POST /calvin/assisted       # Modalidade assistida
```

### Demos para Hackathon
```bash
GET /demo/yduqs-students    # Demo estudantes
GET /demo/sabesp-recovery   # Demo Sabesp
GET /demo/assisted-mode     # Demo modalidade assistida
GET /demo/security-alert    # Demo segurança
```

## 🎪 Demonstrações Prontas

### 1. Estudantes YDUQS
- Contexto de estudante com dificuldades financeiras
- Sugestão de desconto estudantil
- Integração com Smart Checkout

### 2. Sabesp Recuperação
- Pagamento de conta de água
- Recomendação PIX automático
- Otimização baseada no histórico

### 3. Modalidade Assistida
- Interface simplificada para idosos
- Linguagem carinhosa e paciente
- Suporte familiar integrado

### 4. Alerta de Segurança
- Detecção de comportamento suspeito
- Autenticação adaptativa
- Integração com BeTrusty

## 🔧 Integração com Frontend

### React Native Service
```typescript
const calvintApi = 'http://localhost:8000';

// Chat inteligente
const response = await fetch(`${calvinApi}/calvin/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Como pagar minha conta?",
    user_context: { country: "Brazil", age: 25 }
  })
});
```

### Componente React Native
```tsx
import { useState } from 'react';

const CalvinChat = () => {
  const [response, setResponse] = useState('');
  
  const chatWithCalvin = async (message: string) => {
    const result = await fetch('http://localhost:8000/calvin/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    
    const data = await result.json();
    setResponse(data.response);
  };
  
  return (
    // Seu componente de chat aqui
  );
};
```

## 🔄 Facilmente Adaptável

### Trocar Motor de IA
```python
# Substituir AWS Bedrock por OpenAI
# Em calvin_agent.py, método invoke_with_specialty:

# De: self.bedrock_runtime.invoke_model()
# Para: openai.ChatCompletion.create()
```

### Adicionar Nova Especialidade
```python
# Em calvin_agent.py, adicionar no CalvinSpecialty:
FINANCE_COACH = "finance_coach"

# Adicionar contexto especializado:
"finance_coach": {
    "system_prompt": "Você é especialista em educação financeira...",
    "temperature": 0.6
}
```

### Integrar API Real Bemobi
```python
# Substituir BemobiIntegrations por chamadas reais:
def smart_checkout_config(user_context):
    response = requests.post('https://api.bemobi.com/smart-checkout', ...)
    return response.json()
```

## 📊 Logs e Monitoramento

```bash
# Ver logs em tempo real
tail -f logs/calvin.log

# Debug de especialidades
python -c "
from calvin_agent import calvin, CalvinSpecialty
response = calvin.invoke_with_specialty('teste', CalvinSpecialty.PAYMENTS)
print(response)
"
```

## 🎯 Para o Hackathon

### Características Únicas:
- ✅ **Um agente, múltiplas especialidades** via contexto
- ✅ **Modalidade assistida** para inclusão digital
- ✅ **Integração Bemobi** simulada mas realística
- ✅ **Backend modular** facilmente adaptável
- ✅ **AWS Bedrock** como diferencial técnico

### Pitch Points:
- "Democratizamos IA financeira para todos"
- "Um agente que se adapta ao usuário, não o contrário"
- "Arquitetura pronta para integração Bemobi"
- "Inclusão digital para 30 milhões de brasileiros"

---

**🚀 CALVIN está pronto para o hackathon!**

Execute `python calvin_api.py` e comece a integrar com seu frontend React Native.# agente_ia_ebank
