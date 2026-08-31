# TopVenues

**Artefato do artigo #189 — Salão de Ferramentas, SBSeg 2026**
*TopVenues: An Executable Corpus and Research Tool for Cybersecurity Literature Reviews*
Sidnei Barbieri, Ágney Roth Ferraz, Lourenço Alves Pereira Júnior (ITA)

Revisões de literatura em segurança dependem de um denominador estável: o
conjunto de artigos elegíveis antes de a triagem começar. Na prática, esse
denominador é remontado a partir de portais, APIs e exportações que mudam ao
longo do tempo, o que torna o corpus resultante difícil de auditar ou reutilizar.

O TopVenues transforma a construção do corpus em um artefato de pesquisa
executável. Dado um escopo declarado de veículos e anos, ele normaliza metadados
do DBLP, enriquece registros com resumos e entradas BibTeX, e materializa um
snapshot SQLite monotônico exposto por uma interface de linha de comando, uma
aplicação web, busca ranqueada e exportações orientadas a revisão. O release
declara sua política de veículos, distingue registros bibliográficos de registros
enriquecidos com resumo, e registra proveniência em nível de campo. Um revisor
consegue verificar um snapshot fixado offline, exercitar busca ranqueada e
exportações, e reproduzir os fluxos vinculados ao snapshot que acompanham o
release.

> **Documentação em inglês:** [README.en.md](README.en.md) descreve a mesma
> ferramenta para leitores internacionais. Este arquivo é a documentação
> normativa do artefato para o CTA.

---

# Estrutura do readme.md

Este README segue o modelo mínimo exigido pelo CTA do SBSeg 2026.

