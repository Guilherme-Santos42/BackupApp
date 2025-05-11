import os
import time
import zipfile
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Backup Profissional - Manual & Automático")
        self.root.geometry("600x600")
        self.root.resizable(False, False)

        self.pastas_origem = []
        self.pasta_destino = ""
        self.intervalo_segundos = 3600  # 1 hora
        self.tamanho_max_backup_mb = 500
        self.backup_rodando = False
        self.backups_feitos = {}
        self.historico_log = "log.txt"

        self.criar_interface()

    def criar_interface(self):
        # Frame seleção de pastas
        frame_pastas = tk.LabelFrame(self.root, text="Pastas para Backup", padx=10, pady=10)
        frame_pastas.pack(padx=10, pady=5, fill="x")

        botoes_frame = tk.Frame(frame_pastas)
        botoes_frame.pack(fill="x")

        tk.Button(botoes_frame, text="Adicionar Pasta", command=self.adicionar_pasta).pack(side="left", padx=5)
        tk.Button(botoes_frame, text="Remover Todas", command=self.remover_todas_pastas).pack(side="left", padx=5)

        self.lista_pastas = tk.Listbox(frame_pastas, width=80, height=5)
        self.lista_pastas.pack(pady=5)

        # Frame destino
        frame_destino = tk.LabelFrame(self.root, text="Pasta de Destino", padx=10, pady=10)
        frame_destino.pack(padx=10, pady=5, fill="x")

        tk.Button(frame_destino, text="Selecionar Pasta Destino", command=self.selecionar_destino).pack(pady=5)

        # Frame Backup Manual
        frame_manual = tk.LabelFrame(self.root, text="Backup Manual", padx=10, pady=10)
        frame_manual.pack(padx=10, pady=5, fill="x")

        tk.Button(frame_manual, text="Fazer Backup Manual", command=self.fazer_backup_manual).pack(pady=5)

        # Frame Backup Automático
        frame_auto = tk.LabelFrame(self.root, text="Backup Automático", padx=10, pady=10)
        frame_auto.pack(padx=10, pady=5, fill="x")

        tk.Label(frame_auto, text="Intervalo (min):").grid(row=0, column=0, sticky="w")
        self.entrada_intervalo = tk.Entry(frame_auto, width=5)
        self.entrada_intervalo.insert(0, "60")
        self.entrada_intervalo.grid(row=0, column=1, padx=5)

        tk.Label(frame_auto, text="Limite Espaço (MB):").grid(row=0, column=2, sticky="w")
        self.entrada_limite = tk.Entry(frame_auto, width=5)
        self.entrada_limite.insert(0, "500")
        self.entrada_limite.grid(row=0, column=3, padx=5)

        self.botao_automatico = tk.Button(frame_auto, text="Iniciar Backup Automático", command=self.toggle_backup_automatico)
        self.botao_automatico.grid(row=1, column=0, columnspan=4, pady=10)

        # Barra de progresso
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        # Status
        self.status_label = tk.Label(self.root, text="Status: Aguardando ação...", fg="blue")
        self.status_label.pack(pady=5)

    def adicionar_pasta(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.pastas_origem.append(pasta)
            self.lista_pastas.insert(tk.END, pasta)

    def remover_todas_pastas(self):
        self.pastas_origem.clear()
        self.lista_pastas.delete(0, tk.END)
        self.status_label.config(text="Status: Todas as pastas removidas", fg="red")

    def selecionar_destino(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.pasta_destino = pasta
            messagebox.showinfo("Destino Selecionado", f"Pasta destino definida:\n{pasta}")
            self.status_label.config(text="Status: Pasta de destino selecionada", fg="green")

    def escrever_log(self, mensagem):
        with open(self.historico_log, 'a') as log:
            agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log.write(f"[{agora}] {mensagem}\n")

    def calcular_tamanho_destino(self):
        total = 0
        for dirpath, _, filenames in os.walk(self.pasta_destino):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total += os.path.getsize(fp)
        return total / (1024 * 1024)  # Em MB

    def atualizar_progresso(self, valor_atual, valor_max):
        # Atualiza a barra de progresso na thread principal
        self.progress["value"] = valor_atual
        self.progress["maximum"] = valor_max
        self.root.update_idletasks()

    def realizar_backup(self):
        if not self.pastas_origem or not self.pasta_destino:
            messagebox.showwarning("Erro", "Configure pastas antes de iniciar o backup!")
            return

        agora = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        nome_zip = os.path.join(self.pasta_destino, f'backup_{agora}.zip')

        total_arquivos = sum(len(files) for folder in self.pastas_origem for _, _, files in os.walk(folder))
        arquivo_atual = 0

        # Atualiza a barra de progresso
        self.atualizar_progresso(arquivo_atual, total_arquivos)

        with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            for pasta in self.pastas_origem:
                for raiz, dirs, arquivos in os.walk(pasta):
                    for arquivo in arquivos:
                        caminho_completo = os.path.join(raiz, arquivo)
                        caminho_relativo = os.path.relpath(caminho_completo, start=pasta)

                        # Backup incremental
                        if caminho_completo not in self.backups_feitos or \
                           os.path.getmtime(caminho_completo) > self.backups_feitos.get(caminho_completo, 0):
                            backup_zip.write(caminho_completo, arcname=os.path.join(os.path.basename(pasta), caminho_relativo))
                            self.backups_feitos[caminho_completo] = os.path.getmtime(caminho_completo)

                        arquivo_atual += 1
                        # Atualiza a barra de progresso usando o after
                        self.root.after(0, self.atualizar_progresso, arquivo_atual, total_arquivos)

        self.escrever_log(f"Backup criado: {nome_zip}")
        self.status_label.config(text=f"Status: Backup realizado ({nome_zip})", fg="green")
        self.atualizar_progresso(0, 100)

    def fazer_backup_manual(self):
        self.status_label.config(text="Status: Fazendo backup manual...", fg="orange")
        threading.Thread(target=self.realizar_backup, daemon=True).start()

    def agendar_backups(self):
        while self.backup_rodando:
            if self.calcular_tamanho_destino() < self.tamanho_max_backup_mb:
                self.status_label.config(text="Status: Fazendo backup automático...", fg="orange")
                self.realizar_backup()
            else:
                msg = "Espaço excedido! Backup não realizado."
                self.escrever_log(msg)
                self.status_label.config(text=f"Status: {msg}", fg="red")

            time.sleep(self.intervalo_segundos)

    def toggle_backup_automatico(self):
        if not self.pastas_origem or not self.pasta_destino:
            messagebox.showwarning("Erro", "Configure pastas antes de iniciar o backup automático!")
            return

        if not self.backup_rodando:
            try:
                self.intervalo_segundos = int(self.entrada_intervalo.get()) * 60
                self.tamanho_max_backup_mb = int(self.entrada_limite.get())
            except ValueError:
                messagebox.showerror("Erro", "Preencha intervalo e limite corretamente!")
                return

            self.backup_rodando = True
            threading.Thread(target=self.agendar_backups, daemon=True).start()
            self.botao_automatico.config(text="Parar Backup Automático")
            self.escrever_log("Backup automático iniciado.")
            self.status_label.config(text="Status: Backup automático iniciado", fg="green")
        else:
            self.backup_rodando = False
            self.botao_automatico.config(text="Iniciar Backup Automático")
            self.escrever_log("Backup automático parado.")
            self.status_label.config(text="Status: Backup automático parado", fg="blue")

if __name__ == "__main__":
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()
