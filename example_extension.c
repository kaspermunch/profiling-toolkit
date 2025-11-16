
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
