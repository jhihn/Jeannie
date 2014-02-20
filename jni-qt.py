#!/usr/bin/python
#############################################################
class Method:
	def __init__(self, rettype, cname, name, static, native, args=[]):
		self.cname = cname
		self.name = name.replace('.', '_')
		self.args = args
		self.rettype = rettype.replace('.', '_') if rettype is not None else None
		self.static = static
		self.native = native

	def java_signature(self):
		s = '('
		for param in self.args:
			s += self.param_signature(param)
		s+=')'+ self.param_signature(self.rettype)
		return s
	
	def param_signature(self, ctype):
		vm_types = {'boolean': 'Z', 'byte':  'B', 'char':  'C', 'short':  'S', 'int':  'I', 'long':  'J', 'float': 'F', 'double': 'D', 'void':'V', None:'V'}
		if '[]' in ctype:
			s='['
			ctype = ctype.replace('[]', '')
		else:
			s=''		

		if ctype not in vm_types.keys():
			s += 'L'+ctype.replace('.', '/')+';'
		else:
			s += vm_types[ctype]
		return s	
	def javatoctype(self, jt):
		jtypes = {'boolean': 'bool', 'byte':  'unsigned char', 'char':  'char', 'short':  'short', 'int':  'int', 'long':  'long', 'float': 'float', 'double': 'double', 'void':'void', None:None, 'java.lang.String': 'QString'}
		s= ''
		if jt is None: return s
		array = False
		if jt[-2:] == '[]':
			s += 'QVector<'
			jt = jt[0:-2]
			array = True
		if jt not in jtypes.keys():
			s += jt.replace('.', '_')
		else:
			s += jtypes[jt]
		if array:
			s += '>'
		return s
		
	
	def create_header_prototype(self):
		args = []
		for i in range(len(self.args)):
			args.append(self.javatoctype(self.args[i]).replace('.', '_') + ' param' +str(i))
		namedargs = ', '.join(args)
		if self.static:
			s = 'static '
		else:
			s = ''		
		if self.javatoctype(self.rettype) is not None:
			s += '\t' + self.javatoctype(self.rettype) + ' ' + self.name + '(' + namedargs + ');\n'
		else:
			s += '\t' + self.name + '(' + namedargs + ');\n'
		return s


	#the C++ call
	def create_method_code_head(self):
		if self.static:
			s = 'static '
		else:
			s = ''

		if self.rettype is not None and len(self.rettype):
			s += self.javatoctype(self.rettype) + ' '
		s += cclass+'::'+self.name+'('
		params = []
		for i in range(len(self.args)):
			if self.args[i] in ['java.lang.String']:
				params.append('QString param' + str(i))
			else:
				params.append(self.javatoctype(self.args[i])+ ' param' + str(i))
		s += ', '.join(params)
		s += ')\n{\n' 
		return s

	#the C++ call
	def create_method_code_constructor(self):
		s = self.name + '::' + self.create_header_prototype()[1:-2] # trim tab and ;
		s += '\n{\n\tm_' + self.name + 'Object = QAndroidJniObject("' + self.cname + '");\n'
		s += '}\n\n'	
		return s

	#the C++ function call
	def create_method_code_call(self):
		s = ''
		if self.rettype == None: return s #constructors
		refs = []
		marshals = {}
		#marshal params
		#QAndroidJniObject string = QAndroidJniObject::fromString("Hello"); jstring str = string.toString();
		for i in range(len(self.args)):
			if self.args[i] in ['java.lang.String']:
				s += '\tQAndroidJniObject istr'+str(i)+ ' = QAndroidJniObject::fromString(param' + str(i) + ');\n'
				s += '\tjstring jstr'+str(i)+' = istr'+str(i)+ '.toString());\n'
				refs.append('param'+str(i));
				marshals['param'+str(i)]='jstr'+str(i);
		
		#do the call
		retType = self.retTypeStorage(self.rettype)
		if self.rettype != 'void':
			s += '\t' + retType + ' res = m_' + self.cname.replace('/', '_') + 'Object.' + self.functionCall() + '<' + retType + '>("' +self.name + '", "' + self.java_signature() +'"'
		else:
			s += '\tm_' + self.cname.replace('/', '_') + 'Object.callMethod<' + retType + '>("' +self.name + '", "' + self.java_signature() +'"'
		arglist = []
		for i in range(len(self.args)):
			if 'param'+str(i) in marshals.keys():
				arglist.append(marshals['param'+str(i)])
			else:
				arglist.append('param'+str(i))
		if len(arglist):
			s += ', '
		s += ', '.join(arglist)

		s += ');\n'
		
		#do clean-up 
		for i in range(len(self.args)):
			pass
		return s
	#the C++ call
	def create_method_code_tail(self):
		s = ''
		if self.rettype != 'void' and self.rettype is not None: 
			if (self.rettype == 'string'):
				s += '\treturn res.toString();\n'
			elif self.rettype[-2:] == '[]':
				s += '\treturn ' + self.javatoctype(self.rettype)[0:-1] + ',' + self.retTypeStorage(self.rettype)+ '>jniArrayToQVector(qjniEnv, res);\n'
			else:			
				s += '\treturn res;\n'
		else: 
			s+= '\treturn;\n'
		s += '}\n\n'
		return s


	def retTypeStorage(self, retType):
		d = {'void': 'void', 'boolean': 'bool', 'byte': 'jbyte', 'char': 'jchar', 'short': 'jshort', 'int': 'jint', 'long': 'long', 'float': 'jfloat', 'double': 'jdouble', 'string': 'jstring', None: '', 'java_lang_String': 'jstring','java_lang_Object': 'jobject',  
		'boolean[]': 'jbooleanArray', 'byte[]': 'jbyteArray', 'char[]': 'jcharArray', 'short[]': 'jshortArray', 'int[]': 'jintArray', 'long[]': 'longArray', 'float[]': 'jfloatArray', 'double[]': 'jdoubleArray', 'string[]': 'jstringArray'}
		if retType in d:
			return d[retType]
		print "WARNING: NO C++ j* TYPE FOR " + retType + '. Using QAndroidJniObject\t\t\t(' + self.cname + '::' + self.name + ')'
		return 'QAndroidJniObject'
	
	def functionCall(self):
		d = {'void', 'boolean', 'byte', 'char', 'short', 'int', 'long', 'float', 'double', 'string', None, 
		'boolean[]', 'byte[]', 'char[]', 'short[]', 'int[]', 'long[]', 'float[]', 'double[]', 'string[]'}

		s = 'call'
		if self.static == True: s+= 'Static'
		if self.rettype not in d: s += 'Object'
		s += 'Method'
		return s


