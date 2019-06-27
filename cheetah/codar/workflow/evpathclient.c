#include <stdarg.h>
#include "evpath.h"
#include "ev_dfg.h"

enum {
  CHNGE_COMPRESS = 0,
  CHNGE_COMPACC,
  CHNGE_ENGINE,
  SKIP_NTIMESTEP,  
} message_type;

typedef struct _simple_rec {
    int integer_field;
} simple_rec, *simple_rec_ptr;

static FMField simple_field_list[] =
{
    {
integer_field", "integer", sizeof(int), FMOffset(simple_rec_ptr, integer_field)},
    {NULL, NULL, 0, 0}
};

static FMStructDescRec simple_format_list[] =
{
    {"simple", simple_field_list, sizeof(simple_rec), NULL},
    {NULL, NULL}
};




char *conn_string;
int message_type;

static PyObject *
evpathclient_init(PyObject *self, PyObject *args)
{
    va_list conn_strings;
    PyObject *py_tuple;
    int status = 1;
    Py_ssize_t len;
    len = PyTuple_Size(args); 
    conn_strings = malloc(len * sizeof(char*));
 
    if(!len) {
        if(!PyErr_Occurred()) 
            PyErr_SetString(PyExc_TypeError,"You must supply at least one argument.");
        free(conn_strings);
        return NULL;    
    }

    if (!PyArg_ParseTuple(args, "s", &py_tuble)) {
        return NULL;
    }

    int i = 0;
    while (len --) {
        conn_strings[i++] = (char *) PyTuple_GetItem(py_tuple, i);
    }

    return Py_BuildValue("i", status);
}

int main(int argc, char** argv) {

    CManager cm;
    simple_rec data;
    EVstone stone;
    EVsource source;
    char string_list[2048];
    attr_list contact_list;
    EVstone remote_stone;
    
    // create a socket to contact the python workflow manager
    // get all the connections for the python workflow maneger 
    // get control messages from python workflow manager 
    // send EVPATH signal to different processes.
}
