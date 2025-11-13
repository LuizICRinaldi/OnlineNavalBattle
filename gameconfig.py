import random
import sys

inimigos = 14
derrubados = 0

destruidos = 0

linhas = 10
colunas = 10
embarcacoes = {
    "PortaAvioes": 5,
    "Bombardeiro": 4,
    "Submarino": 3,
    "Lancha": 2
}

def criar_grid(linhas, colunas):
    return [[0 for i in range(colunas)] for j in range(linhas)]

defesa = criar_grid(linhas, colunas)
ataque = criar_grid(linhas, colunas)

def exibir_grid(grid):
    print(f"\n--- Grid ---")
    
    header = "   " + " ".join(str(i) for i in range(colunas))
    print(header)
    print("  " + "-" * (colunas * 2 - 1))
    
    # Exibição das Linhas
    for i, row in enumerate(grid):
        display_row = [str(cell) for cell in row]
        print(f"{i}| {' '.join(display_row)}")
    print("------------------------")


# FUNCOES PARA POSICIONAR O CAMPO DE DEFESA

def verificar_posicao(grid, linha_inicial, coluna_inicial, tamanho, orientacao):

    l, c = linha_inicial, coluna_inicial
    
    # Verifica no grid
    if not (0 <= l < linhas and 0 <= c < colunas):
        return False

    if orientacao == 1: # Horizontal
        if c + tamanho > colunas:
            return False
       
        for c in range(c, c + tamanho):
            if grid[l][c] != 0:
                return False
                
    else: # Vertical
      
        if l + tamanho > linhas:
            return False
        
        for l in range(l, l + tamanho):
            if grid[l][c] != 0:
                return False
                
    return True

def colocar_navio(grid, nome_navio, tamanho):
    # 1 = horizontal
    while True:
        
        try:
            entrada = input(f"Posicione {nome_navio} ({tamanho} uni). Digite 1 se quiser que seja na horizontal: ")
            if entrada == "1":
                orientacao = 1
            else:
                orientacao = 0
     
            l = input(f"Posicione {nome_navio} ({tamanho} uni). Digite o numero da linha 0-9: ")
            c = input(f"Posicione {nome_navio} ({tamanho} uni). Digite o numero da coluna 0-9: ")
            l, c = int(l), int(c)
            
            
            if verificar_posicao(grid, l, c, tamanho, orientacao):
                
                # Inserção no Grid
                verifica_insere(grid, l, c, tamanho, orientacao)
                        
                print(f"{nome_navio} colocado com sucesso.")
                exibir_grid(grid)
                return
            else:
                print("Posição inválida: fora do tabuleiro ou colidindo com outro navio. Tente novamente.")

        
                
        except (ValueError, IndexError):
            print("Entrada inválida. Verifique se usou inteiro. As coordenadas devem ser de 0 a 9.")
        exibir_grid(grid)

def iniciar_posicionamento(grid_defesa):
    print("\n===========================================")
    print("      INÍCIO DA FASE DE POSICIONAMENTO     ")
    print("===========================================")
    manual = input("Digite 1 se voce quer posicionar manualmente: ")
    if manual == "1":
        print("\n--- INSERÇAO MANUAL. ---")
        for nome_navio, tamanho in embarcacoes.items():
            colocar_navio(grid_defesa, nome_navio, tamanho) 
    else:
        print("\n--- INSERÇAO ALEATORIA. ---")
        posicionar_navios_aleatoriamente(grid_defesa)

    exibir_grid(grid_defesa)
    print("\n--- TODOS OS NAVIOS POSICIONADOS. ---")

def posicionar_navios_aleatoriamente(grid_defesa):

    
    for nome, tamanho in embarcacoes.items():
        posicionado = False
        
        while not posicionado:
            orientacao = random.choice([1, 0])
            
            if orientacao == 1:
                max_c = colunas - tamanho
                l = random.randint(0, linhas - 1)
                c = random.randint(0, max_c)
            else: 
                max_l = linhas - tamanho
                l = random.randint(0, max_l)
                c = random.randint(0, colunas - 1)

            if verificar_posicao(grid_defesa, l, c, tamanho, orientacao):
                
                # Coloca o Navio no Grid
                verifica_insere(grid_defesa, l, c, tamanho, orientacao)
                        
                posicionado = True
            
    exibir_grid(grid_defesa)
    print("\n--- TODOS OS NAVIOS POSICIONADOS AUTOMATICAMENTE. ---")
    return True

def verifica_insere(grid_defesa, l, c, tamanho, orientacao):
    if orientacao == 1:
        for col in range(c, c + tamanho):
            grid_defesa[l][col] = tamanho
    else:
        for linha in range(l, l + tamanho):
            grid_defesa[linha][c] = tamanho


# FUNCOES RECEBER ATAQUE

def detona(grid_defesa, l, c):
    global destruidos
    local = grid_defesa[l][c] 
    
    if not isinstance(ataque, int) or local == 0:
        grid_defesa[l][c] = 'X' 
        return "miss"
        
    
    grid_defesa[l][c] = 'X' 
    
   
    direcoes = [
        (0, 1), (0, -1),  # Horizontal
        (1, 0), (-1, 0)   # Vertical
    ]
    
    # O navio ainda está vivo?
    navio_vivo = False
    
    for dL, dC in direcoes:
        # Posição adjacente
        nL, nC = l + dL, c + dC
        
        # Percorre o navio nas direções para ver se encontra outra parte intacta (marcador == tamanho_navio)
        for i in range(1, local): # Checa até o tamanho máximo do navio
            if 0 <= nL < linhas and 0 <= nC < colunas:
                parte_adjacente = grid_defesa[nL][nC]
                
                # Se encontrar uma parte INTÁCTA do navio (o marcador original)
                if isinstance(parte_adjacente, int) and parte_adjacente == local:
                    navio_vivo = True
                    break # Encontramos uma parte intacta, navio vivo
                
                # Se encontrarmos uma célula vazia (0) ou um erro ('O'), a direção acabou
                if parte_adjacente == 0 or parte_adjacente == 'O':
                    break
                
                # Move para o próximo passo na mesma direção
                nL, nC = nL + dL, nC + dC
            else:
                break # Saiu do tabuleiro

        if navio_vivo:
            break
            
    if navio_vivo:
        return "hit"
    else:
        destruidos = destruidos + 1
        return "destroyed"

def marca_ataque(ataque, l, c):
    if ataque[l][c] != "X":
        ataque[l][c] = "X"
        exibir_grid(ataque)
        return True
    exibir_grid(ataque)
    return False
        
    

def confirma_ataque():
    global derrubados
    derrubados = derrubados + 1
    



def principal():
    iniciar_posicionamento(defesa)