##################################################
class Constant: #get these from 'javap -constants'
	def __init__(self, dtype, name, value):
		self.type = dtype
		self.name = name
		self.value = value

##################################################
class Class:
	def __init__(self, cname):
		self.qualname = cname.replace('.', '/')
		self.cname = cname.replace('.', '_')
		self.methods = []
		self.constants = []
	def qualifiedName(self):
		return self.qualname

	def cName(self):
		return self.cname

	def methods(self):
		return self.methods.keys()

	def addMember(self, line):
		if '(' in line:
			print 'method:', line
			self.addMethod(line)
		elif 'public static final':
			print 'constant:', line
			self.addConstant(line)

	def addMethod(self, line):
		static = False
		native = False
		words = line.split(' ')
		if words[0] == 'static' and words[1]== '{}': return
		if words[0] == 'static': static = True
		if words[0] == 'public': words = words[1:]
		if words[0] == 'native': 
			words = words[1:]
			native = True
		if words[0] == 'synchronized': words = words[1:]
		if '(' in words[0]: #its a constuctor, no type
			rettype = None			
		else:
			rettype = words[0]
			words =  words[1:]
	
		mname = words[0]
		mname = mname[0:words[0].index('(')] 
		args = "".join(words)
		args = args[args.index('(')+1: args.index(')')]
		if len(args):		
			args = args.split(',')
		else:
			args=[]
		self.methods.append( Method(rettype, self.qualname, mname, static, native, args))
		
			
	def addConstant(self, line):
		words = line.split(' ')
		if len(words) > 6:
			self.constants.append(Constant(words[3], words[4], words[6][0:-1]))

	def create_header_head(self):
		return '#ifndef ' + self.cName().upper() + '_H\n#define ' + self.cName().upper() + '_H\n' + \
			   '#include <QObject>\n#include <QAndroidJniEnvironment>\n#include <QAndroidJniqObject>\n#include <jni.h>\n\n' + \
			   '#include "qtjnihelper.h"\n' + \
			   'class '+ self.cName() + ': public QObject\n{\tQ_OBJECT\n\t' + '\n\tQAndroidJniEnvironment env;\n\tQAndroidJniObject m_' + self.cName() + 'Object;\n'+ \
			   'public:\n\t' + self.cName() + '();\n\t~' + self.cName() + '();\n'
	def create_header_tail(self):
		return '\n};\n#endif //' + self.cName().upper() + '_H\n'

	def create_header_constants(self):
		s = ''
		for constant in self.constants:
			s += '\tstatic const ' + constant.type + ' ' + constant.name + ' = ' + constant.value + ';\n'
		return s


	def create_code_head(self):
		return '#include <QDebug>\n#include "'+self.cName()+'.h"\n\n'

	#the initialization for the C++ call in JNI's OnLoad(), per method
	def create_code_jni_onload_stub(self):
		natives = self.native_funcs()
		s = 'static ' + self.cname + '::jniOnLoad()\n{\n'
		if len(natives):
			s += '\tJNINativeMethod methods[] {\n\t\t'
			s += ",\n\t\t".join(natives)
			s += '\n\t};\n'
			s += '\tQAndroidJniObject javaClass("' + self.cname + '");\n'
			s += '\tjclass objectClass = env->GetObjectClass(javaClass.object<jobject>());\n'
			s += '\tenv->RegisterNatives(objectClass, methods, ' + str(len(natives)) + ');\n'
			s += '\tenv->DeleteLocalRef(objectClass);\n'
		s += '}'
		return s

	def static_decls(self):		
		return ''

	def native_funcs(self):
		decls = []
		natives = [x for x in self.methods if x.native == True and x.static == False]
		for n in natives:
			decls.append('{"' + n.name + '", "' + n.java_signature() + '", reinterpret_cast<void *>(' + n.name + ')}')
		return decls + self.native_static_funcs()

	def native_static_funcs(self):
		decls = []
		natives = [x for x in self.methods if x.native == True and x.static == True]
		for n in natives:
			decls.append('{"' + n.name + '", "' + n.java_signature() + '", reinterpret_cast<void *>(' + n.name + ')}')
		return decls

