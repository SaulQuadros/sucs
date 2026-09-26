# mct_app.py
# Repasse para a página MCT (pages/mct_app.py), mantido por compatibilidade com implantações antigas.
import os
import runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages", "mct_app.py"), run_name="__main__")
