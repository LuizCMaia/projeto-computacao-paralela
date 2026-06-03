import os
import time
import multiprocessing as mp
import numpy as np

# Oculta mensagens de log do TensorFlow no terminal
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

DIRETORIO_ENTRADA = "dados"
LIMITE_IMAGENS = 10000

# Variável global que vai existir de forma independente dentro de cada worker (processo)
modelo_ia_global = None

def inicializar_worker():
    """
    Função chamada apenas UMA VEZ por cada processo filho quando o Pool é criado.
    Carrega o modelo na memória daquele processo específico.
    """
    global modelo_ia_global
    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
    
    # Força o uso da CPU para evitar concorrência desordenada na GPU
    tf.config.set_visible_devices([], 'GPU')
    
    # Instancia o modelo na memória do processo filho
    modelo_ia_global = MobileNetV2(weights='imagenet')

def processar_imagem(caminho):
    """
    Função de inferência que os processos irão executar para cada imagem.
    """
    global modelo_ia_global
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
    
    try:
        # Prepara a imagem e passa pela IA do processo atual
        img = image.load_img(caminho, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        # Faz a previsão com o modelo que já está carregado
        previsoes = modelo_ia_global.predict(x, verbose=0)
        _ = decode_predictions(previsoes, top=1)[0][0] # Opcional: salvar ou usar o resultado
        
        return True
    except Exception:
        # Ignora arquivos corrompidos silenciosamente
        return False

def executar_paralelo():
    caminhos_imagens = []
    formatos_validos = ('.jpg', '.jpeg', '.png', '.webp')
    
    print(f"[*] Varrendo a pasta '{DIRETORIO_ENTRADA}' em busca de imagens...")
    
    for raiz, _, arquivos in os.walk(DIRETORIO_ENTRADA):
        for arquivo in arquivos:
            if arquivo.lower().endswith(formatos_validos):
                caminhos_imagens.append(os.path.join(raiz, arquivo))
                if len(caminhos_imagens) >= LIMITE_IMAGENS:
                    break
        if len(caminhos_imagens) >= LIMITE_IMAGENS:
            break

    total_imagens = len(caminhos_imagens)
    if total_imagens == 0:
        print("[!] Nenhuma imagem encontrada nas pastas.")
        return

    print(f"[*] Encontradas {total_imagens} imagens prontas para processamento.")

    # Lista com as quantidades de processos que você quer testar
    bateria_de_testes = [2, 4, 8, 12]

    for num_processos in bateria_de_testes:
        print(f"\n" + "="*50)
        print(f"[*] INICIANDO TESTE COM {num_processos} PROCESSOS SIMULTÂNEOS")
        print("="*50)
        
        tempo_inicio = time.time()
        
        # Cria um pool de trabalhadores. O 'initializer' carrega o modelo em cada um.
        with mp.Pool(processes=num_processos, initializer=inicializar_worker) as pool:
            # O chunksize=10 agrupa 10 imagens por vez para cada processo,
            # reduzindo o custo de comunicação entre os processos e o gerenciador central.
            pool.map(processar_imagem, caminhos_imagens, chunksize=10)
            
        tempo_total = time.time() - tempo_inicio
        print(f"[+] Finalizado com {num_processos} processos em: {tempo_total:.2f} segundos ({tempo_total / 60:.2f} minutos)\n")

if __name__ == "__main__":
    # Importante manter essa verificação (if __name__) para o multiprocessing rodar bem no Windows
    executar_paralelo()