##################################################
if __name__ == '__main__':
	o=open("classes.txt") 
	classes = []
	current_class = None
	for line in o:	
		line = line.strip()
		words = line.split()	
		if 'public class ' in line:
			classes.append(Class(words[2])) 
			current_class = classes[-1]
		elif line[0] == '}':
			current_class=None
		else: 
			current_class.addMember(line)

	for clas in classes:
		cclass = clas.cName().replace('.', '_')
		head = open(cclass+'.h', 'w')
		head.write(clas.create_header_head())
		head.write(clas.create_header_constants())

		for method in [x for x in clas.methods]:# if x.native == False]:
			head.write(method.create_header_prototype())
		head.write("\tstatic void jniOnLoad();\n")
		head.write(clas.create_header_tail())
		head.close();

		code = open(cclass+'.cpp', 'w')
		code.write(clas.create_code_head())
		code.write(clas.static_decls())
		constructors = [x for x in clas.methods if x.rettype == None]
		natives = clas.native_funcs()
		#statics = clas.native_static_funcs()
		for constuctor in constructors:
			code.write(constuctor.create_method_code_constructor())

		methods = [x for x in clas.methods if x.rettype is not None]
		for method in methods:
			code.write(method.create_method_code_head())
			code.write(method.create_method_code_call())
			code.write(method.create_method_code_tail())


		code.write(clas.create_code_jni_onload_stub())	
		code.close()
	head = open('jni_onload'+'.h', 'w')
	head.write("JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* /*reserved*/);\n")
	head.close()

	code = open('jni_onload'+'.cpp', 'w')
	code.write("jint JNI_OnLoad(JavaVM* vm, void* /*reserved*/)\n{\n")
	for clas in classes:
		code.write("\t"+clas.cname+"::jniOnLoad();\n")
	code.write('}\n')
	code.close()
