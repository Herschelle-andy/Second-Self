import os
import json
import datetime
import streamlit as st
import streamlit.components.v1 as components

# Load local environment files
from lib.utils import load_env, sync_to_github, delete_note, get_secret
load_env(os.path.dirname(os.path.abspath(__file__)))

# Import our local pipeline functions
import capture
import classify
import link
import build_graph
import ask

# Page styling & Configuration
st.set_page_config(
    page_title="SecondSelf - AI Second Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ SCI-FI / NEURAL NETWORK THEME CSS ------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    /* Global Dark Sci-Fi Canvas */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0d1527 0%, #060913 70%, #03050a 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Cyber Matrix Grid Overlay */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-image: 
            linear-gradient(rgba(0, 242, 254, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 242, 254, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }

    /* Main Title */
    .main-title {
        font-family: 'Orbitron', 'Inter', sans-serif;
        font-weight: 900;
        font-size: 2.8rem;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #00ff87 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 25px rgba(0, 242, 254, 0.4);
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        font-family: 'Rajdhani', sans-serif;
        color: #94a3b8;
        font-size: 1.15rem;
        letter-spacing: 1px;
        margin-bottom: 2rem;
    }
    
    .cyber-card {
        padding: 1.4rem;
        border-radius: 12px;
        background: rgba(13, 21, 39, 0.75);
        border: 1px solid rgba(0, 242, 254, 0.25);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .cyber-card:hover {
        border-color: rgba(0, 242, 254, 0.6);
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.25);
    }

    /* Sci-Fi Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(6, 11, 24, 0.6);
        padding: 8px;
        border-radius: 10px;
        border: 1px solid rgba(0, 242, 254, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #94a3b8;
        background-color: transparent;
        border-radius: 6px;
        padding: 0 16px;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        color: #00f2fe !important;
        background: rgba(0, 242, 254, 0.12) !important;
        border: 1px solid #00f2fe !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.35);
    }

    /* Sci-Fi Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #070c18 0%, #0a1122 100%);
        border-right: 1px solid rgba(0, 242, 254, 0.25);
        box-shadow: 5px 0 25px rgba(0, 0, 0, 0.5);
    }

    /* Buttons */
    .stButton > button {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 1px;
        border-radius: 6px;
        transition: all 0.25s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        color: #040814;
        border: 1px solid #00f2fe;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.4);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #38ef7d 0%, #11998e 100%);
        border-color: #38ef7d;
        color: #040814;
        box-shadow: 0 0 25px rgba(56, 239, 125, 0.6);
        transform: translateY(-1px);
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea {
        background: rgba(10, 17, 34, 0.8) !important;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #00f2fe !important;
        box-shadow: 0 0 12px rgba(0, 242, 254, 0.5) !important;
    }

    /* Accordion / Expanders */
    .streamlit-expanderHeader {
        background: rgba(13, 21, 39, 0.8) !important;
        border: 1px solid rgba(0, 242, 254, 0.2) !important;
        border-radius: 8px !important;
        color: #38bdf8 !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ PIPELINE EXECUTION ------------------
def run_post_capture_pipeline(base_dir):
    """Run classify, link, and graph builder sequentially."""
    status_placeholder = st.empty()
    with status_placeholder.status("Processing captured item (AI Organizing & Linking)...", expanded=True) as status:
        try:
            status.write("Classifying note via Llama-3 (PARA)...")
            classify.process_raw_captures(base_dir)
            
            status.write("Computing semantic embeddings & linking related notes...")
            wiki_dir = os.path.join(base_dir, 'wiki')
            link.link_notes(wiki_dir, similarity_threshold=0.45)
            
            status.write("Rebuilding knowledge graph structure...")
            output_json = os.path.join(base_dir, 'graph.json')
            build_graph.build_graph_data(wiki_dir, output_json)
            
            status.write("Syncing knowledge base to GitHub repository...")
            sync_ok, sync_msg = sync_to_github(base_dir)
            
            status.update(label="Second Brain updated successfully!", state="complete", expanded=False)
            if sync_ok:
                st.session_state["capture_success"] = "✅ Successfully captured, classified, and synced to GitHub!"
            else:
                st.session_state["capture_success"] = f"✅ Note captured locally. (Sync Notice: {sync_msg})"
            st.rerun()
        except Exception as e:
            status.update(label=f"Pipeline error: {e}", state="error")
            st.error(f"Post-capture pipeline encountered an error: {e}")

# ------------------ VIS-NETWORK NEURAL GRAPH HTML ------------------
def get_graph_html(graph_data):
    # Sci-Fi / Neural Network Color Mapping for PARA categories
    color_map = {
        "Projects": {
            "background": "#00f2fe", 
            "border": "#38bdf8", 
            "highlight": {"background": "#ffffff", "border": "#00f2fe"}
        }, # Neon Cyan
        "Areas": {
            "background": "#00ff87", 
            "border": "#34d399", 
            "highlight": {"background": "#ffffff", "border": "#00ff87"}
        },    # Emerald Green
        "Resources": {
            "background": "#ffb703", 
            "border": "#fbbf24", 
            "highlight": {"background": "#ffffff", "border": "#ffb703"}
        },# Amber Yellow
        "Archives": {
            "background": "#a855f7", 
            "border": "#c084fc", 
            "highlight": {"background": "#ffffff", "border": "#a855f7"}
        }  # Cosmic Purple
    }
    
    formatted_nodes = []
    for node in graph_data.get("nodes", []):
        cat = node.get("category", "Resources")
        colors = color_map.get(cat, color_map["Resources"])
        
        tooltip = f"""
        <div style="font-family: 'Rajdhani', Arial, sans-serif; padding: 14px; width: 280px; background: rgba(7, 12, 24, 0.95); border: 1px solid #00f2fe; border-radius: 8px; box-shadow: 0 0 15px rgba(0, 242, 254, 0.4); color: #e2e8f0;">
            <b style="font-size: 16px; color: #ffffff; letter-spacing: 0.5px;">{node['label']}</b><br/>
            <span style="display: inline-block; background: rgba(0, 242, 254, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); padding: 2px 8px; font-size: 11px; border-radius: 4px; font-weight: bold; margin-top: 6px; margin-bottom: 8px;">
                {cat}
            </span><br/>
            <p style="font-size: 12px; margin: 0; color: #94a3b8; line-height: 1.4;">{node.get('summary', 'No summary available.')}</p>
            <div style="margin-top: 8px;">
                {' '.join([f'<span style="background: rgba(255, 255, 255, 0.08); border-radius: 3px; font-size: 10px; padding: 2px 6px; color: #a5f3fc; margin-right: 4px;">#{t}</span>' for t in node.get('tags', [])])}
            </div>
        </div>
        """
        
        node_size = 28 if cat == "Projects" else (24 if cat == "Areas" else 18)
        formatted_nodes.append({
            "id": node["id"],
            "label": node["label"],
            "title": tooltip,
            "color": colors,
            "shape": "dot",
            "size": node_size,
            "shadow": {
                "enabled": True,
                "color": colors["border"],
                "size": 12,
                "x": 0,
                "y": 0
            }
        })
        
    formatted_edges = []
    for edge in graph_data.get("edges", []):
        formatted_edges.append({
            "from": edge["from"],
            "to": edge["to"],
            "color": {
                "color": "rgba(0, 242, 254, 0.35)", 
                "highlight": "#00f2fe", 
                "hover": "#00ff87"
            },
            "width": 1.8,
            "smooth": {
                "type": "curvedCW",
                "roundness": 0.15
            }
        })

    nodes_json = json.dumps(formatted_nodes)
    edges_json = json.dumps(formatted_edges)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SecondSelf Graph</title>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            #mynetwork {{
                width: 100%;
                height: 560px;
                background: #030712;
                border: 1px solid rgba(0, 242, 254, 0.25);
                border-radius: 12px;
                box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 242, 254, 0.15);
            }}
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: transparent;
            }}
            .vis-tooltip {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
            }}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        <script type="text/javascript">
            var nodes = new vis.DataSet({nodes_json});
            var edges = new vis.DataSet({edges_json});

            var container = document.getElementById('mynetwork');
            var data = {{
                nodes: nodes,
                edges: edges
            }};
            var options = {{
                nodes: {{
                    font: {{
                        size: 13,
                        face: 'Rajdhani, Arial',
                        color: '#f8fafc',
                        strokeWidth: 3,
                        strokeColor: '#030712'
                    }},
                    borderWidth: 2,
                    shadow: true
                }},
                edges: {{
                    shadow: {{
                        enabled: true,
                        color: 'rgba(0, 242, 254, 0.25)',
                        size: 8
                    }}
                }},
                physics: {{
                    stabilization: true,
                    barnesHut: {{
                        gravitationalConstant: -9000,
                        springConstant: 0.035,
                        springLength: 105,
                        damping: 0.09
                    }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 60,
                    zoomView: true,
                    dragView: true
                }}
            }};
            var network = new vis.Network(container, data, options);
        </script>
    </body>
    </html>
    """
    return html_code

# ------------------ PRE-RUN CALLBACKS ------------------
def capture_note_callback(raw_dir):
    note_content = st.session_state.get("note_input_widget", "")
    if note_content.strip():
        capture.capture_note(raw_dir, note_content)
        st.session_state["note_input_widget"] = ""
        st.session_state["run_pipeline"] = True

def capture_link_callback(raw_dir):
    link_url = st.session_state.get("link_input_widget", "")
    if link_url.strip():
        capture.capture_link(raw_dir, link_url)
        st.session_state["link_input_widget"] = ""
        st.session_state["run_pipeline"] = True

def capture_file_callback(raw_dir, base_dir):
    uploaded_file = st.session_state.get("file_input_widget")
    if uploaded_file is not None:
        temp_path = os.path.join(base_dir, uploaded_file.name)
        try:
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            capture.capture_file(raw_dir, temp_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            st.session_state["file_input_widget"] = None
            st.session_state["run_pipeline"] = True
        except Exception as e:
            st.session_state["capture_error"] = f"Error handling file upload: {e}"

def query_brain_callback(wiki_dir):
    query = st.session_state.get("query_input_widget", "")
    if query.strip():
        import numpy as np
        answer, sources = ask.ask_brain(query, wiki_dir)
        st.session_state["rag_query"] = query
        st.session_state["rag_answer"] = answer
        st.session_state["rag_sources"] = sources
        st.session_state["query_input_widget"] = ""

# ------------------ MAIN INTERFACE ------------------
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir, wiki_dir = capture.setup_directories(base_dir)
    
    # Check if pipeline run flag was set in callbacks
    if st.session_state.get("run_pipeline"):
        del st.session_state["run_pipeline"]
        run_post_capture_pipeline(base_dir)
        
    if "capture_error" in st.session_state:
        st.sidebar.error(st.session_state["capture_error"])
        del st.session_state["capture_error"]
    
    # Title
    st.markdown('<h1 class="main-title">🧠 SecondSelf</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Your self-organizing personal AI Second Brain</p>', unsafe_allow_html=True)
    
    # ------------------ SIDEBAR: INGESTION PIPELINE ------------------
    if "capture_success" in st.session_state:
        st.sidebar.success(st.session_state["capture_success"])
        del st.session_state["capture_success"]
        
    st.sidebar.markdown("### 📥 Capture Anything")
    capture_type = st.sidebar.radio("Input Type", ["Note", "Link / Bookmark", "File Upload"])
    
    if capture_type == "Note":
        st.sidebar.text_area("Write down an idea or note", placeholder="E.g., Remind me to look at visual analytics tools for Python next Monday.", height=150, key="note_input_widget")
        st.sidebar.button("Capture Note", use_container_width=True, on_click=capture_note_callback, args=(raw_dir,))
                
    elif capture_type == "Link / Bookmark":
        st.sidebar.text_area("URL to scrape & capture", placeholder="https://github.com/trending", height=150, key="link_input_widget")
        st.sidebar.button("Capture Link", use_container_width=True, on_click=capture_link_callback, args=(raw_dir,))
                
    elif capture_type == "File Upload":
        uploaded_file = st.sidebar.file_uploader("Upload note, article, or PDF", type=["txt", "md", "json", "html", "pdf"], key="file_input_widget")
        if uploaded_file is not None:
            st.sidebar.button("Capture Uploaded File", use_container_width=True, on_click=capture_file_callback, args=(raw_dir, base_dir))
            
    st.sidebar.markdown("### ⚡ Manual Action")
    if st.sidebar.button("Process New Capture", use_container_width=True):
        run_post_capture_pipeline(base_dir)
        
    # Display configuration/API check in sidebar footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ System Status")
    groq_api_status = "✅ Set" if get_secret("GROQ_API_KEY") else "❌ Missing (Set GROQ_API_KEY)"
    st.sidebar.write(f"Groq API: {groq_api_status}")
    
    gh_token = get_secret("GITHUB_TOKEN") or get_secret("GH_TOKEN")
    gh_status = "✅ Active" if gh_token else "⚠️ Missing GITHUB_TOKEN"
    st.sidebar.write(f"Cloud Auto-Sync: {gh_status}")
    if not gh_token:
        st.sidebar.caption("⚠️ *Add `GITHUB_TOKEN` to Streamlit Cloud Secrets so captures persist permanently across cloud reboots.*")
    
    # Load notes for display/stats
    wiki_notes = ask.load_all_notes(wiki_dir)
    st.sidebar.write(f"Total Wiki Notes: **{len(wiki_notes)}**")
    
    # ------------------ MAIN SECTION: TABS ------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌐 Living Brain Graph", 
        "🔍 Ask Your Brain (RAG)", 
        "📚 Browse Wiki Notes", 
        "🗑️ Manage & Delete Notes"
    ])
    
    # ------------------ TAB 1: GRAPH ------------------
    with tab1:
        st.markdown("### Interactive Knowledge Graph")
        st.caption("Hover over nodes to see summaries. Drag to move, pinch/scroll to zoom.")
        
        graph_path = os.path.join(base_dir, 'graph.json')
        if not os.path.exists(graph_path) or len(wiki_notes) == 0:
            if len(wiki_notes) > 0:
                build_graph.build_graph_data(wiki_dir, graph_path)
            else:
                st.info("No captured notes to display yet. Capture some items on the sidebar to build your brain!")
                
        if os.path.exists(graph_path) and len(wiki_notes) > 0:
            try:
                with open(graph_path, 'r', encoding='utf-8') as f:
                    graph_data = json.load(f)
                
                graph_html = get_graph_html(graph_data)
                if hasattr(st, "iframe"):
                    st.iframe(graph_html, height=580)
                else:
                    components.html(graph_html, height=580)
                
                # Legend
                st.markdown("""
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-top: 12px; padding: 10px 16px; background: rgba(13, 21, 39, 0.6); border: 1px solid rgba(0, 242, 254, 0.2); border-radius: 8px;">
                    <span style="color: #00f2fe; font-weight: bold; font-family: 'Rajdhani', sans-serif;">🔵 Projects (Goal-oriented)</span>
                    <span style="color: #00ff87; font-weight: bold; font-family: 'Rajdhani', sans-serif;">🟢 Areas (Ongoing Standards)</span>
                    <span style="color: #ffb703; font-weight: bold; font-family: 'Rajdhani', sans-serif;">🟡 Resources (Interests & Tools)</span>
                    <span style="color: #a855f7; font-weight: bold; font-family: 'Rajdhani', sans-serif;">🟣 Archives (Inactive)</span>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error displaying graph: {e}")
                
    # ------------------ TAB 2: RAG QUERY ------------------
    with tab2:
        st.markdown("### Ask your SecondSelf anything")
        st.caption("Natural language search synthesizing answers exclusively from your captured documents.")
        
        query = st.text_input("Ask a question about your knowledge base:", placeholder="What did I note down about visual analytics libraries?", key="query_input_widget")
        
        col_btn_left, col_btn_mid, col_btn_right = st.columns([1, 4, 1])
        with col_btn_left:
            st.button("Query Brain", type="primary", on_click=query_brain_callback, args=(wiki_dir,))
        with col_btn_right:
            if "rag_answer" in st.session_state:
                if st.button("Clear Results", type="primary"):
                    del st.session_state["rag_query"]
                    del st.session_state["rag_answer"]
                    del st.session_state["rag_sources"]
                    st.rerun()
                
        # Persistent display of query results
        if "rag_answer" in st.session_state:
            st.markdown("---")
            st.markdown(f"❓ **Question:** *{st.session_state['rag_query']}*")
            
            st.markdown(f"""
            <div class="cyber-card" style="border-left: 4px solid #00f2fe;">
                <div style="font-family: 'Rajdhani', sans-serif; font-size: 16px; font-weight: bold; color: #00f2fe; margin-bottom: 8px;">Response:</div>
                <div style="color: #f1f5f9; line-height: 1.6;">{st.session_state["rag_answer"]}</div>
            </div>
            """, unsafe_allow_html=True)
            
            sources = st.session_state.get("rag_sources", [])
            if sources:
                st.markdown("#### Retrieved Sources:")
                cols = st.columns(len(sources))
                for idx, src in enumerate(sources):
                    with cols[idx]:
                        card_style = f"""
                        <div class="cyber-card" style="padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 242, 254, 0.3); background: rgba(8, 14, 28, 0.85);">
                            <div style="font-size: 10px; font-family: monospace; color: #00f2fe; margin-bottom: 2px;">Relevancy: {src['score']:.2f}</div>
                            <h5 style="margin: 0; color: #ffffff; font-family: 'Rajdhani', sans-serif; font-size: 15px;">{src['title']}</h5>
                            <span style="font-size: 10px; color: #38bdf8; font-weight: bold;">[{src['category']}]</span>
                        </div>
                        """
                        st.markdown(card_style, unsafe_allow_html=True)
                
    # ------------------ TAB 3: BROWSE WIKI ------------------
    with tab3:
        st.markdown("### Browse Wiki Knowledge Base")
        if not wiki_notes:
            st.info("Knowledge base is empty. Capture notes to populate.")
        else:
            categories = ['Projects', 'Areas', 'Resources', 'Archives']
            selected_cat = st.selectbox("Filter Category", ["All"] + categories)
            
            filtered_notes = [
                n for n in wiki_notes 
                if selected_cat == "All" or n["category"] == selected_cat
            ]
            
            if not filtered_notes:
                st.write("No notes found in this category.")
            else:
                for note in filtered_notes:
                    with st.expander(f"📁 {note['category']} | {note['title']}"):
                        st.markdown(f"**Captured At**: `{note.get('captured_at', 'Unknown')}`")
                        st.markdown(f"**Tags**: `{' '.join([f'#{t}' for t in note.get('tags', [])])}`")
                        st.markdown(f"**Summary**: *{note.get('summary', 'No summary available.')}*")
                        st.markdown("---")
                        st.markdown(note["body"])
                        
    # ------------------ TAB 4: MANAGE & DELETE ------------------
    with tab4:
        st.markdown("### 🗑️ Manage & Delete Notes")
        st.caption("Select notes to review their details or permanently delete them from your knowledge base and GitHub repository.")
        
        if "delete_success" in st.session_state:
            st.success(st.session_state["delete_success"])
            del st.session_state["delete_success"]
            
        if not wiki_notes:
            st.info("Your knowledge base is empty. There are no notes to manage.")
        else:
            col_filter_src, col_filter_cat = st.columns(2)
            with col_filter_src:
                src_filter = st.selectbox(
                    "Filter by Origin", 
                    ["All Notes", "App Captures Only (⭐ Newly Captured)", "Pre-existing / Seed Notes"]
                )
            with col_filter_cat:
                cat_filter = st.selectbox("Filter by PARA Category", ["All", "Projects", "Areas", "Resources", "Archives"], key="del_cat_filter")
                
            manage_notes = []
            for n in wiki_notes:
                is_app = n.get("source") == "app_capture"
                if src_filter == "App Captures Only (⭐ Newly Captured)" and not is_app:
                    continue
                if src_filter == "Pre-existing / Seed Notes" and is_app:
                    continue
                if cat_filter != "All" and n["category"] != cat_filter:
                    continue
                manage_notes.append(n)
                
            if not manage_notes:
                st.info("No notes match the selected filters.")
            else:
                def format_timestamp(note):
                    raw_time = note.get("captured_at", "")
                    if raw_time:
                        try:
                            return raw_time.replace("T", " ").split(".")[0]
                        except Exception:
                            return raw_time[:19]
                    try:
                        mtime = os.path.getmtime(note["path"])
                        return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        return "Unknown Date"
                        
                note_options = {}
                for n in manage_notes:
                    time_str = format_timestamp(n)
                    origin_tag = "⭐ App Capture" if n.get("source") == "app_capture" else "📁 Seed Note"
                    label = f"[{time_str}] {n['title']} ({n['category']}) — {origin_tag}"
                    note_options[label] = n
                    
                selected_label = st.selectbox(
                    "Select a note from the menu to inspect or delete:",
                    list(note_options.keys())
                )
                
                selected_note = note_options[selected_label]
                time_str = format_timestamp(selected_note)
                origin_badge = "🟢 New App Capture" if selected_note.get("source") == "app_capture" else "⚪ Pre-existing"
                
                st.markdown(f"""
                <div class="cyber-card" style="border-left: 4px solid #f72585;">
                    <h4 style="margin-top: 0; color: #ffffff; font-family: 'Rajdhani', sans-serif;">{selected_note['title']}</h4>
                    <p style="font-size: 13px; color: #94a3b8; margin-bottom: 8px;">
                        <b>Category:</b> <span style="color: #00f2fe;">{selected_note['category']}</span> &nbsp;|&nbsp; 
                        <b>Captured Date & Time:</b> <code>{time_str}</code> &nbsp;|&nbsp;
                        <b>Origin:</b> {origin_badge}
                    </p>
                    <p style="font-size: 13px; color: #cbd5e1;"><b>Summary:</b> {selected_note.get('summary', 'No summary available.')}</p>
                    <p style="font-size: 11px; color: #64748b;"><b>File Path:</b> <code>{selected_note['path']}</code></p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("📄 View Full Markdown Content"):
                    st.markdown(selected_note["body"])
                    
                is_app_capture = selected_note.get("source") == "app_capture"
                
                if not is_app_capture:
                    st.info("🔒 **Protected Seed Note:** Pre-existing knowledge base notes are permanent and cannot be modified or deleted.")
                else:
                    st.markdown("#### 🔐 Authorization Required")
                    admin_pin = st.text_input(
                        "Enter Admin Passcode to authorize deletion:", 
                        type="password", 
                        placeholder="Enter passcode (Default: 1234)", 
                        key=f"del_pin_{selected_note['id']}"
                    )
                    
                    col_del_btn, col_del_space = st.columns([2, 4])
                    with col_del_btn:
                        if st.button("🗑️ Delete Note", type="primary", use_container_width=True):
                            expected_pin = get_secret("ADMIN_PIN", "1234")
                            if admin_pin.strip() != expected_pin:
                                st.error("❌ Authentication Failed: Invalid Admin Passcode. Note was not deleted.")
                            else:
                                with st.spinner("Deleting note, rebuilding graph, and syncing repository..."):
                                    ok, msg = delete_note(base_dir, selected_note["id"])
                                    if ok:
                                        st.session_state["delete_success"] = f"✅ Successfully deleted note: **{selected_note['title']}**."
                                        st.rerun()
                                    else:
                                        st.error(f"Error deleting note: {msg}")

if __name__ == "__main__":
    main()
