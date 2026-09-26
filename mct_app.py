# mct_app.py
# Mantido por compatibilidade com implantações antigas: abre o app completo (sucs_app.py).
import os
import runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sucs_app.py"), run_name="__main__")
