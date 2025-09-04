#!/usr/bin/env python
# coding: utf-8

import re
import uuid
import json
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st

# =========================
# Helpers
# =========================

BASE_COLS = [
    'id','ramo','ordem','tipo_ini','de_no','para_no',
    'dn_mm','comp_real_m','dz_io_m','peso_trecho','p_min_ref_kPa'
]
DTYPES = {
    'id':'string','ramo':'string','ordem':'Int64','tipo_ini':'string',
    'de_no':'string','para_no':'string',
    'dn_mm':'float','comp_real_m':'float','dz_io_m':'float','peso_trecho':'float','p_min_ref_kPa':'float'
}

def _s(x):
    try:
        if pd.isna(x):
            return ''
    except Exception:
        pass
    return '' if x is None else str(x)

def _num(x, default=0.0):
    try:
        if pd.isna(x):
            return default
    except Exception:
        pass
    try:
        return float(str(x).replace(',', '.'))
    except Exception:
        return default

def normalize_label(value: str, mode: str) -> str:
    """Limpa/valida rótulos conforme o modo escolhido."""
    if mode.startswith('Letras'):
        v = (value or '').strip().upper()
        if not re.fullmatch(r'[A-Z]+', v):
            raise ValueError('Use apenas letras maiúsculas (A–Z, AA, AB, ...).')
        return v
    else:  # Números
        v = (value or '').strip()
        if not re.fullmatch(r'[0-9]+', v):
            raise ValueError('Use apenas dígitos (0–9).')
        return str(int(v))

def _norm_tipo(x:str)->str:
    """Normaliza 'tipo_ini' para comparação robusta (tê/te, entrada de água, cruzeta)."""
    s = _s(x).lower().strip()
    s = ''.join(ch for ch in unicodedata.normalize('NFD', s) if unicodedata.category(ch) != 'Mn')
    s = s.replace(' ', '')
    if 'entrada' in s:
        return 'entrada'
    if 'cruzeta' in s:
        return 'cruzeta'
    if 'te' in s:  # cobre 'tê' e 'te'
        return 'te'
    return s

def _ensure_session_df():
    if 'trechos' not in st.session_state or not isinstance(st.session_state['trechos'], pd.DataFrame):
        st.session_state['trechos'] = pd.DataFrame(columns=BASE_COLS)
    else:
        df = st.session_state['trechos']
        for c in BASE_COLS:
            if c not in df.columns:
                df[c] = pd.Series([None]*len(df))
        st.session_state['trechos'] = df[BASE_COLS]

def _st_rerun():
    if hasattr(st, 'rerun'):
        st.rerun()
    elif hasattr(st, 'experimental_rerun'):
        st.experimental_rerun()

def trecho_label(r):
    return f"{_s(r.get('ramo'))}-{_s(r.get('ordem'))} [{_s(r.get('de_no'))}→{_s(r.get('para_no'))}] ({_s(r.get('tipo_ini'))})"

# =========================
# App
# =========================

st.set_page_config(page_title='SPAF – Trechos', layout='wide')
st.title('SPAF – Cadastro de Trechos (Entrada, Tê, Cruzeta)')

_ensure_session_df()

# Sidebar
with st.sidebar:
    st.header('Parâmetros Globais')
    projeto_nome = st.text_input('Nome do Projeto', 'Projeto Genérico')
    st.markdown('---')
    st.subheader('Notação dos nós (início/fim)')
    notacao_mode = st.radio('Modo de notação', ['Letras (A, B, ..., Z, AA, AB, ...)', 'Números (1, 2, 3, ...)'], index=0)
    st.caption('A validação garante que os rótulos dos nós respeitem o modo escolhido.')
    st.markdown('---')
    st.subheader('Capacidade por tipo de conexão (saídas permitidas por nó de início)')
    cap_ent = st.number_input('Entrada de água – máx. saídas', min_value=1, max_value=10, value=1, step=1)
    cap_te  = st.number_input('Tê – máx. saídas', min_value=1, max_value=10, value=2, step=1)
    cap_crz = st.number_input('Cruzeta – máx. saídas', min_value=1, max_value=10, value=3, step=1)

tab1, tab2 = st.tabs(['Trechos', 'Resultados (prévia)'])

