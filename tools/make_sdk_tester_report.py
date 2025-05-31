import json
import sys


def generate_html(call_data, output_file="coverage.html"):
    functions = list(call_data.keys())
    called_functions = [f for f, count in call_data.items() if count > 0]
    uncalled_functions = [f for f in functions if f not in called_functions]

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Coverage Overview</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 500px; margin: auto; background-color: black; color: white; }}
            .progress-container {{ background: #444; border-radius: 5px; overflow: hidden; height: 20px; margin-bottom: 10px; position: relative; }}
            .progress-green {{ height: 100%; background: #4caf50; position: absolute; left: 0; top: 0; width: 0%; }}
            .progress-blue {{ height: 100%; background: #2196F3; position: absolute; left: 0; top: 0; width: 0%; }}
            .todo-item {{ display: flex; align-items: center; margin: 5px 0; }}
            .completed {{ text-decoration: line-through; color: gray; }}
            input[type="checkbox"] {{ margin-right: 10px; }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"></script>
    </head>
    <body>
        <h2>Coverage Overview</h2>
        <div class="progress-container">
            <div class="progress-green" id="progress-green"></div>
            <div class="progress-blue" id="progress-blue"></div>
        </div>
        <div id="todo-list"></div>

        <script>
            const functions = {json.dumps(uncalled_functions)};
            const calledFunctions = {json.dumps(list(called_functions))};
            const todoList = document.getElementById("todo-list");
            
            function generateColor(module) {{
                const hash = module.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                const hue = (hash * 137) % 360; // Use a larger multiplier to spread out the hues
                const color = chroma.hsl(hue, 0.7, 0.5); // Fixed saturation and lightness for better contrast
                return color.hex();
            }}
            
            function formatFunctionName(func) {{
                const parts = func.split('_').filter(Boolean);
                const module = parts[1];
                const color = generateColor(module);
                const formatted = parts.slice(2).join('_');
                return `<span style="color: ${{color}};">${{module}}</span> → ${{formatted}}`;
            }}
            

            function updateProgress() {{
                const total = functions.length + calledFunctions.length;
                const called = calledFunctions.length;
                const checked = document.querySelectorAll("input[type='checkbox']:checked").length;

                const greenWidth = (called / total * 100) + "%";
                const blueWidth = (checked / total * 100) + "%";
            
                document.getElementById("progress-green").style.width = greenWidth;
                document.getElementById("progress-blue").style.width = blueWidth;
                document.getElementById("progress-blue").style.left = greenWidth;
            }}

            function loadTodos() {{
                functions.forEach(func => {{
                    const item = document.createElement("div");
                    item.className = "todo-item";

                    const checkbox = document.createElement("input");
                    checkbox.type = "checkbox";
                    checkbox.id = func;
                    checkbox.checked = localStorage.getItem(func) === "true";

                    checkbox.addEventListener("change", () => {{
                        localStorage.setItem(func, checkbox.checked);
                        updateProgress();
                    }});

                    const label = document.createElement("label");
                    label.htmlFor = func;
                    label.innerHTML = formatFunctionName(func);

                    item.appendChild(checkbox);
                    item.appendChild(label);
                    todoList.appendChild(item);
                }});

                calledFunctions.forEach(func => {{
                    const item = document.createElement("div");
                    item.className = "todo-item completed";
                    item.textContent = func;
                    todoList.appendChild(item);
                }});

                updateProgress();
            }}

            loadTodos();
        </script>
    </body>
    </html>
    """

    with open(output_file, "w", encoding='utf-8') as f:
        f.write(html_content)


# Example usage
with open('../content/.temporary/extension_calls.json', 'r') as f:
    call_data = json.load(f)[sys.argv[1] if len(sys.argv) > 1 else input("Enter the SDK tester extension name: ")]

generate_html({key: call_data[key] for key in sorted(call_data, key=lambda x: x[1:] if x[0] == '_' else x)})
