# Widdershins GUI

> Interface gráfica moderna e intuitiva para o gerador de documentação Widdershins

## 🎯 Objetivo

O **Widdershins GUI** foi desenvolvido para simplificar a geração de documentação markdown a partir de especificações OpenAPI/Swagger, oferecendo uma interface visual amigável que elimina a necessidade de usar linha de comando.

### Principais benefícios:
- ✅ **Simplicidade**: Interface drag & drop intuitiva
- ✅ **Produtividade**: Presets e configurações reutilizáveis
- ✅ **Portabilidade**: Executável standalone sem dependências
- ✅ **Flexibilidade**: Suporte completo às opções do Widdershins
- ✅ **Postman**: Conversão automática de Collections para OpenAPI

## 🚀 Funcionamento

A aplicação funciona como uma camada visual sobre o Widdershins CLI:

1. **Entrada**: Arquivo OpenAPI (JSON/YAML)
2. **Processamento**: Widdershins local integrado
3. **Saída**: Documentação Markdown formatada

### Fluxo de trabalho:
```
Arquivo OpenAPI/Postman → Interface GUI → Widdershins → Documentação MD
```

### Suporte a Postman Collections:
```
Postman Collection → Conversor Integrado → OpenAPI 3.0 → Widdershins → Documentação MD
```

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

### Modo Individual
1. Selecione um arquivo OpenAPI/Postman ou arraste para a interface
2. Configure as opções desejadas
3. Clique em "Gerar Documentação"

### Modo Lote
1. Marque a opção "Conversão em Lote"
2. Selecione a pasta de saída
3. Adicione múltiplos arquivos:
   - Clique em "Selecionar Arquivos" ou
   - Arraste múltiplos arquivos para a interface
4. Configure as opções (aplicadas a todos os arquivos)
5. Clique em "Processar Lote"

**Vantagens do Modo Lote:**
- ✅ Processa dezenas de arquivos automaticamente
- ✅ Aplica as mesmas configurações para todos
- ✅ Conversão automática de Postman Collections
- ✅ Relatório detalhado de sucessos/erros
- ✅ Nomeação automática dos arquivos de saída

## Compilação (Executável)

Para gerar um executável standalone:

### Usando PyInstaller
```bash
# Instalar PyInstaller
pip install pyinstaller

# Gerar executável
pyinstaller --onefile --windowed --name "WiddershinsGUI" widdershins_gui.py

# Executável estará em dist/WiddershinsGUI.exe
```

### Usando cx_Freeze
```bash
# Instalar cx_Freeze
pip install cx_freeze

# Criar setup.py e executar
python setup.py build
```

### Usando Auto-py-to-exe (Interface Gráfica)
```bash
# Instalar auto-py-to-exe
pip install auto-py-to-exe

# Abrir interface gráfica
auto-py-to-exe
```

**Nota**: Certifique-se de que `node_modules/` esteja na mesma pasta do executável.

### Configurações de Build

#### PyInstaller (Recomendado)
```bash
# Build completo com dependências
pyinstaller --onefile --windowed \
  --name "WiddershinsGUI" \
  --add-data "node_modules;node_modules" \
  --add-data "package.json;." \
  widdershins_gui.py
```

#### Requisitos para Build
- Python 3.7+
- Node.js instalado
- Dependências do requirements.txt
- npm install executado

### Funcionalidades

#### 🎆 **Novas Funcionalidades de UX**
- **Drag & Drop**: Arraste arquivos OpenAPI diretamente para a interface
- **Conversão em Lote**: Processe múltiplos arquivos de uma só vez
- **Presets Inteligentes**: Configurações pré-definidas (Básico, Completo, Mínimo)
- **Auto-nomeação**: Sugestão automática de nome do arquivo de saída
- **Seleção de Linguagens**: Checkboxes para cURL, JavaScript, Python, Java, Go, PHP, Ruby, C#
- **Preview de Arquivos**: Visualize o conteúdo do OpenAPI antes da geração
- **Validação Rápida**: Verifique se o arquivo OpenAPI é válido
- **Salvar/Carregar Configurações**: Reutilize suas configurações favoritas
- **Interface Simplificada**: Opções avançadas ocultas, seleção objetiva

#### 🔧 **Funcionalidades Core**
- **Seleção de arquivos**: Interface gráfica para selecionar arquivos OpenAPI e definir saída
- **Conversão em lote**: Processe múltiplos arquivos OpenAPI/Postman simultaneamente
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
├── .gitignore           # Arquivos ignorados pelo Git
└── README.md            # Este arquivo
```

## Solução de Problemas

### Arquivos do Postman
- ✅ **Suporte Automático**: A aplicação detecta e converte automaticamente Postman Collections
- ✅ **Conversão Transparente**: Collections são convertidas para OpenAPI 3.0 antes do processamento
- ✅ **Preservação de Dados**: Mantém endpoints, parâmetros, headers e exemplos de response
- ⚠️ **Arquivo Temporário**: Cria um arquivo `*_openapi.json` na mesma pasta da collection

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

## 👨‍💻 Desenvolvedor

**DSantos Info**
- 🌐 Website: [dsantosinfo.com.br](https://dsantosinfo.com.br)
- 📧 Email: [contato@dsantosinfo.com.br](mailto:contato@dsantosinfo.com.br)

---

## 🛠️ Desenvolvimento

### Tecnologias utilizadas:
- **Python 3.7+** - Linguagem principal
- **Tkinter** - Interface gráfica
- **TkinterDnD2** - Funcionalidade drag & drop
- **Node.js** - Runtime para Widdershins
- **Widdershins** - Gerador de documentação

### Arquitetura:
- **Threading** - Execução não-bloqueante
- **Subprocess** - Execução segura do Widdershins
- **JSON** - Persistência de configurações
- **Pathlib** - Manipulação segura de caminhos

### Contribuindo:
1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request