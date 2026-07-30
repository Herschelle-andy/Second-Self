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

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir, wiki_dir = capture.setup_directories(base_dir)
    
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
        note_content = st.sidebar.text_area("Write down an idea or note", placeholder="E.g., Remind me to look at visual analytics tools for Python next Monday.", height=150, key="note_input_widget")
        if st.sidebar.button("Capture Note", use_container_width=True):
            if note_content.strip():
                note_id = capture.capture_note(raw_dir, note_content)
                # Clear the text area widget state
                st.session_state["note_input_widget"] = ""
                run_post_capture_pipeline(base_dir)
            else:
                st.sidebar.warning("Note content cannot be empty!")
                
    elif capture_type == "Link / Bookmark":
        link_url = st.sidebar.text_input("URL to scrape & capture", placeholder="https://github.com/trending", key="link_input_widget")
        if st.sidebar.button("Capture Link", use_container_width=True):
            if link_url.strip():
                note_id = capture.capture_link(raw_dir, link_url)
                # Clear the link input widget state
                st.session_state["link_input_widget"] = ""
                run_post_capture_pipeline(base_dir)
            else:
                st.sidebar.warning("Please provide a valid URL!")
                
    elif capture_type == "File Upload":
        uploaded_file = st.sidebar.file_uploader("Upload note, article, or PDF", type=["txt", "md", "json", "html", "pdf"], key="file_input_widget")
        if uploaded_file is not None:
            if st.sidebar.button("Capture Uploaded File", use_container_width=True):
                # Save uploaded file temporarily to project root so we can ingest it
                temp_path = os.path.join(base_dir, uploaded_file.name)
                try:
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    note_id = capture.capture_file(raw_dir, temp_path)
                    
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        
                    # Clear the file uploader widget state
                    st.session_state["file_input_widget"] = None
                    
                    run_post_capture_pipeline(base_dir)
                except Exception as e:
                    st.sidebar.error(f"Error handling file upload: {e}")
                    
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
        
        query = st.text_input("Ask a question about your knowledge base:", placeholder="What did I note down about visual analytics libraries?")
        
        if st.button("Query Brain", type="primary"):
            if query.strip():
                with st.spinner("Retrieving notes and synthesizing answer..."):
                    import numpy as np # Ensure numpy imported
                    answer, sources = ask.ask_brain(query, wiki_dir)
                    
                    st.markdown("#### Response:")
                    st.write(answer)
                    
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
            else:
                st.warning("Please enter a question to query!")
                
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
