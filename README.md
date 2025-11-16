# Widdershins GUI

Interface gráfica para o gerador de documentação Widdershins.

## Pré-requisitos

1. **Python 3.7+** com Tkinter (incluído na maioria das instalações)
2. **Node.js** instalado

## Instalação

1. Clone ou baixe este repositório
2. Instale as dependências Node.js:
   ```bash
   npm install
   ```
3. Instale as dependências Python (opcional, para desenvolvimento):
   ```bash
   pip install -r requirements.txt
   ```

## Uso

Execute a aplicação:
```bash
python widdershins_gui.py
```

### Funcionalidades

#### 🎆 **Novas Funcionalidades de UX**
- **Drag & Drop**: Arraste arquivos OpenAPI diretamente para a interface
- **Presets Inteligentes**: Configurações pré-definidas (Básico, Completo, Mínimo)
- **Auto-nomeação**: Sugestão automática de nome do arquivo de saída
- **Seleção de Linguagens**: Checkboxes para cURL, JavaScript, Python, Java, Go, PHP, Ruby, C#
- **Preview de Arquivos**: Visualize o conteúdo do OpenAPI antes da geração
- **Validação Rápida**: Verifique se o arquivo OpenAPI é válido
- **Salvar/Carregar Configurações**: Reutilize suas configurações favoritas
- **Interface Simplificada**: Opções avançadas ocultas, seleção objetiva

#### 🔧 **Funcionalidades Core**
- **Seleção de arquivos**: Interface gráfica para selecionar arquivos OpenAPI e definir saída
- **Opções configuráveis**: Checkboxes para principais opções do Widdershins
- **Configurações avançadas**: Suporte a templates customizados e variáveis de ambiente
- **Console integrado**: Visualização em tempo real da execução
- **Validação de entrada**: Verificação de arquivos e parâmetros antes da execução
- **Execução segura**: Proteção contra injeção de comandos

### Segurança

A aplicação implementa várias medidas de segurança:
- Validação rigorosa de caminhos de arquivo
- Lista branca de flags permitidas
- Execução de subprocess sem shell
- Timeout para processos longos
- Tratamento robusto de erros

## Estrutura do Projeto

```
widdershins_gui/
├── widdershins_gui.py    # Aplicação principal
├── package.json          # Dependências Node.js
├── node_modules/         # Widdershins local (após npm install)
├── requirements.txt      # Dependências Python
└── README.md            # Este arquivo
```

## Solução de Problemas

### Erro "widdershins não encontrado"
- Execute: `npm install` na pasta da aplicação
- Verifique se o Node.js está instalado
- Como alternativa, instale globalmente: `npm install -g widdershins`

### Problemas de permissão
- Execute como administrador (Windows) ou com sudo (Linux/Mac)
- Verifique permissões de escrita no diretório de saída

### Interface não responde
- A aplicação usa threading para evitar travamentos
- Aguarde a conclusão ou reinicie se necessário