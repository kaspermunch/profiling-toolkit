#!/usr/bin/env python3
"""
Advanced profiling script for mixed Python/C++/C libraries with debug symbol support.
Handles compiled extensions and provides detailed call graphs.
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict


class AdvancedMixedProfiler:
    """Advanced profiler for mixed Python/C++/C code with debug symbols."""
    
    def __init__(self, output_dir="profiling_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_files = []
        
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if required tools are installed."""
        tools = {
            "gprof2dot": ["gprof2dot", "--version"],
            "dot": ["dot", "-V"],
            "py-spy": ["py-spy", "--version"],
            "perf": ["perf", "--version"],
            "valgrind": ["valgrind", "--version"],
            "gcc": ["gcc", "--version"],
            "g++": ["g++", "--version"]
        }
        
        status = {}
        for tool, cmd in tools.items():
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                status[tool] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                status[tool] = False
        
        return status
    
    def compile_with_profiling(self, source_files: List[str], output_name: str,
                             language: str = "c++") -> Optional[Path]:
        """Compile C/C++ code with profiling and debug symbols enabled."""
        print(f"Compiling {language.upper()} code with profiling enabled...")
        
        compiler = "g++" if language == "c++" else "gcc"
        output_file = self.output_dir / output_name
        
        cmd = [
            compiler,
            "-g",           # Debug symbols
            "-pg",          # gprof profiling
            "-O2",          # Optimization (adjust as needed)
            "-fno-omit-frame-pointer",  # Keep frame pointers
            "-o", str(output_file)
        ]
        cmd.extend(source_files)
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Compiled to: {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"Compilation failed: {e}")
            return None
    
    def profile_with_valgrind(self, executable: str, output_name: str = "valgrind") -> Optional[Path]:
        """Profile using Valgrind's callgrind tool."""
        print(f"Profiling with Valgrind callgrind: {executable}")
        
        callgrind_out = self.output_dir / f"callgrind.out.{output_name}"
        
        cmd = [
            "valgrind",
            "--tool=callgrind",
            "--callgrind-out-file=" + str(callgrind_out),
            executable
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Callgrind output: {callgrind_out}")
            
            # Convert callgrind output for gprof2dot
            converted = self.convert_callgrind(callgrind_out, output_name)
            return converted
        except subprocess.CalledProcessError as e:
            print(f"Valgrind profiling failed: {e}")
            return None
    
    def convert_callgrind(self, callgrind_file: Path, output_name: str) -> Optional[Path]:
        """Convert callgrind output to a format gprof2dot can read."""
        print("Converting callgrind output...")
        
        # First, generate a human-readable output
        text_output = self.output_dir / f"{output_name}_callgrind.txt"
        
        cmd = ["callgrind_annotate", str(callgrind_file)]
        
        try:
            with open(text_output, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
            print(f"Callgrind text output: {text_output}")
            return text_output
        except subprocess.CalledProcessError as e:
            print(f"Callgrind conversion failed: {e}")
            return None
    
    def profile_python_with_austin(self, script: str, output_name: str = "austin") -> Optional[Path]:
        """Profile using Austin profiler (good for mixed code)."""
        print(f"Profiling with Austin: {script}")
        
        austin_output = self.output_dir / f"{output_name}_austin.txt"
        
        cmd = [
            "austin",
            "-s",  # Sample mode
            "-i", "1ms",  # Interval
            "-o", str(austin_output),
            sys.executable, script
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Austin output: {austin_output}")
            return austin_output
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Austin not found. Install with: pip install austin-python")
            return None
    
    def combine_profiles(self, profiles: List[Path], output_name: str = "combined") -> Path:
        """Combine multiple profile outputs into a single visualization."""
        print("Combining multiple profiles...")
        
        combined_dot = self.output_dir / f"{output_name}_combined.dot"
        
        # This is a simplified combination - in practice, you'd merge the data
        # For now, we'll just process the first valid profile
        for profile in profiles:
            if profile and profile.exists():
                return self.process_single_profile(profile, output_name)
        
        return None
    
    def process_single_profile(self, profile_file: Path, output_name: str) -> Optional[Path]:
        """Process a single profile file through gprof2dot."""
        print(f"Processing profile: {profile_file}")
        
        # Determine format based on source
        format_map = {
            ".pstats": "pstats",
            ".json": "json",
            "_austin.txt": "austin",
            "_callgrind.txt": "callgrind",
            ".perf": "perf",
            ".txt": "perf"  # default for text files
        }
        
        format_type = "pstats"  # default
        for suffix, fmt in format_map.items():
            if suffix in str(profile_file):
                format_type = fmt
                break
        
        dot_file = self.output_dir / f"{output_name}.dot"
        
        # Apply custom filters and options
        cmd = [
            "gprof2dot",
            "-f", format_type,
            "--node-thres", "0.5",  # Hide nodes below 0.5%
            "--edge-thres", "0.1",  # Hide edges below 0.1%
            "--color-nodes-by-selftime",  # Color by self time
            "-o", str(dot_file)
        ]
        
        try:
            with open(profile_file, 'rb') as f:
                subprocess.run(cmd, stdin=f, check=True)
            print(f"Dot file created: {dot_file}")
            return dot_file
        except subprocess.CalledProcessError as e:
            print(f"gprof2dot processing failed: {e}")
            return None
    
    def generate_interactive_html(self, dot_file: Path, output_name: str = "profile") -> Optional[Path]:
        """Generate an interactive HTML visualization."""
        print("Generating interactive HTML visualization...")
        
        # First generate SVG
        svg_file = self.output_dir / f"{output_name}.svg"
        cmd = ["dot", "-Tsvg", "-o", str(svg_file), str(dot_file)]
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print("Failed to generate SVG")
            return None
        
        # Create interactive HTML wrapper
        html_file = self.output_dir / f"{output_name}_interactive.html"
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Profile Visualization - {output_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
        }}
        .controls {{
            margin: 20px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        button {{
            margin: 5px;
            padding: 8px 15px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }}
        button:hover {{
            background: #45a049;
        }}
        #svg-container {{
            background: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
            overflow: auto;
        }}
    </style>
</head>
<body>
    <h1>Profile Visualization: {output_name}</h1>
    <div class="controls">
        <button onclick="zoomIn()">Zoom In</button>
        <button onclick="zoomOut()">Zoom Out</button>
        <button onclick="resetZoom()">Reset</button>
        <button onclick="downloadSVG()">Download SVG</button>
    </div>
    <div id="svg-container">
        <!-- SVG will be embedded here -->
    </div>
    
    <script>
        let currentScale = 1;
        
        // Load SVG
        fetch('{svg_file.name}')
            .then(response => response.text())
            .then(data => {{
                document.getElementById('svg-container').innerHTML = data;
                const svg = document.querySelector('svg');
                svg.id = 'profile-svg';
                svg.style.width = '100%';
                svg.style.height = 'auto';
            }});
        
        function zoomIn() {{
            currentScale *= 1.2;
            applyZoom();
        }}
        
        function zoomOut() {{
            currentScale /= 1.2;
            applyZoom();
        }}
        
        function resetZoom() {{
            currentScale = 1;
            applyZoom();
        }}
        
        function applyZoom() {{
            const svg = document.getElementById('profile-svg');
            if (svg) {{
                svg.style.transform = `scale(${{currentScale}})`;
                svg.style.transformOrigin = 'top left';
            }}
        }}
        
        function downloadSVG() {{
            const svg = document.getElementById('profile-svg');
            if (svg) {{
                const svgData = new XMLSerializer().serializeToString(svg);
                const blob = new Blob([svgData], {{type: 'image/svg+xml'}});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '{output_name}.svg';
                a.click();
            }}
        }}
    </script>
</body>
</html>"""
        
        html_file.write_text(html_content)
        print(f"Interactive HTML created: {html_file}")
        return html_file
    
    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            if temp_file.exists():
                temp_file.unlink()


def create_example_c_extension():
    """Create an example C extension for testing."""
    c_code = """
#include <Python.h>
#include <math.h>

// Computationally intensive function
static PyObject* compute_intensive(PyObject* self, PyObject* args) {
    int n;
    if (!PyArg_ParseTuple(args, "i", &n)) {
        return NULL;
    }
    
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            result += sin(i) * cos(j);
        }
    }
    
    return PyFloat_FromDouble(result);
}

