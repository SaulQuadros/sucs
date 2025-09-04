#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st

def _st_rerun():
    # Compat handler without recursion
    if hasattr(st, 'rerun'):
        st.rerun()
    elif hasattr(st, 'experimental_rerun'):
        st.experimental_rerun()
    else:
        return

import pandas as pd
import json
from pathlib import Path
import uuid

# ----------------- Constants -----------------
KPA_PER_M = 9.80665  # 1 m.c.a. ≈ 9.80665 kPa

# ----------------- Small helpers -----------------
def _s(x):
    try:
        if pd.isna(x): return ''
    except Exception:
        pass
    return '' if x is None else str(x)

def _num(x, default=0.0):
    try:
        if pd.isna(x): return default
    except Exception:
        pass
    try:
        return float(str(x).replace(',', '.'))
    except Exception:
        return default

def _i(x, default=0):
    try: return int(_num(x, default))
    except Exception: return default

def trecho_label(r):
    return f"{_s(r.get('ramo'))}-{_i(r.get('ordem'))} [{_s(r.get('de_no'))}→{_s(r.get('para_no'))}] id={_s(r.get('id'))}"

# ----------------- Tables -----------------
def load_tables():
    base = Path(__file__).parent
    pvc = pd.read_csv(base / 'data/pvc_pl_eqlen.csv')
    fofo = pd.read_csv(base / 'data/fofo_pl_eqlen.csv')
    return pvc, fofo

def get_dn_series(table):
    for nm in table.columns:
        low = nm.lower()
        if ('de' in low or 'dn' in low or 'diam' in low) and 'mm' in low:
            return table[nm], nm
    return table.iloc[:, 0], table.columns[0]

def piece_columns_for(table):
    dn_series, dn_name = get_dn_series(table)
    cols = [c for c in table.columns if c not in (dn_name, 'dref_pol')]
    return cols, dn_name

def lookup_row_by_mm(table, ref_mm):
    dn_series, dn_name = get_dn_series(table)
    try: x = float(ref_mm)
    except Exception: x = 0.0
    idx = (dn_series - x).abs().idxmin()
    row = table.loc[idx]
    de_ref_mm = float(row.get(dn_name, 0) or 0)
    pol_ref = _s(row.get('dref_pol'))
    return row, de_ref_mm, pol_ref

def pretty(name: str):
    name = (name or '').strip()
    name = name.replace('_', ' ')
    name = name.replace(' de ', ' DE ')
    name = name.replace(' mm', ' (mm)')
    return name

# ----------------- Hidráulica -----------------
def j_fair_whipple_hsiao_kPa_per_m(Q_Ls, D_mm, material: str):
    Q = max(0.0, _num(Q_Ls, 0.0))
    D = max(0.0, _num(D_mm, 0.0))
    if D <= 0.0:
        return 0.0
    mat = (material or '').strip().lower()
    if mat == 'pvc':
        return 8.695e6 * (Q ** 1.75) / (D ** 4.75)
    else:
        return 20.2e6  * (Q ** 1.88) / (D ** 4.88)

def j_hazen_williams(Q_Ls, D_mm, C):
    # Q in L/s -> m3/s ; D in mm -> m ; J in m/m
    Q = max(0.0, _num(Q_Ls, 0.0)) / 1000.0
    D = max(0.0, _num(D_mm, 0.0)) / 1000.0
    if D <= 0.0 or C <= 0.0: return 0.0
    return 10.67 * (Q ** 1.852) / ( (C ** 1.852) * (D ** 4.87) )

def j_fair_whipple_hsiao(Q_Ls, D_mm):
    # Provided form, already for Q in L/s and D in mm ; J in m/m
    Q = max(0.0, _num(Q_Ls, 0.0))
    D = max(0.0, _num(D_mm, 0.0))
    if D <= 0.0: return 0.0
    return 20.2e6 * (Q ** 1.88) / (D ** 4.88)

# ----------------- App -----------------
st.set_page_config(page_title='SPAF – kPa + HW/FWH + L_eq por DN ref. + P(A)', layout='wide')
st.title('Dimensionamento – Barrilete e Colunas (kPa • Hazen-Williams / Fair-Whipple-Hsiao • Nível do Reservatório)')

pvc_table, fofo_table = load_tables()

BASE_COLS = ['id','ramo','ordem','de_no','para_no','dn_mm','de_ref_mm','pol_ref','comp_real_m','dz_io_m','peso_trecho','leq_m','p_min_ref_kPa']
DTYPES = {'id':'string','ramo':'string','ordem':'Int64','de_no':'string','para_no':'string',
          'dn_mm':'float','de_ref_mm':'float','pol_ref':'string',
          'comp_real_m':'float','dz_io_m':'float','peso_trecho':'float','leq_m':'float','p_min_ref_kPa':'float'}

