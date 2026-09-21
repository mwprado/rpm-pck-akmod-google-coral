# Google Coral Edge TPU on Fedora / Silverblue

Pacotes RPM para usar **Google Coral Edge TPU PCIe/M.2** em Fedora, com foco em
Fedora Silverblue e outros sistemas baseados em rpm-ostree.

O objetivo deste repositório é substituir a pilha antiga baseada em DKMS por
uma integração nativa com **akmods**, além de empacotar o runtime
`libedgetpu` e fornecer ferramentas de diagnóstico.

Estado atual: **testado em hardware real com Fedora 44 Silverblue e Coral
M.2/PCIe**.

## Arquitetura

```text
Aplicação / LiteRT
        |
        v
   libedgetpu
        |
        v
   /dev/apex_0
        |
        v
   apex + gasket
        |
        v
 Google Coral Edge TPU
```

O repositório contém três specs principais:

| Spec | Pacotes principais | Função |
| --- | --- | --- |
| `gasket-kmod.spec` | `akmod-gasket`, `kmod-gasket-*`, `gasket-kmod-common` | Driver de kernel `gasket`/`apex`, integração akmods, regra udev e carregamento dos módulos |
| `libedgetpu.spec` | `libedgetpu`, `libedgetpu-devel` | Runtime userspace do Edge TPU para dispositivos PCIe/M.2 |
| `coral-smi.spec` | `coral-smi` | Ferramenta de monitoramento e diagnóstico do Coral |

Também existe `examples/infer.py`, um teste de inferência usando LiteRT e o
delegate do Edge TPU.

---

## gasket-kmod.spec