# ---------------- TAB 1: Cadastro ----------------
with tab1:
    st.subheader('Cadastrar trechos')
    with st.form('frm_add'):
        # Linha 1 – identificação
        c1,c2,c3 = st.columns([1.2,1,1])
        id_val = c1.text_input('id (opcional)')
        ramo = c2.text_input('ramo', value='A')
        ordem = c3.number_input('ordem', min_value=1, step=1, value=1)

        # Linha 2 – tipo do ponto inicial, início e fim
        st.markdown('**Ponto inicial e final**')
        c4, c5, c6 = st.columns([1.4, 1, 1])
        tipo_ini = c4.selectbox('Tipo da conexão no INÍCIO', ['Entrada de Água','Tê','Cruzeta'])
        de_no_raw = c5.text_input('de_no (início)', value='A' if notacao_mode.startswith('Let') else '1')
        para_no_raw = c6.text_input('para_no (fim)', value='B' if notacao_mode.startswith('Let') else '2')

        # Linha 3 – DN, comprimento, desnível
        c7,c8,c9 = st.columns(3)
        dn_mm = c7.number_input('dn_mm (mm, interno)', min_value=0.0, step=1.0, value=32.0)
        comp_real_m = c8.number_input('comp_real_m (m)', min_value=0.0, step=0.1, value=6.0, format='%.2f')
        dz_io_m = c9.number_input("dz_io_m (m) (z_inicial - z_final; desce>0, sobe<0)", step=0.1, value=0.0, format="%.2f")

        # Linha 4 – peso e ponto final (mín. de pressão)
        c10,c11 = st.columns([1,1])
        peso_trecho = c10.number_input('peso_trecho (UC)', min_value=0.0, step=1.0, value=10.0, format='%.2f')
        tipo_ponto = c11.selectbox('Tipo do ponto no final do trecho', ['Sem utilização (5 kPa)','Ponto de utilização (10 kPa)'])
        p_min_ref_kPa = st.number_input('p_min_ref (kPa)', min_value=0.0, step=0.5,
                                        value=(5.0 if 'Sem' in tipo_ponto else 10.0), format='%.2f')

        ok = st.form_submit_button("➕ Adicionar trecho")

        if ok:
            # 1) Notação dos nós
            try:
                de_no = normalize_label(de_no_raw, notacao_mode)
                para_no = normalize_label(para_no_raw, notacao_mode)
            except ValueError as e:
                st.error(f'Erro na notação dos nós: {e}')
                st.stop()
            if de_no == para_no:
                st.error('Início e fim do trecho não podem ser iguais.')
                st.stop()

            df = pd.DataFrame(st.session_state['trechos']).copy()

            # 2) Duplicidade global (de_no + para_no) — independente do ramo
            if not df.empty and {'de_no','para_no'} <= set(df.columns):
                dup = df[(df['de_no'].astype(str)==de_no) & (df['para_no'].astype(str)==para_no)]
                if not dup.empty:
                    st.error(f'Já existe um trecho {de_no} → {para_no}. Não é permitido duplicar essa ligação.')
                    st.stop()

            # 3) Limite de saídas por nó de início + consistência de tipo
            count_out = 0
            if not df.empty and {'de_no','tipo_ini'} <= set(df.columns):
                subset = df[df['de_no'].astype(str)==de_no]
                if not subset.empty:
                    tipos_exist_norm = set(_norm_tipo(x) for x in subset['tipo_ini'].tolist())
                    tipo_sel_norm = _norm_tipo(tipo_ini)
                    if len(tipos_exist_norm) > 1 and tipo_sel_norm not in tipos_exist_norm:
                        st.error('O nó de início já foi cadastrado com tipos diferentes. Padronize o tipo.')
                        st.stop()
                    if len(tipos_exist_norm) == 1 and tipo_sel_norm not in tipos_exist_norm:
                        st.error(f'O nó "{de_no}" já está definido como "{list(subset["tipo_ini"].unique())[0]}".')
                        st.stop()
                    count_out = len(subset)

            cap_map = {'entrada': int(cap_ent), 'te': int(cap_te), 'cruzeta': int(cap_crz)}
            cap_allowed = cap_map.get(_norm_tipo(tipo_ini), 2)
            if count_out >= cap_allowed:
                st.error(f'O nó de início "{de_no}" ({tipo_ini}) já atingiu o limite de {cap_allowed} saída(s).')
                st.stop()

            # 4) Monta nova linha (ID único)
            base_exist = pd.DataFrame(st.session_state['trechos'])
            existing_ids = set(
                base_exist.get('id', pd.Series([], dtype=str)).astype(str).fillna('').str.strip().tolist()
            )
            raw_id = (id_val or '').strip()
            if (not raw_id) or (raw_id in existing_ids):
                base_tag = raw_id if raw_id else 'row'
                raw_id = f"{base_tag}_{uuid.uuid4().hex[:6]}"

            nova = {
                'id': raw_id,'ramo':ramo,'ordem':int(ordem),'tipo_ini':tipo_ini,
                'de_no':de_no,'para_no':para_no,
                'dn_mm':float(dn_mm),'comp_real_m':float(comp_real_m),
                'dz_io_m':float(dz_io_m),'peso_trecho':float(peso_trecho),
                'p_min_ref_kPa':float(p_min_ref_kPa)
            }

            base = pd.concat([df, pd.DataFrame([nova])], ignore_index=True)
            for c,t in DTYPES.items():
                try: base[c] = base[c].astype(t)
                except Exception: pass
            st.session_state['trechos'] = base[BASE_COLS]
            st.success(f'Trecho adicionado: {ramo}: {de_no} → {para_no} ({tipo_ini}).')

    # Tabela
    st.dataframe(pd.DataFrame(st.session_state['trechos'])[BASE_COLS], use_container_width=True, height=360)

# ---------------- TAB 2: Resultados (prévia) ----------------
with tab2:
    st.subheader('Prévia de resultados / exportação')
    base = pd.DataFrame(st.session_state['trechos']).copy()
    if base.empty:
        st.info('Cadastre trechos na aba 1.')
    else:
        params = {
            'projeto': projeto_nome,
            'capacidade': {'entrada': int(cap_ent), 'te': int(cap_te), 'cruzeta': int(cap_crz)}
        }
        show_cols = [c for c in BASE_COLS if c in base.columns]
        proj = {'params': params, 'trechos': base[show_cols].to_dict(orient='list')}
        st.download_button('Baixar projeto (.json)',
                           data=json.dumps(proj, ensure_ascii=False, indent=2).encode('utf-8'),
                           file_name='spaf_projeto.json', mime='application/json')