with st.sidebar:
    st.header('Parâmetros Globais')
    projeto_nome = st.text_input('Nome do Projeto', 'Projeto Genérico')
    material_sistema = st.selectbox('Material do Sistema', ['(selecione)','PVC','FoFo'], index=0)
    modelo_perda = st.selectbox('Modelo de perda de carga', ['Hazen-Williams','Fair-Whipple-Hsiao'], index=0)
    C_PVC_default = 150.0
    C_FoFo_default = 130.0
    c_pvc = st.number_input('C (PVC, Hazen-Williams)', min_value=1.0, value=C_PVC_default, step=1.0, format='%.0f')
    c_fofo = st.number_input('C (FoFo, Hazen-Williams)', min_value=1.0, value=C_FoFo_default, step=1.0, format='%.0f')
    KPA_PER_M = st.number_input('Conversão kPa por m.c.a.', min_value=9.0, max_value=10.0, value=9.81, step=0.01, format='%.2f')
    st.caption('Para cálculo rápido de pressões: 1 m.c.a. ≈ 9,81 kPa.')

tab1, tab2, tab3 = st.tabs(['Trechos', 'L_eq por DN (referencial)', 'Resultados'])

# TAB 1 — CADASTRO DE TRECHOS
with tab1:
    st.subheader('Cadastrar trechos')
    with st.form('frm_add'):
        c1,c2,c3 = st.columns([1.2,1,1])
        id_val = c1.text_input('id (opcional)')
        ramo = c2.text_input('ramo', value='A')
        ordem = c3.number_input('ordem', min_value=1, step=1, value=1)
        c4,c5 = st.columns(2)
        de_no = c4.text_input('de_no', value='A')
        para_no = c5.text_input('para_no', value='B')
        c6,c7,c8 = st.columns(3)
        dn_mm = c6.number_input('dn_mm (mm, interno)', min_value=0.0, step=1.0, value=32.0)
        comp_real_m = c7.number_input('comp_real_m (m)', min_value=0.0, step=0.1, value=6.0, format='%.2f')
        dz_io_m = c8.number_input(
        "dz_io_m (m) (z_inicial - z_final; desce>0, sobe<0)",
        step=0.1, value=0.0, format="%.2f"
        )

        peso_trecho = st.number_input('peso_trecho (UC)', min_value=0.0, step=1.0, value=10.0, format='%.2f')
        c9,c10 = st.columns([1,1])
        tipo_ponto = c9.selectbox('Tipo do ponto no final do trecho', ['Sem utilização (5 kPa)','Ponto de utilização (10 kPa)'])
        p_min_ref_kPa = c10.number_input('p_min_ref (kPa)', min_value=0.0, step=0.5, value=(5.0 if 'Sem' in tipo_ponto else 10.0), format='%.2f')
        ok = st.form_submit_button("➕ Adicionar trecho", disabled=(material_sistema == "(selecione)"))
    

        if ok:
            # --- garantir ID único ---
            base_exist = pd.DataFrame(st.session_state['trechos'])
            existing_ids = set(
                base_exist.get('id', pd.Series([], dtype=str)).astype(str).fillna('').str.strip().tolist()
            )
            raw_id = (id_val or '').strip()
            if (not raw_id) or (raw_id in existing_ids):
                base_tag = raw_id if raw_id else 'row'
                raw_id = f"{base_tag}_{uuid.uuid4().hex[:6]}"

            mat_key = 'FoFo' if isinstance(material_sistema,str) and material_sistema.strip().lower()=='fofo' else 'PVC'
            table_mat = pvc_table if mat_key=='PVC' else fofo_table
            st.caption(f'Tabela L_eq em uso: **{mat_key}**')
            _row, de_ref_mm, pol_ref = lookup_row_by_mm(table_mat, dn_mm)
            base = pd.DataFrame(st.session_state['trechos']).reindex(columns=BASE_COLS).copy()
            nova = {'id': raw_id,'ramo':ramo,'ordem':int(ordem),'de_no':de_no,'para_no':para_no,
                    'dn_mm':float(dn_mm),'de_ref_mm':float(de_ref_mm),'pol_ref':pol_ref,
                    'comp_real_m':float(comp_real_m),'dz_io_m':float(dz_io_m),
                    'peso_trecho':float(peso_trecho),'leq_m':0.0,'p_min_ref_kPa':float(p_min_ref_kPa)}
            base = pd.concat([base, pd.DataFrame([nova])], ignore_index=True)
            for c,t in DTYPES.items():
                try: base[c] = base[c].astype(t)
                except Exception: pass
            st.session_state['trechos'] = base
            st.success('Trecho adicionado! DN referencial (nominal/externo) e "Dref Pol" preenchidos.')
        vis = pd.DataFrame(st.session_state['trechos']).reindex(columns=[c for c in BASE_COLS if c!='leq_m'])
        st.dataframe(vis, use_container_width=True, height=320)

