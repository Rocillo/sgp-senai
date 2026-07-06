import sys
import os
import winreg

def register_protocol():
    # Caminho do executável do python e do script
    python_path = sys.executable
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "collector.py"))
    
    # Comando a ser executado pelo Windows
    # %1 representa o argumento de URL completo repassado pelo Windows
    command = f'"{python_path}" "{script_path}" "%1"'
    
    try:
        # Cria a chave hipot no HKEY_CLASSES_ROOT do usuário atual (não requer privilégios de Admin)
        key_path = r"Software\Classes\hipot"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:Hipot Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
        # Cria a subchave shell\open\command
        cmd_key_path = rf"{key_path}\shell\open\command"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_key_path) as cmd_key:
            winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
            
        print("==================================================")
        print(" Protocolo 'hipot://' registrado com sucesso!")
        print(" Agora o navegador pode chamar o coletor local.")
        print(f" Comando registrado: {command}")
        print("==================================================")
    except Exception as e:
        print(f"Erro ao registrar protocolo: {e}")

if __name__ == "__main__":
    register_protocol()
