import os
import time
import multiprocessing as mp
import numpy as np

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

DIRETORIO_ENTRADA = "dados"
LIMITE_IMAGENS = 2000
TOTAL_NUCLEOS_FISICOS = 6  # Ryzen 5 5600X — ajuste se rodar em outra máquina

modelo_ia_global = None

def inicializar_worker(num_processos: int):
    """
    Função chamada apenas UMA VEZ por cada processo filho quando o Pool é criado.
    Carrega o modelo na memória daquele processo específico.

    A chave da eficiência: cada processo recebe apenas sua fatia dos núcleos físicos.
    Ex: 2 processos → 3 threads cada | 6 processos → 1 thread cada
    Isso evita que os processos briguem pelos mesmos núcleos do CPU.
    """
    global modelo_ia_global

    threads_por_processo = max(1, TOTAL_NUCLEOS_FISICOS // num_processos)

    # Limita as bibliotecas de álgebra linear ANTES de importar o TensorFlow
    os.environ['OMP_NUM_THREADS']     = str(threads_por_processo)
    os.environ['MKL_NUM_THREADS']     = str(threads_por_processo)
    os.environ['OPENBLAS_NUM_THREADS'] = str(threads_por_processo)

    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2

    tf.config.set_visible_devices([], 'GPU')
    tf.config.threading.set_intra_op_parallelism_threads(threads_por_processo)
    tf.config.threading.set_inter_op_parallelism_threads(max(1, threads_por_processo // 2))

    modelo_ia_global = MobileNetV2(weights='imagenet')


def processar_imagem(caminho):
    """
    Função de inferência que os processos irão executar para cada imagem.
    """
    global modelo_ia_global
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions

    try:
        img = image.load_img(caminho, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)

        previsoes = modelo_ia_global.predict(x, verbose=0)
        _ = decode_predictions(previsoes, top=1)[0][0]

        return True
    except Exception:
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

    # Baseline serial (1 processo) para calcular speedup real
    print(f"\n" + "="*50)
    print(f"[*] INICIANDO BASELINE COM 1 PROCESSO (SERIAL)")
    print("="*50)
    tempo_inicio = time.time()
    with mp.Pool(processes=1, initializer=inicializar_worker, initargs=(1,)) as pool:
        pool.map(processar_imagem, caminhos_imagens, chunksize=10)
    tempo_baseline = time.time() - tempo_inicio
    print(f"[+] Baseline: {tempo_baseline:.2f}s\n")

    bateria_de_testes = [2, 4, 8, 12]

    for num_processos in bateria_de_testes:
        print(f"\n" + "="*50)
        print(f"[*] INICIANDO TESTE COM {num_processos} PROCESSOS SIMULTÂNEOS")
        print(f"    ({TOTAL_NUCLEOS_FISICOS // num_processos} thread(s) TF por processo)")
        print("="*50)

        tempo_inicio = time.time()

        with mp.Pool(
            processes=num_processos,
            initializer=inicializar_worker,
            initargs=(num_processos,)   # passa num_processos para calcular a fatia interna
        ) as pool:
            pool.map(processar_imagem, caminhos_imagens, chunksize=10)

        tempo_total = time.time() - tempo_inicio
        speedup    = tempo_baseline / tempo_total
        eficiencia = speedup / num_processos

        print(f"[+] {num_processos} processos: {tempo_total:.2f}s | "
              f"Speedup: {speedup:.2f} | Eficiência: {eficiencia:.2f}\n")


if __name__ == "__main__":
    executar_paralelo()
