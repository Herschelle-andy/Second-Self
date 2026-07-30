import os
import json
import streamlit as st
import streamlit.components.v1 as components

# Load local environment files
from lib.utils import load_env
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

# Custom premium styling via Streamlit Markdown
st.markdown("""
<style>
    .main-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.8rem;
        background: linear-gradient(90deg, #FF4B4B 0%, #FF8F8F 50%, #4B8EFF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-family: 'Inter', sans-serif;
        color: #7f8c8d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 12px;
        background-color: #f8f9fa;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 9px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Helper to run the pipeline automatically after capture
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
            
            status.update(label="Second Brain updated successfully!", state="complete", expanded=False)
            st.session_state["capture_success"] = "Successfully captured, classified, and linked your new note!"
            st.rerun()
        except Exception as e:
            status.update(label=f"Pipeline error: {e}", state="error")
            st.error(f"Post-capture pipeline encountered an error: {e}")

# HTML/JS generator for vis-network graph visualization
def get_graph_html(graph_data):
    # Color mapping for PARA categories
    color_map = {
        "Projects": {"background": "#3498db", "border": "#2980b9", "highlight": {"background": "#5dade2", "border": "#2980b9"}}, # Blue
        "Areas": {"background": "#2ecc71", "border": "#27ae60", "highlight": {"background": "#58d68d", "border": "#27ae60"}},    # Green
        "Resources": {"background": "#f1c40f", "border": "#f39c12", "highlight": {"background": "#f7dc6f", "border": "#f39c12"}},# Yellow
        "Archives": {"background": "#95a5a6", "border": "#7f8c8d", "highlight": {"background": "#bdc3c7", "border": "#7f8c8d"}}  # Grey
    }
    
    # Process nodes to inject colors and formatted tooltips
    formatted_nodes = []
    for node in graph_data.get("nodes", []):
        cat = node.get("category", "Resources")
        colors = color_map.get(cat, color_map["Resources"])
        
        # Tooltip content using HTML format in vis-network
        tooltip = f"""
        <div style="font-family: Arial, sans-serif; padding: 10px; width: 250px;">
            <b style="font-size: 14px; color: #2c3e50;">{node['label']}</b><br/>
            <span style="display: inline-block; background: #e7f3fe; color: #1e90ff; padding: 2px 6px; font-size: 10px; border-radius: 4px; font-weight: bold; margin-top: 5px; margin-bottom: 5px;">
                {cat}
            </span><br/>
            <p style="font-size: 12px; margin: 0; color: #555;">{node.get('summary', 'No summary.')}</p>
            <div style="margin-top: 5px;">
                {' '.join([f'<span style="background: #f1f1f1; border-radius: 3px; font-size: 10px; padding: 1px 4px; margin-right: 3px;">#{t}</span>' for t in node.get('tags', [])])}
            </div>
        </div>
        """
        
        formatted_nodes.append({
            "id": node["id"],
            "label": node["label"],
            "title": tooltip,
            "color": colors,
            "shape": "dot",
            "size": 25 if cat == "Projects" else (20 if cat == "Areas" else 15)
        })
        
    formatted_edges = []
    for edge in graph_data.get("edges", []):
        formatted_edges.append({
            "from": edge["from"],
            "to": edge["to"],
            "color": {"color": "#cbd5e1", "highlight": "#3b82f6"},
            "width": 1.5
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
                height: 550px;
                border: none;
                background-color: #ffffff;
            }}
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
            }}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        <script type="text/javascript">
            // parse data
            var nodes = new vis.DataSet({nodes_json});
            var edges = new vis.DataSet({edges_json});

            // create a network
            var container = document.getElementById('mynetwork');
            var data = {{
                nodes: nodes,
                edges: edges
            }};
            var options = {{
                nodes: {{
                    font: {{
                        size: 13,
                        face: 'Arial',
                        color: '#2c3e50'
                    }},
                    borderWidth: 2,
                    shadow: true
                }},
                edges: {{
                    smooth: {{
                        type: 'continuous'
                    }}
                }},
                physics: {{
                    stabilization: true,
                    barnesHut: {{
                        gravitationalConstant: -8000,
                        springConstant: 0.04,
                        springLength: 95
                    }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 100
                }}
            }};
            var network = new vis.Network(container, data, options);
            
            // Add double click logic to alert parent if wanted, or log
            network.on("doubleClick", function (params) {{
                if (params.nodes.length > 0) {{
                    var nodeId = params.nodes[0];
                    console.log("Selected node: " + nodeId);
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_code

# Callback functions to safely modify widget state before re-running script
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
        import numpy as np # Ensure numpy is imported
        answer, sources = ask.ask_brain(query, wiki_dir)
        st.session_state["rag_query"] = query
        st.session_state["rag_answer"] = answer
        st.session_state["rag_sources"] = sources
        st.session_state["query_input_widget"] = ""

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
        # Do not delete yet so it displays for one run, but we delete it after rendering
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
                    
    # Display configuration/API check in sidebar footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ System Status")
    groq_api_status = "✅ Set" if os.environ.get("GROQ_API_KEY") else "❌ Missing (Set GROQ_API_KEY environment var)"
    st.sidebar.write(f"Groq API: {groq_api_status}")
    
    # Load notes for display/stats
    wiki_notes = ask.load_all_notes(wiki_dir)
    st.sidebar.write(f"Total Wiki Notes: **{len(wiki_notes)}**")
    
    st.sidebar.markdown("### ⚡ Manual Action")
    if st.sidebar.button("Process New Capture", use_container_width=True):
        run_post_capture_pipeline(base_dir)
    
    # ------------------ MAIN SECTION: TABS ------------------
    tab1, tab2, tab3 = st.tabs(["🌐 Living Brain Graph", "🔍 Ask Your Brain (RAG)", "📚 Browse Wiki Notes"])
    
    with tab1:
        st.markdown("### Interactive Knowledge Graph")
        st.caption("Hover over nodes to see summaries. Drag to move, pinch/scroll to zoom.")
        
        # Load or generate graph
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
                
                # Write HTML to static folder to serve via iframe (avoids deprecation warnings)
                graph_html = get_graph_html(graph_data)
                static_dir = os.path.join(base_dir, 'static')
                os.makedirs(static_dir, exist_ok=True)
                with open(os.path.join(static_dir, 'graph_viewer.html'), 'w', encoding='utf-8') as sf:
                    sf.write(graph_html)
                
                st.iframe(src="static/graph_viewer.html", height=580)
                
                # Legend
                col1, col2, col3, col4 = st.columns(4)
                col1.markdown("🔵 **Projects** (Goal-oriented)")
                col2.markdown("🟢 **Areas** (Ongoing Standards)")
                col3.markdown("🟡 **Resources** (Interests & Tools)")
                col4.markdown("⚫ **Archives** (Inactive)")
            except Exception as e:
                st.error(f"Error displaying graph: {e}")
                
    with tab2:
        st.markdown("### Ask your SecondSelf anything")
        st.caption("Natural language search synthesizing answers exclusively from your captured documents.")
        
        query = st.text_input("Ask a question about your knowledge base:", placeholder="What did I note down about visual analytics libraries?", key="query_input_widget")
        
        # Horizontal columns for query actions (opposite sides of page)
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
            st.markdown("#### Response:")
            st.write(st.session_state["rag_answer"])
            
            sources = st.session_state.get("rag_sources", [])
            if sources:
                st.markdown("#### Retrieved Sources:")
                cols = st.columns(len(sources))
                for idx, src in enumerate(sources):
                    with cols[idx]:
                        card_style = f"""
                        <div style="border:1px solid #ddd; padding: 12px; border-radius: 8px; background-color: #fcfcfc;">
                            <h5 style="margin:0; color:#2c3e50;">{src['title']}</h5>
                            <span style="font-size: 10px; color:#1e90ff; font-weight:bold;">{src['category']}</span><br/>
                            <span style="font-size: 11px; color:#555;">Relevancy: {src['score']:.2f}</span>
                        </div>
                        """
                        st.markdown(card_style, unsafe_allow_html=True)
                
    with tab3:
        st.markdown("### Browse Wiki Knowledge Base")
        if not wiki_notes:
            st.info("Knowledge base is empty. Capture notes to populate.")
        else:
            # Group notes by Category
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

if __name__ == "__main__":
    main()
