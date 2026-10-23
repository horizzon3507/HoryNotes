# HoryNotes

Versão atual: `0.1.4-beta`.

![HoryNotes](assets/HoryNotes-Lockup.svg)

Uma nota rápida Linux em formato de bolinha com o símbolo `✦`. Ela solicita
ficar no topo quando o compositor permitir, abre um editor compacto em tons
escuros suaves ao clicar, anima a expansão/encolhimento e salva o texto
localmente.

## Rodar

```bash
./run.sh
```

Ou direto:

```bash
python3 horyhours_notes.py
```

O app pode ser encerrado normalmente com `Ctrl+C` quando iniciado por `./run.sh`.

Em sessões Wayland com XWayland disponível, o app usa XWayland automaticamente
para que o modo sempre no topo, o arraste da bolinha e o atalho global possam
funcionar. Para voltar ao backend Wayland nativo, use
`HORYHOURS_NATIVE_WAYLAND=1 ./run.sh`.
Para reduzir movimentos, use `HORYHOURS_REDUCED_MOTION=1 ./run.sh`.

### Dependências

Se o PyQt6 não estiver instalado:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python horyhours_notes.py
```

## Controles

- arraste a bolinha `✦` para reposicionar; o anel verde indica uma partida com
  nota em andamento;
- clique na bolinha para abrir;
- use `Concluído` ao lado de HoryNotes para arquivar a nota da partida e começar
  outra; ele só fica disponível com texto no editor;
- use `◷` para consultar até 1024 notas arquivadas, exportar uma como `.txt` ou
  todas em um arquivo `.zip`;
- use `☷` para consultar as tarefas; o seletor no topo abre sempre em The Skeld
  e também inclui MIRA HQ, Polus, The Airship e The Fungle;
- no The Skeld, alterne entre categoria e sala; em painéis estreitos, Histórico
  e Tarefas ficam no menu `⋯`;
- use o botão de minimizar `—` ou `Esc` para encolher novamente;
- use o botão de fechar `×` para sair;
- `Ctrl+Shift+Space` abre/fecha a nota globalmente em X11/XWayland; no Wayland
  nativo, ele funciona enquanto o HoryNotes estiver em foco devido às restrições
  de segurança do compositor.
- `Ctrl+Alt+Shift+H` alterna a presença no `Alt+Tab`; três cliques em `HoryNotes`
  fazem a mesma alternância.

As notas e o histórico ficam no armazenamento local do Qt (`QSettings`), sem
servidor.

## Identidade visual

A marca fica em [`assets/`](assets/):

| Arquivo | Uso |
|---|---|
| [`HoryNotes-Lockup.svg`](assets/HoryNotes-Lockup.svg) | marca + wordmark `HORY NOTES` (1244×394) |
| [`HoryNotes-Logo.svg`](assets/HoryNotes-Logo.svg) | só a marca: hexágono + estrela (356×394) |
| [`HoryNotes-Wordmark.svg`](assets/HoryNotes-Wordmark.svg) | só o texto `HORY NOTES` (850×326) |
| [`HoryNotes-Icon.svg`](assets/HoryNotes-Icon.svg) | ícone quadrado (434×434), para avatar |
| [`HoryNotes-Identity-Preview.png`](assets/HoryNotes-Identity-Preview.png) | prévia das quatro variações |

Hexágono, estrela e wordmark em khaki `#A99A7A`, na família visual do HoryTools.
Exports PNG transparentes de 2400 px acompanham a marca, lockup e wordmark;
`HoryNotes-Icon-512.png` é a versão quadrada de 512 px.

Para regerar os assets: `python3 assets/generate-horynotes-logo.py`.
O gerador reaproveita o módulo do gerador do HoryTools (`generate-horytools-logo.py`)
para sair com o hexágono e o `HORY` byte a byte idênticos aos do HoryTools —
por isso ele espera essa pasta em `../assets/` (relativa a `HoryTools/`).
Os SVGs já prontos estão commitados; o gerador é necessário só para mudar algo.
