Jeannie
=======

"Cute Genie" - Python Script to generate QObject proxies using QAndroidJNI*

USAGE
=====
Run:
javap -constants some.jar > classes.txt
python jni-qt.py

Then examine the files generated in the directory. Include these in your project. 

Workings
========
The script will generate a header and cpp for each class in the jar file. And a final jni_onload.h and jni_onload.cpp to register native functions. 




