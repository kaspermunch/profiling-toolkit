# Profiling Toolkit for Mixed Python/C++/C Libraries

A comprehensive toolkit for profiling and visualizing performance of Python libraries that contain Python, C++, and C code using `gprof2dot`.


  export TARGET=test_extension.py
  make profile

or

  make profile TARGET=test_extension.py

or

  python profile_mixed_library.py test_extension.py --method cprofile

To profile C/C++ extensions, you must be on Linux:

  make profile-native

---


## Features

- **Multiple profiling methods**: cProfile, py-spy, pyinstrument, perf, valgrind
- **Mixed code support**: Handles pure Python, C extensions, and compiled C/C++ code
- **Visual output**: Generates call graphs in SVG, PNG, PDF formats
- **Interactive visualizations**: HTML wrappers for exploring large graphs
- **Debug symbol support**: Properly handles compiled extensions with debug info

## Installation

### Quick Install

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or using make
make install
```

### System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get install graphviz linux-tools-common linux-tools-generic
# Optional: for C/C++ profiling
sudo apt-get install valgrind gcc g++ gdb
```

#### macOS
```bash
brew install graphviz
# For py-spy (requires sudo to profile)
sudo pip install py-spy
```

## Usage

### Basic Profiling

#### 1. Simple Python Script
```bash
# Using the main script
python profile_mixed_library.py your_script.py

# Using make
make profile TARGET=your_script.py
```

#### 2. With C Extensions (e.g., NumPy, SciPy)
```bash
# Use py-spy for native code visibility (requires sudo)
python profile_mixed_library.py your_script.py --method py-spy

# Or with make
make profile-native TARGET=your_script.py
```

#### 3. Test with Example
```bash
# Creates and profiles a test script
python profile_mixed_library.py

# Or
make test
```

### Advanced Options

#### Choose Profiling Method
```bash
# cProfile (default) - Python-level profiling
python profile_mixed_library.py script.py --method cprofile

# pyinstrument - Statistical profiler, good for mixed code
python profile_mixed_library.py script.py --method pyinstrument

# py-spy - Can see into native C/C++ code (requires sudo)
sudo python profile_mixed_library.py script.py --method py-spy

# perf - Linux perf tools (requires perf installed)
python profile_mixed_library.py script.py --method perf
```

#### Output Formats
```bash
# Generate different output formats
python profile_mixed_library.py script.py --format svg  # Default
python profile_mixed_library.py script.py --format png
python profile_mixed_library.py script.py --format pdf
```

#### Custom Output Directory
```bash
python profile_mixed_library.py script.py --output-dir my_profiles
```

### Real-World Examples

#### Example 1: Profile NumPy Operations
```python
# Create numpy_example.py
import numpy as np

def matrix_operations():
    for _ in range(100):
        a = np.random.rand(500, 500)
        b = np.random.rand(500, 500)
        c = np.dot(a, b)
        eigenvalues = np.linalg.eigvals(c)
    return eigenvalues

if __name__ == "__main__":
    matrix_operations()
```

```bash
# Profile it
python profile_mixed_library.py numpy_example.py --method pyinstrument
```

#### Example 2: Profile with C Extension
```bash
# Create C extension example
python advanced_profiler.py --create-example

# Build the extension
python setup_extension.py build_ext --inplace

# Create test script using the extension
cat > test_extension.py << EOF
import example_extension

for i in range(10):
    result = example_extension.compute_intensive(100)
    print(f"Iteration {i}: {result}")
EOF

# Profile with native code support
sudo python profile_mixed_library.py test_extension.py --method py-spy
```

#### Example 3: Profile Pandas Operations
```python
# Create pandas_example.py
import pandas as pd
import numpy as np

def pandas_operations():
    # Create large DataFrame
    df = pd.DataFrame(np.random.randn(10000, 100))
    
    # Various operations
    result = df.groupby(df.index % 100).agg(['mean', 'std', 'min', 'max'])
    pivoted = df.pivot_table(index=df.index % 50, columns=df.index % 20)
    rolled = df.rolling(window=100).mean()
    
    return result

if __name__ == "__main__":
    pandas_operations()
```

