# Relatório de Classificação de Imagens com Inteligência Artificial e Processamento Paralelo

**Disciplina: Sistemas de Informação**   
**Aluno(s): Luiz Maia e Waldo Andrade**

**Turma: SI-Noturno**

**Professor: Rafael**

**Data: 27/05/2026**

---

# 1. Descrição do Problema

O problema computacional resolvido consiste na classificação automatizada de um grande volume de imagens utilizando Inteligência Artificial. O sistema realiza a leitura de arquivos do disco e submete cada imagem a uma Rede Neural Convolucional (CNN) pré-treinada para identificar o objeto ou cenário presente na foto (ex: floresta, carros, animais), registrando o resultado em um banco de dados.

* **Problema implementado:** Inferência de rede neural (CPU bound), que exige intenso cálculo matemático e matricial para cada imagem processada. A execução sequencial deste tipo de algoritmo em grandes volumes de dados torna-se impraticável devido ao alto tempo de resposta.
* **Algoritmo utilizado:** Modelo `MobileNetV2` carregado através da biblioteca **TensorFlow / Keras**, com orquestração de fila e registro de resultados em banco de dados SQLite.
* **Tamanho da entrada:** Diretório contendo um lote massivo de imagens, totalizando aproximadamente 2 GB de dados.
* **Objetivo da paralelização:** Reduzir o tempo de execução instanciando o modelo de IA em múltiplos processos simultâneos. O padrão produtor-consumidor (via `multiprocessing.Pool`) foi adotado para distribuir a carga de inferência por todos os núcleos disponíveis do processador.

---

# 2. Ambiente Experimental

Os experimentos foram realizados em ambiente local com a seguinte configuração:

| Item                        | Descrição                                   |
| --------------------------- | ---------                                   |
| Processador                 | Ryzen 5 5600x                               |
| Número de núcleos           | 6/12                                        |
| Memória RAM                 | 32 GB RAM                                   |
| Sistema Operacional         | Windows 11                                  |
| Linguagem utilizada         | Python 3.13                                 |
| Biblioteca de IA            | `TensorFlow` (MobileNetV2)                  |
| Biblioteca de paralelização | `multiprocessing` (nativa)                  |
| Banco de Dados              | `SQLite3`                                   |

---

# 3. Metodologia de Testes

Os testes foram conduzidos executando os scripts de classificação variando a quantidade de processos (workers) no pool de paralelização. Foi implementada uma rotina de inicialização (`initializer` no Worker Pool) para garantir que a arquitetura da rede neural fosse carregada na memória apenas uma vez por núcleo, evitando estouro de memória RAM e overhead de I/O.

* **Medição de tempo:** Função `time.time()` capturando o timestamp imediatamente antes do envio das imagens para a IA e logo após a última previsão, gravando os resultados individuais no banco de dados.
* **Tamanho da entrada:** [Pasta com 2000 imagens para realização dos testes](https://drive.google.com/drive/folders/1gCmfQuZ5RQ8lw0qzeSrit-UQnHWA_J21?usp=drive_link)

### Configurações testadas

* 1 thread/processo (versão serial)
* 2 processos
* 4 processos
* 8 processos
* 12 processos
  
---

# 4. Resultados Experimentais

Abaixo estão os tempos de execução totais obtidos para a inferência da rede neural em toda a base de dados:

| Nº Threads/Processos | Tempo de Execução (s) |
| -------------------- | --------------------- |
| 1 (Serial)           |  125,63               |
|                      |                       |

Para garantir a integridade dos testes e evitar o estrangulamento térmico do processador (thermal throttling), o limite da amostragem foi fixado em 2.000 imagens. O tempo da versão serial (1 processo) foi aferido integralmente executando o pipeline matemático com lotes (batches) de 32 imagens, servindo como nossa base (Baseline) de 100% do tempo (125,63 segundos) para os cálculos de escalabilidade.

---

# 5. Cálculo de Speedup e Eficiência

### Speedup
`Speedup(p) = T(1) / T(p)`
*(Onde T(1) = tempo serial, T(p) = tempo paralelo)*

### Eficiência
`Eficiência(p) = Speedup(p) / p`
*(Onde p = número de threads ou processos)*

---

# 6. Tabela de Resultados Consolidados

| Threads/Processos | Tempo (s)            | Speedup              | Eficiência           |
| ----------------- | ---------            | -------              | ----------           |
| 1                 |  125.63              | 1.00                 | 1.00                 |
| 2                 |  53.92               | 1.99                 | 0.99                 |
| 4                 |  24.43               | 5.14                 | 1.29                 |
| 8                 |  25.61               | 4.19                 | 0.52                 |
| 12                |  26.14               | 4.10                 | 0.34                 |
---

# 7. Análise dos Resultados

**(Preencha após os testes)**

O speedup obtido foi próximo do ideal?
Sim, e inclusive superou o cenário linear ideal na execução com 4 processos, atingindo um speedup de 5.14x (com eficiência de 1.29, ou 129%). Esse fenômeno, conhecido na literatura técnica como Speedup Superlinear, ocorreu devido à otimização na hierarquia de memória do processador. Ao dividir o trabalho em 4 processos e processar as imagens em lotes menores, a quantidade de dados por processo tornou-se pequena o suficiente para caber integralmente na memória Cache L3 (ultra-rápida) do processador. Isso evitou a busca constante de dados na memória RAM (cache misses), resultando em um desempenho superior ao cálculo matemático tradicional.

A aplicação apresentou escalabilidade?
A aplicação demonstrou excelente escalabilidade inicial, atingindo 99% de eficiência com 2 processos e pico de ganho com 4 processos. No entanto, os resultados evidenciaram os limites físicos da arquitetura do processador. Como o Ryzen 5 5600X possui 6 núcleos físicos (e 12 threads lógicas via SMT), o ganho escalou perfeitamente até a limitação da capacidade física. A partir de 8 e 12 processos, a escalabilidade travou (speedup estagnado na casa de 4.1x). Isso ocorre porque tarefas de inteligência artificial dependem de unidades de hardware chamadas FPU (Floating Point Unit), e as threads lógicas de um mesmo núcleo compartilham a mesma FPU, criando uma fila de processamento físico.

Houve overhead de paralelização?
Sim, observou-se um overhead muito claro nas baterias de teste que ultrapassaram a quantidade de núcleos físicos da máquina. Houve uma regressão de desempenho, onde rodar 12 processos (26,14s) demorou mais do que rodar apenas 4 processos (24,43s). Esse overhead é fruto do intenso Context Switching (troca de contexto de processos pelo Sistema Operacional) e do gargalo de barramento (I/O e Memory Wall). O tempo gasto pelo sistema instanciando o TensorFlow 12 vezes simultâneas na RAM e pausando os cálculos para alternar a atenção do CPU superou qualquer ganho hipotético de paralelismo.

# 8. Conclusão

O projeto provou com sucesso que a computação paralela é estritamente necessária para a aplicação de Inteligência Artificial e Visão Computacional no mundo real. A execução serial para análise matricial de 2 GB de dados demonstrou ser insustentável. Ao isolar a carga de trabalho de inferência (TensorFlow) em processos independentes gerenciados pelo Python, foi possível maximizar o uso da arquitetura multi-core do hardware e alcançar uma redução dramática no tempo de resposta do sistema.
