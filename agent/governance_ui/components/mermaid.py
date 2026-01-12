"""
Mermaid Diagram Rendering Component for Trame.

Per RULE-039: Context Compression Standard (Mermaid for diagrams).
Per GAP-UI-xxx: Impact view diagram rendering.

This component renders mermaid diagrams client-side using mermaid.js.
"""

from trame.widgets import html


# Mermaid.js CDN URL
MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"


def inject_mermaid_script() -> None:
    """
    Inject mermaid.js script into the page.

    Call this once in the layout (e.g., in build_layout).
    Uses esm.min.js for module support.
    """
    # Script to load mermaid and initialize
    html.Script(
        f"""
        // Load mermaid if not already loaded
        if (typeof mermaid === 'undefined') {{
            const script = document.createElement('script');
            script.src = '{MERMAID_CDN}';
            script.onload = function() {{
                mermaid.initialize({{
                    startOnLoad: false,
                    theme: 'default',
                    securityLevel: 'loose',
                    flowchart: {{
                        useMaxWidth: true,
                        htmlLabels: true,
                        curve: 'basis'
                    }}
                }});
                console.log('Mermaid.js loaded and initialized');
                // Render any existing diagrams
                window.renderMermaidDiagrams();
            }};
            document.head.appendChild(script);
        }}

        // Global function to render mermaid diagrams
        window.renderMermaidDiagrams = async function() {{
            const elements = document.querySelectorAll('.mermaid-source');
            for (const el of elements) {{
                const source = el.textContent.trim();
                if (!source || source === '') continue;

                const targetId = el.getAttribute('data-target');
                const target = document.getElementById(targetId);
                if (!target) continue;

                try {{
                    const {{ svg }} = await mermaid.render(targetId + '-svg', source);
                    target.innerHTML = svg;
                    target.classList.add('mermaid-rendered');
                }} catch (e) {{
                    console.error('Mermaid render error:', e);
                    target.innerHTML = '<pre style="color: red;">Error rendering diagram</pre>';
                }}
            }}
        }};
        """
    )


def build_mermaid_diagram(diagram_id: str, source_var: str) -> None:
    """
    Build a mermaid diagram component.

    Args:
        diagram_id: Unique ID for the diagram container
        source_var: Vue reactive variable containing mermaid source (e.g., "mermaid_diagram")

    Usage:
        build_mermaid_diagram("impact-graph", "mermaid_diagram")
    """
    # Hidden source element (Vue will update this)
    html.Div(
        f"{{{{ {source_var} }}}}",
        classes="mermaid-source",
        style="display: none;",
        **{
            "data-target": diagram_id,
            # Trigger re-render when source changes
            "v-effect": "renderMermaidDiagrams()",
        }
    )

    # Container where SVG will be rendered
    html.Div(
        id=diagram_id,
        classes="mermaid-container",
        style=(
            "background: #f8f9fa; "
            "padding: 16px; "
            "border-radius: 8px; "
            "min-height: 200px; "
            "display: flex; "
            "align-items: center; "
            "justify-content: center; "
            "overflow: auto;"
        ),
        __properties=["data-testid"],
        **{"data-testid": f"mermaid-{diagram_id}"}
    )


def build_mermaid_with_fallback(diagram_id: str, source_var: str) -> None:
    """
    Build mermaid diagram with text fallback for accessibility.

    Args:
        diagram_id: Unique ID for the diagram
        source_var: Vue variable with mermaid source
    """
    with html.Div(classes="mermaid-wrapper"):
        # Mermaid diagram (visual)
        build_mermaid_diagram(diagram_id, source_var)

        # Collapsible source view (for copy/debug)
        with html.Details(classes="mt-2"):
            html.Summary(
                "View Source",
                style="cursor: pointer; color: #666; font-size: 12px;"
            )
            html.Pre(
                f"{{{{ {source_var} }}}}",
                style=(
                    "background: #272822; "
                    "color: #f8f8f2; "
                    "padding: 12px; "
                    "border-radius: 4px; "
                    "font-size: 11px; "
                    "overflow-x: auto; "
                    "max-height: 200px;"
                )
            )
