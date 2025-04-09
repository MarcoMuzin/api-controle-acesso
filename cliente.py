import requests
import uuid
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pyautogui
import threading
import time
import cv2
import os
import pygame
import numpy as np

IMAGENS_PASTA = "imagens"
AUDIOS_PASTA = "audios"
API_URL = "https://controle-acesso-api.onrender.com"

itens_ferir = ["Bless", "Claw", "Splinter"]
joias = ["Gemstone", "Jewel"]
selecionados = {}
monitorando = False

def obter_id_maquina():
    return str(uuid.getnode())

def enviar_id_para_api():
    user_id = obter_id_maquina()
    for i in range(3):
        try:
            resposta = requests.post(f"{API_URL}/registrar", json={"id": user_id})
            if resposta.status_code == 200:
                print("✅ ID registrado com sucesso.")
                return
            elif resposta.status_code == 403:
                print("⚠️ Limite de usuários atingido. Entre em contato com o suporte.")
                return
            else:
                print(f"⚠️ Tentativa {i+1} falhou. Status: {resposta.status_code}")
        except Exception as e:
            print(f"❌ Tentativa {i+1} erro: {e}")
        time.sleep(3)
    print("❌ Todas as tentativas de registro falharam.")

def verificar_acesso_remoto(login, senha):
    user_id = obter_id_maquina()
    try:
        resposta = requests.get(f"{API_URL}/verificar", params={"id": user_id, "login": login, "senha": senha})
        if resposta.status_code == 200:
            dados = resposta.json()
            status = dados.get("status")
            if status == "liberado":
                print("✅ Acesso liberado.")
                return True
            elif status == "trial":
                dias_restantes = dados.get("dias_restantes", 0)
                if dias_restantes > 0:
                    print(f"🕒 Trial ativo. Dias restantes: {dias_restantes}")
                    return True
                else:
                    print("❌ Trial expirado.")
            else:
                print("⛔ Acesso bloqueado.")
        elif resposta.status_code == 403:
            print("❌ Credenciais inválidas ou acesso negado.")
        else:
            print(f"⚠️ Erro inesperado: {resposta.status_code}")
    except Exception as e:
        print(f"❌ Erro de conexão com a API: {e}")
    return False

def tocar_som(item):
    caminho_audio = os.path.join(AUDIOS_PASTA, f"{item}.mp3")
    if os.path.exists(caminho_audio):
        pygame.mixer.init()
        pygame.mixer.music.load(caminho_audio)
        pygame.mixer.music.play()

def procurar_item(item):
    caminho_imagem = os.path.join(IMAGENS_PASTA, f"{item}.png")
    if not os.path.exists(caminho_imagem):
        return
    imagem = cv2.imread(caminho_imagem)
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    resultado = cv2.matchTemplate(screenshot, imagem, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(resultado)
    if max_val > 0.8:
        print(f"🎯 {item} detectado!")
        tocar_som(item)

def monitorar():
    global monitorando
    while monitorando:
        for item, var in selecionados.items():
            if var.get():
                procurar_item(item)
        time.sleep(1)

def iniciar_monitoramento():
    global monitorando
    monitorando = True
    threading.Thread(target=monitorar, daemon=True).start()

def parar_monitoramento():
    global monitorando
    monitorando = False

def sair():
    parar_monitoramento()
    janela_principal.destroy()

def criar_interface():
    global janela_principal
    janela_principal = tk.Tk()
    janela_principal.title("Monitoramento de Itens - Mu C.A Brasil")
    janela_principal.geometry("600x400")
    janela_principal.configure(bg="#0d1117")

    try:
        imagem_fundo = Image.open("imagens/logo.png").resize((150, 150))
        imagem_tk = ImageTk.PhotoImage(imagem_fundo)
        tk.Label(janela_principal, image=imagem_tk, bg="#0d1117").place(relx=0.5, rely=0.08, anchor="n")
        janela_principal.image = imagem_tk
    except:
        pass

    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("TNotebook", background="#0d1117", borderwidth=0)
    estilo.configure("TNotebook.Tab", background="#161b22", foreground="lime", padding=10)
    estilo.map("TNotebook.Tab", background=[("selected", "#238636")])

    notebook = ttk.Notebook(janela_principal)
    aba_monitoramento = ttk.Frame(notebook)
    notebook.add(aba_monitoramento, text="Monitoramento")
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    def criar_subaba(pai, titulo, itens):
        frame = ttk.Labelframe(pai, text=titulo, padding=10)
        frame.pack(fill="x", padx=5, pady=5)
        for item in itens:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(frame, text=item, variable=var, bg="#0d1117", fg="skyblue", selectcolor="#0d1117")
            chk.pack(anchor="w")
            selecionados[item] = var

    criar_subaba(aba_monitoramento, "Itens Ferir", itens_ferir)
    criar_subaba(aba_monitoramento, "Joias", joias)

    frame_botoes = tk.Frame(janela_principal, bg="#0d1117")
    frame_botoes.pack(pady=10)
    tk.Button(frame_botoes, text="Iniciar", command=iniciar_monitoramento, bg="#238636", fg="white", width=10).pack(side="left", padx=5)
    tk.Button(frame_botoes, text="Parar", command=parar_monitoramento, bg="#da3633", fg="white", width=10).pack(side="left", padx=5)
    tk.Button(frame_botoes, text="Sair", command=sair, bg="#484f58", fg="white", width=10).pack(side="left", padx=5)

    janela_principal.mainloop()

# Execução principal
if __name__ == "__main__":
    enviar_id_para_api()
    login = input("🔐 Digite seu login: ")
    senha = input("🔐 Digite sua senha: ")
    if verificar_acesso_remoto(login, senha):
        criar_interface()
    else:
        print("⛔ Acesso negado. Encerrando.")
        sys.exit()
