import os
import time
import sqlite3
from PIL import Image, ImageOps
from multiprocessing import Pool, cpu_count

DB_FILE = "processador.db"
DIRETORIO_SAIDA = "dados/saida"
LARGURA_ALVO = 1920  # Redimensiona as imagens para Full HD

def processar_imagem_task(payload):
    """
    Função paralela: Cada núcleo do seu processador vai pegar uma imagem
    da fila e rodar essa função de forma independente.
    """
    id_registro, caminho_entrada = payload
    inicio_individual = time.time()
    
    try:
        nome_base = os.path.splitext(os.path.basename(caminho_entrada))[0]
        caminho_final = os.path.join(DIRETORIO_SAIDA, f"{nome_base}.webp")
        
        with Image.open(caminho_entrada) as img:
            # 1. Redimensiona mantendo a proporção original
            img.thumbnail((LARGURA_ALVO, LARGURA_ALVO))
            # 2. Aplica o filtro de Tons de Cinza (Preto e Branco)
            img = ImageOps.grayscale(img)
            # 3. Converte e salva no formato otimizado WebP
            img.save(caminho_final, formato="WEBP", quality=80)
            
        tempo_gasto = (time.time() - inicio_individual) * 1000  # em milissegundos
        return id_registro, "Concluído", tempo_gasto
    except Exception as e:
        return id_registro, f"Erro: {str(e)}", 0.0

if __name__ == "__main__":
    # Cria a pasta de saída se ela não existir
    os.makedirs(DIRETORIO_SAIDA, exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Puxa do banco apenas as tarefas que estão marcadas como 'Pendente'
    cursor.execute("SELECT id, caminho_original FROM inventario_imagens WHERE status_processamento = 'Pendente';")
    linhas = cursor.fetchall()
    
    if not linhas:
        print("[!] Nenhuma imagem pendente encontrada no banco.")
        print("[!] Certifique-se de colocar as fotos na pasta 'dados/entrada' e rodar o 'cadastrar_banco.py' primeiro.")
        exit()
        
    nucleos = cpu_count()
    print(f"[*] Iniciando processamento paralelo de {len(linhas)} imagens usando {nucleos} núcleos de CPU...")
    
    # O Pool divide a lista de imagens entre as CPUs do seu PC automaticamente
    tempo_inicio_global = time.time()
    with Pool(processes=nucleos) as pool:
        resultados = pool.map(processar_imagem_task, linhas)
    tempo_total = time.time() - tempo_inicio_global
    
    print(f"\n[+] Processamento paralelo concluído em {tempo_total:.2f} segundos!")
    
    # Grava os resultados de performance de volta no SQLite
    print("[*] Gravando métricas de tempo e performance no banco de dados...")
    for id_reg, status, tempo_ms in resultados:
        cursor.execute(
            "UPDATE inventario_imagens SET status_processamento = ?, tempo_execucao_ms = ? WHERE id = ?;",
            (status, tempo_ms, id_reg)
        )
        
    conn.commit()
    cursor.close()
        
    conn.close()
    print("[+] Banco de dados atualizado com sucesso!")