# ============================
# Painel de gerenciamento de trechos (excluir / mover)
# ============================

st.subheader('Gerenciar trechos')
import pandas as pd

def _move_row_action(row_id, ramo_val, direction):
    df = pd.DataFrame(st.session_state.get('trechos', pd.DataFrame()))
    if df.empty or 'ramo' not in df.columns or 'ordem' not in df.columns:
        return
    if 'id' not in df.columns:
        # fallback: attach a synthetic id based on current order
        df = df.reset_index().rename(columns={'index':'id'})
    sub = df[df['ramo']==ramo_val].sort_values('ordem', kind='stable')
    ids = sub['id'].tolist()
    if row_id not in ids:
        return
    i = ids.index(row_id)
    if direction == 'up' and i > 0:
        ids[i-1], ids[i] = ids[i], ids[i-1]
    elif direction == 'down' and i < len(ids)-1:
        ids[i], ids[i+1] = ids[i+1], ids[i]
    # aplica nova ordem
    sub = sub.set_index('id').loc[ids].reset_index()
    sub['ordem'] = range(1, len(sub)+1)
    df.loc[df['ramo']==ramo_val, 'ordem'] = None
    for _, r in sub.iterrows():
        df.loc[(df['ramo']==ramo_val) & (df['id']==r['id']), 'ordem'] = r['ordem']
    # reatribui 'ordem' sequencial dentro do ramo
    for k, rid in enumerate(ids, start=1):
        df.loc[df['id']==rid, 'ordem'] = k
    st.session_state['trechos'] = df
    if hasattr(st, 'rerun'):
        st.rerun()
    else:
        st.experimental_rerun()

def _delete_row_action(row_id, ramo_val):
    df = pd.DataFrame(st.session_state.get('trechos', pd.DataFrame()))
    if df.empty:
        return
    if 'id' not in df.columns:
        df = df.reset_index().rename(columns={'index':'id'})
    df = df[df['id'] != row_id].reset_index(drop=True)
    # reordenar dentro de cada ramo
    if 'ramo' in df.columns and 'ordem' in df.columns:
        for rv in df['ramo'].dropna().unique().tolist():
            sub = df[df['ramo']==rv].sort_values('ordem', kind='stable').copy()
            sub['ordem'] = range(1, len(sub)+1)
            df.loc[df['ramo']==rv, 'ordem'] = None
            for _, r in sub.iterrows():
                df.loc[(df['ramo']==rv) & (df['id']==r['id']), 'ordem'] = r['ordem']
    st.session_state['trechos'] = df
    _st_rerun()

if 'trechos' in st.session_state and isinstance(st.session_state['trechos'], pd.DataFrame) and not st.session_state['trechos'].empty:
    tman = st.session_state['trechos'].copy()
    if 'ramo' in tman.columns and 'ordem' in tman.columns:
        tman = tman.sort_values(['ramo','ordem'], kind='stable').reset_index(drop=True)
    else:
        tman = tman.reset_index(drop=True)
    r_opt = ['Todos'] + (sorted([str(x) for x in tman['ramo'].dropna().unique().tolist()]) if 'ramo' in tman.columns else [])
    ramo_sel = st.selectbox('Filtrar por ramo', r_opt or ['Todos'], key='manage_ramo_sel')

    if ramo_sel != 'Todos' and 'ramo' in tman.columns:
        tview = tman[tman['ramo'].astype(str)==ramo_sel].reset_index(drop=True)
    else:
        tview = tman.copy()

    default_cols = [c for c in ['id','ramo','ordem','de_no','para_no','dn_mm','de_ref_mm','pol_ref','comp_real_m','dz_io_m','peso_trecho'] if c in tview.columns]
    show_cols = default_cols

    st.caption('Use os botões no final de cada linha para reordenar (↑, ↓) ou excluir (🗑).')
    head = st.columns([*([1]*len(show_cols)), 1.2], gap='small')
    for c, name in zip(head[:-1], show_cols):
        c.markdown(f"**{name}**")
    head[-1].markdown("**Ações**")

    tv = tview.reset_index(drop=True)
    for i, row in tv.iterrows():
        row_cols = st.columns([*([1]*len(show_cols)), 1.2], gap='small')
        for c, name in zip(row_cols[:-1], show_cols):
            c.markdown(f"{row.get(name, '')}")
        with row_cols[-1]:
            a1, a2, a3 = st.columns(3, gap='small')
            rid = str(row.get('id', '')).strip()
            if not rid:
                rid = f"row_{i}"
            rid_key = f"{rid}_{i}"
            with a1:
                up = st.button("↑", key=f"mgr_up_{rid_key}", help="Mover para cima", disabled=(i==0))
            with a2:
                down = st.button("↓", key=f"mgr_down_{rid_key}", help="Mover para baixo", disabled=(i==len(tv)-1))
            with a3:
                delete = st.button("🗑", key=f"mgr_del_{rid_key}", help="Excluir esta linha")
        ramo_val = row.get('ramo', None)
        if up:
            _move_row_action(rid, ramo_val, 'up')
        if down:
            _move_row_action(rid, ramo_val, 'down')
        if delete:
            _delete_row_action(rid, ramo_val)
