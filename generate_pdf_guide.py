#!/usr/bin/env python3
"""
Convert Training Implementation Guide to a printable HTML
User can open in browser and print to PDF (Ctrl+P)
"""

import markdown2
from pathlib import Path

def create_html():
    """Convert markdown to styled HTML for printing"""

    # Read the markdown file
    md_file = Path("TRAINING_IMPLEMENTATION_GUIDE.md")
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert markdown to HTML
    html_content = markdown2.markdown(
        md_content,
        extras=[
            "fenced-code-blocks",
            "tables",
            "header-ids",
            "toc",
            "code-friendly"
        ]
    )

    # Create styled HTML document optimized for printing to PDF
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Training Implementation Guide - Smart ML Assistant</title>
        <style>
            /* Print-optimized styles */
            @media print {{
                @page {{
                    size: A4;
                    margin: 2cm;
                }}

                body {{
                    font-size: 11pt;
                }}

                h1 {{
                    page-break-before: always;
                }}

                h1:first-of-type {{
                    page-break-before: avoid;
                }}

                h2, h3, h4 {{
                    page-break-after: avoid;
                }}

                pre, table, blockquote {{
                    page-break-inside: avoid;
                }}

                a {{
                    color: #3498db;
                    text-decoration: none;
                }}

                a[href]:after {{
                    content: "" !important;
                }}
            }}

            /* Screen and print styles */
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.7;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #fff;
            }}

            h1 {{
                color: #2c3e50;
                border-bottom: 4px solid #3498db;
                padding-bottom: 12px;
                margin-top: 40px;
                margin-bottom: 20px;
                font-size: 2.2em;
            }}

            h1:first-of-type {{
                text-align: center;
                font-size: 2.8em;
                border: none;
                color: #3498db;
                margin-top: 20px;
                margin-bottom: 10px;
            }}

            h2 {{
                color: #34495e;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 10px;
                margin-top: 35px;
                margin-bottom: 18px;
                font-size: 1.8em;
            }}

            h3 {{
                color: #2c3e50;
                margin-top: 25px;
                margin-bottom: 15px;
                font-size: 1.4em;
            }}

            h4 {{
                color: #555;
                margin-top: 20px;
                margin-bottom: 12px;
                font-size: 1.2em;
            }}

            p {{
                margin: 15px 0;
                text-align: justify;
            }}

            code {{
                background-color: #f4f4f4;
                padding: 3px 7px;
                border-radius: 4px;
                font-family: 'Courier New', Courier, monospace;
                font-size: 0.92em;
                color: #c7254e;
                border: 1px solid #e1e1e1;
            }}

            pre {{
                background-color: #2d2d2d;
                color: #f8f8f2;
                padding: 18px;
                border-radius: 6px;
                overflow-x: auto;
                font-family: 'Courier New', Courier, monospace;
                font-size: 0.88em;
                line-height: 1.5;
                border: 1px solid #444;
                margin: 20px 0;
            }}

            pre code {{
                background-color: transparent;
                color: #f8f8f2;
                padding: 0;
                border: none;
            }}

            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 25px 0;
                font-size: 0.95em;
            }}

            table th {{
                background-color: #3498db;
                color: white;
                padding: 13px;
                text-align: left;
                font-weight: 600;
            }}

            table td {{
                padding: 12px;
                border: 1px solid #ddd;
            }}

            table tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}

            table tr:hover {{
                background-color: #f0f0f0;
            }}

            blockquote {{
                border-left: 5px solid #3498db;
                padding-left: 22px;
                margin: 25px 0;
                color: #555;
                background-color: #f8f9fa;
                padding: 18px 22px;
                border-radius: 5px;
                font-style: italic;
            }}

            ul, ol {{
                margin: 18px 0;
                padding-left: 35px;
            }}

            li {{
                margin: 10px 0;
            }}

            a {{
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}

            a:hover {{
                text-decoration: underline;
                color: #2980b9;
            }}

            hr {{
                border: none;
                border-top: 2px solid #ddd;
                margin: 40px 0;
            }}

            /* Flow diagram boxes */
            pre:contains("┌"),
            pre:contains("│"),
            pre:contains("└") {{
                background-color: #f8f9fa;
                color: #2c3e50;
                border: 2px solid #3498db;
                font-family: 'Courier New', monospace;
            }}

            /* Print instructions banner */
            .print-instructions {{
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
                text-align: center;
                font-size: 1.1em;
            }}

            @media print {{
                .print-instructions {{
                    display: none;
                }}
            }}

            .print-button {{
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 30px;
                font-size: 1em;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 15px;
                font-weight: 600;
            }}

            .print-button:hover {{
                background-color: #2980b9;
            }}

            /* Subtitle */
            .subtitle {{
                text-align: center;
                color: #666;
                font-size: 1.2em;
                margin-bottom: 40px;
            }}

            /* Status badges */
            .badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 0.9em;
                font-weight: 600;
                margin: 0 5px;
            }}

            .badge-success {{
                background-color: #27ae60;
                color: white;
            }}

            /* Table of contents styling */
            nav {{
                background-color: #f8f9fa;
                padding: 25px;
                border-radius: 8px;
                margin: 35px 0;
                border: 1px solid #ddd;
            }}

            nav h2 {{
                margin-top: 0;
                border: none;
            }}

            nav ul {{
                list-style-type: none;
                padding-left: 20px;
            }}

            nav li {{
                margin: 12px 0;
            }}

            nav a {{
                color: #2c3e50;
                font-weight: 500;
            }}

            nav a:hover {{
                color: #3498db;
            }}
        </style>
        <script>
            function printToPDF() {{
                window.print();
            }}
        </script>
    </head>
    <body>
        <div class="print-instructions">
            <strong>📄 To save as PDF:</strong><br>
            Click the button below or press <kbd>Ctrl+P</kbd> (Windows) or <kbd>Cmd+P</kbd> (Mac),<br>
            then select "Save as PDF" as the printer destination.
            <br>
            <button class="print-button" onclick="printToPDF()">🖨️ Print to PDF</button>
        </div>

        {html_content}

        <div class="print-instructions" style="margin-top: 50px;">
            <strong>End of Document</strong><br>
            <small>Generated from TRAINING_IMPLEMENTATION_GUIDE.md</small>
        </div>
    </body>
    </html>
    """

    # Save HTML file
    output_file = Path("TRAINING_IMPLEMENTATION_GUIDE.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(styled_html)

    print("✅ HTML file created successfully!")
    print(f"📄 File: {output_file.absolute()}")
    print(f"📊 Size: {output_file.stat().st_size / 1024:.2f} KB")
    print()
    print("📋 To create PDF:")
    print("   1. Open the HTML file in your browser")
    print("   2. Press Ctrl+P (Windows) or Cmd+P (Mac)")
    print("   3. Select 'Save as PDF' as destination")
    print("   4. Click 'Save'")
    print()
    print(f"🌐 Opening in browser now...")

    return output_file

if __name__ == "__main__":
    try:
        html_file = create_html()

        # Try to open in default browser
        import webbrowser
        webbrowser.open(str(html_file.absolute()))

        print(f"\n🎉 Success! Browser opened with the guide.")
        print(f"   If it didn't open, manually open: {html_file.absolute()}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
