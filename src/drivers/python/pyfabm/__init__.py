#!/usr/bin/env python

import sys,os,ctypes,re
import numpy

# Determine potential names of FABM dynamic library.
if os.name=='nt':
   dllpaths = ('python_fabm.dll','libpython_fabm.dll')
elif os.name == "posix" and sys.platform == "darwin":
   dllpaths = ('libpython_fabm.dylib',)
else:
   dllpaths = ('libpython_fabm.so',)

# Determine name of existing FABM dynamic library.
for dllpath in dllpaths:
   dllpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),dllpath)
   if os.path.isfile(dllpath): break
else:
   print 'Unable to locate FABM dynamic library %s.' % (' or '.join(dllpaths),)
   sys.exit(1)

# Load FABM library.
fabm = ctypes.CDLL(dllpath)

# Specify arguments and return types for FABM interfaces.
fabm.initialize.argtypes = [ctypes.c_char_p]
fabm.get_variable_counts.argtypes = [ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int)]
fabm.get_variable_metadata.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p]
fabm.get_parameter_metadata.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int)]
fabm.get_dependency_metadata.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p]
fabm.get_real_parameter.argtypes = [ctypes.c_int,ctypes.c_int]
fabm.get_real_parameter.restype = ctypes.c_double
fabm.get_integer_parameter.argtypes = [ctypes.c_int,ctypes.c_int]
fabm.get_integer_parameter.restype = ctypes.c_int
fabm.get_logical_parameter.argtypes = [ctypes.c_int,ctypes.c_int]
fabm.get_logical_parameter.restype = ctypes.c_int
fabm.get_string_parameter.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_char_p]
fabm.reset_parameter.argtypes = [ctypes.c_int]
fabm.set_real_parameter.argtypes = [ctypes.c_char_p,ctypes.c_double]
fabm.set_integer_parameter.argtypes = [ctypes.c_char_p,ctypes.c_int]
fabm.set_logical_parameter.argtypes = [ctypes.c_char_p,ctypes.c_int]
fabm.set_string_parameter.argtypes = [ctypes.c_char_p,ctypes.c_char_p]
fabm.link_bulk_state_data.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.c_double)]
fabm.link_surface_state_data.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.c_double)]
fabm.link_bottom_state_data.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.c_double)]
fabm.link_dependency_data.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.c_double)]
fabm.get_bulk_diagnostic_data.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.POINTER(ctypes.c_double))]
fabm.get_horizontal_diagnostic_data.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.POINTER(ctypes.c_double))]
fabm.get_rates.argtypes = [numpy.ctypeslib.ndpointer(dtype=ctypes.c_double, ndim=1, flags='CONTIGUOUS')]

BULK_STATE_VARIABLE            = 1
SURFACE_STATE_VARIABLE         = 2
BOTTOM_STATE_VARIABLE          = 3
BULK_DIAGNOSTIC_VARIABLE       = 4
HORIZONTAL_DIAGNOSTIC_VARIABLE = 5
CONSERVED_QUANTITY             = 6
ATTRIBUTE_LENGTH               = 256

unicodesuperscript = {'1':u'\u00B9','2':u'\u00B2','3':u'\u00B3',
                      '4':u'\u2074','5':u'\u2075','6':u'\u2076',
                      '7':u'\u2077','8':u'\u2078','9':u'\u2079',
                      '0':u'\u2070','-':u'\u207B'}
supnumber = re.compile('(?<=\w)(-?\d+)(?=[ \*+\-/]|$)')
supenumber = re.compile('(?<=\d)e-(\d+)(?=[ \*+\-/]|$)')
oldsupminus = re.compile('/(\w+)\*\*(\d+)(?=[ \*+\-/]|$)')
oldsup = re.compile('/(\w+)\*\*(\d+)(?=[ \*+\-/]|$)')
def createPrettyUnit(unit):
    def repl(m):
        return u''.join([unicodesuperscript[n] for n in m.group(1)])
    def reple(m):
        return u'\u00D710\u207B%s' % u''.join([unicodesuperscript[n] for n in m.group(1)])
    def replold(m):
        return u' %s\u207B%s' % (m.group(1),u''.join([unicodesuperscript[n] for n in m.group(2)]))
    unit = supenumber.sub(reple,unit)
    unit = supnumber.sub(repl,unit)
    unit = oldsupminus.sub(replold,unit)
    return unit

