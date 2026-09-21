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
               +--> grupo apex
```

O pacote `akmod-gasket` mantém a fonte necessária para que o `akmods`
recompile os módulos quando um novo kernel é instalado.

O subpacote `gasket-kmod-common` é produzido pelo **mesmo SRPM**. Isso é
intencional: versões anteriores usavam um pacote common separado, o que
criava problemas de resolução de dependências durante builds COPR e
transações rpm-ostree.

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

Este foi um dos pontos menos óbvios durante a validação.

A regra udev dá acesso ao dispositivo ao grupo `apex`:

```text
crw-rw---- root apex ... /dev/apex_0
```

Portanto o usuário que executará inferências precisa pertencer a esse grupo.

Em uma instalação Fedora tradicional, normalmente basta:

```bash
sudo usermod -aG apex "$USER"
```

No Silverblue, porém, contas e grupos do sistema podem estar distribuídos entre
os bancos imutáveis em `/usr/lib/group` e os bancos locais graváveis em
`/etc/group`.

Durante o teste deste projeto ocorreu a seguinte situação:

```text
getent group apex
apex:x:<gid>:
```

mas o usuário ainda não aparecia como membro do grupo. Tentativas de copiar ou
criar entradas manualmente sem verificar o estado anterior também podem
produzir entradas `apex` duplicadas em `/etc/group`, fazendo ferramentas
como `usermod` recusarem a alteração.

### Diagnóstico

Primeiro verifique as três visões:

```bash
getent group apex
grep '^apex:' /etc/group /usr/lib/group 2>/dev/null
id
```

O GID não deve ser fixado na documentação: use o GID retornado pelo sistema.

### Ajuste local

Se o grupo existe no banco fornecido pelo sistema, mas não há uma entrada local
adequada para manter a associação do usuário, edite cuidadosamente
`/etc/group` com:

```bash
sudo vigr
```

e mantenha **uma única entrada local** para `apex`, usando o GID já existente:

```text
apex:x:<gid>:seu_usuario
```

Não crie várias entradas `apex` em `/etc/group`.

Depois encerre a sessão gráfica/SSH e entre novamente. Para um teste imediato
em shell também é possível usar:

```bash
newgrp apex
```

Valide:

```bash
id
test -r /dev/apex_0 && echo READ-OK
test -w /dev/apex_0 && echo WRITE-OK
```

### Sobre grpck no Silverblue

`grpck` pode listar vários grupos que existem em um dos bancos do sistema mas
não aparecem da mesma forma no outro. Em Silverblue isso não significa
necessariamente corrupção.

Evite remover em massa grupos sugeridos pelo `grpck` apenas para silenciar os
avisos. O objetivo aqui é corrigir somente a entrada `apex`, preservando o
modelo de contas/grupos do sistema imutável.

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
