#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright (c) 2014-2021 Beartype authors.
# See "LICENSE" for further details.

'''
**Beartype.**

For PEP 8 compliance, this namespace exposes a subset of the metadata constants
provided by the top-level :mod:`meta` submodule commonly inspected by external
automation.
'''

# ....................{ TODO                              }....................
#FIXME: Consider significantly expanding the above module docstring, assuming
#Sphinx presents this module in its generated frontmatter.

#FIXME: [NEW PROJECT] Consider creating a new public subpackage named either:
#* "beartype.annotated".
#* "beartype.bearcat".
#Okay, definitely "beartype.annotated". "beartype.bearcat" is cute -- but
#cuteness has its limit. This is that limit.
#
#In any case, this subpackage declares a number of public factory classes
#and/or callables resembling those declared by the "typing" module, intended to
#be listed after the first argument of any "typing.Annotated" type hint to
#perform traditional data validation on the internal structure of a passed or
#returned value annotated with that hint with a beartype-specific constraint:
#    from beartype import beartype
#    from beartype.annotated import LengthMinimum, LengthMaximum
#    from typing import Annotated
#
#    @beartype
#    def muh_func(muh_param: Annotated[
#        str, LengthMinimum[4], LengthMaximum[44]] -> bool:
#        '''
#        ``True`` only if the passed string with 4 <= length <= 44 contains a
#        particular phrase of no particular import.
#        '''
#
#        return 'The dream that dreams.' in muh_param
#
#Let's spin this up as rapidly as possible. To do so, *THE VERY FIRST PUBLIC
#THING* the "beartype.annotated" subpackage should provide is a public factory
#class and/or callable named "Constraint", which accepts as subscripted
#arguments one or more arbitrary caller-defined callables required to have
#signature resembling "def is_constrained(obj: Any) -> bool" and then validates
#each passed or returned value annotated with that hint to satisfy those
#constraints such that each of those caller-defined callables returns true when
#passed that value: e.g.,
#    from beartype import beartype
#    from beartype.annotated import Constraint
#    from typing import Annotated
#
#    @beartype
#    def muh_func(muh_param: Annotated[
#        str, Constraint[lambda text: return 4 <= len(text) <= 44]] -> bool:
#        '''
#        ``True`` only if the passed string with 4 <= length <= 44 contains a
#        particular phrase of no particular import.
#        '''
#
#        return 'The dream that dreams.' in muh_param
#
#Clearly, the above two examples are equivalent. The advantage of the latter
#approach, however, is that it dramatically simplifies our life by offloading
#*MUST* of the work onto the caller. Indeed, given the "Constraint" object, we
#could then define all higher-level constraints (e.g., "LengthMinimum",
#"LengthMaximum") in terms of that single lower-level primitive.
#FIXME: Note that we prominently discuss this topic in this issue comment:
#    https://github.com/beartype/beartype/issues/32#issuecomment-799796945

