#!/usr/bin/env python3
"""
Simulador do Fluxo Bemobi - Para Gravação de Vídeos
Simula todas as interações do sistema Bemobi com mensagens estáticas
"""

import time
import random
from typing import Dict, List, Any

class SimuladorFluxoBemobi:
    def __init__(self):
        self.mensagens_grace = {
            "inicial": """
🤖 **Grace - Assistente de Verificação de Cobranças**

Olá! Sou a Grace, sua assistente especializada em verificar a autenticidade de boletos e cobranças.

Utilizo agentes de IA especializados para:
🔍 Extrair dados de documentos
📊 Analisar dados nos sistemas Bemobi  
🛡️ Detectar possíveis fraudes
📊 Dar uma resposta clara e segura

**Envie sua cobrança para começar!**
            """,
            
            "menu_principal": """
❓ **Como usar o Grace:**

**1. Envie uma foto do boleto**
- Tire uma foto clara do boleto
- Certifique-se que todos os dados estão visíveis

**2. Envie dados do PIX**
- Cole o texto do PIX recebido
- Inclua valor, beneficiário e chave

**3. Receba sua análise**
- 🟢 Verde: Cobrança segura
- ⚠️ Amarelo: Verificar com suporte  
- 🚨 Vermelho: Golpe detectado

**Precisa de ajuda?** Digite "ajuda" a qualquer momento.
            """,
            
            "processando": """
🔍 **Analisando sua cobrança...**

Nossos agentes especializados estão trabalhando:

🤖 **Agente Leitor** - Extraindo dados do documento
📊 **Agente Consultor** - Verificando nos sistemas Bemobi
🛡️ **Agente Detetive** - Detectando possíveis fraudes
📋 **Agente Orquestrador** - Consolidando análise

⏳ Aguarde alguns segundos...
            """,
            
            "resultado_seguro": """
✅ **ANÁLISE CONCLUÍDA - COBRANÇA SEGURA**

🎯 **Status:** SEGURO
📊 **Confiança:** 94%
⏱️ **Tempo de análise:** 2.3s

📋 **Dados verificados:**
• Beneficiário: Bemobi Telecomunicações LTDA
• CPF/CNPJ: 12.345.678/0001-90
• Valor: R$ 89,90
• Vencimento: 15/12/2024

✅ **Validações aprovadas:**
• Cliente ativo nos sistemas Bemobi
• Beneficiário legítimo
• Valor compatível com histórico
• Nenhum padrão de fraude detectado

🟢 **RECOMENDAÇÃO:** Pode pagar com segurança!
            """,
            
            "resultado_suspeito": """
⚠️ **ANÁLISE CONCLUÍDA - VERIFICAR COM SUPORTE**

🎯 **Status:** SUSPEITO
📊 **Confiança:** 67%
⏱️ **Tempo de análise:** 3.1s

📋 **Dados verificados:**
• Beneficiário: Bemobi Telecomunicações LTDA
• CPF/CNPJ: 12.345.678/0001-90
• Valor: R$ 89,90
• Vencimento: 15/12/2024

⚠️ **Alertas encontrados:**
• Valor diferente do histórico
• Beneficiário com nome similar
• Necessária verificação manual

🟡 **RECOMENDAÇÃO:** Entre em contato com o suporte antes de pagar.
            """,
            
            "resultado_golpe": """
🚨 **ANÁLISE CONCLUÍDA - GOLPE DETECTADO**

🎯 **Status:** GOLPE
📊 **Confiança:** 89%
⏱️ **Tempo de análise:** 2.8s

📋 **Dados analisados:**
• Beneficiário: Bemobi Telecom LTDA
• CPF/CNPJ: 98.765.432/0001-10
• Valor: R$ 89,90
• Vencimento: 15/12/2024

🚨 **Fraudes detectadas:**
• Beneficiário não cadastrado nos sistemas
• CPF/CNPJ inválido
• Padrão de golpe conhecido
• Valor suspeito para o serviço

🔴 **RECOMENDAÇÃO:** NÃO PAGUE! Esta é uma tentativa de golpe.
            """,
            
            "demo_verificacao": """
🎬 **DEMO - Verificação de Cobrança**

Vou simular uma verificação completa para você ver como funciona:

**📸 Simulando envio de boleto...**
*[Imagem do boleto seria processada aqui]*

**🤖 Agentes trabalhando...**
• Agente Leitor: Extraindo dados...
• Agente Consultor: Verificando sistemas...
• Agente Detetive: Analisando padrões...
• Agente Orquestrador: Consolidando...

**⏳ Processando...**
            """,
            
            "sobre_agentes": """
🤖 **Nossos Agentes Especializados**

**🔍 Agente Leitor**
• Extrai dados de boletos e documentos
• Usa OCR e NLP para entender textos
• Estrutura informações automaticamente

**📊 Agente Consultor**  
• Verifica dados nos sistemas Bemobi
• Valida beneficiários e valores
• Consulta histórico do cliente

**🛡️ Agente Detetive**
• Detecta padrões de fraude
• Analisa comportamentos suspeitos
• Identifica tentativas de golpe

**📋 Agente Orquestrador**
• Consolida todas as análises
• Gera pontuação de confiança
• Define status final da verificação
            """,
            
            "erro": """
❌ **Erro no Processamento**

Ocorreu um erro ao analisar sua cobrança. Isso pode acontecer por:

• Imagem com baixa qualidade
• Dados incompletos ou ilegíveis
• Problema temporário nos sistemas

**Tente novamente:**
• Envie uma foto mais clara
• Verifique se todos os dados estão visíveis
• Aguarde alguns minutos e tente novamente
            """
        }
        
        self.botoes_opcoes = {
            "menu_principal": [
                {"id": "demo_verificacao", "title": "🎬 Demo IA"},
                {"id": "verificar_cobranca", "title": "🔍 Verificar"},
                {"id": "sobre_agentes", "title": "🤖 Sobre Agentes"}
            ],
            
            "demo": [
                {"id": "iniciar_demo", "title": "▶️ Iniciar Demo"},
                {"id": "voltar_menu", "title": "🔙 Voltar"}
            ],
            
            "verificacao": [
                {"id": "enviar_boleto", "title": "📸 Enviar Boleto"},
                {"id": "enviar_pix", "title": "💳 Enviar PIX"},
                {"id": "voltar_menu", "title": "🔙 Voltar"}
            ],
            
            "resultado": [
                {"id": "nova_verificacao", "title": "🔄 Nova Verificação"},
                {"id": "relatorio_detalhado", "title": "📊 Relatório"},
                {"id": "voltar_menu", "title": "🔙 Menu"}
            ],
            
            "sobre": [
                {"id": "voltar_menu", "title": "🔙 Voltar ao Menu"},
                {"id": "demo_verificacao", "title": "🎬 Ver Demo"}
            ]
        }
    
    def mostrar_mensagem(self, tipo: str, delay: float = 1.0):
        """Mostra uma mensagem com delay para simular digitação"""
        mensagem = self.mensagens_grace.get(tipo, "Mensagem não encontrada")
        print(f"\n{'='*60}")
        print(f"📱 GRACE: {tipo.upper()}")
        print(f"{'='*60}")
        
        # Simular digitação
        for linha in mensagem.strip().split('\n'):
            print(linha)
            time.sleep(delay * 0.1)
        
        print(f"{'='*60}")
        time.sleep(delay)
    
    def mostrar_botoes(self, tipo: str):
        """Mostra os botões disponíveis"""
        botoes = self.botoes_opcoes.get(tipo, [])
        print(f"\n🔘 OPÇÕES DISPONÍVEIS:")
        for i, botao in enumerate(botoes, 1):
            print(f"  {i}. {botao['title']}")
        print()
    
    def simular_interacao_usuario(self, opcao: str):
        """Simula a interação do usuário"""
        print(f"\n👤 USUÁRIO: Clica em '{opcao}'")
        time.sleep(0.5)
    
    def simular_fluxo_completo(self):
        """Simula o fluxo completo do sistema"""
        print("🎬 INICIANDO SIMULAÇÃO DO FLUXO BEMOBI")
        print("=" * 60)
        
        # 1. Mensagem inicial
        self.mostrar_mensagem("inicial")
        self.mostrar_botoes("menu_principal")
        
        # 2. Usuário clica em "Demo IA"
        self.simular_interacao_usuario("🎬 Demo IA")
        self.mostrar_mensagem("demo_verificacao")
        self.mostrar_botoes("demo")
        
        # 3. Usuário clica em "Iniciar Demo"
        self.simular_interacao_usuario("▶️ Iniciar Demo")
        self.mostrar_mensagem("processando")
        
        # 4. Resultado da demo (aleatório)
        resultados = ["resultado_seguro", "resultado_suspeito", "resultado_golpe"]
        resultado = random.choice(resultados)
        self.mostrar_mensagem(resultado)
        self.mostrar_botoes("resultado")
        
        # 5. Usuário volta ao menu
        self.simular_interacao_usuario("🔙 Menu")
        self.mostrar_mensagem("menu_principal")
        self.mostrar_botoes("menu_principal")
        
        # 6. Usuário clica em "Sobre Agentes"
        self.simular_interacao_usuario("🤖 Sobre Agentes")
        self.mostrar_mensagem("sobre_agentes")
        self.mostrar_botoes("sobre")
        
        # 7. Usuário volta ao menu
        self.simular_interacao_usuario("🔙 Voltar ao Menu")
        self.mostrar_mensagem("menu_principal")
        self.mostrar_botoes("menu_principal")
        
        # 8. Usuário clica em "Verificar"
        self.simular_interacao_usuario("🔍 Verificar")
        self.mostrar_mensagem("processando")
        
        # 9. Resultado da verificação real
        resultado_real = random.choice(resultados)
        self.mostrar_mensagem(resultado_real)
        self.mostrar_botoes("resultado")
        
        print("\n🎬 SIMULAÇÃO CONCLUÍDA!")
        print("=" * 60)
    
    def simular_cenarios_especificos(self):
        """Simula cenários específicos para gravação"""
        cenarios = [
            {
                "nome": "Cenário Seguro",
                "fluxo": ["inicial", "menu_principal", "demo_verificacao", "processando", "resultado_seguro"]
            },
            {
                "nome": "Cenário Suspeito", 
                "fluxo": ["inicial", "menu_principal", "demo_verificacao", "processando", "resultado_suspeito"]
            },
            {
                "nome": "Cenário Golpe",
                "fluxo": ["inicial", "menu_principal", "demo_verificacao", "processando", "resultado_golpe"]
            },
            {
                "nome": "Cenário Sobre Agentes",
                "fluxo": ["inicial", "menu_principal", "sobre_agentes"]
            }
        ]
        
        for cenario in cenarios:
            print(f"\n🎬 {cenario['nome'].upper()}")
            print("=" * 60)
            
            for mensagem in cenario['fluxo']:
                self.mostrar_mensagem(mensagem)
                if mensagem in ["menu_principal", "demo", "resultado", "sobre"]:
                    self.mostrar_botoes(mensagem)
                time.sleep(1)
            
            print(f"\n✅ {cenario['nome']} concluído!")
            time.sleep(2)

