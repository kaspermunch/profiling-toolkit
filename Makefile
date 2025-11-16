# Makefile for profiling mixed Python/C++/C code

PYTHON := python3
OUTPUT_DIR := profiling_results
SCRIPT := profile_mixed_library.py

# Default target
.PHONY: help
help:
	@echo "Profiling toolkit for mixed Python/C++/C code"
	@echo ""
	@echo "Available targets:"
	@echo "  make install       - Install required dependencies"
	@echo "  make test         - Run test profiling with example code"
	@echo "  make profile      - Profile your code (set TARGET=yourscript.py)"
	@echo "  make profile-native - Profile with native code support"
	@echo "  make profile-all  - Run all profiling methods"
	@echo "  make clean        - Remove profiling results"
	@echo "  make view         - Open the most recent visualization"
	@echo ""
	@echo "Examples:"
	@echo "  make profile TARGET=myapp.py"
	@echo "  make profile-native TARGET=myapp.py"

# Install dependencies
.PHONY: install
install:
	@echo "Installing Python dependencies..."
	pip install --upgrade pip
	pip install gprof2dot
	pip install py-spy
	pip install pyinstrument
	pip install austin-python
	pip install numpy  # For test examples
	@echo ""
	@echo "Installing system dependencies..."
	@echo "Ubuntu/Debian:"
	@echo "  sudo apt-get install graphviz linux-tools-common linux-tools-generic valgrind"
	@echo ""
	@echo "macOS:"
	@echo "  brew install graphviz"
	@echo ""
	@echo "For py-spy with sudo access:"
	@echo "  sudo pip install py-spy"

# Test with example code
.PHONY: test
test:
	@$(PYTHON) $(SCRIPT) --output-dir $(OUTPUT_DIR)
	@echo "Test profiling complete. Check $(OUTPUT_DIR)/"

# Basic profiling with cProfile
.PHONY: profile
profile:
ifndef TARGET
	@echo "Error: Please specify TARGET"
	@echo "Usage: make profile TARGET=yourscript.py"
	@exit 1
endif
	@$(PYTHON) $(SCRIPT) $(TARGET) --method cprofile --output-dir $(OUTPUT_DIR)

# Profile with native code support using py-spy
.PHONY: profile-native
profile-native:
ifndef TARGET
	@echo "Error: Please specify TARGET"
	@echo "Usage: make profile-native TARGET=yourscript.py"
	@exit 1
endif
	@echo "Note: This requires sudo access for py-spy"
	@$(PYTHON) $(SCRIPT) $(TARGET) --method py-spy --output-dir $(OUTPUT_DIR)

# Profile with pyinstrument (good for mixed code)
.PHONY: profile-pyinstrument
profile-pyinstrument:
ifndef TARGET
	@echo "Error: Please specify TARGET"
	@echo "Usage: make profile-pyinstrument TARGET=yourscript.py"
	@exit 1
endif
	@$(PYTHON) $(SCRIPT) $(TARGET) --method pyinstrument --output-dir $(OUTPUT_DIR)

# Run all profiling methods
.PHONY: profile-all
profile-all:
ifndef TARGET
	@echo "Error: Please specify TARGET"
	@echo "Usage: make profile-all TARGET=yourscript.py"
	@exit 1
endif
	@echo "Running all profiling methods..."
	@$(PYTHON) $(SCRIPT) $(TARGET) --method cprofile --output-dir $(OUTPUT_DIR)
	@$(PYTHON) $(SCRIPT) $(TARGET) --method pyinstrument --output-dir $(OUTPUT_DIR)
	@echo "Note: Skipping py-spy (requires sudo)"
	@echo "Run 'make profile-native TARGET=$(TARGET)' separately for py-spy"

# View the most recent SVG output
.PHONY: view
view:
	@if [ -d $(OUTPUT_DIR) ]; then \
		latest=$$(ls -t $(OUTPUT_DIR)/*.svg 2>/dev/null | head -1); \
		if [ -n "$$latest" ]; then \
			echo "Opening $$latest"; \
			if command -v xdg-open > /dev/null; then \
				xdg-open "$$latest"; \
			elif command -v open > /dev/null; then \
				open "$$latest"; \
			else \
				echo "Please open $$latest manually"; \
			fi \
		else \
			echo "No SVG files found in $(OUTPUT_DIR)"; \
		fi \
	else \
		echo "Output directory $(OUTPUT_DIR) does not exist"; \
	fi

# Clean profiling results
.PHONY: clean
clean:
	@echo "Cleaning profiling results..."
	@rm -rf $(OUTPUT_DIR)
	@rm -f *.pstats *.dot *.svg *.png *.pdf
	@rm -f gmon.out callgrind.out.*
	@rm -f test_mixed_code.py
	@echo "Clean complete"

# Check dependencies
.PHONY: check-deps
check-deps:
	@$(PYTHON) advanced_profiler.py --check-deps

# Create C extension example
.PHONY: create-extension
create-extension:
	@$(PYTHON) advanced_profiler.py --create-example
	@echo "Building extension..."
	@$(PYTHON) setup_extension.py build_ext --inplace

# Profile specific library (e.g., numpy operations)
.PHONY: profile-numpy
profile-numpy:
	@echo "import numpy as np" > numpy_test.py
	@echo "def test():" >> numpy_test.py
	@echo "    for _ in range(100):" >> numpy_test.py
	@echo "        a = np.random.rand(100, 100)" >> numpy_test.py
	@echo "        b = np.random.rand(100, 100)" >> numpy_test.py
	@echo "        c = np.dot(a, b)" >> numpy_test.py
	@echo "        d = np.linalg.svd(c)" >> numpy_test.py
	@echo "test()" >> numpy_test.py
	@$(PYTHON) $(SCRIPT) numpy_test.py --method cprofile --output-dir $(OUTPUT_DIR)
	@rm numpy_test.py