#FIXME: [NEW PROJECT] Consider creating a new private "beartype._bearable"
#subpackage to enable arbitrary O(1) runtime type checking. By "arbitrary," we
#mean just that: O(1) runtime type checking that anyone can perform in any
#arbitrary expression without having to isolate that checking to a callable
#signature.
#
#First, let's spec the public API. Fortunately, that's trivial. Just as with
#"beartype", we define only a single public turbo-charged function:
#* Define a private "beartype._bearable" submodule *OR SOMETHING.*
#* In that submodule:
#  * Define a public is_bearable() tester with the signature:
#
#    def is_bearable(obj: object, hint: object) -> bool:
#
#    ...where "obj" is any arbitrary object and "hint" is any PEP-compliant
#    type hint (or, more generally, any @beartype-compliant type hint).
#  * Actually, define a public is_typed_as() alias to the is_bearable() tester.
#    Not everyone wants cute names; PEP 8-compliant snake case is often
#    preferable and we ourselves would probably prefer the former, for example.
#* Expose that tester as beartype.is_bearable() by importing into this module:
#     from beartype._bearable import is_bearable
#
#*YUP.* is_bearable() is the single public turbo-charged function declared by
#this package. The nomenclature for this tester derives, of course, from the
#builtin isinstanceof() and issubclassof() builtins. is_bearable() could be
#considered a generalization or proper superset of both -- in that anything you
#can do with those builtins you can do with is_bearable(), but you can also do
#*MUCH* more with is_bearable().
#
#Fortuitously, implementing is_bearable() in terms of the existing @beartype
#decorator is trivial and requires absolutely *NO* refactoring of the
#"beartype" codebase itself, which is certainly nice (albeit non-essential):
#* Internally, is_bearable() should maintain a *non-LRU* cache (probably in a
#  separate "_bearable._cache" submodule as a simple dictionary) named
#  "HINT_OR_HINT_REPR_TO_BEARTYPE_WRAPPER" mapping from each arbitrary
#  PEP-compliant type hint (passed as the second parameter to is_bearable()) to
#  the corresponding wrapper function dynamically generated by the @beartype
#  decorator checking an arbitrary object against that hint. However, note
#  there there's a significant caveat here:
#  * *NOT ALL HINTS ARE CACHABLE.* If the passed hint is *NOT* cachable, we
#    should instead cache that hint under its machine-readable repr() string.
#    While slower to generate, generating that string is still guaranteed to be
#    *MUCH* faster than dynamically declaring a new function each call.
#* The trivial way to implement the prior item is to dynamically define one new
#  private @beartype-decorated noop function accepting an arbitrary parameter
#  type-hinted by each type hint: e.g.,
#      # Pseudo-code, obviously. Again, this snippet should probably be
#      # shifted into a new "_bearable._snip" submodule.
#      is_typed_as_wrapper = exec(f'''
#      @beartype
#      def is_typed_as_wrapper(obj: {hint}): pass
#      ''')
#* After either defining and caching that wrapper into the above dictionary
#  *OR* retrieved a previously wrapper from that dictionary, trivially
#  implement this check with EAFP as follows:
#      try:
#          is_typed_as_wrapper(obj)
#          return True
#      except:
#          return False
#
#*DONE.* Sweet, yah? The above can and should be heavily optimized, of course.
#How? That remains to be determined. The principle issue with the above
#approach is that it unnecessarily incurs an additional stack frame. Since the
#original is_typed_as_wrapper() function wrapped by @beartype doesn't actually
#do anything, it would be really nice if the wrapper generated by @beartype
#omitted the call to that original function.
#
#This might be easier than expected. You're probably thinking AST inspector or
#disassembly, right? Neither of those two things are easy or fast, so let's do
#neither. Is there any alternative? There might be. In theory, the code object
#for any callable whose implementation is literally "pass" should be trivially
#detectable via metadata on that object. If nothing else, the byte code for
#that object should be a constant size; any code object whose byte code is
#larger than that size is *NOT* a "pass" noop.
#
#In any case, @beartype should efficiently detect noop callables and avoid
#calling those callables from the wrapper functions it generates for those
#callables. This would be genuinely useful from the general-purpose
#perspective, which means we should make this happen.
#FIXME: Note that we discuss is_bearable() with respect to variable annotations
#in this issue comment. See the fragment leading with 'The simple answer is:
#"Nope, but a related package called bearcall will let you do that soon!"':
#    https://github.com/beartype/beartype/issues/30#issuecomment-792176571

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid race conditions during setuptools-based installation, this
# module may import *ONLY* from modules guaranteed to exist at the start of
# installation. This includes all standard Python and package submodules but
# *NOT* third-party dependencies, which if currently uninstalled will only be
# installed at some later time in the installation. Likewise, to avoid circular
# import dependencies, the top-level of this module should avoid importing
# package submodules where feasible.
# WARNING: To avoid polluting the public module namespace, external attributes
# should be locally imported at module scope *ONLY* under alternate private
# names (e.g., "from argparse import ArgumentParser as _ArgumentParser" rather
# than merely "from argparse import ArgumentParser").
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ....................{ IMPORTS                           }....................
# Publicize the private @beartype._decor.beartype decorator as
# @beartype.beartype, preserving all implementation details as private.
from beartype._decor.main import beartype

# For PEP 8 compliance, versions constants expected by external automation are
# imported under their PEP 8-mandated names.
from beartype.meta import VERSION as __version__
from beartype.meta import VERSION_PARTS as __version_info__

# ....................{ GLOBALS                           }....................
# Document all global variables imported into this namespace above.

__version__ = __version__
'''
Human-readable package version as a ``.``-delimited string.

For PEP 8 compliance, this specifier has the canonical name ``__version__``
rather than that of a typical global (e.g., ``VERSION_STR``).
'''


__version_info__ = __version_info__
'''
Machine-readable package version as a tuple of integers.

For PEP 8 compliance, this specifier has the canonical name
``__version_info__`` rather than that of a typical global (e.g.,
``VERSION_PARTS``).
'''


__all__ = ['beartype',]
'''
Special list global of the unqualified names of all public package attributes
explicitly exported by and thus safely importable from this package.

Caveats
-------
**This global is defined only for conformance with static type checkers,** a
necessary prerequisite for `PEP 561`_-compliance. This global is *not* intended
to enable star imports of the form ``from beartype import *`` (now largely
considered a harmful anti-pattern by the Python community), although it
technically does the latter as well.

This global would ideally instead reference *only* a single package attribute
guaranteed *not* to exist (e.g., ``'STAR_IMPORTS_CONSIDERED_HARMFUL'``),
effectively disabling star imports. Since doing so induces spurious static
type-checking failures, we reluctantly embrace the standard approach. For
example, :mod:`mypy` emits an error resembling ``"error: Module 'beartype' does
not explicitly export attribute 'beartype'; implicit reexport disabled."``

.. _PEP 561:
   https://www.python.org/dev/peps/pep-0561
'''
