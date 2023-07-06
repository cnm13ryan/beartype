#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright (c) 2014-2023 Beartype authors.
# See "LICENSE" for further details.

'''
**Beartype import hook API.**

This subpackage publishes :pep:`302`- and :pep:`451`-compliant import hooks
enabling external callers to automatically decorate well-typed third-party
packages and modules with runtime type-checking dynamically generated by the
:func:`beartype.beartype` decorator in a single line of code.
'''

# ....................{ TODO                               }....................
#FIXME: Technically, we're not quite done here. The "beartype.claw" API
#currently silently ignores attempts to subject the "beartype" package itself to
#@beartyping. Ideally, that API should instead raise human-readable exceptions
#when users explicitly attempt to do so when calling either the
#beartype_package() or beartype_packages() functions. After implementing that
#functionality, assert that in our test suite, please.

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid polluting the public module namespace, external attributes
# should be locally imported at module scope *ONLY* under alternate private
# names (e.g., "from argparse import ArgumentParser as _ArgumentParser" rather
# than merely "from argparse import ArgumentParser").
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
from beartype.claw._clawmain import (
    beartype_all as beartype_all,
    beartype_package as beartype_package,
    beartype_packages as beartype_packages,
    beartype_this_package as beartype_this_package,
)
from beartype.claw._pkg.clawpkgcontext import (
    beartyping as beartyping,
)

# ....................{ TODO                               }....................
#FIXME: The following commentary seems mildly useful to retain for a bit. It
#delves deep into "pytest" internals and is, indeed, the only documentation
#we've seen *ANYWHERE* on that dicey subject. So... here we go!
#FIXME: Generalize this class to support stacking. What? Okay, so the core
#issue with the prior approach is that it only works with standard Python
#modules defined as standard files in standard directories. This assumption
#breaks down for Python modules embedded within other files (e.g., as frozen
#archives or zip files). The key insight here is given by Iguananaut in this
#StackOverflow answer:
#  https://stackoverflow.com/a/48671982/2809027
#This approach "...installs a special hook in sys.path_hooks that acts almost
#as a sort of middle-ware between the PathFinder in sys.meta_path, and the
#hooks in sys.path_hooks where, rather than just using the first hook that
#says 'I can handle this path!' it tries all matching hooks in order, until it
#finds one that actually returns a useful ModuleSpec from its find_spec
#method."
#Note that "hooks" in "sys.path_hooks" are actually *FACTORY FUNCTIONS*,
#typically defined by calling the FileFinder.path_hook() class method.
#We're unclear whether we want a full "ModuleSpec," however. It seems
#preferable to merely search for a working hook in "sys.path_hooks" that
#applies to the path. Additionally, if that hook defines a get_source() method
#*AND* that method returns a non-empty string (i.e., that is neither "None"
#*NOR* the empty string), then we want to munge that string with our AST
#transformation. The advantages of this approach are multitude:
#* This approach supports pytest, unlike standard "meta_path" approaches.
#* This approach supports embedded files, unlike the first approach above. In
#  particular, note that the standard
#  "zipimporter.zipimporter(_bootstrap_external._LoaderBasics)" class for
#  loading Python modules from arbitrary zip files does *NOT* subclass any of
#  the standard superclasses you might expect it to (e.g.,
#  "importlib.machinery.SourceFileLoader"). Ergo, a simple inheritance check
#  fails to suffice. Thankfully, that class *DOES* define a get_source()
#  method resembling that of SourceFileLoader.get_source().
#FIXME: I've confirmed by deep inspection of both the standard "importlib"
#package and the third-party "_pytest.assertion.rewrite" subpackage that the
#above should (but possible does *NOT*) suffice to properly integrate with
#pytest. Notably, the
#_pytest.assertion.rewrite.AssertionRewritingHook.find_spec() class method
#improperly overwrites the "importlib._bootstrap.ModuleSpec.loader" instance
#variable with *ITSELF* here:
#
#    class AssertionRewritingHook(importlib.abc.MetaPathFinder, importlib.abc.Loader):
#        ...
#
#        _find_spec = importlib.machinery.PathFinder.find_spec
#
#        def find_spec(
#            self,
#            name: str,
#            path: Optional[Sequence[Union[str, bytes]]] = None,
#            target: Optional[types.ModuleType] = None,
#        ) -> Optional[importlib.machinery.ModuleSpec]:
#            ...
#
#            # *SO FAR, SO GOOD.* The "spec.loader" instance variable now refers
#            # to an instance of our custom "SourceFileLoader" subclass.
#            spec = self._find_spec(name, path)  # type: ignore
#            ...
#
#            # *EVEN BETTER.* This might save us. See below.
#            if not self._should_rewrite(name, fn, state):
#                return None
#
#            # And... everything goes to Heck right here. Passing "loader=self"
#            # completely replaces the loader that Python just helpfully
#            # provided with this "AssertionRewritingHook" instance, which is
#            # all manner of wrong.
#            return importlib.util.spec_from_file_location(
#                name,
#                fn,
#                loader=self,  # <-- *THIS IS THE PROBLEM, BRO.*
#                submodule_search_locations=spec.submodule_search_locations,
#            )
#
#Ultimately, it's no surprise whatsoever that this brute-force behaviour from
#pytest conflicts with everyone else in the Python ecosystem. That said, this
#might still not be an issue. Why? Because the call to self._should_rewrite()
#*SHOULD* cause "AssertionRewritingHook" to silently reduce to a noop for
#anything that beartype would care about.
#
#If true (which it should be), the above approach *SHOULD* still actually work.
#So why does pytest conflict with other AST transformation approaches? Because
#those other approaches also leverage "sys.meta_path" machinery, typically by
#forcefully prepending their own "MetaPathFinder" instance onto "sys.meta_path",
#which silently overwrites pytest's "MetaPathFinder" instance. Since we're *NOT*
#doing that, we should be fine with our approach. *sweat beads brow*
#FIXME: Is the above commentary still required? The "BeartypeSourceFileLoader"
#docstring now documents this fairly extensively, we should think. Still, let's
#preserve this until we can be sure this behaves as expected.