```bash
# Profile with multiple methods
make profile-all TARGET=pandas_example.py
```

### Viewing Results

```bash
# View the generated graph
make view

# Or manually open the SVG
xdg-open profiling_results/profile_graph.svg  # Linux
open profiling_results/profile_graph.svg       # macOS
```

### Understanding the Output

The generated graphs show:
- **Nodes**: Functions/methods with execution time percentages
- **Edges**: Call relationships with call counts
- **Colors**: Heat map indicating time spent (red = hot, blue = cold)
- **Node size**: Proportional to time spent in function

Key metrics shown:
- **Self time**: Time spent in the function itself
- **Total time**: Time including all called functions
- **Call count**: Number of times the function was called

## Advanced Features

### Interactive HTML Visualization

```bash
python advanced_profiler.py your_script.py --interactive
```

This creates an HTML file with:
- Zoom controls
- Pan functionality
- Downloadable SVG
- Search capabilities

### Combining Multiple Profiles

```python
# In your Python script
from advanced_profiler import AdvancedMixedProfiler

profiler = AdvancedMixedProfiler()

# Profile different parts
profile1 = profiler.profile_python("part1.py")
profile2 = profiler.profile_c_extension("part2.py")

# Combine and visualize
combined = profiler.combine_profiles([profile1, profile2])
profiler.generate_interactive_html(combined)
```

### Filtering Results

You can adjust the visualization thresholds in the scripts:

```python
# In profile_mixed_library.py, modify the gprof2dot command:
cmd = [
    "gprof2dot",
    "-f", format_type,
    "--node-thres", "1.0",  # Show only nodes > 1% of time
    "--edge-thres", "0.5",  # Show only edges > 0.5% of calls
    "--color-nodes-by-selftime",  # Color by self time
    "-o", str(dot_file)
]
```

## Troubleshooting

### Common Issues

1. **"gprof2dot not found"**
   ```bash
   pip install gprof2dot
   ```

2. **"dot not found" or "Graphviz not installed"**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install graphviz
   
   # macOS
   brew install graphviz
   ```

3. **"Permission denied" with py-spy**
   ```bash
   # py-spy needs sudo to access process memory
   sudo python profile_mixed_library.py script.py --method py-spy
   ```

4. **Empty or minimal graphs**
   - Your script might be too fast. Add loops or larger datasets
   - Adjust thresholds in gprof2dot (lower --node-thres value)

5. **C extension functions not showing**
   - Use py-spy or perf methods instead of cProfile
   - Compile C extensions with debug symbols (-g flag)

### Debug Tips

```bash
# Check installed dependencies
python advanced_profiler.py --check-deps

# Verbose output
python profile_mixed_library.py script.py 2>&1 | tee profile.log

# Keep intermediate files for debugging
# Edit the script to not delete .pstats, .dot files
```

## Performance Tips

1. **For production profiling**: Use pyinstrument (low overhead)
2. **For detailed analysis**: Use py-spy with native support
3. **For memory profiling**: Add memory_profiler to your workflow
4. **For line-by-line**: Use line_profiler for Python code

## Integration with CI/CD

```yaml
# Example GitHub Actions workflow
name: Performance Profiling

on: [push, pull_request]

jobs:
  profile:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y graphviz
        pip install -r requirements.txt
    - name: Run profiling
      run: |
        python profile_mixed_library.py tests/performance_test.py
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: profiling-results
        path: profiling_results/
```

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

MIT License - Use freely in your projects

## Additional Resources

- [gprof2dot documentation](https://github.com/jrfonseca/gprof2dot)
- [py-spy documentation](https://github.com/benfred/py-spy)
- [Python profiling guide](https://docs.python.org/3/library/profile.html)
- [Graphviz documentation](https://graphviz.org/documentation/)
