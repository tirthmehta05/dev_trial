import streamlit as st
import requests
import yaml
from pathlib import Path

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000"
DATA_MODELS_PATH = "../data_models"  # Relative to this file

# --- Helper Functions ---

@st.cache_data
def get_available_schemas():
    """Scans the data_models directory for available YAML schemas."""
    p = Path(__file__).parent / DATA_MODELS_PATH
    if not p.exists():
        return []
    return [f.stem for f in p.glob("*.yaml")]

@st.cache_data
def load_schema(model_name):
    """Loads a specific YAML schema file."""
    schema_path = Path(__file__).parent / DATA_MODELS_PATH / f"{model_name}.yaml"
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def format_schema_name(name: str) -> str:
    """Formats a schema filename into a clean title."""
    return name.replace('_', ' ').title()

def render_form_inputs(schema_fields, is_advanced, parent_key=""):
    """Recursively renders form widgets for a given schema.
    This function is called INSIDE an st.form.
    """
    data = {}
    for field_name, props in schema_fields.items():
        widget_key = f"{parent_key}_{field_name}"
        is_required = props.get('required', False)

        if not is_required and not is_advanced:
            continue

        st.markdown(f"**{field_name}**{' *' if is_required else ''}")

        if props.get('type') == 'list[model]':
            # For lists, we render inputs for items that already exist in session_state
            items = st.session_state.get(widget_key, [])
            data[field_name] = []
            for i, item_data in enumerate(items):
                with st.expander(f"{field_name} Item {i+1}", expanded=True):
                    item_form_data = render_form_inputs(
                        props['model']['fields'], is_advanced, parent_key=f"{widget_key}_{i}"
                    )
                    data[field_name].append(item_form_data)

        elif 'union' in props:
            type_choices = [t.get('type', 'str') for t in props['union']]
            selected_type = st.selectbox(f"Choose type for {field_name}", type_choices, key=f"{widget_key}_type_selector")
            selected_schema = next(t for t in props['union'] if t.get('type', 'str') == selected_type)
            # The actual input is rendered based on the selected type
            data[field_name] = render_form_inputs({field_name: selected_schema}, is_advanced, parent_key=widget_key)[field_name]

        elif props.get('type') == 'model':
            with st.expander(f"{field_name} Details", expanded=True):
                data[field_name] = render_form_inputs(props['model']['fields'], is_advanced, parent_key=widget_key)

        else:  # Handle basic types
            default = props.get('default')
            validation = props.get('validation', {})
            field_type = props.get('type', 'str')

            if 'choices' in validation:
                data[field_name] = st.selectbox(field_name, options=validation['choices'], index=validation['choices'].index(default) if default in validation['choices'] else 0, key=widget_key)
            elif field_type == 'bool':
                data[field_name] = st.checkbox(field_name, value=default if default is not None else False, key=widget_key)
            elif field_type == 'int':
                data[field_name] = st.number_input(field_name, value=default, step=1, key=widget_key)
            else:
                data[field_name] = st.text_input(field_name, value=default if default is not None else "", key=widget_key)
    return data

def manage_dynamic_lists(schema_fields, is_advanced, parent_key=""):
    """Renders the Add/Remove buttons for list[model] fields OUTSIDE the form."""
    for field_name, props in schema_fields.items():
        widget_key = f"{parent_key}_{field_name}"
        is_required = props.get('required', False)

        if not is_required and not is_advanced:
            continue

        if props.get('type') == 'list[model]':
            label = props.get('label', field_name.replace('_', ' ').title())
            st.markdown(f"#### Manage {label}")
            if st.button(f"Add {label}", key=f"{widget_key}_add"):
                if widget_key not in st.session_state:
                    st.session_state[widget_key] = []
                st.session_state[widget_key].append({})
                st.rerun()

            items_in_state = st.session_state.get(widget_key, [])
            for i, item_data in enumerate(items_in_state):
                item_label = props.get('label', field_name.replace('_', ' ').title())
                with st.expander(f"Controls for {item_label} Item {i+1}"):
                    manage_dynamic_lists(
                        props['model']['fields'], 
                        is_advanced, 
                        parent_key=f"{widget_key}_{i}"
                    )
                    if st.button(f"Remove {item_label} Item {i+1}", key=f"{widget_key}_remove_{i}"):
                        st.session_state[widget_key].pop(i)
                        st.rerun()

        elif props.get('type') == 'model':
            manage_dynamic_lists(props['model']['fields'], is_advanced, parent_key=widget_key)

# --- Main Application ---
st.set_page_config(layout="wide")
st.title("Dynamic Configuration Generator")

schemas = get_available_schemas()
if not schemas:
    st.warning("No data model schemas found in the data_models directory.")
    st.stop()

# --- Sidebar ---
st.sidebar.title("Navigation")
selected_schema_name = st.sidebar.radio(
    "Choose a Data Model", 
    schemas, 
    format_func=format_schema_name
)
st.sidebar.markdown("---")
is_advanced_mode = st.sidebar.toggle("Show Advanced Fields", value=False)

# --- Main Content ---
st.header(f"Configuration for: {format_schema_name(selected_schema_name)}")
schema = load_schema(selected_schema_name)

# Create a two-column layout
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Controls")
    # 1. Render buttons to manage list items OUTSIDE the form
    manage_dynamic_lists(schema['fields'], is_advanced_mode)

with col2:
    st.subheader("Inputs")
    # 2. Render the form with data inputs
    with st.form(key=f"{selected_schema_name}_form"):
        form_data = render_form_inputs(schema['fields'], is_advanced_mode)
        submitted = st.form_submit_button("Generate Configuration")

    # 3. Process submission
    if submitted:
        with st.spinner("Generating configuration..."):
            try:
                api_url = f"{BACKEND_URL}/api/generate-config/{selected_schema_name}"
                response = requests.post(api_url, json=form_data)

                if response.status_code == 200:
                    st.subheader("Generated Configuration")
                    st.code(response.text, language="yaml")
                else:
                    st.error(f"Error from backend: {response.status_code}")
                    try:
                        st.json(response.json())
                    except:
                        st.text(response.text)

            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to the backend at {BACKEND_URL}. Please ensure the backend is running.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