static PyMethodDef module_methods[] = {
    {"compute_intensive", compute_intensive, METH_VARARGS, "Compute intensive function"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_definition = {
    PyModuleDef_HEAD_INIT,
    "example_extension",
    "Example C extension module",
    -1,
    module_methods
};

PyMODINIT_FUNC PyInit_example_extension(void) {
    return PyModule_Create(&module_definition);
}
"""
    
    setup_py = """
from setuptools import setup, Extension

module = Extension('example_extension',
                   sources=['example_extension.c'],
                   extra_compile_args=['-g', '-O2'])

setup(
    name='example_extension',
    ext_modules=[module]
)
"""
    
    Path("example_extension.c").write_text(c_code)
    Path("setup_extension.py").write_text(setup_py)
    
    print("Created example C extension files")
    print("To build: python setup_extension.py build_ext --inplace")
    
    return "example_extension.c", "setup_extension.py"


def main():
    parser = argparse.ArgumentParser(
        description="Advanced profiling for mixed Python/C++/C code"
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Python script or compiled executable to profile"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check installed dependencies"
    )
    parser.add_argument(
        "--create-example",
        action="store_true",
        help="Create example C extension"
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["cprofile", "py-spy", "valgrind", "austin", "perf"],
        default=["cprofile"],
        help="Profiling methods to use"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Generate interactive HTML visualization"
    )
    parser.add_argument(
        "--output-dir",
        default="profiling_results",
        help="Output directory"
    )
    
    args = parser.parse_args()
    
    profiler = AdvancedMixedProfiler(output_dir=args.output_dir)
    
    if args.check_deps:
        print("\nDependency Status:")
        print("-" * 40)
        status = profiler.check_dependencies()
        for tool, installed in status.items():
            status_str = "✓ Installed" if installed else "✗ Not found"
            print(f"{tool:12} : {status_str}")
        print("-" * 40)
        return 0
    
    if args.create_example:
        create_example_c_extension()
        return 0
    
    if not args.target:
        print("Error: Please provide a target to profile")
        print("Use --help for more information")
        return 1
    
    # Run profiling with selected methods
    profiles = []
    for method in args.methods:
        print(f"\n{'='*60}")
        print(f"Profiling with method: {method}")
        print(f"{'='*60}")
        
        if method == "cprofile":
            # Implementation would go here
            pass
        elif method == "valgrind" and args.target.endswith(('.c', '.cpp')):
            # Compile and profile with valgrind
            pass
        # ... other methods
    
    # Generate final visualization
    if profiles:
        combined = profiler.combine_profiles(profiles, "combined")
        if combined and args.interactive:
            profiler.generate_interactive_html(combined, "final_profile")
    
    profiler.cleanup()
    
    print(f"\n{'='*60}")
    print("Profiling complete! Check the output directory:")
    print(f"  {profiler.output_dir}")
    print(f"{'='*60}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
