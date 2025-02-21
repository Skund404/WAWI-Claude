import os
import ast
import json
from typing import Dict, List
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class FunctionInfo:
    name: str
    docstring: str
    args: List[str]

@dataclass
class ClassInfo:
    name: str
    docstring: str
    methods: List[FunctionInfo]
    base_classes: List[str]

@dataclass
class FileInfo:
    path: str
    imports: List[str]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    global_variables: List[str]

class ProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.files_info: Dict[str, FileInfo] = {}

    def analyze_project(self) -> Dict:
        for file_path in self.project_path.rglob("*.py"):
            if "__pycache__" not in str(file_path):
                try:
                    self.analyze_file(file_path)
                except Exception as e:
                    print(f"Warning: Could not analyze {file_path}: {str(e)}")
        return self.generate_summary()

    def analyze_file(self, file_path: Path) -> None:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {str(e)}")
            return

        imports = []
        classes = []
        functions = []
        global_vars = []

        # Analyze module level nodes
        for node in tree.body:
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for name in node.names:
                    imports.append(f"{module}.{name.name}")
            elif isinstance(node, ast.ClassDef):
                classes.append(self._extract_class_info(node))
            elif isinstance(node, ast.FunctionDef):
                functions.append(self._extract_function_info(node))
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        global_vars.append(target.id)

        relative_path = str(file_path.relative_to(self.project_path))
        self.files_info[relative_path] = FileInfo(
            path=relative_path,
            imports=imports,
            classes=classes,
            functions=functions,
            global_variables=global_vars
        )

    def _extract_function_info(self, node: ast.FunctionDef) -> FunctionInfo:
        docstring = ast.get_docstring(node) or ""
        args = [arg.arg for arg in node.args.args]
        return FunctionInfo(
            name=node.name,
            docstring=docstring,
            args=args
        )

    def _extract_class_info(self, node: ast.ClassDef) -> ClassInfo:
        docstring = ast.get_docstring(node) or ""
        methods = []
        base_classes = []
        
        # Extract base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                try:
                    base_classes.append(f"{base.value.id}.{base.attr}")
                except AttributeError:
                    base_classes.append(base.attr)

        # Extract methods
        for body_node in node.body:
            if isinstance(body_node, ast.FunctionDef):
                methods.append(self._extract_function_info(body_node))

        return ClassInfo(
            name=node.name,
            docstring=docstring,
            methods=methods,
            base_classes=base_classes
        )

    def generate_summary(self) -> Dict:
        return {
            "project_name": self.project_path.name,
            "total_files": len(self.files_info),
            "files": {path: asdict(info) for path, info in self.files_info.items()}
        }

def format_for_chat(summary: Dict) -> str:
    output = [f"# Project Analysis: {summary['project_name']}"]
    output.append(f"Total Python files: {summary['total_files']}\n")
    
    for file_path, info in summary['files'].items():
        output.append(f"## {file_path}")
        
        if info['imports']:
            output.append("\n### Imports:")
            for imp in info['imports']:
                output.append(f"- {imp}")
        
        if info['classes']:
            output.append("\n### Classes:")
            for cls in info['classes']:
                output.append(f"\n#### {cls['name']}")
                if cls['base_classes']:
                    output.append(f"Inherits from: {', '.join(cls['base_classes'])}")
                if cls['docstring']:
                    output.append(f"```\n{cls['docstring']}\n```")
                
                if cls['methods']:
                    output.append("\nMethods:")
                    for method in cls['methods']:
                        output.append(f"- {method['name']}({', '.join(method['args'])})")
                        if method['docstring']:
                            output.append(f"  ```\n  {method['docstring']}\n  ```")
        
        if info['functions']:
            output.append("\n### Functions:")
            for func in info['functions']:
                output.append(f"\n#### {func['name']}({', '.join(func['args'])})")
                if func['docstring']:
                    output.append(f"```\n{func['docstring']}\n```")
        
        if info['global_variables']:
            output.append("\n### Global Variables:")
            for var in info['global_variables']:
                output.append(f"- {var}")
        
        output.append("\n---\n")
    
    return "\n".join(output)

def analyze_project(project_path: str) -> None:
    analyzer = ProjectAnalyzer(project_path)
    summary = analyzer.analyze_project()
    
    # Generate both markdown and plain text outputs
    markdown_output = format_for_chat(summary)
    
    # Save markdown output
    with open("project_summary.md", 'w', encoding='utf-8') as f:
        f.write(markdown_output)
    
    # Save raw JSON data
    with open("project_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(markdown_output)
    print("\nAnalysis has been saved to project_summary.md and project_summary.json")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        analyze_project(project_path)
    else:
        print("Please provide the project path as an argument")
