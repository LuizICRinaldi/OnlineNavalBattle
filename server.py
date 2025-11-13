import socket
import select
import sys
import time
import ast
import threading

from gameconfig import *

UDP_PORT = 5000
TCP_PORT = 5001
BROADCAST_MESSAGE = "Conectando"
MY_IP = '192.168.0.104' 


PARTICIPANTS = [MY_IP] 
socket_udp = None
socket_tcp = None


CLI_RUNNING = True 

def debug(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

# INICIALIZACAO DOS SOCKETS 

def init_sockets():
    """Inicializa UDP (5000) e TCP (5001)."""
    global socket_udp, socket_tcp
    
    # 1. Socket UDP
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    socket_udp.bind(('', UDP_PORT))
    
    # 2. Socket TCP
    socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_tcp.bind(('', TCP_PORT))
    socket_tcp.listen(5)
    
    debug(f"Sockets prontos. UDP:{UDP_PORT} TCP:{TCP_PORT}")

    return [socket_udp, socket_tcp]

#Envio e recebimento TCP para IP especifico

def send_tcp_message(ip, msg):
    """Envia mensagem TCP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((ip, TCP_PORT))
        s.send(msg.encode())
        return True
    except Exception:
        return False
    finally:
        s.close()

def handle_tcp_message(data, src_ip):
    """Processa mensagens TCP recebidas."""
    
    if data == "hit":
        confirma_ataque()
        print(f"\n[RESPOSTA TCP de {src_ip}]: Seu tiro atingiu uma embarcacao")
        return
    elif data == "destroyed":
        confirma_ataque()
        print(f"\n[RESPOSTA TCP de {src_ip}]:Seu tiro destruiu uma embarcacao!")
        return
    

    elif data.startswith("participantes:"):
        try:
            lst = ast.literal_eval(data.split(":", 1)[1].strip())
            for ip in lst:
                if ip not in PARTICIPANTS:
                    PARTICIPANTS.append(ip)
            PARTICIPANTS.sort()
            debug(f"Lista de participantes atualizada: {PARTICIPANTS}")
        except Exception:
            debug(f"Erro ao processar lista de {src_ip}.")
        return



def broadcast():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return s

def broadcast_connect():
    s = broadcast()
    s.sendto(BROADCAST_MESSAGE.encode(), ('255.255.255.255', UDP_PORT))
    s.close()

def broadcast_message(msg):
    s = broadcast()
    if msg.startswith("shot:"):
        coords_str = msg.split(":", 1)[1]
        l, c = map(int, coords_str.split(',')) 
        posicaoValida = marca_ataque(ataque, l, c)
        if posicaoValida:
            s.sendto(msg.encode(), ('255.255.255.255', UDP_PORT))
            print(f"Comando SHOT enviado via BROADCAST.")
        else: 
            print(f"Comando SHOT NAO enviado via BROADCAST.")  
    s.sendto(msg.encode(), ('255.255.255.255', UDP_PORT))
    print(f"Comando SHOT enviado via BROADCAST.")
    s.close()

def handle_udp_message(msg, src_ip):
    
    if src_ip == MY_IP: return
    
    if msg == BROADCAST_MESSAGE:
        debug(f"Recebi CONECTANDO de {src_ip}")
        if src_ip not in PARTICIPANTS:
            PARTICIPANTS.append(src_ip)
            PARTICIPANTS.sort()
            debug(f"-> {src_ip} adicionado.")
            print(PARTICIPANTS)
        send_participants(src_ip)
    
    

    elif msg.startswith("shot:"):
        try:
            myIpIndex = PARTICIPANTS.index(MY_IP)
            atackIPindex = 0
            if  myIpIndex == 0:
                atackIPindex = len(PARTICIPANTS) -1 
            else:
                atackIPindex = PARTICIPANTS.index(MY_IP) - 1

            if src_ip == PARTICIPANTS[atackIPindex]:

                coords_str = msg.split(":", 1)[1]
                l, c = map(int, coords_str.split(','))                
                resultado = detona(defesa,l,c)

                if resultado == "hit":
                    send_tcp_message(src_ip, "hit")
                    print(f"\n[TIRO RECEBIDO de {src_ip}]: Resposta TCP hit enviada.")
                if resultado == "destroyed":
                    if destruidos < 4:
                        send_tcp_message(src_ip, "destroyed")
                        print(f"\n[TIRO RECEBIDO de {src_ip}]: Resposta TCP destroyed enviada.")
                    else:
                        send_tcp_message(src_ip, "lost")
                        handle_cli_command("quit")
                        print(f"\n[TIRO RECEBIDO de {src_ip}]: Jogo perdido.")

                    
            sys.stdout.flush() 
        except Exception:
            debug(f"Erro ao processar tiro de {src_ip}.")

    elif msg.startswith("quit"):
        try:
            if src_ip in PARTICIPANTS:
                PARTICIPANTS.remove(src_ip)
                PARTICIPANTS.sort()
                debug(f"Participante {src_ip} saiu do jogo.")
            else:
                debug(f"Recebi QUIT de IP desconhecido: {src_ip}")

        except Exception as e:
            debug(f"Erro ao processar QUIT de {src_ip}. Erro: {e}")
            

def send_participants(ip):
    lst = list(dict.fromkeys(PARTICIPANTS))
    msg = "participantes:" + repr(lst)
    send_tcp_message(ip, msg)
        


def handle_cli_command(line):
    """Processa comandos digitados no terminal."""
    global CLI_RUNNING
    parts = line.split()
    if not parts: return
        
    cmd = parts[0].lower()
    
    if cmd == "participants":
        print(f"Lista de Participantes: {PARTICIPANTS}")
    
    elif cmd == "shot" and len(parts) == 3:
        try:
            x = int(parts[1])
            y = int(parts[2])
            if 0 <= x <= 9 and 0 <= y <= 9:
                message = f"shot:{x},{y}"
                broadcast_message(message)
            else:
                print("Coordenadas inválidas. Use números inteiros de 0 a 9.")
        except ValueError:
            print("Coordenadas devem ser números inteiros.")
    
    elif cmd == "quit":
        CLI_RUNNING = False # Sinaliza o fim da thread
        # Este sys.exit força o encerramento no loop principal.
        sys.exit(0)
        
    else:
        print("\nComandos disponíveis:")
        print("  participants - Exibe a lista de IPs conhecidos.")
        print("  shot <X> <Y> - Envia um tiro via BROADCAST (X, Y de 0 a 9).")
        print("  quit - Encerra o programa.")

def cli_thread_function():
    """Função que executa em uma thread separada para capturar o input."""
    global CLI_RUNNING
    while CLI_RUNNING:
        try:
            # input() é BLOQUEANTE, mas não afeta o Loop Principal
            line = input() 
            handle_cli_command(line)
        except EOFError:
            break # Fim da entrada (Ctrl+D)
        except SystemExit:
            # Captura o sys.exit do comando 'quit'
            break
        except Exception:
            if CLI_RUNNING:
                # Volta a mostrar o prompt
                sys.stdout.flush() 
                
# --- Loop Principal (MAIN) ---

def process_messages():
    """Loop principal: Inicia a thread CLI e gerencia os sockets com select."""
    
    socket_listen = init_sockets() 
    broadcast_connect()
    
    # 1. Inicia a thread de CLI (O comando 'input()' não vai bloquear o select)
    cli_thread = threading.Thread(target=cli_thread_function)
    cli_thread.daemon = True 
    cli_thread.start()
    global CLI_RUNNING
    
    print("\n--- Rede Inicializada. Digite 'help' para comandos. ---")
    
    try:
        while CLI_RUNNING:
            
            listen, escrita, erro = select.select(socket_listen, [], [], 0.001) 
            
            for ready_io in listen:
                if ready_io is socket_udp: 
                    data, addr = socket_udp.recvfrom(4096)
                    handle_udp_message(data.decode(errors='ignore').strip(), addr[0])
                
                elif ready_io is socket_tcp: 
                    conn, addr = socket_tcp.accept()
                    data = conn.recv(4096).decode().strip() 
                    conn.close()
                    handle_tcp_message(data, addr[0])
                
    except Exception as e:
        debug(f"Erro crítico no loop principal: {e}")
    finally:
        
        CLI_RUNNING = False # Garante que a thread da CLI pare
        if socket_udp: socket_udp.close()
        if socket_tcp: socket_tcp.close()
        debug("Conexões encerradas.")
        sys.exit(0)
