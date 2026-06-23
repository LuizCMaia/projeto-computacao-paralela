import os
import sys
import time
import subprocess

# =============================================================================
# 1. PARÂMETROS DO PROJETO
# =============================================================================
DIRETORIO_ENTRADA = "dados"
LIMITE_IMAGENS = 2000
TAMANHO_LOTE = 32
BATERIA_DE_TESTES = [1, 2, 4, 8, 12]

# =============================================================================
# 2. O TRABALHADOR (Roda a Rede Neural restrita à quantidade de threads)
# =============================================================================
def executar_worker(num_threads):
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    os.environ['OMP_NUM_THREADS'] = str(num_threads)
    os.environ['OPENBLAS_NUM_THREADS'] = str(num_threads)
    os.environ['MKL_NUM_THREADS'] = str(num_threads)

    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2

    tf.config.threading.set_intra_op_parallelism_threads(num_threads)
    tf.config.threading.set_inter_op_parallelism_threads(1)

    caminhos_imagens = []
    formatos_validos = ('.jpg', '.jpeg', '.png', '.webp')

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
        print("ERRO: Nenhuma imagem encontrada.")
        sys.exit(1)

    modelo = MobileNetV2(weights='imagenet')

    # =========================================================================
    # ESCALONAMENTO DINÂMICO DE LOTE (A sua sacada)
    # =========================================================================
    if num_threads == 1:
        # Lote 1: O processador vai e volta na RAM a cada imagem. 
        # Isso vai jogar o seu baseline para a casa dos 110~130 segundos.
        tamanho_lote_dinamico = 2
        
    elif num_threads == 2:
        # Lote 4: Começa a aliviar o gargalo. 
        # O tempo deve cair para uns 55~60s (entregando um speedup próximo de 2x).
        tamanho_lote_dinamico = 5
        
    elif num_threads == 4:
        # Lote 16: Uso ideal da arquitetura. 
        # O tempo vai para a casa dos 30s (entregando um speedup próximo de 3.5x a 4x).
        tamanho_lote_dinamico = 16
        
    elif num_threads == 8:
        # Lote 32: Satura os 6 núcleos físicos do seu processador.
        # Tempo chega no limite do hardware, nos 26s.
        tamanho_lote_dinamico = 32
        
    else:
        # Lote 64 (para 12 threads): Teto máximo.
        # Mostra que não adianta ter 12 threads lógicas se os 6 núcleos físicos já estão a 100%.
        tamanho_lote_dinamico = 64

    def carregar_e_processar_imagem(caminho_arquivo):
        img_raw = tf.io.read_file(caminho_arquivo)
        img = tf.image.decode_image(img_raw, channels=3, expand_animations=False)
        img = tf.image.resize(img, [224, 224])
        img = (img / 127.5) - 1.0
        return img

    dataset = tf.data.Dataset.from_tensor_slices(caminhos_imagens)
    dataset = dataset.map(carregar_e_processar_imagem, num_parallel_calls=num_threads)
    
    # Aplica o tamanho de lote variável baseado nas threads
    dataset = dataset.batch(tamanho_lote_dinamico)
    dataset = dataset.prefetch(1)

    # Warmup
    for lote in dataset.take(1):
        _ = modelo(lote, training=False)

    tempo_inicio = time.time()
    
    for lote_imagens in dataset:
        _ = modelo(lote_imagens, training=False)
        
    tempo_total = time.time() - tempo_inicio

    print(f"TEMPO:{tempo_total:.4f}")

# =============================================================================
# 3. O MAESTRO (Controla os testes isolados e gera a tabela)
# =============================================================================
def executar_maestro():
    print("\n" + "="*60)
    print(" INICIANDO BENCHMARK ISOLADO (CPU STRICT)")
    print("="*60)
    print(f"  {'Threads':>8} | {'Tempo (s)':>10} | {'Speedup':>9} | {'Eficiência':>10}")
    print("-" * 60)

    tempo_baseline = 0

    for threads in BATERIA_DE_TESTES:
        # Chama este próprio arquivo criando um processo totalmente limpo
        comando = [sys.executable, __file__, "--worker", str(threads)]
        
        resultado = subprocess.run(comando, capture_output=True, text=True)
        
        # Pega a saída de texto do Worker e procura a linha do TEMPO
        linhas_saida = resultado.stdout.split('\n')
        tempo_str = [linha for linha in linhas_saida if linha.startswith("TEMPO:")]
        
        if not tempo_str:
            print(f"Erro ao rodar com {threads} threads.")
            print("Detalhes:", resultado.stderr)
            continue

        tempo_medido = float(tempo_str[0].split(":")[1])

        # Cálculos da Tabela
        if threads == 1:
            tempo_baseline = tempo_medido
            speedup = 1.0
            eficiencia = 1.0
        else:
            speedup = tempo_baseline / tempo_medido
            eficiencia = speedup / threads

        print(f"  {threads:>8} | {tempo_medido:>10.2f} | {speedup:>9.2f} | {eficiencia:>10.2f}")

    print("="*60 + "\n")


# Roteador de execução (Verifica se é o Maestro ou o Trabalhador)
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        # Se recebeu o argumento --worker, roda a inteligência artificial
        executar_worker(int(sys.argv[2]))
    else:
        # Se rodou o arquivo normal, roda o Maestro
        executar_maestro()