def printTree(root,stringmapper,indent=''):
    """Print an indented tree of objects, encoded by dictionaries linking the names of children to
    their subtree, or to their object. Objects are finally printed as string obtained by
    calling the provided stringmapper method."""
    for name,item in root.iteritems():
        if isinstance(item,dict):
            print '%s%s' % (indent,name)
            printTree(item,stringmapper,indent+'   ')
        else:
            print '%s%s = %s' % (indent,name,stringmapper(item))

class Variable(object):
    def __init__(self,name,units=None,long_name=None,path=None):
        self.name = name
        self.units = units
        if units is None:
           self.units_unicode = None
        else:
           self.units_unicode = createPrettyUnit(units)
        if long_name is None: long_name = name
        if path is None: path = name
        self.long_name = long_name
        self.path = path

class Dependency(Variable):
    def __init__(self,name,index,units=None,long_name=None):
        if long_name is None: long_name = name
        Variable.__init__(self,name,units,long_name.replace('_',' '))
        self.data = ctypes.c_double(0.)
        fabm.link_dependency_data(index+1,ctypes.byref(self.data))

    def getValue(self):
        return self.data.value

    def setValue(self,value):
        self.data.value = value

    value = property(getValue, setValue)

class StateVariable(Variable):
    def __init__(self,statearray,name,index,units=None,long_name=None,path=None):
        Variable.__init__(self,name,units,long_name,path)
        self.index = index
        self.statearray = statearray

    def getValue(self):
        return float(self.statearray[self.index])

    def setValue(self,value):
        self.statearray[self.index] = value

    value = property(getValue, setValue)

class DiagnosticVariable(Variable):
    def __init__(self,name,index,horizontal,units=None,long_name=None,path=None):
        Variable.__init__(self,name,units,long_name,path)
        pdata = ctypes.POINTER(ctypes.c_double)()
        if horizontal:
            fabm.get_horizontal_diagnostic_data(index+1,ctypes.byref(pdata))
        else:
            fabm.get_bulk_diagnostic_data(index+1,ctypes.byref(pdata))
        self.data = pdata.contents

    def getValue(self):
        return self.data.value

    value = property(getValue)

class Parameter(Variable):
    def __init__(self,name,index,units=None,long_name=None,type=None,model=None,has_default=False):
        Variable.__init__(self,name,units,long_name)
        self.type = type
        self.index = index+1
        self.model = model
        self.has_default = has_default

    def getValue(self,default=False):
        default = 1 if default else 0
        if self.type==1:
            return fabm.get_real_parameter(self.index,default)
        elif self.type==2:
            return fabm.get_integer_parameter(self.index,default)
        elif self.type==3:
            return fabm.get_logical_parameter(self.index,default)!=0
        elif self.type==4:
            result = ctypes.create_string_buffer(ATTRIBUTE_LENGTH)
            fabm.get_string_parameter(self.index,default,ATTRIBUTE_LENGTH,result)
            return result.value

    def setValue(self,value):
        settings = self.model.saveSettings()

        if self.type==1:
            fabm.set_real_parameter(self.name,value)
        elif self.type==2:
            fabm.set_integer_parameter(self.name,value)
        elif self.type==3:
            fabm.set_logical_parameter(self.name,value)
        elif self.type==4:
            fabm.set_string_parameter(self.name,value)

        # Update the model configuration (arrays with variables and parameters have changed)
        self.model.updateConfiguration(settings)

    def getDefault(self):
       if not self.has_default: return None
       return self.getValue(True)

    def reset(self):
        settings = self.model.saveSettings()
        fabm.reset_parameter(self.index)
        self.model.updateConfiguration(settings)

    value = property(getValue, setValue)
    default = property(getDefault)

