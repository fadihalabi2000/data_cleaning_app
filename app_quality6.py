import runpy

import streamlit as st
import engine_generalfix
from general_diag_filter import general_diagnosis_columns, is_general_diagnosis

# تستخدم الواجهة والمحرك المرشح نفسه، لذلك لا يمكن أن تظهر أعمدة Drugs في
# الاختيار الافتراضي ثم تدخل إلى قاعدة غياب التشخيص من مسار آخر.
engine_generalfix.is_general_diagnosis = is_general_diagnosis
engine_generalfix.general_diagnosis_columns = general_diagnosis_columns

base_set_page_config = st.set_page_config


def rtl_set_page_config(*args, **kwargs):
    result = base_set_page_config(*args, **kwargs)
    st.markdown(
        """
        <style>
        html,body,.stApp,[data-testid="stAppViewContainer"],
        [data-testid="stMarkdownContainer"],[data-testid="stWidgetLabel"],
        label,p,small,h1,h2,h3,h4,h5,h6 {
            direction:rtl!important;
            text-align:right!important;
        }
        [data-testid="stMarkdownContainer"],.card,.card small {
            display:block!important;
            width:100%!important;
        }
        [data-baseweb="tab-list"],[role="tablist"] {
            direction:rtl!important;
            justify-content:flex-start!important;
        }
        [data-baseweb="select"]>div,[data-baseweb="tag"],
        [data-testid="stMultiSelect"] {
            direction:rtl!important;
            text-align:right!important;
        }
        .step {
            direction:rtl!important;
            justify-content:flex-start!important;
            text-align:right!important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    return result


st.set_page_config = rtl_set_page_config
runpy.run_path("app_quality5.py", run_name="__main__")
