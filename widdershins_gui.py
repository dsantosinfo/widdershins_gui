import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinterdnd2 import DND_FILES, TkinterDnD
import subprocess
import threading
import queue
import shlex
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

# Constantes de UI
APP_TITLE = "Widdershins GUI Generator"
BG_COLOR = "#f0f0f0"
LABEL_WIDTH = 20
INPUT_WIDTH = 70

class WiddershinsGUI:
    """
    Interface Gráfica (Tkinter) para o Widdershins CLI.
    
    Esta classe encapsula toda a lógica da UI, gerenciamento de estado
    e a execução do processo 'widdershins' em um thread separado
    para evitar o congelamento da GUI.
    """

    def __init__(self, root: TkinterDnD.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("900x800")
        self.root.configure(bg=BG_COLOR)
        
        # Configurar drag and drop
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self._on_drop)

        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Fila para comunicação entre threads (logs do subprocesso)
        self.log_queue = queue.Queue()
        
        # Tooltip reference
        self.tooltip: Optional[tk.Toplevel] = None
        
        # Configurações e presets
        self.config_file = Path(__file__).parent / "config.json"
        self.presets = {
            "Básico": {
                "opt_code": True,
                "opt_summary": True,
                "opt_omit_header": False,
                "opt_raw": False,
                "opt_resolve": False,
                "lang_curl": True,
                "lang_javascript": True,
                "lang_python": True
            },
            "Completo": {
                "opt_code": True,
                "opt_summary": True,
                "opt_omit_header": False,
                "opt_raw": False,
                "opt_resolve": True,
                "lang_curl": True,
                "lang_javascript": True,
                "lang_python": True,
                "lang_java": True,
                "lang_go": True
            },
            "Mínimo": {
                "opt_code": False,
                "opt_summary": False,
                "opt_omit_header": True,
                "opt_raw": True,
                "opt_resolve": False
            }
        }

        # --- Variáveis de Estado (Tkinter) ---
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.user_templates = tk.StringVar()
        self.environment_file = tk.StringVar()
        self.other_flags = tk.StringVar()
        
        # Linguagens de código (checkboxes)
        self.lang_curl = tk.BooleanVar(value=True)
        self.lang_javascript = tk.BooleanVar(value=True)
        self.lang_python = tk.BooleanVar(value=True)
        self.lang_java = tk.BooleanVar(value=False)
        self.lang_go = tk.BooleanVar(value=False)
        self.lang_php = tk.BooleanVar(value=False)
        self.lang_ruby = tk.BooleanVar(value=False)
        self.lang_csharp = tk.BooleanVar(value=False)

        # Opções booleanas (Checkboxes)
        self.opt_code = tk.BooleanVar(value=True)
        self.opt_summary = tk.BooleanVar(value=True)
        self.opt_omit_header = tk.BooleanVar(value=False)
        self.opt_raw = tk.BooleanVar(value=False)
        self.opt_resolve = tk.BooleanVar(value=False)

        # Construção da UI
        self._create_widgets()
        
        # Carregar configurações salvas
        self._load_config()

        # Inicia o "polling" da fila de logs
        self._poll_log_queue()

    def _create_widgets(self):
        """Cria e posiciona todos os widgets na janela principal."""
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Seção 0: Presets e Modo ---
        preset_frame = ttk.LabelFrame(main_frame, text="⚡ Início Rápido", padding="10")
        preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(preset_frame, text="Preset:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.preset_var = tk.StringVar(value="Básico")
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, values=list(self.presets.keys()), state="readonly")
        preset_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)
        preset_combo.bind('<<ComboboxSelected>>', self._apply_preset)
        
        ttk.Button(preset_frame, text="💾 Salvar Config", command=self._save_config).grid(row=0, column=2, padx=5)
        ttk.Button(preset_frame, text="📂 Carregar Config", command=self._load_config_dialog).grid(row=0, column=3, padx=5)
        
        preset_frame.grid_columnconfigure(1, weight=1)

        # --- Seção 1: Arquivos (Entrada/Saída) ---
        file_frame = ttk.LabelFrame(main_frame, text="📁 Arquivos (Arraste arquivos aqui!)", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        # Configurar drag and drop para o frame
        file_frame.drop_target_register(DND_FILES)
        file_frame.dnd_bind('<<Drop>>', self._on_drop)

        self._create_file_entry(file_frame, "📄 Arquivo OpenAPI:", self.input_file, self._browse_input_file, row=0)
        self._create_file_entry(file_frame, "📝 Arquivo Markdown:", self.output_file, self._browse_output_file, row=1)
        
        # Auto-sugestão de nome
        ttk.Button(file_frame, text="🔄 Auto-nomear saída", command=self._auto_name_output).grid(row=1, column=3, padx=5)

        # --- Seção 2: Opções Principais ---
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ Opções de Geração", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        self._create_checkbox(options_frame, self.opt_code, "Incluir código", "Incluir exemplos de código").grid(row=0, column=0, sticky=tk.W)
        self._create_checkbox(options_frame, self.opt_summary, "Usar summary", "Usar 'summary' como título").grid(row=0, column=1, sticky=tk.W, padx=10)
        self._create_checkbox(options_frame, self.opt_resolve, "Resolver $refs", "Resolver referências externas").grid(row=0, column=2, sticky=tk.W, padx=10)
        
        # --- Seção 2.1: Linguagens de Código ---
        lang_frame = ttk.LabelFrame(main_frame, text="💻 Linguagens para Exemplos de Código", padding="10")
        lang_frame.pack(fill=tk.X, pady=5)
        
        # Primeira linha
        self._create_checkbox(lang_frame, self.lang_curl, "cURL", "Comandos cURL").grid(row=0, column=0, sticky=tk.W)
        self._create_checkbox(lang_frame, self.lang_javascript, "JavaScript", "Node.js/JavaScript").grid(row=0, column=1, sticky=tk.W, padx=10)
        self._create_checkbox(lang_frame, self.lang_python, "Python", "Python requests").grid(row=0, column=2, sticky=tk.W, padx=10)
        self._create_checkbox(lang_frame, self.lang_java, "Java", "Java OkHttp").grid(row=0, column=3, sticky=tk.W, padx=10)
        
        # Segunda linha
        self._create_checkbox(lang_frame, self.lang_go, "Go", "Go net/http").grid(row=1, column=0, sticky=tk.W, pady=5)
        self._create_checkbox(lang_frame, self.lang_php, "PHP", "PHP cURL").grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        self._create_checkbox(lang_frame, self.lang_ruby, "Ruby", "Ruby net/http").grid(row=1, column=2, sticky=tk.W, padx=10, pady=5)
        self._create_checkbox(lang_frame, self.lang_csharp, "C#", "C# HttpClient").grid(row=1, column=3, sticky=tk.W, padx=10, pady=5)

        # --- Seção 3: Opções Avançadas (Texto) ---
        self.advanced_frame = ttk.LabelFrame(main_frame, text="🔧 Opções Avançadas", padding="10")
        self.advanced_frame.pack(fill=tk.X, pady=5)
        
        # Botão para mostrar/ocultar opções avançadas
        self.show_advanced = tk.BooleanVar(value=False)
        advanced_toggle = ttk.Checkbutton(self.advanced_frame, text="Mostrar opções avançadas", variable=self.show_advanced, command=self._toggle_advanced)
        advanced_toggle.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Frame para opções avançadas (inicialmente oculto)
        self.advanced_options_frame = ttk.Frame(self.advanced_frame)
        
        advanced_frame = self.advanced_options_frame
        
        # Opções avançadas simplificadas
        self._create_checkbox(advanced_frame, self.opt_omit_header, "Omitir cabeçalho", "Gerar MD puro sem YAML").grid(row=0, column=0, sticky=tk.W, pady=5)
        self._create_checkbox(advanced_frame, self.opt_raw, "Modo raw", "Não processar Markdown").grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        self._create_file_entry(advanced_frame, "📁 Templates customizados:", self.user_templates, self._browse_templates_dir, row=1)
        self._create_file_entry(advanced_frame, "🌍 Arquivo environment:", self.environment_file, self._browse_env_file, row=2)
        
        self._create_text_entry(advanced_frame, "🔧 Flags extras:", self.other_flags, 3, 
                                help_text="(Ex: --maxHeadingDepth 3 --shallow)")

        # --- Seção 4: Ação e Console ---
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        self.generate_button = ttk.Button(action_frame, text="🚀 Gerar Documentação", command=self._start_generation_thread)
        self.generate_button.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        
        ttk.Button(action_frame, text="👁️ Preview", command=self._preview_file).pack(side=tk.RIGHT, padx=(10,0))
        ttk.Button(action_frame, text="✅ Validar", command=self._validate_openapi).pack(side=tk.RIGHT, padx=(5,0))

        console_frame = ttk.LabelFrame(main_frame, text="📋 Console de Saída", padding="5")
        console_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.console_output = ScrolledText(console_frame, wrap=tk.WORD, height=12, state=tk.DISABLED, bg="#2b2b2b", fg="#f0f0f0", font=('Consolas', 9))
        self.console_output.pack(fill=tk.BOTH, expand=True)

    # --- Métodos de Criação de Widgets (Helpers) ---

    def _create_file_entry(self, parent: ttk.Frame, label_text: str, var: tk.StringVar, browse_cmd: callable, row: int):
        """Helper para criar um conjunto [Label | Entry | Button]."""
        ttk.Label(parent, text=label_text, width=LABEL_WIDTH).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        entry = ttk.Entry(parent, textvariable=var, width=INPUT_WIDTH)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=5)
        button = ttk.Button(parent, text="Procurar...", command=browse_cmd)
        button.grid(row=row, column=2, sticky=tk.E, padx=5)
        parent.grid_columnconfigure(1, weight=1)

    def _create_text_entry(self, parent: ttk.Frame, label_text: str, var: tk.StringVar, row: int, help_text: str = None):
        """Helper para criar um conjunto [Label | Entry]."""
        ttk.Label(parent, text=label_text, width=LABEL_WIDTH).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, columnspan=2, sticky=tk.EW, padx=5)
        if help_text:
            ttk.Label(parent, text=help_text, font=("TkDefaultFont", 8, "italic")).grid(row=row+1, column=1, columnspan=2, sticky=tk.W, padx=5)
        parent.grid_columnconfigure(1, weight=1)

    def _create_checkbox(self, parent: ttk.Frame, var: tk.BooleanVar, flag: str, help_text: str) -> ttk.Checkbutton:
        """Helper para criar um Checkbutton com tooltip (via texto)."""
        cb = ttk.Checkbutton(parent, text=flag, variable=var)
        # Adicionar tooltip simples (usando Label)
        cb.bind("<Enter>", lambda e, t=help_text: self._show_tooltip(t))
        cb.bind("<Leave>", lambda e: self._hide_tooltip())
        return cb

    # --- Métodos de Navegação (File Dialogs) ---

    def _browse_input_file(self):
        try:
            file = filedialog.askopenfilename(
                title="Selecionar Arquivo OpenAPI", 
                filetypes=[("JSON/YAML", "*.json *.yaml *.yml"), ("Todos", "*.*")]
            )
            if file and self._validate_file_path(file):
                self.input_file.set(file)
                self._auto_name_output()  # Auto-sugerir nome de saída
        except Exception as e:
            self.logger.error(f"Erro ao selecionar arquivo de entrada: {e}")
            messagebox.showerror("Erro", f"Erro ao selecionar arquivo: {e}")

    def _browse_output_file(self):
        try:
            file = filedialog.asksaveasfilename(
                title="Salvar Arquivo Markdown Como...", 
                filetypes=[("Markdown", "*.md"), ("Todos", "*.*")], 
                defaultextension=".md"
            )
            if file:
                self.output_file.set(file)
        except Exception as e:
            self.logger.error(f"Erro ao selecionar arquivo de saída: {e}")
            messagebox.showerror("Erro", f"Erro ao selecionar arquivo: {e}")

    def _browse_templates_dir(self):
        try:
            directory = filedialog.askdirectory(title="Selecionar Pasta de Templates")
            if directory and self._validate_directory_path(directory):
                self.user_templates.set(directory)
        except Exception as e:
            self.logger.error(f"Erro ao selecionar diretório de templates: {e}")
            messagebox.showerror("Erro", f"Erro ao selecionar diretório: {e}")

    def _browse_env_file(self):
        try:
            file = filedialog.askopenfilename(
                title="Selecionar Arquivo de Environment", 
                filetypes=[("JSON/YAML", "*.json *.yaml *.yml"), ("Todos", "*.*")]
            )
            if file and self._validate_file_path(file):
                self.environment_file.set(file)
        except Exception as e:
            self.logger.error(f"Erro ao selecionar arquivo de environment: {e}")
            messagebox.showerror("Erro", f"Erro ao selecionar arquivo: {e}")

    # --- Lógica de Geração (Threading e Subprocess) ---

    def _start_generation_thread(self):
        """Inicia a execução do Widdershins em um thread separado."""
        
        try:
            # Validação completa
            if not self._validate_inputs():
                return

            self._set_console_state(tk.NORMAL)
            self.console_output.delete("1.0", tk.END)
            self._log_to_console(f"Iniciando geração...\n{'-'*30}\n")
            self._set_console_state(tk.DISABLED)

            self.generate_button.config(text="Gerando... Aguarde...", state=tk.DISABLED)

            command = self._build_secure_command()
            
            # Inicia o thread de execução
            threading.Thread(
                target=self._run_widdershins_process,
                args=(command,),
                daemon=True
            ).start()

        except Exception as e:
            self.logger.error(f"Erro ao iniciar geração: {e}")
            self._log_to_console(f"Erro ao construir comando: {e}\n")
            self.generate_button.config(text="Gerar Documentação", state=tk.NORMAL)
            messagebox.showerror("Erro", f"Erro ao iniciar geração: {e}")

    def _build_secure_command(self) -> List[str]:
        """Monta a lista de argumentos para o subprocesso de forma segura."""
        
        try:
            # Usar Widdershins local se disponível, senão global
            widdershins_path = self._get_widdershins_path()
            command = [widdershins_path]

            # Arquivos (validados)
            input_file = self.input_file.get().strip()
            output_file = self.output_file.get().strip()
            
            if not input_file or not output_file:
                raise ValueError("Arquivos de entrada e saída são obrigatórios")
            
            command.append(input_file)
            command.extend(['-o', output_file])

            # Opções booleanas (seguras)
            boolean_options = {
                self.opt_code.get(): '--code',
                self.opt_summary.get(): '--summary',
                self.opt_omit_header.get(): '--omitHeader',
                self.opt_raw.get(): '--raw',
                self.opt_resolve.get(): '--resolve'
            }
            
            for condition, flag in boolean_options.items():
                if condition:
                    command.append(flag)

            # Campos de texto (validados)
            if self.user_templates.get().strip():
                templates_path = self.user_templates.get().strip()
                if self._validate_directory_path(templates_path):
                    command.extend(['--user_templates', templates_path])
                    
            if self.environment_file.get().strip():
                env_file = self.environment_file.get().strip()
                if self._validate_file_path(env_file):
                    command.extend(['--environment', env_file])

            # Language Tabs (baseado nos checkboxes)
            lang_tabs = self._build_language_tabs()
            if lang_tabs:
                command.append('--language_tabs')
                command.extend(lang_tabs)

            # Outras flags (parsing seguro)
            other_flags = self.other_flags.get().strip()
            if other_flags:
                try:
                    parsed_flags = shlex.split(other_flags)
                    # Validar flags permitidas
                    for flag in parsed_flags:
                        if self._validate_flag(flag):
                            command.append(flag)
                except ValueError as e:
                    self.logger.warning(f"Erro ao processar flags adicionais: {e}")

            self._log_to_console(f"Comando Executado:\n{' '.join(shlex.quote(c) for c in command)}\n{'-'*30}\n")
            return command
            
        except Exception as e:
            self.logger.error(f"Erro ao construir comando: {e}")
            raise

    def _run_widdershins_process(self, command: List[str]):
        """
        Executa o processo 'widdershins' (roda no thread de trabalho).
        Envia a saída (stdout/stderr) para a fila (self.log_queue).
        """
        process = None
        try:
            # Configuração para ocultar a janela do console no Windows
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            # Configurações de segurança para subprocess
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                shell=False,  # Importante para segurança
                cwd=None,     # Não herdar diretório de trabalho
                env=None      # Usar ambiente limpo
            )

            # Leitura segura do stdout
            try:
                for line in iter(process.stdout.readline, ''):
                    if line.strip():  # Evitar linhas vazias
                        self.log_queue.put(line)
            except Exception as e:
                self.logger.error(f"Erro ao ler stdout: {e}")
            finally:
                if process.stdout:
                    process.stdout.close()

            # Leitura segura do stderr
            try:
                for line in iter(process.stderr.readline, ''):
                    if line.strip():  # Evitar linhas vazias
                        self.log_queue.put(f"STDERR: {line}")
            except Exception as e:
                self.logger.error(f"Erro ao ler stderr: {e}")
            finally:
                if process.stderr:
                    process.stderr.close()

            # Aguardar conclusão com timeout
            try:
                return_code = process.wait(timeout=300)  # 5 minutos timeout
                
                if return_code == 0:
                    self.log_queue.put("\n--- SUCESSO! Geração concluída. ---")
                else:
                    self.log_queue.put(f"\n--- ERRO! Processo finalizou com código {return_code} ---")
                    
            except subprocess.TimeoutExpired:
                self.log_queue.put("\n--- TIMEOUT! Processo cancelado por exceder tempo limite. ---")
                process.kill()
                process.wait()

        except FileNotFoundError:
            self.logger.error("Comando widdershins não encontrado")
            self.log_queue.put("\n--- ERRO CRÍTICO ---")
            self.log_queue.put("Comando 'widdershins' não encontrado.\n")
            self.log_queue.put("Soluções possíveis:")
            self.log_queue.put("1. Execute 'npm install' na pasta da aplicação")
            self.log_queue.put("2. Ou instale globalmente: 'npm install -g widdershins'")
            self.log_queue.put("3. Verifique se o Node.js está instalado")
        
        except PermissionError as e:
            self.logger.error(f"Erro de permissão: {e}")
            self.log_queue.put(f"\n--- ERRO DE PERMISSÃO ---")
            self.log_queue.put(f"Sem permissão para executar o comando: {e}")
            
        except Exception as e:
            self.logger.error(f"Erro inesperado no processo: {e}")
            self.log_queue.put(f"\n--- ERRO INESPERADO (Thread) ---")
            self.log_queue.put(str(e))
        
        finally:
            # Cleanup seguro
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    pass
            self.log_queue.put("DONE")  # Sinaliza o fim para a GUI

    # --- Métodos de Atualização da GUI (Thread-safe) ---

    def _poll_log_queue(self):
        """Verifica a fila de logs e atualiza a GUI (executa no main thread)."""
        try:
            processed_items = 0
            max_items_per_poll = 10  # Limitar processamento por ciclo
            
            while processed_items < max_items_per_poll:
                try:
                    line = self.log_queue.get_nowait()
                    processed_items += 1
                    
                    if line == "DONE":
                        self._handle_process_completion()
                        break
                    else:
                        self._log_to_console(line)
                        
                except queue.Empty:
                    break
                    
            # Força atualização da UI de forma segura
            try:
                self.root.update_idletasks()
            except tk.TclError:
                # Widget foi destruído
                return

        except Exception as e:
            self.logger.error(f"Erro no polling da fila: {e}")
        
        finally:
            # Reagenda a verificação
            try:
                self.root.after(100, self._poll_log_queue)
            except tk.TclError:
                # Widget foi destruído
                pass

    def _set_console_state(self, state: str):
        """Habilita/Desabilita o console de saída."""
        try:
            self.console_output.configure(state=state)
        except tk.TclError as e:
            self.logger.error(f"Erro ao configurar estado do console: {e}")

    def _log_to_console(self, message: str):
        """Escreve uma mensagem no console de saída (thread-safe)."""
        try:
            self.console_output.configure(state=tk.NORMAL)
            self.console_output.insert(tk.END, message)
            self.console_output.see(tk.END)  # Auto-scroll
            self.console_output.configure(state=tk.DISABLED)
        except tk.TclError as e:
            self.logger.error(f"Erro ao escrever no console: {e}")

    # --- Tooltip Helpers ---
    
    def _show_tooltip(self, text: str):
        try:
            if self.tooltip:
                self.tooltip.destroy()
                
            self.tooltip = tk.Toplevel(self.root)
            self.tooltip.wm_overrideredirect(True)
            
            x, y = self.root.winfo_pointerxy()
            self.tooltip.wm_geometry(f"+{x+15}+{y+10}")
            
            label = tk.Label(
                self.tooltip, 
                text=text, 
                background="#FFFFE0", 
                relief="solid", 
                borderwidth=1, 
                padx=5, 
                pady=5
            )
            label.pack()
        except Exception as e:
            self.logger.error(f"Erro ao mostrar tooltip: {e}")

    def _hide_tooltip(self):
        try:
            if self.tooltip:
                self.tooltip.destroy()
                self.tooltip = None
        except Exception as e:
            self.logger.error(f"Erro ao esconder tooltip: {e}")
    
    # --- Métodos de Validação ---
    
    def _validate_inputs(self) -> bool:
        """Valida todas as entradas do usuário."""
        try:
            input_file = self.input_file.get().strip()
            output_file = self.output_file.get().strip()
            
            if not input_file or not output_file:
                messagebox.showerror(
                    "Entrada Inválida", 
                    "O arquivo de entrada (OpenAPI) e o arquivo de saída (Markdown) são obrigatórios."
                )
                return False
            
            if not self._validate_file_path(input_file):
                messagebox.showerror(
                    "Arquivo Inválido", 
                    f"O arquivo de entrada não existe ou não é acessível: {input_file}"
                )
                return False
                
            # Validar diretório de saída
            output_dir = Path(output_file).parent
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    messagebox.showerror(
                        "Erro de Diretório", 
                        f"Não foi possível criar o diretório de saída: {e}"
                    )
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na validação de entradas: {e}")
            messagebox.showerror("Erro de Validação", f"Erro ao validar entradas: {e}")
            return False
    
    def _validate_file_path(self, file_path: str) -> bool:
        """Valida se um caminho de arquivo é seguro e existe."""
        try:
            if not file_path or not file_path.strip():
                return False
                
            path = Path(file_path)
            
            # Verificar se o arquivo existe
            if not path.exists() or not path.is_file():
                return False
                
            # Verificar se o caminho é absoluto ou relativo seguro
            if path.is_absolute():
                # Verificar se não contém componentes perigosos
                parts = path.parts
                dangerous_parts = {"..", "~", "$"}
                if any(part in dangerous_parts for part in parts):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao validar caminho do arquivo: {e}")
            return False
    
    def _validate_directory_path(self, dir_path: str) -> bool:
        """Valida se um caminho de diretório é seguro e existe."""
        try:
            if not dir_path or not dir_path.strip():
                return False
                
            path = Path(dir_path)
            
            # Verificar se o diretório existe
            if not path.exists() or not path.is_dir():
                return False
                
            # Verificar se o caminho é seguro
            if path.is_absolute():
                parts = path.parts
                dangerous_parts = {"..", "~", "$"}
                if any(part in dangerous_parts for part in parts):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao validar caminho do diretório: {e}")
            return False
    
    def _validate_language_tab(self, tab: str) -> bool:
        """Valida uma language tab."""
        try:
            # Verificar formato básico (deve conter ':')
            if ':' not in tab:
                return False
                
            # Verificar caracteres perigosos
            dangerous_chars = {'&', '|', ';', '`', '$', '(', ')', '<', '>', '\n', '\r'}
            if any(char in tab for char in dangerous_chars):
                return False
                
            return True
            
        except Exception:
            return False
    
    def _validate_flag(self, flag: str) -> bool:
        """Valida uma flag adicional."""
        try:
            # Lista de flags permitidas (whitelist)
            allowed_flags = {
                '--maxHeadingDepth', '--shallow', '--verbose', '--help',
                '--version', '--theme', '--search', '--includes'
            }
            
            # Verificar se é uma flag conhecida ou um valor
            if flag.startswith('--'):
                flag_name = flag.split('=')[0]  # Remover valor se houver
                return flag_name in allowed_flags
            else:
                # Valores devem ser seguros
                dangerous_chars = {'&', '|', ';', '`', '$', '(', ')', '<', '>'}
                return not any(char in flag for char in dangerous_chars)
                
        except Exception:
            return False
    
    def _get_widdershins_path(self) -> str:
        """Determina o caminho para o executável Widdershins."""
        try:
            # Primeiro, tentar Widdershins local
            local_path = Path(__file__).parent / "node_modules" / ".bin" / "widdershins"
            if sys.platform == "win32":
                local_path = local_path.with_suffix(".cmd")
            
            if local_path.exists():
                self.logger.info(f"Usando Widdershins local: {local_path}")
                return str(local_path)
            
            # Fallback para Widdershins global
            self.logger.info("Usando Widdershins global")
            return "widdershins"
            
        except Exception as e:
            self.logger.error(f"Erro ao determinar caminho do Widdershins: {e}")
            return "widdershins"
    
    def _handle_process_completion(self):
        """Manipula a conclusão do processo de geração."""
        try:
            self.generate_button.config(text="Gerar Documentação", state=tk.NORMAL)
            
            # Verificar resultado
            content = self.console_output.get("1.0", tk.END)
            if "--- SUCESSO!" in content:
                messagebox.showinfo("Sucesso", "Documentação gerada com sucesso!")
            elif "--- ERRO!" in content or "--- ERRO CRÍTICO" in content:
                messagebox.showerror(
                    "Erro na Geração", 
                    "Ocorreu um erro durante a geração. Verifique o console de saída para detalhes."
                )
            elif "--- TIMEOUT!" in content:
                messagebox.showwarning(
                    "Timeout", 
                    "A geração foi cancelada por exceder o tempo limite."
                )
                
        except Exception as e:
            self.logger.error(f"Erro ao manipular conclusão do processo: {e}")
    
    # --- Novos Métodos de UX ---
    
    def _on_drop(self, event):
        """Manipula arquivos arrastados para a interface."""
        try:
            files = self.root.tk.splitlist(event.data)
            if files:
                file_path = files[0]
                if self._validate_file_path(file_path):
                    self.input_file.set(file_path)
                    self._auto_name_output()
                    self._log_to_console(f"Arquivo carregado: {Path(file_path).name}\n")
        except Exception as e:
            self.logger.error(f"Erro no drag and drop: {e}")
    
    def _auto_name_output(self):
        """Sugere automaticamente o nome do arquivo de saída."""
        try:
            input_path = self.input_file.get().strip()
            if input_path:
                input_file = Path(input_path)
                output_name = input_file.stem + "_docs.md"
                output_path = input_file.parent / output_name
                self.output_file.set(str(output_path))
        except Exception as e:
            self.logger.error(f"Erro ao auto-nomear saída: {e}")
    
    def _build_language_tabs(self) -> List[str]:
        """Constrói a lista de language tabs baseada nos checkboxes."""
        tabs = []
        
        if self.lang_curl.get():
            tabs.append("'shell:cURL'")
        if self.lang_javascript.get():
            tabs.append("'javascript:Node.js'")
        if self.lang_python.get():
            tabs.append("'python:Python'")
        if self.lang_java.get():
            tabs.append("'java:Java'")
        if self.lang_go.get():
            tabs.append("'go:Go'")
        if self.lang_php.get():
            tabs.append("'php:PHP'")
        if self.lang_ruby.get():
            tabs.append("'ruby:Ruby'")
        if self.lang_csharp.get():
            tabs.append("'csharp:C#'")
            
        return tabs
    
    def _apply_preset(self, event=None):
        """Aplica um preset de configuração."""
        try:
            preset_name = self.preset_var.get()
            if preset_name in self.presets:
                preset = self.presets[preset_name]
                
                # Aplicar opções básicas
                self.opt_code.set(preset.get("opt_code", True))
                self.opt_summary.set(preset.get("opt_summary", True))
                self.opt_omit_header.set(preset.get("opt_omit_header", False))
                self.opt_raw.set(preset.get("opt_raw", False))
                self.opt_resolve.set(preset.get("opt_resolve", False))
                
                # Resetar todas as linguagens primeiro
                self.lang_curl.set(False)
                self.lang_javascript.set(False)
                self.lang_python.set(False)
                self.lang_java.set(False)
                self.lang_go.set(False)
                self.lang_php.set(False)
                self.lang_ruby.set(False)
                self.lang_csharp.set(False)
                
                # Aplicar linguagens do preset
                self.lang_curl.set(preset.get("lang_curl", False))
                self.lang_javascript.set(preset.get("lang_javascript", False))
                self.lang_python.set(preset.get("lang_python", False))
                self.lang_java.set(preset.get("lang_java", False))
                self.lang_go.set(preset.get("lang_go", False))
                
                self._log_to_console(f"Preset '{preset_name}' aplicado.\n")
        except Exception as e:
            self.logger.error(f"Erro ao aplicar preset: {e}")
    
    def _save_config(self):
        """Salva a configuração atual."""
        try:
            config = {
                "input_file": self.input_file.get(),
                "output_file": self.output_file.get(),
                "opt_code": self.opt_code.get(),
                "opt_summary": self.opt_summary.get(),
                "opt_omit_header": self.opt_omit_header.get(),
                "opt_raw": self.opt_raw.get(),
                "opt_resolve": self.opt_resolve.get(),
                "lang_curl": self.lang_curl.get(),
                "lang_javascript": self.lang_javascript.get(),
                "lang_python": self.lang_python.get(),
                "lang_java": self.lang_java.get(),
                "lang_go": self.lang_go.get(),
                "lang_php": self.lang_php.get(),
                "lang_ruby": self.lang_ruby.get(),
                "lang_csharp": self.lang_csharp.get(),
                "user_templates": self.user_templates.get(),
                "environment_file": self.environment_file.get(),
                "other_flags": self.other_flags.get()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar configuração: {e}")
    
    def _load_config(self):
        """Carrega configuração salva."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.input_file.set(config.get("input_file", ""))
                self.output_file.set(config.get("output_file", ""))
                self.opt_code.set(config.get("opt_code", True))
                self.opt_summary.set(config.get("opt_summary", True))
                self.opt_omit_header.set(config.get("opt_omit_header", False))
                self.opt_raw.set(config.get("opt_raw", False))
                self.opt_resolve.set(config.get("opt_resolve", False))
                
                # Carregar configurações de linguagem
                self.lang_curl.set(config.get("lang_curl", True))
                self.lang_javascript.set(config.get("lang_javascript", True))
                self.lang_python.set(config.get("lang_python", True))
                self.lang_java.set(config.get("lang_java", False))
                self.lang_go.set(config.get("lang_go", False))
                self.lang_php.set(config.get("lang_php", False))
                self.lang_ruby.set(config.get("lang_ruby", False))
                self.lang_csharp.set(config.get("lang_csharp", False))
                
                self.user_templates.set(config.get("user_templates", ""))
                self.environment_file.set(config.get("environment_file", ""))
                self.other_flags.set(config.get("other_flags", ""))
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
    
    def _load_config_dialog(self):
        """Carrega configuração de um arquivo específico."""
        try:
            file = filedialog.askopenfilename(
                title="Carregar Configuração",
                filetypes=[("JSON", "*.json"), ("Todos", "*.*")]
            )
            if file:
                with open(file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Aplicar todas as configurações
                self.input_file.set(config.get("input_file", ""))
                self.output_file.set(config.get("output_file", ""))
                self.opt_code.set(config.get("opt_code", True))
                self.opt_summary.set(config.get("opt_summary", True))
                self.opt_omit_header.set(config.get("opt_omit_header", False))
                self.opt_raw.set(config.get("opt_raw", False))
                self.opt_resolve.set(config.get("opt_resolve", False))
                
                # Linguagens
                self.lang_curl.set(config.get("lang_curl", True))
                self.lang_javascript.set(config.get("lang_javascript", True))
                self.lang_python.set(config.get("lang_python", True))
                self.lang_java.set(config.get("lang_java", False))
                self.lang_go.set(config.get("lang_go", False))
                self.lang_php.set(config.get("lang_php", False))
                self.lang_ruby.set(config.get("lang_ruby", False))
                self.lang_csharp.set(config.get("lang_csharp", False))
                
                self.user_templates.set(config.get("user_templates", ""))
                self.environment_file.set(config.get("environment_file", ""))
                self.other_flags.set(config.get("other_flags", ""))
                
                messagebox.showinfo("Sucesso", "Configuração carregada com sucesso!")
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar configuração: {e}")
    
    def _toggle_advanced(self):
        """Mostra/oculta opções avançadas."""
        if self.show_advanced.get():
            self.advanced_options_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=5)
        else:
            self.advanced_options_frame.grid_remove()
    
    def _preview_file(self):
        """Mostra preview do arquivo OpenAPI."""
        try:
            input_file = self.input_file.get().strip()
            if not input_file or not Path(input_file).exists():
                messagebox.showwarning("Aviso", "Selecione um arquivo OpenAPI válido primeiro.")
                return
            
            # Janela de preview
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"Preview: {Path(input_file).name}")
            preview_window.geometry("600x400")
            
            text_widget = ScrolledText(preview_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Ler e mostrar conteúdo
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Limitar a 10000 caracteres para performance
                if len(content) > 10000:
                    content = content[:10000] + "\n\n... (arquivo truncado para preview)"
                text_widget.insert(tk.END, content)
            
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            self.logger.error(f"Erro no preview: {e}")
            messagebox.showerror("Erro", f"Erro ao mostrar preview: {e}")
    
    def _validate_openapi(self):
        """Valida o arquivo OpenAPI."""
        try:
            input_file = self.input_file.get().strip()
            if not input_file or not Path(input_file).exists():
                messagebox.showwarning("Aviso", "Selecione um arquivo OpenAPI válido primeiro.")
                return
            
            # Validação básica de JSON/YAML
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                if input_file.endswith('.json'):
                    json.loads(content)
                    messagebox.showinfo("Validação", "✅ Arquivo JSON válido!")
                elif input_file.endswith(('.yaml', '.yml')):
                    # Validação básica para YAML
                    if 'openapi:' in content or 'swagger:' in content:
                        messagebox.showinfo("Validação", "✅ Arquivo YAML aparenta ser válido!")
                    else:
                        messagebox.showwarning("Validação", "⚠️ Arquivo pode não ser um OpenAPI válido.")
                else:
                    messagebox.showwarning("Validação", "⚠️ Formato de arquivo não reconhecido.")
            except json.JSONDecodeError as e:
                messagebox.showerror("Validação", f"❌ Erro no JSON: {e}")
                
        except Exception as e:
            self.logger.error(f"Erro na validação: {e}")
            messagebox.showerror("Erro", f"Erro ao validar arquivo: {e}")


# --- Ponto de Entrada (Main) ---
def main():
    """Função principal da aplicação."""
    root = None
    try:
        root = TkinterDnD.Tk()
        app = WiddershinsGUI(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nAplicação interrompida pelo usuário.")
    except Exception as e:
        logging.error(f"Erro fatal na aplicação: {e}")
        try:
            if root:
                root.destroy()
        except:
            pass
        
        # Fallback para mostrar erro
        try:
            root_fallback = tk.Tk()
            root_fallback.withdraw()
            messagebox.showerror(
                "Erro Crítico", 
                f"Ocorreu um erro fatal ao iniciar a aplicação:\n{e}"
            )
            root_fallback.destroy()
        except:
            print(f"Erro crítico: {e}")
    finally:
        try:
            if root:
                root.quit()
        except:
            pass

if __name__ == "__main__":
    main()