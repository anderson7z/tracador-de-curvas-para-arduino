import sys
import re
import threading
import time
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import serial
    import serial.tools.list_ports
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import numpy as np
except Exception as e:
    print(f"Erro ao importar bibliotecas: {e}")
    sys.exit(1)

# --- Configurações Padrão ---
DEFAULT_BAUD = 9600
MAX_POINTS_DISPLAY = 2000 # Limita o gráfico para não travar se tiver muitos dados

class SerialPlotter:
    def __init__(self, root):
        self.root = root
        self.root.title("Plotador Serial Genérico (X vs Y)")
        self.root.geometry("1100x700")

        # Variáveis de Controle
        self.serial_port = None
        self.is_connected = False
        self.is_paused = False
        self.data_x = []
        self.data_y = []
        
        # Variáveis da Interface
        self.invert_axes = tk.BooleanVar(value=False)
        self.baud_rate = tk.StringVar(value="9600")
        self.line_style = tk.BooleanVar(value=True) # True = Linha, False = Apenas Pontos
        self.status_text = tk.StringVar(value="Desconectado")

        self.setup_ui()
        self.setup_plot()

    def setup_ui(self):
        # --- Frame de Controle Superior ---
        control_frame = ttk.LabelFrame(self.root, text="Configuração da Conexão", padding="5")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Seleção de Porta
        ttk.Label(control_frame, text="Porta:").pack(side=tk.LEFT, padx=5)
        self.port_combo = ttk.Combobox(control_frame, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        self.refresh_ports()
        
        ttk.Button(control_frame, text="↻", width=3, command=self.refresh_ports).pack(side=tk.LEFT, padx=2)

        # Seleção de Baud Rate
        ttk.Label(control_frame, text="Baud:").pack(side=tk.LEFT, padx=5)
        bauds = ["9600", "14400", "19200", "38400", "57600", "115200", "230400", "250000"]
        self.baud_combo = ttk.Combobox(control_frame, width=10, textvariable=self.baud_rate, values=bauds)
        self.baud_combo.pack(side=tk.LEFT, padx=5)

        # Botão Conectar
        self.btn_connect = ttk.Button(control_frame, text="Conectar", command=self.toggle_connection)
        self.btn_connect.pack(side=tk.LEFT, padx=10)

        # --- Frame de Ferramentas do Gráfico ---
        tools_frame = ttk.LabelFrame(self.root, text="Opções do Gráfico", padding="5")
        tools_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(tools_frame, text="Inverter Eixos (Trocar X/Y)", variable=self.invert_axes).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(tools_frame, text="Unir pontos com linha", variable=self.line_style).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(tools_frame, text="Limpar Gráfico", command=self.clear_data).pack(side=tk.LEFT, padx=10)
        
        self.btn_pause = ttk.Button(tools_frame, text="Pausar Plotagem", command=self.toggle_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=10)

        # Botões de Salvar (Lado direito)
        ttk.Button(tools_frame, text="Salvar CSV", command=self.save_csv).pack(side=tk.RIGHT, padx=5)
        ttk.Button(tools_frame, text="Salvar Imagem", command=self.save_image).pack(side=tk.RIGHT, padx=5)

        # --- Barra de Status ---
        status_bar = ttk.Label(self.root, textvariable=self.status_text, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_plot(self):
        # Configuração do Matplotlib
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.fig.subplots_adjust(bottom=0.15, left=0.10)
        
        self.ax.set_title("Dados em Tempo Real")
        self.ax.set_xlabel("Eixo X")
        self.ax.set_ylabel("Eixo Y")
        self.ax.grid(True, linestyle='--', alpha=0.7)

        # Inicializa a linha do gráfico
        self.line, = self.ax.plot([], [], 'o-', markersize=4, linewidth=1, color='#007acc')

        # Canvas Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Barra de ferramentas nativa do Matplotlib (Zoom, Pan, Save)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Animação
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=100, blit=False, cache_frame_data=False)

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)
        else:
            self.port_combo.set("")

    def toggle_connection(self):
        if not self.is_connected:
            try:
                port = self.port_combo.get()
                baud = int(self.baud_rate.get())
                
                if not port:
                    messagebox.showwarning("Aviso", "Selecione uma porta COM.")
                    return

                self.serial_port = serial.Serial(port, baud, timeout=1)
                self.serial_port.flushInput()
                
                self.is_connected = True
                self.btn_connect.config(text="Desconectar")
                self.status_text.set(f"Conectado a {port} @ {baud} bps")
                
                # Inicia Thread de Leitura
                self.read_thread = threading.Thread(target=self.read_serial_loop, daemon=True)
                self.read_thread.start()
                
            except Exception as e:
                messagebox.showerror("Erro de Conexão", str(e))
        else:
            self.disconnect()

    def disconnect(self):
        self.is_connected = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.btn_connect.config(text="Conectar")
        self.status_text.set("Desconectado")

    def read_serial_loop(self):
        while self.is_connected:
            try:
                if self.serial_port.in_waiting:
                    raw_line = self.serial_port.readline()
                    try:
                        line = raw_line.decode('utf-8', errors='ignore').strip()
                        if line:
                            self.parse_data(line)
                    except:
                        pass
            except Exception as e:
                print(f"Erro na thread: {e}")
                break
            time.sleep(0.005) # Pequeno sleep para não fritar a CPU

    def parse_data(self, line):
        """
        Tenta extrair dois números de qualquer string.
        Exemplos aceitos: "10 20", "10, 20", "(10, 20)", "x:10 y:20"
        """
        # Regex para encontrar números (inteiros ou floats com ponto)
        numbers = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line)
        
        if len(numbers) >= 2:
            try:
                # Pega os dois primeiros números encontrados
                val1 = float(numbers[0])
                val2 = float(numbers[1])
                
                # Armazena (protegendo a lista se necessário, mas em Py append é thread-safe)
                self.data_x.append(val1)
                self.data_y.append(val2)
                
                # Log no console para debug
                # print(f"Recebido: {val1}, {val2}")
                
            except ValueError:
                pass

    def update_plot(self, frame):
        if self.is_paused or not self.data_x:
            return

        # Copia dados para plotagem para evitar conflito com a thread de leitura
        x_plot = list(self.data_x)
        y_plot = list(self.data_y)
        
        # Inverter Eixos se a opção estiver marcada
        if self.invert_axes.get():
            x_final = y_plot
            y_final = x_plot
            self.ax.set_xlabel("Y (Serial 2º Valor)")
            self.ax.set_ylabel("X (Serial 1º Valor)")
        else:
            x_final = x_plot
            y_final = y_plot
            self.ax.set_xlabel("X (Serial 1º Valor)")
            self.ax.set_ylabel("Y (Serial 2º Valor)")

        # Estilo da Linha
        fmt = 'o-' if self.line_style.get() else 'o'
        self.line.set_linestyle('-' if self.line_style.get() else 'None')
        self.line.set_marker('o')

        self.line.set_data(x_final, y_final)
        
        # Ajuste automático dos eixos
        self.ax.relim()
        self.ax.autoscale_view()
        
        # Se você quiser que o gráfico "corra" (mostrando apenas os ultimos N pontos)
        # Descomente abaixo se preferir janelas deslizantes
        # if len(x_final) > 50:
        #     self.ax.set_xlim(min(x_final[-50:]), max(x_final[-50:]))

        self.canvas.draw()

    def clear_data(self):
        self.data_x = []
        self.data_y = []
        self.line.set_data([], [])
        self.canvas.draw()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        text = "Retomar Plotagem" if self.is_paused else "Pausar Plotagem"
        self.btn_pause.config(text=text)

    def save_csv(self):
        if not self.data_x:
            messagebox.showwarning("Aviso", "Não há dados para salvar.")
            return
            
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["X_Original", "Y_Original"])
                    for x, y in zip(self.data_x, self.data_y):
                        writer.writerow([x, y])
                messagebox.showinfo("Sucesso", "Arquivo salvo com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def save_image(self):
        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if filename:
            try:
                self.fig.savefig(filename, dpi=300)
                messagebox.showinfo("Sucesso", "Imagem salva com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar imagem: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialPlotter(root)
    
    # Tratamento para fechar corretamente
    def on_closing():
        app.disconnect()
        root.destroy()
        sys.exit(0)
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()