import time
import urllib.request
import urllib.error
import json
import os
from PySide6.QtCore import QThread, Signal
from database import obter_testes_pendentes, marcar_como_sincronizado

CONFIG_FILE = "config.json"

def carregar_config():
    default_config = {
        "sgp_url": "http://localhost:5000"
    }
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
        except Exception:
            pass
        return default_config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            if "sgp_url" not in config:
                config["sgp_url"] = "http://localhost:5000"
            return config
    except Exception:
        return default_config


class SyncWorker(QThread):
    # status_signal: (sucesso, pendentes_restantes, mensagem_erro_ou_sucesso)
    status_signal = Signal(bool, int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.force_sync_trigger = False

    def trigger_sync(self):
        self.force_sync_trigger = True

    def run(self):
        # Aguarda 2 segundos na inicialização para a interface estar pronta e carregar logs
        time.sleep(2)
        
        while self.running:
            config = carregar_config()
            sgp_url = config["sgp_url"].rstrip("/")
            api_url = f"{sgp_url}/producao/gp/hipot/api/result"
            
            # Consulta testes pendentes no banco local
            try:
                pendentes = obter_testes_pendentes()
            except Exception as e:
                self.status_signal.emit(False, 0, f"Erro ao acessar banco local: {str(e)}")
                time.sleep(10)
                continue

            total_inicial = len(pendentes)
            if total_inicial > 0:
                sucesso_todos = True
                erro_msg = ""
                
                for test in pendentes:
                    if not self.running:
                        break
                        
                    payload = {
                        "serial": test["numero_serie"],
                        "status": test["resultado"],
                        "operador": test["operador"],
                        "relatorio": test["relatorio"],
                        "porta_com": test["porta_com"],
                        "baudrate": test["baudrate"],
                        "data_hora": test["data_hora"]
                    }
                    
                    try:
                        data = json.dumps(payload).encode('utf-8')
                        req = urllib.request.Request(
                            api_url,
                            data=data,
                            headers={'Content-Type': 'application/json'},
                            method='POST'
                        )
                        with urllib.request.urlopen(req, timeout=5) as response:
                            res_data = json.loads(response.read().decode('utf-8'))
                            if res_data.get("ok"):
                                marcar_como_sincronizado(test["id"])
                            else:
                                sucesso_todos = False
                                erro_msg = res_data.get("error", "Erro retornado do SGP")
                                break
                    except urllib.error.URLError as ue:
                        sucesso_todos = False
                        erro_msg = f"Servidor SGP offline ({ue.reason})"
                        break
                    except Exception as ex:
                        sucesso_todos = False
                        erro_msg = f"Erro de comunicação: {str(ex)}"
                        break
                
                # Recarrega pendentes para atualizar quantidade na UI
                try:
                    pendentes_restantes = len(obter_testes_pendentes())
                except Exception:
                    pendentes_restantes = total_inicial

                if sucesso_todos:
                    self.status_signal.emit(True, pendentes_restantes, f"Sincronizado ({total_inicial} enviados)")
                else:
                    self.status_signal.emit(False, pendentes_restantes, erro_msg)
            else:
                self.status_signal.emit(True, 0, "Banco de dados sincronizado")

            # Dorme por 30 segundos, ou acorda imediatamente se houver gatilho de sync manual/novo teste
            for _ in range(30):
                if not self.running:
                    break
                if self.force_sync_trigger:
                    self.force_sync_trigger = False
                    break
                time.sleep(1)

    def parar(self):
        self.running = False
        self.force_sync_trigger = True
        self.wait()
