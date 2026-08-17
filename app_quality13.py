import runpy

import utils.export_charts as export_charts
import utils.export_compat as export_compat

export_compat.export_workbook = export_charts.export_workbook
runpy.run_path("app_quality12.py", run_name="__main__")