def main():
    """Função principal"""
    simulador = SimuladorFluxoBemobi()
    
    print("🎬 SIMULADOR FLUXO BEMOBI - PARA GRAVAÇÃO DE VÍDEOS")
    print("=" * 60)
    print("Escolha uma opção:")
    print("1. Fluxo completo")
    print("2. Cenários específicos")
    print("3. Mensagens individuais")
    print("4. Sair")
    
    while True:
        try:
            opcao = input("\nDigite sua opção (1-4): ").strip()
            
            if opcao == "1":
                simulador.simular_fluxo_completo()
            elif opcao == "2":
                simulador.simular_cenarios_especificos()
            elif opcao == "3":
                print("\nMensagens disponíveis:")
                for i, (key, _) in enumerate(simulador.mensagens_grace.items(), 1):
                    print(f"{i}. {key}")
                
                try:
                    msg_num = int(input("Digite o número da mensagem: ")) - 1
                    msg_keys = list(simulador.mensagens_grace.keys())
                    if 0 <= msg_num < len(msg_keys):
                        simulador.mostrar_mensagem(msg_keys[msg_num])
                    else:
                        print("Número inválido!")
                except ValueError:
                    print("Digite um número válido!")
            elif opcao == "4":
                print("👋 Até logo!")
                break
            else:
                print("Opção inválida! Digite 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Até logo!")
            break
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    main()