class Model(object):
    def __init__(self,path='fabm.yaml'):
        fabm.initialize(path)
        self.updateConfiguration()

    def saveSettings(self):
        environment = dict([(dependency.name,dependency.value) for dependency in self.dependencies])
        state = dict([(variable.name,variable.value) for variable in self.state_variables])
        return environment,state

    def restoreSettings(self,data):
        environment,state = data
        for dependency in self.dependencies:
            if dependency.name in environment: dependency.value = environment[dependency.name]
        for variable in self.state_variables:
            if variable.name in state: variable.value = state[variable.name]

    def updateConfiguration(self,settings=None):
        # Get number of model variables per category
        nstate_bulk = ctypes.c_int()
        nstate_surface = ctypes.c_int()
        nstate_bottom = ctypes.c_int()
        ndiag_bulk = ctypes.c_int()
        ndiag_horizontal = ctypes.c_int()
        nconserved = ctypes.c_int()
        ndependencies = ctypes.c_int()
        nparameters = ctypes.c_int()
        fabm.get_variable_counts(ctypes.byref(nstate_bulk),ctypes.byref(nstate_surface),ctypes.byref(nstate_bottom),
                                 ctypes.byref(ndiag_bulk),ctypes.byref(ndiag_horizontal),
                                 ctypes.byref(nconserved),ctypes.byref(ndependencies),ctypes.byref(nparameters))

        # Allocate memory for state variable values, and send ctypes.pointer to this memory to FABM.
        self.state = numpy.empty((nstate_bulk.value+nstate_surface.value+nstate_bottom.value,),dtype=float)
        for i in range(nstate_bulk.value):
            fabm.link_bulk_state_data(i+1,self.state[i:].ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
        for i in range(nstate_surface.value):
            fabm.link_surface_state_data(i+1,self.state[i+nstate_bulk.value:].ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
        for i in range(nstate_bottom.value):
            fabm.link_bottom_state_data(i+1,self.state[i+nstate_bulk.value+nstate_surface.value:].ctypes.data_as(ctypes.POINTER(ctypes.c_double)))

        # Retrieve variable metadata
        strname = ctypes.create_string_buffer(ATTRIBUTE_LENGTH)
        strunits = ctypes.create_string_buffer(ATTRIBUTE_LENGTH)
        strlong_name = ctypes.create_string_buffer(ATTRIBUTE_LENGTH)
        strpath = ctypes.create_string_buffer(ATTRIBUTE_LENGTH)
        typecode = ctypes.c_int()
        has_default = ctypes.c_int()
        self.bulk_state_variables = []
        self.surface_state_variables = []
        self.bottom_state_variables = []
        self.bulk_diagnostic_variables = []
        self.horizontal_diagnostic_variables = []
        self.conserved_quantities = []
        self.parameters = []
        self.dependencies = []
        for i in range(nstate_bulk.value):
            fabm.get_variable_metadata(BULK_STATE_VARIABLE,i+1,ATTRIBUTE_LENGTH,strname,strunits,strlong_name,strpath)
            self.bulk_state_variables.append(StateVariable(self.state,strname.value,i,strunits.value,strlong_name.value,strpath.value))
        for i in range(nstate_surface.value):
            fabm.get_variable_metadata(SURFACE_STATE_VARIABLE,i+1,ATTRIBUTE_LENGTH,strname,strunits,strlong_name,strpath)
            self.surface_state_variables.append(StateVariable(self.state,strname.value,nstate_bulk.value+i,strunits.value,strlong_name.value,strpath.value))
        for i in range(nstate_bottom.value):
            fabm.get_variable_metadata(BOTTOM_STATE_VARIABLE,i+1,ATTRIBUTE_LENGTH,strname,strunits,strlong_name,strpath)
            self.bottom_state_variables.append(StateVariable(self.state,strname.value,nstate_bulk.value+nstate_surface.value+i,strunits.value,strlong_name.value,strpath.value))
        for i in range(ndiag_bulk.value):
            fabm.get_variable_metadata(BULK_DIAGNOSTIC_VARIABLE,i+1,ATTRIBUTE_LENGTH,strname,strunits,strlong_name,strpath)
            self.bulk_diagnostic_variables.append(DiagnosticVariable(strname.value,i,False,strunits.value,strlong_name,strpath.value))
        for i in range(ndiag_horizontal.value):
            fabm.get_variable_metadata(HORIZONTAL_DIAGNOSTIC_VARIABLE,i+1,ATTRIBUTE_LENGTH,strname,strunits,strlong_name,strpath)
            self.horizontal_diagnostic_variables.append(DiagnosticVariable(strname.value,i,True,strunits.value,strlong_name,strpath.value))
        for i in range(nconserved.value):
            fabm.get_variable_metadata(CONSERVED_QUANTITY,i+1,ATTRIBUTE_LENGTH,strname,strunits,strlong_name,strpath)
            self.conserved_quantities.append(Variable(strname.value,strunits.value,strlong_name,strpath.value))
        for i in range(nparameters.value):
            fabm.get_parameter_metadata(i+1,ATTRIBUTE_LENGTH,strname,strunits,strlong_name,ctypes.byref(typecode),ctypes.byref(has_default))
            self.parameters.append(Parameter(strname.value,i,type=typecode.value,units=strunits.value,long_name=strlong_name.value,model=self,has_default=has_default.value!=0))
        for i in range(ndependencies.value):
            fabm.get_dependency_metadata(i+1,ATTRIBUTE_LENGTH,strname,strunits)
            self.dependencies.append(Dependency(strname.value,i,units=strunits.value))

        # Arrays that combine variables from pelagic and boundary domains.
        self.state_variables = self.bulk_state_variables + self.surface_state_variables + self.bottom_state_variables
        self.diagnostic_variables = self.bulk_diagnostic_variables + self.horizontal_diagnostic_variables

        if settings is not None: self.restoreSettings(settings)

    def getRates(self):
        """Returns the local rate of change in state variables,
        given the current state and environment.
        """
        localrates = numpy.empty_like(self.state)
        consrates = numpy.empty((len(self.conserved_quantities),))
        fabm.get_rates(localrates)
        return localrates,consrates

    def findParameter(self,name):
        for parameter in self.parameters:
            if parameter.name==name: return parameter
        raise Exception('Parameter "%s" was not found.' % name)

    def findDependency(self,name):
        for dependency in self.dependencies:
            if dependency.name==name: return dependency
        raise Exception('Dependency "%s" was not found.' % name)

    def findStateVariable(self,name):
        for variable in self.state_variables:
            if variable.name==name: return variable
        raise Exception('State variable "%s" was not found.' % name)

    def getParameterTree(self):
        root = {}
        for parameter in self.parameters:
            pathcomps = parameter.name.split('/')
            parent = root
            for component in pathcomps[:-1]:
                parent = root.setdefault(component,{})
            parent[pathcomps[-1]] = parameter
        return root

    def printInformation(self):
        """Show information about the model."""
        def printArray(classname,array):
            if not array: return
            print ' %i %s:' % (len(array),classname)
            for variable in array: print '    %s = %s %s' % (variable.name,variable.value,variable.units)

        print 'FABM model contains the following:'
        printArray('bulk state variables',self.bulk_state_variables)
        printArray('bottom state variables',self.bottom_state_variables)
        printArray('surface state variables',self.surface_state_variables)
        printArray('bulk diagnostic variables',self.bulk_diagnostic_variables)
        printArray('horizontal diagnostic variables',self.horizontal_diagnostic_variables)
        printArray('external variables',self.dependencies)
        print ' %i parameters:' % len(self.parameters)
        printTree(self.getParameterTree(),lambda x:'%s %s' % (x.value,x.units),'    ')