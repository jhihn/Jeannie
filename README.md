Jeannie
=======

"Cute Genie" - Python Script to generate QObject proxies using QAndroidJNI*

USAGE
=====
Assumption: some.jar is the library you are trying to use.

Run:
javap -constants some.jar > classes.txt
python jni-qt.py

Then examine the files generated in the directory. Include these in your project. 

WORKINGS
========
The script will generate a header and cpp for each class in the jar file. And a final jni_onload.h and jni_onload.cpp to register native functions. 

It attempts to serialize to java types and deserialize to Qt types transparently.

STATUS
======
Initial development, not tested. Being published so I don't lose the work.
Feel free to hack at it. Don't ask for permission, ask for forgiveness. It's easier that way.




