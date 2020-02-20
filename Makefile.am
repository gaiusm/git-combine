SHELL=/bin/bash

prefix= @prefix@
datarootdir= @datarootdir@
srcdir= @srcdir@
mandir= @mandir@
exec_prefix=@exec_prefix@
bindir= @bindir@
INSTALL_PROGRAM = install

DISTFILES = Makefile.am configure.ac configure \
            README version.c COPYING examples \
            git-combine.in combine.py fsalias.py configure.py

all: force
	echo "nothing to be done for all"

install: force
	if [ ! -f configure.py ] ; then cp $(srcdir)/configure.py . ; fi
	if [ ! -f combine.py ] ; then cp $(srcdir)/combine.py . ; fi
	if [ ! -f fsalias.py ] ; then cp $(srcdir)/fsalias.py . ; fi
	mkdir -p $(DESTDIR)/$(datarootdir)/git-combine
	$(INSTALL_PROGRAM) -m 644 configure.py $(DESTDIR)/$(datarootdir)/git-combine
	$(INSTALL_PROGRAM) -m 644 fsalias.py $(DESTDIR)/$(datarootdir)/git-combine
	$(INSTALL_PROGRAM) -m 644 combine.py $(DESTDIR)/$(datarootdir)/git-combine
	$(INSTALL_PROGRAM) -m 755 git-combine $(DESTDIR)/$(bindir)

documentation:

release: force
	pwd
	echo touchgui-`sed -e '/version_string/!d' \
          -e 's/[^0-9.]*\([0-9.]*\).*/\1/' -e q $(srcdir)/version.c` > .fname
	-rm -rf `cat .fname`
	mkdir `cat .fname`
	dst=`cat .fname`; for f in $(DISTFILES); do \
           cp -rp $(srcdir)/$$f $$dst/$$f ; \
        done
	tar --gzip -chf `cat .fname`.tar.gz `cat .fname`
	-rm -rf `cat .fname` .fname

clean: force
	$(RM) *.o *.m *.cpp *~ $(EXAMPLES) *.so *.lo *.la
	$(RM) -rf .libs *_m2.cpp

clear: force

force:
