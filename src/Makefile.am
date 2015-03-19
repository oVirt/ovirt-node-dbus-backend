# Copyright (C) 2015 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.

export PYTHONPATH=$(top_srcdir)/src
export PYFLAKES_BUILTINS=_

PYTHONSOURCES:=$(shell find . -name '*.py')

nodeconfdir = $(sysconfdir)/sysconfig

pyovirtdbusdir = $(pythondir)/ovirt/node/dbus
pyovirtdbus_PYTHON = \
  __init__.py \
  factory.py \
  log.py \
  service.py \
  testers.py \
  wrappers.py

check-local: check-static
	@echo -e "---\n Passed $@\n---"

check-static: check-static-doctests check-static-pep8 check-static-pyflakes
	@echo Passed $@

check-static-xmllint: $(XMLSOURCES:%=%.xmllint)
	@echo Passed $@

%.xmllint:
	xmllint --noout "$*"

check-static-doctests: $(PYTHONSOURCES:%=%.doctest)
	@echo Passed $@

%.doctest:
	@if grep -q ">>>" "$*" ; then set -x ; python -m doctest "$*" ; fi ;

check-static-pep8: $(PYTHONSOURCES:%=%.pep8)
	@echo Passed $@

%.pep8:
	pep8 -r "$*"

# FIXME Pylint is very strict, needs to be configured
# Maybe take a peek at a diff. proj. to find a sane configuration
PYLINT=pylint -f parseable --include-ids=yes --rcfile=.pylintrc
check-static-pylint: $(PYTHONSOURCES:%=%.pylint)
	@echo Passed $@

%.pylint:
	$(PYLINT) "$*"

check-static-pyflakes: $(PYTHONSOURCES:%=%.pyflakes)
	@echo Passed $@

PYFLAKES_BUILTINS = "_"
%.pyflakes:
	pyflakes "$*"