| Seção | Conteúdo |
| --- | --- |
| [Selos Considerados](#selos-considerados) | Quais selos são pleiteados |
| [Informações básicas](#informações-básicas) | Ambiente de execução, hardware e software |
| [Dependências](#dependências) | Versões, fixação por hash e recursos de terceiros |
| [Preocupações com segurança](#preocupações-com-segurança) | Riscos para o revisor (nenhum) |
| [Instalação](#instalação) | Clone e um único comando |
| [Teste mínimo](#teste-mínimo) | Verificação rápida de que a ferramenta funciona |
| [Experimentos](#experimentos) | Uma subseção por reivindicação do artigo |
| [LICENSE](#license) | Licença do código e dos dados |

O apêndice do artefato exigido pelo CTA, com os mesmos dados em formato PDF, está
em [`docs/artifact-appendix/`](docs/artifact-appendix/TopVenues-189-Apendice.pdf).

Organização do repositório:

```
topvenues-tool/
├── README.md                  este arquivo (documentação normativa do CTA)
├── README.en.md               documentação em inglês
├── reproduce.sh               reprodução em uma linha (macOS e Linux)
├── reproduce.ps1              reprodução em uma linha (Windows / PowerShell)
├── Dockerfile                 imagem alternativa, mesmas dependências fixadas
├── docker-compose.yml         atalho de uma linha para a imagem
├── requirements-frozen.txt    dependências fixadas e verificadas por hash
├── uv.lock                    lockfile equivalente para o gerenciador uv
├── config.yaml                escopo declarado de veículos e anos
├── profiles/                  configuração de cada perfil imutável
├── data/profiles/             snapshots comprimidos e seus manifestos
├── src/                       biblioteca e interface de linha de comando
├── web/                       aplicação Streamlit
├── scripts/                   automação de verificação e de experimentos
├── tests/                     359 testes automatizados
└── docs/                      guia do revisor, protocolo de auditoria, demonstração
```

---

# Selos Considerados

Os selos considerados são: **Disponíveis (SeloD)**, **Funcionais (SeloF)**,
**Sustentáveis (SeloS)** e **Experimentos Reprodutíveis (SeloR)**.

| Selo | Onde é atendido |
| --- | --- |
| **SeloD** | Repositório público e estável no GitHub, com este README no modelo do CTA e release marcado por tag. |
| **SeloF** | [Dependências](#dependências) com versões fixadas, [Informações básicas](#informações-básicas) com o ambiente, [Instalação](#instalação) e [Teste mínimo](#teste-mínimo). |
| **SeloS** | Código modularizado com documentação por módulo e função, parametrização fora do código (`config.yaml`, `profiles/`), e as reivindicações do artigo identificadas no artefato por `scripts/verify_paper_claims.py`. |
| **SeloR** | [Experimentos](#experimentos), uma subseção por reivindicação, com comando, tempo, recursos, resultado esperado e linha de base para comparação. |

---

# Informações básicas

## Ambiente utilizado nos experimentos

Os resultados relatados no artigo e nesta documentação foram obtidos no
seguinte ambiente:

| Item | Valor |
| --- | --- |
| Sistema operacional | macOS 26.5.2 (build 25F84) |
| Kernel | Darwin 25.5.0 |
| Arquitetura | arm64 (Apple Silicon) |
| Processador | Apple M4 Max, 16 núcleos |
| Memória RAM | 64 GB |
| Armazenamento livre | 53 GB |
| Python | 3.14.7 |

## Requisitos mínimos para reprodução

O artefato não exige o hardware acima. Os requisitos mínimos verificados são:

| Recurso | Mínimo | Observação |
| --- | --- | --- |
| Sistema operacional | Linux, macOS ou Windows 10+ | `reproduce.sh` em Linux/macOS; `reproduce.ps1` em Windows |
| Python | 3.11 ou superior | Testado em 3.11, 3.12, 3.13 e 3.14 |
| Memória RAM | 4 GB | O pico de uso observado é inferior a 1 GB |
| Espaço em disco | 3 GB | 76 MB de snapshot, ~450 MB de banco materializado, ~1,5 GB de ambiente virtual |
| Rede | Apenas na instalação | Necessária para baixar as dependências. A verificação, a busca e as exportações são offline. |
| Navegador | Qualquer navegador atual | Somente para a interface web; a linha de comando não precisa dele. |
| Privilégios | Usuário comum | Não requer administrador nem `sudo`. |

## Tempo total esperado

| Etapa | Tempo no ambiente acima | Tempo estimado em máquina modesta |
| --- | --- | --- |
| Instalação das dependências | 60–120 s | até 5 min |
| Reprodução completa (`reproduce.sh`) | ~4 min | até 12 min |
| Teste mínimo | ~90 s | até 4 min |

---

# Dependências

## Fixação de versões

Todas as dependências de execução são instaladas a partir de
**`requirements-frozen.txt`**, que fixa 71 pacotes por versão exata e contém
1.161 hashes SHA-256. A instalação usa `pip install --require-hashes`, portanto
qualquer divergência de bytes interrompe a instalação em vez de produzir um
ambiente diferente do relatado. O mesmo conjunto está disponível como
**`uv.lock`** para quem usa o gerenciador `uv`, que o `reproduce.sh` prefere
quando encontra.

**As dependências da interface web estão incluídas nesse mesmo arquivo.** Não há
passo adicional: `streamlit`, `altair` e `watchdog` são instalados junto com o
restante, e o `reproduce.sh` exibe isso explicitamente na primeira etapa. O
arquivo `requirements-web.txt` existe apenas como declaração legível do
subconjunto web e **não** é usado por nenhum caminho de instalação.

## Dependências principais

<!-- dependency-table:start -->

| Pacote | Versão fixada | Função |
| --- | --- | --- |
| `pandas` | 3.0.3 | Manipulação tabular e exportações |
| `pyarrow` | 24.0.0 | Escrita de Parquet |
| `pydantic` | 2.13.4 | Modelos de dados validados |
| `httpx` | 0.28.1 | Cliente HTTP dos coletores |
| `beautifulsoup4` | 4.15.0 | Extração de resumos em HTML |
| `click` | 8.4.2 | Interface de linha de comando |
| `rich` | 15.0.0 | Saída formatada no terminal |
| `pyyaml` | 6.0.3 | Leitura da configuração declarada |
| `streamlit` | 1.58.0 | Interface web |
| `altair` | 6.2.2 | Gráficos da interface web |
| `pytest` | 9.1.1 | Suíte de testes automatizados |
| `ruff` | 0.15.20 | Verificação de estilo e lint |

<!-- dependency-table:end -->

A lista completa, com hashes, está em `requirements-frozen.txt`.

## Recursos de terceiros

**Nenhuma chave de API, credencial ou conta é necessária para reproduzir o
artefato.** O snapshot já acompanha o repositório.

Serviços externos são usados apenas pelos comandos opcionais de coleta
(`download`, `consolidate`, `extract`), que **não** fazem parte da reprodução e
**não** alteram o snapshot publicado: DBLP, Semantic Scholar, OpenAlex, CrossRef,
ACM Digital Library, IEEE Xplore, USENIX e NDSS. Todos são consultados por
endpoints públicos e sem autenticação.

---

# Preocupações com segurança

**A execução deste artefato não oferece risco ao revisor.**

- Não requer privilégios de administrador nem `sudo`.
- Não instala serviços, não altera configurações do sistema e não abre portas
  para fora da máquina. A interface web escuta apenas em `localhost`.
- Não executa código de terceiros baixado em tempo de execução: as dependências
  são fixadas por hash na instalação.
- Não coleta, transmite nem armazena dados pessoais do revisor.
- A reprodução é **offline** após a instalação das dependências. Os comandos que
  acessam a rede são opcionais, estão claramente identificados e não são
  exercitados por `reproduce.sh`.
- Todos os arquivos criados ficam dentro do diretório do repositório clonado.
  Remover o diretório desfaz completamente a instalação.
- O snapshot é aberto em modo somente leitura (`mode=ro&immutable=1`), de forma
  que a execução não pode corromper o corpus verificado.

---

# Instalação

## Linux e macOS

```bash
git clone https://github.com/sidneibarbieri/topvenues-tool
cd topvenues-tool
bash reproduce.sh --profile security-20
```

## Windows (PowerShell)

```powershell
git clone https://github.com/sidneibarbieri/topvenues-tool
cd topvenues-tool
powershell -ExecutionPolicy Bypass -File .\reproduce.ps1 -Profile security-20
```

## Docker (alternativa)

```bash
docker compose up          # interface web em http://localhost:8501
docker compose run --rm app python -m pytest -q
```

A imagem instala exatamente as mesmas dependências fixadas por hash do
`reproduce.sh`.

## Solução de problemas

**"Cannot refresh papers.db because it is open" / erro ao iniciar o banco.**
Ocorre quando a interface web (ou outro processo) está com o corpus aberto e o
script tenta materializá-lo de novo. No Windows o sistema operacional bloqueia o
arquivo de forma mais estrita que no Linux e no macOS, então esse caso aparece
primeiro ali. Feche a aba do Streamlit, encerre o processo `streamlit` e execute
o script novamente. A materialização é protegida por um lock atômico e
multiplataforma: duas execuções simultâneas se serializam em vez de corromper o
banco, e a segunda espera até 30 segundos antes de relatar `CorpusBusyError` com
a instrução acima.

**PowerShell recusa executar o script.** Use exatamente a forma documentada,
`powershell -ExecutionPolicy Bypass -File .\reproduce.ps1`, que não altera a
política do sistema — ela vale só para aquela invocação.

**`python` não encontrado no Windows.** O script tenta `py -3`, `python3` e
`python`, nessa ordem. Se nenhum existir, instale o Python 3.11+ pela
[python.org](https://www.python.org/downloads/) marcando *Add python.exe to PATH*.

**A execução deixou `data/papers.db` para trás.** É o banco materializado e
descartável; pode ser apagado a qualquer momento. O snapshot comprimido em
`data/profiles/` é a fonte de verdade e nunca é modificado.

O script cria um ambiente virtual isolado em `.venv/`, instala as dependências
fixadas, materializa o snapshot comprimido, verifica seu SHA-256 contra o
manifesto, executa a suíte de testes, renderiza a interface, confere as
reivindicações do artigo, compara a busca ranqueada com a linha de base e exporta
uma amostra BibTeX. **Ao final desse comando a ferramenta está instalada e
verificada.**

---

# Teste mínimo

Este teste confirma, em cerca de 90 segundos, que a instalação funciona e que as
principais funcionalidades são observáveis.

```bash
# 1. Estado do corpus: contagens por veículo e cobertura de resumos
python -m src.cli --profile security-20 stats

# 2. Busca por substring no título
python -m src.cli --profile security-20 search --title "intrusion detection"

# 3. Busca ranqueada por relevância (FTS5/BM25)
python -m src.cli --profile security-20 search --rank "memory corruption mitigation" --limit 10

# 4. Exportação pronta para revisão
python -m src.cli --profile security-20 export --title intrusion --format bibtex --output amostra.bib

# 5. Interface web
python -m streamlit run web/app.py
```

**Resultado esperado:**

| Passo | Saída esperada |
| --- | --- |
| 1 | `Total Papers: 20305`, `With Abstracts: 17491 (86.14%)`, `With BibTeX: 20305 (100.00%)` |
| 2 | 50 registros exibidos (limite padrão); use `--limit 100000` para ver os 157 que casam |
| 3 | 7 registros ordenados por relevância BM25 (`--limit 10` é um teto, não uma cota) |
| 4 | `amostra.bib` com 2.928 linhas (122.391 bytes) |
| 5 | Interface em `http://localhost:8501`, com as cinco páginas navegáveis |

---

# Experimentos

Todas as reivindicações abaixo são verificadas automaticamente por um único
comando:

```bash
python scripts/verify_paper_claims.py --profile security-20
```

O mesmo script é executado dentro de `reproduce.sh` e de `reproduce.ps1`, de modo
que a reprodução completa já cobre todas as reivindicações. Cada subseção abaixo
indica também o comando isolado, o tempo, os recursos e o resultado esperado.

**Recursos comuns a todos os experimentos:** menos de 1 GB de RAM, menos de 3 GB
de disco, sem rede e sem GPU.

## Reivindicação #1 — O snapshot publicado contém 20.305 artigos entre 2017 e 2026

Seção 4 do artigo (*The Corpus as an Artifact*).

```bash
python scripts/verify_paper_claims.py --profile security-20
python -m src.cli --profile security-20 stats
```

- **Tempo esperado:** ~20 s
- **Resultado esperado:** `Claim #1 ... expected 20305, observed 20305` e
  `Claim #2 ... expected '2017-2026', observed '2017-2026'`.

## Reivindicação #2 — O escopo declarado é de 20 veículos

Seção 3 do artigo (*Design*). O escopo é dado por `config.yaml`, fora do código.

```bash
python scripts/verify_paper_claims.py --profile security-20
```

- **Tempo esperado:** ~20 s
- **Resultado esperado:** `Claim #3 ... expected 20, observed 20`.

## Reivindicação #3 — 17.491 dos 20.305 registros têm resumo (86,1%)

Seção 4 do artigo (*Coverage*).

```bash
python scripts/verify_paper_claims.py --profile security-20
```

- **Tempo esperado:** ~20 s
- **Resultado esperado:** `Claim #4 ... expected 17491, observed 17491` e
  `Claim #5 ... expected 86.1, observed 86.1`.

## Reivindicação #4 — Todo registro carrega uma entrada BibTeX

Seção 5 do artigo (*Exports*).

```bash
python scripts/verify_paper_claims.py --profile security-20
python -m src.cli --profile security-20 export --title intrusion --format bibtex --output amostra.bib
```

- **Tempo esperado:** ~30 s
- **Resultado esperado:** `Claim #6 ... expected 20305, observed 20305`; o arquivo
  `amostra.bib` tem 2.928 linhas (122.391 bytes).

## Reivindicação #5 — A identidade do corpus é verificável offline por SHA-256

Seção 6 do artigo (*Reviewer-path validation*).

```bash
python scripts/verify_profile_snapshot.py --profile security-20
```

- **Tempo esperado:** ~15 s
- **Resultado esperado:** o SHA-256 do snapshot confere com o manifesto:
  `5a35bd6e3ec6845a0fde4cc3d6aa05b1db04e511cb39e783eeaee2cea7493b08`.

## Reivindicação #6 — A busca ranqueada supera a busca por substring

Seção 5 do artigo (*Search*). Este experimento traz a **linha de base para
comparação**: a busca por substring (`LIKE`), que é o que uma planilha ou um
`grep` fazem, medida contra a busca ranqueada por FTS5/BM25 sobre o mesmo corpus
e na mesma máquina.

```bash
python scripts/benchmark_search.py --profile security-20 --trials 11
```

- **Tempo esperado:** ~40 s (11 repetições por consulta, mediana relatada)
- **Resultado esperado no ambiente descrito:**

| Consulta | Linha de base `LIKE` | Ranqueada BM25 | Ganho de tempo |
| --- | --- | --- | --- |
| `machine learning` | 1.962 res., 37,6 ms | 2.093 res., 27–32 ms | ~1,3× |
| `fuzzing` | 661 res., 36,0 ms | 661 res., 6,1 ms | ~5,9× |
| `intrusion detection` | 337 res., 65,5 ms | 354 res., 3,9 ms | ~16,8× |
| `ransomware` | 84 res., 55,8 ms | 84 res., 1,5 ms | ~37× |

As contagens de resultados são determinísticas e se repetem a cada execução. Os
tempos são medianas de 11 repetições e variam alguns milissegundos entre
execuções e bastante entre máquinas; o que o experimento demonstra é a **relação
entre as duas colunas**, não o valor absoluto.

A linha de base retorna registros em ordem arbitrária, que é o comportamento de
uma planilha ou de um `grep`. A busca ranqueada os ordena de forma determinística
por BM25, com peso maior para correspondências no título — por isso ela encontra
mais registros em `machine learning` e `intrusion detection`: o índice FTS5
casa tokens que a busca literal por substring não alcança.

## Reivindicação #7 — A suíte de testes é executada offline

Seção 6 do artigo. O artigo submetido informa **238 testes**, número correto na
data da submissão. Desde então o artefato recebeu correções, e a suíte cresceu
para **359 testes**; nenhum teste foi removido. As contagens do corpus permanecem
idênticas às do artigo, como as reivindicações #1 a #4 demonstram.

```bash
python -m pytest -q
```

- **Tempo esperado:** ~10 s
- **Resultado esperado:** `359 passed`, sem acesso à rede.

## Reprodução completa

```bash
bash reproduce.sh --profile security-20        # Linux e macOS
.\reproduce.ps1 -Profile security-20           # Windows
```

- **Tempo esperado:** ~4 min no ambiente descrito
- **Resultado esperado:** todas as etapas com `✓`, encerrando em
  `Profile security-20 reproduced successfully`.

---

# LICENSE

O código do TopVenues é distribuído sob a **licença MIT**, reproduzida em
[LICENSE](LICENSE).

Os metadados bibliográficos e as entradas BibTeX provêm do DBLP e seguem os
termos **CC0** do DBLP. O texto original dos resumos permanece sob os direitos de
seus respectivos editores e é redistribuído aqui apenas para fins de pesquisa,
com a proveniência de cada campo registrada no snapshot.
