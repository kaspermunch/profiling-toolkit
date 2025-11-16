#!/usr/bin/env python3
"""
Script to profile and visualize a mixed Python/C++/C library using gprof2dot.
Supports multiple profiling methods for different code types.
"""

import os
import sys
import argparse
import subprocess
import tempfile
import platform
from pathlib import Path


class MixedCodeProfiler:
    """Handle profiling of mixed Python/C++/C code and visualization."""
    
    def __init__(self, output_dir="profiling_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def profile_python(self, script_path, args="", output_name="python_profile"):
        """Profile Python code using cProfile."""
        print(f"Profiling Python code: {script_path}")
        
        profile_file = self.output_dir / f"{output_name}.pstats"
        
        # Run Python profiling
        cmd = [
            sys.executable, "-m", "cProfile",
            "-o", str(profile_file),
            script_path
        ]
        if args:
            cmd.extend(args.split())
            
        try:
            subprocess.run(cmd, check=True)
            print(f"Python profile saved to: {profile_file}")
            return profile_file
        except subprocess.CalledProcessError as e:
            print(f"Error profiling Python code: {e}")
            return None
    
    def profile_python_with_pyinstrument(self, script_path, args="", output_name="python_profile"):
        """Profile Python code using pyinstrument (better for mixed code)."""
        print(f"Profiling with pyinstrument: {script_path}")
        
        profile_file = self.output_dir / f"{output_name}_pyinstrument.json"
        
        cmd = [
            sys.executable, "-m", "pyinstrument",
            "--renderer", "json",
            "-o", str(profile_file),
            script_path
        ]
        if args:
            cmd.extend(args.split())
            
        try:
            subprocess.run(cmd, check=True)
            print(f"Pyinstrument profile saved to: {profile_file}")
            return profile_file
        except subprocess.CalledProcessError as e:
            print(f"Error with pyinstrument: {e}")
            return None
    
    def profile_c_extension(self, python_script, output_name="c_profile"):
        """Profile C/C++ extensions using py-spy."""
        print(f"Profiling C/C++ extensions with py-spy")

        profile_file = self.output_dir / f"{output_name}_flame.svg"

        # Use py-spy for native code profiling
        cmd = [
            "sudo", "py-spy", "record",
            "--output", str(profile_file),
            "--format", "flamegraph",
            "--", sys.executable, python_script
        ]

        # Only add --native on Linux where it's supported
        if platform.system() == "Linux":
            cmd.insert(3, "--native")  # Insert after "record"
            print("Note: Including native C/C++ frames (--native)")
        else:
            print(f"Note: --native flag not supported on {platform.system()}, profiling Python frames only")
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Flame graph saved to: {profile_file}")
            return profile_file
        except subprocess.CalledProcessError as e:
            print(f"Error with py-spy: {e}")
            print("Make sure py-spy is installed: pip install py-spy")
            return None
    
    def profile_with_perf(self, python_script, output_name="perf_profile"):
        """Profile using Linux perf (requires perf installed)."""
        print(f"Profiling with perf: {python_script}")
        
        perf_data = self.output_dir / f"{output_name}.perf"
        
        # Record with perf
        cmd = [
            "perf", "record",
            "-g",  # Call graph
            "--call-graph", "dwarf",
            "-o", str(perf_data),
            sys.executable, python_script
        ]
        
        try:
            subprocess.run(cmd, check=True)
            
            # Convert perf data to text format
            perf_script = self.output_dir / f"{output_name}_script.txt"
            with open(perf_script, 'w') as f:
                subprocess.run(
                    ["perf", "script", "-i", str(perf_data)],
                    stdout=f, check=True
                )
            
            print(f"Perf data saved to: {perf_data}")
            return perf_script
        except subprocess.CalledProcessError as e:
            print(f"Error with perf: {e}")
            print("Make sure perf is installed and you have appropriate permissions")
            return None
    
    def convert_to_dot(self, profile_file, output_name="profile", format_type="auto"):
        """Convert profile data to dot format using gprof2dot."""
        print(f"Converting to dot format: {profile_file}")
        
        dot_file = self.output_dir / f"{output_name}.dot"
        
        # Determine format based on file extension if auto
        if format_type == "auto":
            ext = profile_file.suffix.lower()
            if ext == ".pstats":
                format_type = "pstats"
            elif ext == ".json":
                format_type = "json"
            elif ext in [".txt", ".perf"]:
                format_type = "perf"
            else:
                format_type = "pstats"  # default
        
        cmd = [
            "gprof2dot",
            "-f", format_type,
            "-o", str(dot_file),
            str(profile_file)
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"Dot file created: {dot_file}")
            return dot_file
        except subprocess.CalledProcessError as e:
            print(f"Error with gprof2dot: {e}")
            print("Make sure gprof2dot is installed: pip install gprof2dot")
            return None
    
    def generate_graph(self, dot_file, output_format="svg", output_name="profile_graph"):
        """Generate visual graph from dot file using graphviz."""
        print(f"Generating {output_format} graph from: {dot_file}")
        
        output_file = self.output_dir / f"{output_name}.{output_format}"
        
        cmd = [
            "dot",
            f"-T{output_format}",
            "-o", str(output_file),
            str(dot_file)
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Graph generated: {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"Error with graphviz: {e}")
            print("Make sure graphviz is installed: apt-get install graphviz")
            return None
    
    def full_pipeline(self, script_path, method="cprofile", output_format="svg"):
        """Run the full profiling and visualization pipeline."""
        print(f"\n{'='*60}")
        print(f"Starting full profiling pipeline")
        print(f"Method: {method}")
        print(f"Script: {script_path}")
        print(f"{'='*60}\n")
        
        profile_file = None
        
        # Step 1: Profile based on method
        if method == "cprofile":
            profile_file = self.profile_python(script_path)
            format_type = "pstats"
        elif method == "pyinstrument":
            profile_file = self.profile_python_with_pyinstrument(script_path)
            format_type = "json"
        elif method == "py-spy":
            # py-spy generates SVG directly
            return self.profile_c_extension(script_path)
        elif method == "perf":
            profile_file = self.profile_with_perf(script_path)
            format_type = "perf"
        else:
            print(f"Unknown profiling method: {method}")
            return None
        
        if not profile_file or not profile_file.exists():
            print("Profiling failed")
            return None
        
        # Step 2: Convert to dot
        dot_file = self.convert_to_dot(profile_file, format_type=format_type)
        if not dot_file:
            return None
        
        # Step 3: Generate graph
        graph_file = self.generate_graph(dot_file, output_format=output_format)
        
        return graph_file


def create_test_script():
    """Create a test script that simulates mixed Python/C code."""
    test_script = """
import time
import numpy as np  # Uses C extensions
import json

def python_function(n):
    \"\"\"Pure Python function.\"\"\"
    result = 0
    for i in range(n):
        result += i ** 2
    return result

def numpy_function(size):
    \"\"\"Function using NumPy (C extension).\"\"\"
    arr = np.random.rand(size, size)
    return np.dot(arr, arr.T)

def json_function(data):
    \"\"\"Function using json (C extension).\"\"\"
    json_str = json.dumps(data)
    return json.loads(json_str)

def main():
    # Pure Python work
    for _ in range(100):
        python_function(1000)
    
    # NumPy work (C extension)
    for _ in range(10):
        numpy_function(100)
    
    # JSON work (C extension)
    data = {"key": list(range(1000))}
    for _ in range(100):
        json_function(data)

if __name__ == "__main__":
    main()
"""
    
    test_file = Path("test_mixed_code.py")
    test_file.write_text(test_script)
    print(f"Created test script: {test_file}")
    return test_file


def main():
    parser = argparse.ArgumentParser(
        description="Profile and visualize mixed Python/C++/C code with gprof2dot"
    )
    parser.add_argument(
        "script",
        nargs="?",
        help="Python script to profile (creates test script if not provided)"
    )
    parser.add_argument(
        "--method",
        choices=["cprofile", "pyinstrument", "py-spy", "perf"],
        default="cprofile",
        help="Profiling method to use"
    )
    parser.add_argument(
        "--format",
        choices=["svg", "png", "pdf", "ps"],
        default="svg",
        help="Output graph format"
    )
    parser.add_argument(
        "--output-dir",
        default="profiling_results",
        help="Directory for output files"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Show installation commands for dependencies"
    )
    
    args = parser.parse_args()
    
    if args.install_deps:
        print("\nInstallation commands for dependencies:")
        print("-" * 40)
        print("# Python packages:")
        print("pip install gprof2dot py-spy pyinstrument")
        print("\n# System packages (Ubuntu/Debian):")
        print("sudo apt-get install graphviz linux-tools-common linux-tools-generic")
        print("\n# System packages (macOS):")
        print("brew install graphviz")
        print("-" * 40)
        return
    
    # Create test script if none provided
    if not args.script:
        args.script = str(create_test_script())
        print(f"No script provided, using test script: {args.script}\n")
    
    # Verify script exists
    if not Path(args.script).exists():
        print(f"Error: Script '{args.script}' not found")
        return 1
    
    # Run profiling
    profiler = MixedCodeProfiler(output_dir=args.output_dir)
    result = profiler.full_pipeline(
        args.script,
        method=args.method,
        output_format=args.format
    )
    
    if result:
        print(f"\n{'='*60}")
        print(f"SUCCESS! Graph saved to: {result}")
        print(f"Open with: xdg-open {result}  # Linux")
        print(f"           open {result}       # macOS")
        print(f"{'='*60}")
    else:
        print("\nProfiling failed. Check the error messages above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