else:
    st.info('Nenhum trecho cadastrado ainda.')

# TAB 2 — L_eq por trecho (baseado no DN referencial)
with tab2:
    st.subheader('Comprimento Equivalente — editar por trecho (baseado no DN **referencial**)')
    base = pd.DataFrame(st.session_state['trechos'])
    if base.empty:
        st.info('Cadastre trechos na aba 1.')
    elif material_sistema == '(selecione)':
        st.warning('Selecione o Material do Sistema na barra lateral.')
    else:
        mat_key = 'FoFo' if isinstance(material_sistema,str) and material_sistema.strip().lower()=='fofo' else 'PVC'
        table_mat = pvc_table if mat_key=='PVC' else fofo_table
        st.caption(f'Tabela L_eq em uso: **{mat_key}**')
        piece_cols, dn_name = piece_columns_for(table_mat)
        base = base.copy()
        sel = st.selectbox('Selecione o trecho', [trecho_label(r) for _, r in base.iterrows()])
        if sel:
            # edita L_eq pelo DN referencial do trecho
            # OBS: este trecho depende de como você indexa/seleciona; pode ser refinado conforme sua estrutura
            # Aqui, recompute DN ref pela primeira ocorrência encontrada
            idx_sel = None
            for idx, r in base.iterrows():
                if trecho_label(r) == sel:
                    idx_sel = idx
                    break
            if idx_sel is not None:
                eql_row, de_ref_mm, pol_ref = lookup_row_by_mm(table_mat, base.loc[idx_sel, 'dn_mm'])
                display_labels = [pretty(c) for c in piece_cols]
                df = pd.DataFrame({
                    'Conexão/Peça': display_labels,
                    '(m)': [ _num(eql_row.get(c, 0.0), 0.0) for c in piece_cols ],
                    '(Qt.)': [0]*len(piece_cols),
                }).set_index('Conexão/Peça')
                edited = st.data_editor(
                    df,
                    use_container_width=True,
                    num_rows='fixed',
                    column_config={
                        '(m)': st.column_config.NumberColumn(disabled=True, format='%.2f'),
                        '(Qt.)': st.column_config.NumberColumn(min_value=0, step=1)
                    },
                    key=f'eq_editor_{mat_key}_{sel}'
                )
                # salva L_eq total calculada
                leq_total = float((edited['(m)'] * edited['(Qt.)']).sum())
                st.session_state['trechos'].loc[idx_sel, 'leq_m'] = leq_total
                st.success(f'L_eq total para o trecho selecionado: {leq_total:.2f} m')

# TAB 3 — Resultados
with tab3:
    st.subheader('Resultados')
    base = pd.DataFrame(st.session_state['trechos']).copy()
    if base.empty:
        st.info('Cadastre trechos na aba 1.')
    else:
        # cálculos resumidos (exemplo de exibição)
        st.write('Em construção: aqui você pode calcular perdas, somatórios por ramo, etc.')
        # Exporte o projeto
        params = {'projeto': projeto_nome, 'material': material_sistema, 'modelo_perda': modelo_perda,
                  'k_uc': None, 'exp_uc': None, 'C_PVC': c_pvc, 'C_FoFo': c_fofo,
                  'H_max_m': None, 'H_min_m': None, 'H_op_m': None, 'KPA_PER_M': KPA_PER_M}
        t_display = base.copy()
        show_cols = ['id','ramo','ordem','de_no','para_no','dn_mm','de_ref_mm','pol_ref','comp_real_m','dz_io_m','peso_trecho','leq_m','p_min_ref_kPa']
        proj = {'params': params, 'trechos': t_display[show_cols].to_dict(orient='list')}
        st.download_button('Baixar projeto (.json)',
                           data=json.dumps(proj, ensure_ascii=False, indent=2).encode('utf-8'),
                           file_name='spaf_projeto.json', mime='application/json')
