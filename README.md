# Classificador SUCS — DNIT (Streamlit)

App web para classificar solos pelo **SUCS** (Sistema Unificado de Classificação de Solos), seguindo a prática do DNIT.
- Calcula **IP = LL − LP** e usa a **linha A** (IP = 0,73 · (LL − 20)) para distinguir **M × C**.
- Decide **L × H** por **LL < 50**.
- Para granulação grossa (≥ 50% retido na #200), decide **G × S** e, com finos < 5%, permite **GW/GP** ou **SW/SP** via **Cu/Cc**.
- Suporta casos orgânicos (**OL/OH**) e turfa (**Pt**).
- Inclui **classificação em lote (CSV)** e **gráfico de plasticidade**.

## ▶️ Executar localmente

```bash
git clone <SEU_REPO_GITHUB>.git
cd <SEU_REPO_GITHUB>
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## ☁️ Deploy no Streamlit Community Cloud

1. Crie um repositório no GitHub com estes arquivos (use este diretório como base).  
2. No [streamlit.io](https://streamlit.io/cloud), clique em **New app**, selecione o repositório e informe:  
   - **Branch:** `main` (ou a que você usar)  
   - **Main file path:** `streamlit_app.py`  
3. Deploy! Não precisa de secrets.

## 📁 Estrutura

```
.
├── streamlit_app.py        # App web (UI)
├── sucs_core.py            # Lógica SUCS (reutilizável em scripts/planilhas)
├── requirements.txt        # Dependências
├── .streamlit/
│   └── config.toml         # Configuração do servidor/tema
├── samples.csv             # Exemplo de CSV para lote
├── LICENSE                 # MIT
└── README.md               # Este arquivo
```

## 🧪 CSV em lote (colunas esperadas)

```
projeto,tecnico,amostra,pct_retido_200,pct_pedregulho_coarse,pct_areia_coarse,LL,LP,Cu,Cc,organico,turfa
```
- `organico` e `turfa` podem ser `True/False` ou `1/0`.
- `Cu` e `Cc` só são usados para decidir **W/P** quando os finos são `< 5%`.

## ⚙️ Regras implementadas (resumo)

- **Split grossa/fina:** `≥ 50%` retido na #200 ⇒ grossa; senão fina.  
- **Grossa (G/S):**
  - G se pedregulho (> #4) ≥ areia (fração > #200); senão S.  
  - Finos `< 5%` ⇒ usar **Cu/Cc**:  
    - **Areias (S):** `Cu ≥ 6` e `1 ≤ Cc ≤ 3` ⇒ **SW**; senão **SP**.  
    - **Cascalhos (G):** `Cu ≥ 4` e `1 ≤ Cc ≤ 3` ⇒ **GW**; senão **GP**.  
  - Finos `5–12%` ⇒ **limítrofe** (símbolo duplo), combinando graduação e natureza dos finos.  
  - Finos `> 12%` ⇒ **GM/GC** ou **SM/SC** conforme M/C.  
- **Fina:** Linha A define **M × C**; `LL < 50` define **L × H** ⇒ **ML, CL, MH, CH**.  
- **Orgânico:** **OL/OH**; **Pt** para materiais altamente orgânicos (turfas).

> **Atenção**: entradas devem se referir à mesma amostra e à fração indicada (ex.: pedregulho/areia na **fração > #200**).

## 📜 Licença
MIT — veja `LICENSE`.