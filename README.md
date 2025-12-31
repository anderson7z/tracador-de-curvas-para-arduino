# Traçador de Curvas I-V com Arduino e Python

Este projeto consiste em um sistema para traçar curvas Características I-V (Corrente vs Tensão) de componentes eletrônicos utilizando um Arduino e uma interface gráfica em Python.

O software em Python atua como um "Plotador Serial Genérico", recebendo dados enviados pelo Arduino via porta USB (Serial) e plotando-os em tempo real.

## 🚀 Funcionalidades

- **Plotagem em Tempo Real**: Visualização instantânea da curva característica à medida que o Arduino envia os dados.
- **Detecção Automática de Portas**: Identifica automaticamente as portas COM disponíveis no sistema.
- **Configuração de Conexão**: Seleção de Porta Serial e Baud Rate (velocidade de transmissão).
- **Controles de Visualização**:
  - Inversão de Eixos (trocar X por Y).
  - Alternar entre visualização apenas pontos ou pontos conectados por linhas.
  - Pausa e retomada da plotagem.
- **Exportação de Dados**:
  - Salvar os dados adquiridos em arquivo **CSV** (compatível com Excel).
  - Salvar o gráfico gerado como imagem (**PNG**).

## 🛠️ Requisitos

### Hardware
- Arduino (Uno, Nano, Mega, etc.)
- Sensores de Corrente/Tensão (Recomendado: **INA219** ou **INA226**)
- Circuito de controle de tensão (ex: DAC ou PWM filtrado controlando a base de um transistor/fonte de corrente).

### Software
- Python 3.x instalado.
- Bibliotecas Python necessárias:
  - `pyserial`
  - `matplotlib`
  - `numpy`
  - `tkinter` (Geralmente já vem instalado com o Python)

## 📦 Instalação

1. Clone ou baixe este repositório.
2. Instale as dependências do Python executando o seguinte comando no terminal:

```bash
pip install pyserial matplotlib numpy
```

## 📖 Como Usar

### 1. Arduino
Certifique-se de que seu Arduino está programado para enviar os dados pela porta Serial no seguinte formato (ou similar):
```text
<valor_x> <valor_y>
```
Exemplo: `2.5 0.015` (onde 2.5 pode ser a tensão e 0.015 a corrente). O separador pode ser espaço, vírgula ou outro caractere não numérico.

### 2. Python
1. Execute o script Python:
   ```bash
   python tracador_curvas_arduino.py
   ```
2. Na janela que abrir:
   - Selecione a **Porta COM** onde o Arduino está conectado.
   - Selecione o **Baud Rate** (deve ser o mesmo configurado no código do Arduino, padrão sugerido: 9600).
   - Clique em **Conectar**.
3. O gráfico começará a ser desenhado automaticamente conforme os dados chegam.

## ⚙️ Compilando para Executável (.exe)

Se você deseja gerar um arquivo `.exe` para rodar sem precisar instalar o Python, utilize o `pyinstaller`:

1. Instale o PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Gere o executável:
   ```bash
   pyinstaller --noconsole --onefile tracador_curvas_arduino.py
   ```
3. O arquivo executável estará na pasta `dist`.

## 📄 Estrutura do Projeto

- `tracador_curvas_arduino.py`: Código fonte principal da interface gráfica.
- `README.md`: Documentação do projeto.
