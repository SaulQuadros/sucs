Patch — Excel writer engine fix
Date: 2025-09-07 23:43:55

What changed
------------
1) SoilClass/streamlit_app.py
   - Added `_resolve_xlsx_engine()` to choose a working XLSX engine at runtime (prefers XlsxWriter, falls back to openpyxl).
   - Replaced hard-coded `engine="openpyxl"` / `engine="xlsxwriter"` in `pd.ExcelWriter(...)` with `engine=_resolve_xlsx_engine()`.

2) SoilClass/pages/trb_app.py
   - Same dynamic engine resolver added and used in all `pd.ExcelWriter(...)` calls.

3) SoilClass/requirements.txt
   - Ensured the following dependencies are present/pinned to avoid Streamlit Cloud runtime errors:
       XlsxWriter>=3.2.0
       openpyxl>=3.1.2
       pandas>=2.1.0
       streamlit>=1.29.0

Why this fixes the error
------------------------
Your app crashed when trying to generate the XLSX template because the "openpyxl" (or any Excel engine) package wasn't available in the deployment environment. 
By (a) adding the packages to requirements.txt and (b) selecting an available engine dynamically at runtime, the app can create the workbook reliably.

What you need to replace in your repo
-------------------------------------
- SoilClass/streamlit_app.py
- SoilClass/pages/trb_app.py
- SoilClass/requirements.txt

Deployment notes
----------------
- After pushing these files, trigger a redeploy on Streamlit Cloud so the environment installs the new dependencies.
- If your environment uses Python 3.13, XlsxWriter is typically the safest writer engine (pure Python). The resolver prefers it automatically.