Este spec empacota o driver oficial
[`google/gasket-driver`](https://github.com/google/gasket-driver).

Ele fornece os dois módulos necessários para o Coral PCIe/M.2:

- `gasket.ko` — Google ASIC Software Kernel Extensions and Tools;
- `apex.ko` — driver PCIe do Edge TPU v1.

O código base usado atualmente é o commit:

```text
5815ee3908a46a415aac616ac7b9aedcb98a504c
```

Também são aplicados patches de compatibilidade provenientes do projeto
`KyleGospo/gasket-dkms` para kernels modernos, incluindo alterações em
`no_llseek`, `class_create()`, `eventfd_signal()`, namespace
`DMA_BUF` e `zap_special_vma_range()`.

Além desses patches de compatibilidade, este repositório mantém três correções
locais de lógica encontradas durante a auditoria do driver Google arquivado:

- `0001-apex-fix-reset-error-handling-and-probe-delay.patch` — verifica o
  retorno de `apex_reset()` durante o probe e substitui o uso incorreto de
  `schedule_timeout()` em estado `TASK_RUNNING` por `msleep()`;
- `0002-gasket-make-device-slot-allocation-race-free.patch` — reserva o slot
  em `internal_desc->devs[]` ainda sob o mutex, evitando corrida entre probes
  simultâneos de múltiplos Edge TPUs;
- `0003-gasket-propagate-pci-and-dma-setup-errors.patch` — verifica os
  retornos de `dma_set_mask()` e `dma_set_coherent_mask()` e preserva o erro
  real produzido durante a configuração PCI.

Os patches são aplicados depois das correções de compatibilidade do
`gasket-dkms` e foram verificados contra o commit Google fixado pelo spec.

### Por que akmods em vez de DKMS?

A implementação antiga do driver Coral normalmente é distribuída usando
DKMS. Isso não se encaixa bem no modelo de sistemas imutáveis como
Silverblue, onde o sistema base é administrado por rpm-ostree.

Neste repositório o driver foi convertido para o modelo Fedora/RPM Fusion de
**kmod + akmod**:

```text
gasket-kmod.spec
       |
       +--> akmod-gasket
       |       |
       |       +--> recompila gasket/apex para novos kernels
       |
       +--> kmod-gasket-<kernel>
       |
       +--> gasket-kmod-common
               |
               +--> 65-apex.rules
               +--> modules-load.d/gasket.conf
               +--> sysusers.d/gasket.conf
                       |
                       +--> grupo apex
```

O pacote `akmod-gasket` mantém a fonte necessária para que o `akmods`
recompile os módulos quando um novo kernel é instalado.

O subpacote `gasket-kmod-common` é produzido pelo **mesmo SRPM**. Isso é
intencional: versões anteriores usavam um pacote common separado, o que
criava problemas de resolução de dependências durante builds COPR e
transações rpm-ostree.

O grupo de acesso ao dispositivo também é declarado pelo pacote usando
`systemd-sysusers`, em vez de chamar `groupadd` diretamente. O arquivo
fonte `apex.sysusers` contém:

```text
g apex - - -
```

e é instalado como:

```text
/usr/lib/sysusers.d/gasket.conf
```

O GID fica como `-`, portanto é alocado dinamicamente pelo sistema. O spec
usa `%sysusers_create_package` no `%pre` do `gasket-kmod-common` para
materializar essa definição sem manipular diretamente `/etc/group`. Isso
também preserva a precedência normal de overrides administrativos em
`/etc/sysusers.d/`.

A regra udev oficial instala o dispositivo com:

```text
SUBSYSTEM=="apex", MODE="0660", GROUP="apex"
```

Depois do carregamento correto dos módulos, o dispositivo normalmente aparece
como:

```text
/dev/apex_0
```

---

## libedgetpu.spec

Este spec compila o runtime oficial
[`google-coral/libedgetpu`](https://github.com/google-coral/libedgetpu).

A versão atual é baseada no commit:

```text
e35aed18fea2e2d25d98352e5a5bd357c170bd4d
```

correspondente ao suporte upstream para TensorFlow 2.16.1.

O pacote gera:

- `libedgetpu` — runtime e SONAME `libedgetpu.so.1`;
- `libedgetpu-devel` — headers C/C++ e symlink de desenvolvimento.

### PCIe/M.2 somente

A implementação atual deste repositório é deliberadamente **PCIe/M.2-only**.

Os componentes USB/DFU do upstream foram removidos do build porque a prioridade
foi primeiro recuperar e validar o Coral M.2 em Fedora moderno. O suporte USB
pode ser tratado separadamente no futuro.

### TensorFlow Lite e FlatBuffers

O Makefile standalone do `libedgetpu` é anterior ao layout final do
TensorFlow 2.16.1. O spec ajusta a lista de fontes para usar, entre outros:

```text
tensorflow/lite/core/c/common.cc
tensorflow/lite/util.cc
tensorflow/lite/array.cc
```

TensorFlow 2.16.1 também depende de FlatBuffers 23.5.26, enquanto Fedora 44
fornece uma versão mais nova e incompatível com os headers gerados daquela
versão do TensorFlow.

Por isso o spec compila **privadamente** o FlatBuffers 23.5.26 fixado pelo
TensorFlow e o incorpora estaticamente no `libedgetpu`. Essa cópia privada
não é instalada no sistema e não substitui o FlatBuffers do Fedora.

O `%check` também executa um `dlopen()` real da biblioteca produzida para
detectar símbolos não resolvidos antes de publicar o RPM.

### Correções locais do libedgetpu

Além das adaptações de build necessárias para TensorFlow 2.16.1 e Fedora,
este repositório mantém três patches de correção encontrados durante a
auditoria do código upstream arquivado:

- `0001-libedgetpu-fix-mmu-ioctl-fallback-and-open-cleanup.patch` — corrige
  o fallback de `GASKET_IOCTL_MAP_BUFFER_FLAGS` para o ioctl legado. Em Linux,
  `ioctl()` retorna `-1` e informa o erro em `errno`; o upstream comparava
  diretamente o retorno com `-EPERM`, `-ENOTTY` e `-EINVAL`, portanto o
  fallback nunca era ativado. O mesmo patch também fecha o descritor do
  dispositivo se a partição da page table falhar durante `Open()`;
- `0002-libedgetpu-clean-up-partial-register-mappings.patch` — desfaz
  mappings PCI já criados se um `mmap()` posterior falhar, evitando deixar
  regiões parcialmente mapeadas. Também corrige a condição invertida que
  registrava sucesso de `munmap()` como erro e corrige a mensagem de
  alinhamento de `Read32()`;
- `0003-libedgetpu-validate-eventfd-and-event-index.patch` — detecta falha
  na criação de `eventfd`, limpa os descritores já criados e valida o índice
  do evento antes de acessar os vetores internos.

Esses patches alteram apenas o runtime userspace; não modificam a ABI pública
`libedgetpu.so.1`. Eles são aplicados pelo `libedgetpu.spec` antes das
adaptações do Makefile standalone.

---

## coral-smi.spec

Empacota a ferramenta `coral-smi` incluída neste repositório.

Ela consulta o estado disponibilizado pelo driver `apex/gasket` por meio de:

- `/sys/class/apex/apex_*`;
- `/dev/apex_N`;
- `/proc/interrupts`;
- descritores abertos em `/proc/*/fd`.

Exemplo:

```bash
coral-smi
coral-smi -w 0.5
coral-smi --json
```

São exibidos dados como temperatura, limites térmicos, endereço PCI, páginas
mapeadas, interrupções e processos usando o dispositivo.

O driver Apex não fornece um contador confiável de ciclos ocupados, portanto
`coral-smi` **não inventa um percentual de utilização**. Em modo contínuo,
atividade é inferida pela taxa de interrupções e pelos processos com o
dispositivo aberto.

---

## Instalação no Silverblue

Com os pacotes disponíveis em um repositório RPM/COPR:

```bash
sudo rpm-ostree install akmod-gasket libedgetpu coral-smi
systemctl reboot
```

O `gasket-kmod-common` é uma dependência do pacote akmod e deve ser resolvido
automaticamente.

Depois do reboot:

```bash
lsmod | grep -E 'gasket|apex'
ls -l /dev/apex_0
```

Um sistema funcional deve mostrar os módulos `gasket` e `apex` carregados e
um character device `/dev/apex_0`.

---

## O grupo apex no Silverblue

A regra udev do driver dá acesso ao dispositivo ao grupo `apex`:

```text
crw-rw---- root apex ... /dev/apex_0
```

A primeira versão deste pacote criava esse grupo diretamente no scriptlet RPM:

```bash
groupadd -r apex
```

Essa abordagem funcionava em Fedora tradicional, mas mostrou uma dificuldade
no Silverblue: grupos do sistema podem aparecer por meio dos bancos fornecidos
pela imagem em `/usr/lib/group`, enquanto alterações administrativas locais
ficam em `/etc/group`. A mistura das duas origens tornou operações com
`groupadd`, `usermod` e `grpck` menos previsíveis durante os testes.

A implementação atual evita isso. O pacote contém uma definição declarativa:

```text
# apex.sysusers
g apex - - -
```

que é instalada em:

```text
/usr/lib/sysusers.d/gasket.conf
```

e processada por `systemd-sysusers` através de
`%sysusers_create_package`.

Com isso:

- o pacote não edita diretamente `/etc/group`;
- o GID não é fixado no spec;
- a criação do grupo passa a seguir o mecanismo nativo do systemd;
- configurações locais podem usar `/etc/sysusers.d/` sem alterar arquivos
  fornecidos pelo RPM.

### Verificação

Depois da instalação/reboot:

```bash
getent group apex
ls -l /dev/apex_0
```

O esperado é algo equivalente a:

```text
apex:x:<gid>:
crw-rw---- root apex ... /dev/apex_0
```

O número do GID pode variar e não deve ser codificado em scripts locais.

### Associação do usuário ao grupo

A criação do grupo pelo pacote e a autorização de um usuário humano são
problemas diferentes. O RPM cria `apex`, mas deliberadamente não decide quais
usuários locais devem acessar o Edge TPU.

Em Fedora tradicional, normalmente basta:

```bash
sudo usermod -aG apex "$USER"
```

Depois é necessário encerrar a sessão e entrar novamente.

No Silverblue, se `usermod` encontrar conflito por causa da separação entre
os bancos de grupos do sistema e os locais, prefira uma associação declarativa
local em vez de duplicar manualmente a entrada `apex` em `/etc/group`:

```bash
printf 'm %s apex\n' "$USER" | sudo tee /etc/sysusers.d/90-apex-local.conf
sudo systemd-sysusers /etc/sysusers.d/90-apex-local.conf
```

A diretiva `m` significa "adicionar este usuário como membro deste grupo".

Depois faça novo login ou, para um teste imediato no shell:

```bash
newgrp apex
```

Valide:

```bash
id
test -r /dev/apex_0 && echo READ-OK
test -w /dev/apex_0 && echo WRITE-OK
```

### Sobre `/usr/lib/group`, `/etc/group` e `grpck`

Durante os testes do Silverblue, o grupo `apex` podia ser visível por
`getent` mesmo quando não havia uma entrada equivalente em `/etc/group`.
Isso é importante porque `getent` consulta a visão NSS completa do sistema,
não apenas um arquivo.

Por isso, para diagnóstico, compare:

```bash
getent group apex
grep '^apex:' /etc/group /usr/lib/group 2>/dev/null
id
```

Não copie automaticamente uma entrada de `/usr/lib/group` para
`/etc/group`: isso pode criar nomes duplicados e fazer ferramentas como
`usermod` recusarem a operação.

Da mesma forma, `grpck` pode emitir avisos ao enxergar bancos distribuídos
entre a imagem imutável e `/etc`. Não remova grupos em massa apenas para
eliminar esses avisos. A definição de fornecedor deve permanecer em
`/usr/lib/sysusers.d/gasket.conf`; personalizações locais pertencem a
`/etc/sysusers.d/`.

Essa separação é a razão para o pacote ter migrado de `groupadd` para
`systemd-sysusers`.

---

## Teste de inferência

O exemplo em:

```text
examples/infer.py
```

usa o pacote Python `ai-edge-litert` e carrega explicitamente o delegate:

```python
from ai_edge_litert.interpreter import Interpreter, load_delegate

delegate = load_delegate(
    "/usr/lib64/libedgetpu.so.1",
    {"device": "pci:0"},
)
```

A pilha validada é:

```text
Python
  |
  v
LiteRT
  |
  v
libedgetpu delegate
  |
  v
/dev/apex_0
  |
  v
gasket/apex
  |
  v
Coral M.2
```

O exemplo destrói explicitamente o `Interpreter` antes do delegate. Isso foi
adicionado porque o shutdown automático do Python/LiteRT apresentou um
segmentation fault após inferências bem-sucedidas, enquanto a destruição
explícita dos objetos encerrou normalmente.

### Resultado observado

No hardware usado para validar este repositório:

```text
1000 inferências
média       ~3.12 ms
mediana     ~3.13 ms
p95         ~3.35 ms
p99         ~3.43 ms
throughput  ~320 inferências/s
```

Esses números são apenas uma referência da máquina de teste, não um benchmark
universal do Edge TPU.

---

## Escopo atual

Validado:

- Fedora 44 Silverblue;
- x86_64;
- Coral Edge TPU PCIe/M.2;
- `gasket` + `apex` via akmods;
- `/dev/apex_0`;
- `libedgetpu`;
- LiteRT Python;
- inferência real em modelo compilado para Edge TPU;
- execução contínua de 1000 inferências;
- `coral-smi`.

Ainda fora do escopo validado:

- Coral USB;
- outras arquiteturas;
- PyCoral como dependência obrigatória.

PyCoral não é necessário para a pilha atual. O exemplo usa diretamente LiteRT
com o delegate `libedgetpu`.

## Licenças

Cada componente preserva a licença correspondente ao upstream. O
`coral-smi` é distribuído sob licença MIT.
