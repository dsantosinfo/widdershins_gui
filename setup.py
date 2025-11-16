from cx_Freeze import setup, Executable
import sys

# Dependências que devem ser incluídas
build_exe_options = {
    "packages": ["tkinter", "tkinterdnd2", "subprocess", "threading", "queue", "json", "pathlib"],
    "excludes": ["unittest"],
    "include_files": [
        ("node_modules/", "node_modules/"),
        ("package.json", "package.json")
    ]
}

# Configuração para Windows
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="WiddershinsGUI",
    version="1.0.0",
    description="Interface gráfica para Widdershins",
    options={"build_exe": build_exe_options},
    executables=[Executable("widdershins_gui.py", base=base, target_name="WiddershinsGUI")]
)