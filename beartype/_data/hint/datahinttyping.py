#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright (c) 2014-2024 Beartype authors.
# See "LICENSE" for further details.

'''
Project-wide **type hints** (i.e., PEP-compliant type hints annotating callables
and classes declared throughout this codebase, either for compliance with
:pep:`561`-compliant static type checkers like :mod:`mypy` or simply for
documentation purposes).

This private submodule is *not* intended for importation by downstream callers.
'''

# ....................{ IMPORTS                            }....................
import beartype #  <-- satisfy mypy [note to self: i can't stand you, mypy]
from ast import (
    AST,
    AsyncFunctionDef,
    ClassDef,
    FunctionDef,
)
from beartype.typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    ForwardRef,
    Iterable,
    Iterator,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from beartype._cave._cavefast import (
    MethodBoundInstanceOrClassType,
    MethodDecoratorClassType,
    MethodDecoratorPropertyType,
    MethodDecoratorStaticType,
)
from beartype._data.hint.pep.sign.datapepsigncls import HintSign
from beartype._data.func.datafuncarg import ARG_VALUE_UNPASSED
from collections.abc import Callable as CallableABC
from importlib.abc import PathEntryFinder
from pathlib import Path
from types import (
    CodeType,
    FrameType,
    GeneratorType,
)

# ....................{ TYPEVARS                           }....................
S = TypeVar('S')
'''
**Unbound type variable** (i.e., matching *any* arbitrary type) locally bound to
different types than the :data:`.T` type variable.
'''


T = TypeVar('T')
'''
**Unbound type variable** (i.e., matching *any* arbitrary type) locally bound to
different types than the :data:`.S` type variable.
'''


CallableT = TypeVar('CallableT', bound=CallableABC)
'''
**Callable type variable** (i.e., bound to match *only* callables).
'''


NodeT = TypeVar('NodeT', bound=AST)
'''
**Node type variable** (i.e., type variable constrained to match *only* abstract
syntax tree (AST) nodes).
'''

# ....................{ AST                                }....................
NodeCallable = Union[FunctionDef, AsyncFunctionDef]
'''
PEP-compliant type hint matching a **callable node** (i.e., abstract syntax tree
(AST) node encapsulating the definition of a pure-Python function or method that
is either synchronous or asynchronous).
'''


NodeDecoratable = Union[NodeCallable, ClassDef]
'''
PEP-compliant type hint matching a **decoratable node** (i.e., abstract syntax
tree (AST) node encapsulating the definition of a pure-Python object supporting
decoration by one or more ``"@"``-prefixed decorations, including both
pure-Python classes *and* callables).
'''


NodeVisitResult = Optional[Union[AST, List[AST]]]
'''
PEP-compliant type hint matching a **node visitation result** (i.e., object
returned by any visitor method of an :class:`ast.NodeVisitor` subclass).

Specifically, this hint matches either:

* A single node, in which case a visitor method has effectively preserved the
  currently visited node passed to that method in the AST.
* A list of zero or more nodes, in which case a visitor method has replaced the
  currently visited node passed to that method with those nodes in the AST.
* :data:`None`, in which case a visitor method has effectively destroyed the
  currently visited node passed to that method from the AST.
'''


NodesList = List[AST]
'''
PEP-compliant type hint matching an **abstract syntax tree (AST) node list**
(i.e., list of zero or more AST nodes).
'''

# ....................{ BOOL                               }....................
BoolTristate = Literal[True, False, None]
'''
PEP-compliant type hint matching a **tri-state boolean** whose value may be
either:

* :data:`True`.
* :data:`False`.
* :data:`None`, implying that the actual value of this boolean is contextually
  dependent on context-sensitive program state.
'''


BoolTristateUnpassable = Literal[True, False, None, ARG_VALUE_UNPASSED]  # type: ignore[valid-type]
'''
PEP-compliant type hint matching an **unpassable tri-state boolean** whose value
may be either:

* :data:`True`.
* :data:`False`.
* :data:`None`, implying that the actual value of this boolean is contextually
  dependent on context-sensitive program state.
* :data:`.ARG_VALUE_UNPASSED`, enabling any callable that annotates a tri-state
  boolean parameter by this type hint to deterministically identify whether the
  caller explicitly passed that parameter or not. Since the caller may
  explicitly pass :data:`None` as a valid value, testing that parameter against
  :data:`None` does *not* suffice to decide this decision problem.
'''

# ....................{ CALLABLE ~ early                   }....................
# Callable-specific type hints required by subsequent type hints below.

CallableAny = Callable[..., Any]
'''
PEP-compliant type hint matching any callable in a manner explicitly matching
all possible callable signatures.
'''

# ....................{ TYPEVAR ~ early                    }....................
# Type variables required by subsequent type hints below.

BeartypeableT = TypeVar(
    'BeartypeableT',
    # The @beartype decorator decorates objects that are either...
    bound=Union[
        # An arbitrary class *OR*...
        type,

        # An arbitrary callable *OR*...
        CallableAny,

        # A C-based unbound class method descriptor (i.e., a pure-Python unbound
        # function decorated by the builtin @classmethod decorator) *OR*...
        MethodDecoratorClassType,

        # A C-based unbound property method descriptor (i.e., a pure-Python
        # unbound function decorated by the builtin @property decorator) *OR*...
        MethodDecoratorPropertyType,

        # A C-based unbound static method descriptor (i.e., a pure-Python
        # unbound function decorated by the builtin @staticmethod decorator).
        MethodDecoratorStaticType,

        #FIXME: Currently unused, but preserved for posterity.
        # # A C-based bound method descriptor (i.e., a pure-Python unbound
        # # function bound to an object instance on Python's instantiation of that
        # # object) *OR*...
        # MethodBoundInstanceOrClassType,
    ],
)
'''
:pep:`484`-compliant **generic beartypeable type variable** (i.e., type hint
matching any arbitrary object decoratable by the :func:`beartype.beartype`
decorator, including pure-Python callables and classes, C-based descriptors, and
even more exotic objects).

This type variable notifies static analysis performed by both static type
checkers (e.g., :mod:`mypy`) and type-aware IDEs (e.g., VSCode) that the
:func:`beartype.beartype` decorator preserves:

* Callable signatures by creating and returning callables with the same
  signatures as passed callables.
* Class hierarchies by preserving passed classes with respect to inheritance,
  including metaclasses and method-resolution orders (MRO) of those classes.
'''

# ....................{ CALLABLE                           }....................
# Callable-specific type hints *NOT* required by subsequent type hints below.

CallableRaiser = Callable[[object], None]
'''
PEP-compliant type hint matching a **raiser callable** (i.e., arbitrary callable
accepting a single arbitrary object and either raising an exception or emitting
a warning rather than returning any value).
'''


CallableRaiserOrTester = Callable[[object], Optional[bool]]
'''
PEP-compliant type hint matching a **raiser or tester callable** (i.e.,
arbitrary callable accepting a single arbitrary object and either returning no
value or returning either :data:`True` if that object satisfies an arbitrary
constraint *or* :data:`False` otherwise).
'''


CallableTester = Callable[[object], bool]
'''
PEP-compliant type hint matching a **tester callable** (i.e., arbitrary callable
accepting a single arbitrary object and returning either :data:`True` if that
object satisfies an arbitrary constraint *or* :data:`False` otherwise).
'''


Codeobjable = Union[Callable, CodeType, FrameType, GeneratorType]
'''
PEP-compliant type hint matching a **codeobjable** (i.e., pure-Python object
directly associated with a code object and thus safely passable as the first
parameter to the :func:`beartype._util.func.utilfunccodeobj.get_func_codeobj`
getter retrieving the code object associated with this codeobjable).

Specifically, this hint matches:

* Code objects.
* Pure-Python callables, including generators (but *not* C-based callables,
  which lack code objects).
* Pure-Python callable stack frames.
'''


MethodDescriptorNondata = Union[
    # A C-based unbound class method descriptor (i.e., a pure-Python unbound
    # function decorated by the builtin @classmethod decorator) *OR*...
    MethodDecoratorClassType,

    # A C-based unbound static method descriptor (i.e., a pure-Python
    # unbound function decorated by the builtin @staticmethod decorator).
    MethodDecoratorStaticType,

    # A C-based bound method descriptor (i.e., a pure-Python unbound
    # function bound to an object instance on Python's instantiation of that
    # object) *OR*...
    MethodBoundInstanceOrClassType,
]
'''
PEP-compliant type hint matching any **builtin method non-data descriptor**
(i.e., C-based descriptor builtin to Python defining only the ``__get__()``
dunder method, encapsulating read-only access to some kind of method).
'''

# ....................{ CALLABLE ~ args                    }....................
CallableMethodGetitemArg = Union[int, slice]
'''
PEP-compliant type hint matching the standard type of the single positional
argument accepted by the ``__getitem__` dunder method.
'''

# ....................{ CALLABLE ~ decorator               }....................
BeartypeConfedDecorator = Callable[[BeartypeableT], BeartypeableT]
'''
PEP-compliant type hint matching a **configured beartype decorator** (i.e.,
closure created and returned from the :func:`beartype.beartype` decorator when
passed a beartype configuration via the optional ``conf`` parameter rather than
an arbitrary object to be decorated via the optional ``obj`` parameter).
'''


BeartypeReturn = Union[BeartypeableT, BeartypeConfedDecorator]
'''
PEP-compliant type hint matching any possible value returned by any invocation
of the :func:`beartype.beartype` decorator, including calls to that decorator
in both configuration and decoration modes.
'''

# ....................{ CALLABLE ~ decorator               }....................
CallableStrFormat = Callable[..., str]
'''
PEP-compliant type hint matching the signature of the standard
:meth:`str.format` method.
'''

# ....................{ DICT                               }....................
HintSignTrie = Dict[str, Union[HintSign, 'HintSignTrie']]
'''
PEP-compliant type hint matching a **sign trie** (i.e.,
dictionary-of-dictionaries tree data structure enabling efficient mapping from
the machine-readable representations of type hints created by an arbitrary
number of type hint factories defined by an external third-party package to
their identifying sign).
'''


HintSignToCallableStrFormat = Dict[HintSign, CallableStrFormat]
'''
PEP-compliant type hint matching a **sign-to-string-formatter map** (i.e.,
dictionary mapping from signs uniquely identifying type hints to
:meth:`str.format` methods bound to code snippets type-checking various aspects
of those type hints).
'''

# ....................{ DICT ~ any                         }....................
DictStrToAny = Dict[str, Any]
'''
PEP-compliant type hint matching a mapping whose keys are *all* strings.
'''


HintAnnotations = DictStrToAny
'''
PEP-compliant type hint matching **annotations** (i.e., dictionary mapping from
the name of each annotated parameter or return of a callable or annotated
variable of a class to the type hint annotating that parameter, return, or
variable).
'''


MappingStrToAny = Mapping[str, object]
'''
PEP-compliant type hint matching a mapping whose keys are *all* strings.
'''

# ....................{ CODE                               }....................
LexicalScope = DictStrToAny
'''
PEP-compliant type hint matching a **lexical scope** (i.e., dictionary mapping
from the relative unqualified name to value of each locally or globally scoped
attribute accessible to a callable or class).
'''


CodeGenerated = Tuple[str, LexicalScope, Tuple[str, ...]]
'''
PEP-compliant type hint matching **generated code** (i.e., a tuple containing
a Python code snippet dynamically generated on-the-fly by a
:mod:`beartype`-specific code generator and metadata describing that code).

Specifically, this hint matches a 3-tuple ``(func_wrapper_code,
func_wrapper_scope, hint_refs_type_basename)``, where:

* ``func_wrapper_code`` is a Python code snippet type-checking an arbitrary
  object against this hint. For the common case of code generated for a
  :func:`beartype.beartype`-decorated callable, this snippet type-checks a
  previously localized parameter or return value against this hint.
* ``func_wrapper_scope`` is the **local scope** (i.e., dictionary mapping from
  the name to value of each attribute referenced one or more times in this code)
  of the body of the function embedding this code.
* ``hint_refs_type_basename`` is a tuple of the unqualified classnames
  of :pep:`484`-compliant relative forward references visitable from this hint
  (e.g., ``('MuhClass', 'YoClass')`` given the hint ``Union['MuhClass',
  List['YoClass']]``).
'''

# ....................{ ITERABLE                           }....................
IterableStrs = Iterable[str]
'''
PEP-compliant type hint matching *any* iterable of zero or more strings.
'''

# ....................{ ITERATOR                           }....................
Enumerator = Iterator[Tuple[int, object]]
'''
PEP-compliant type hint matching *any* **enumerator** (i.e., arbitrary iterator
satisfying the :func:`enumerate` protocol). This iterator is expected to yield
zero or more 2-tuples of the form ``(item_index, item)``, where:

* ``item_index`` is the 0-based index of the currently enumerated item.
* ``item`` is the currently enumerated item.
'''

# ....................{ PATH                               }....................
CommandWords = IterableStrs
'''
PEP-compliant type hint matching **command words** (i.e., an iterable of one or
more shell words comprising a shell command, suitable for passing as the
``command_words`` parameter accepted by most callables declared in the
test-specific :mod:`beartype_test._util.command.pytcmdrun` submodule).
'''

# ....................{ TUPLE                              }....................
TupleTypes = Tuple[type, ...]
'''
PEP-compliant type hint matching a tuple of zero or more classes.

Equivalently, this hint matches all tuples passable as the second parameters to
the :func:`isinstance` and :func:`issubclass` builtins.
'''


#FIXME: *INSUFFICIENT.* Generalize this to additionally accept the types of PEP
#604-compliant new unions (e.g., "int | str").
TypeOrTupleTypes = Union[type, TupleTypes]
'''
PEP-compliant type hint matching either a single class *or* a tuple of zero or
more classes.

Equivalently, this hint matches all objects passable as the second parameters
to the :func:`isinstance` and :func:`issubclass` builtins.
'''


SetOrTupleTypes = Union[AbstractSet[type], TupleTypes]
'''
PEP-compliant type hint matching a set *or* tuple of zero or more classes.
'''

# ....................{ TUPLE ~ stack                      }....................
TypeStack = Optional[Tuple[type, ...]]
'''
PEP-compliant type hint matching a **type stack** (i.e., either tuple of zero or
more arbitrary types *or* :data:`None`).

Objects matched by this hint are guaranteed to be either:

* If the **beartypeable** (i.e., object currently being decorated by the
  :func:`beartype.beartype` decorator) is an attribute (e.g., method, nested
  class) of a class currently being decorated by that decorator, the **type
  stack** (i.e., tuple of one or more lexically nested classes that are either
  currently being decorated *or* have already been decorated by this decorator
  in descending order of top- to bottom-most lexically nested) such that:

  * The first item of this tuple is expected to be the **root decorated class**
    (i.e., module-scoped class initially decorated by this decorator whose
    lexical scope encloses this beartypeable).
  * The last item of this tuple is expected to be the **current decorated
    class** (i.e., possibly nested class currently being decorated by this
    decorator).

* Else, this beartypeable was decorated directly by this decorator. In this
  case, :data:`None`.

Parameters annotated by this hint typically default to :data:`None`.

Note that :func:`beartype.beartype` requires *both* the root and currently
decorated class to correctly resolve edge cases under :pep:`563`: e.g.,

.. code-block:: python

   from __future__ import annotations
   from beartype import beartype

   @beartype
   class Outer(object):
       class Inner(object):
           # At this time, the "Outer" class has been fully defined but is *NOT*
           # yet accessible as a module-scoped attribute. Ergo, the *ONLY* means
           # of exposing the "Outer" class to the recursive decoration of this
           # get_outer() method is to explicitly pass the "Outer" class as the
           # "cls_root" parameter to all decoration calls.
           def get_outer(self) -> Outer:
               return Outer()

Note also that nested classes have *no* implicit access to either their parent
classes *or* to class variables declared by those parent classes. Nested classes
*only* have explicit access to module-scoped classes -- exactly like any other
arbitrary objects: e.g.,

.. code-block:: python

   class Outer(object):
       my_str = str

       class Inner(object):
           # This induces a fatal compile-time exception resembling:
           #     NameError: name 'my_str' is not defined
           def get_str(self) -> my_str:
               return 'Oh, Gods.'

Ergo, the *only* owning class of interest to :mod:`beartype` is the root owning
class containing other nested classes; *all* of those other nested classes are
semantically and syntactically irrelevant. Nonetheless, this tuple intentionally
preserves *all* of those other nested classes. Why? Because :pep:`563`
resolution can only find the parent callable lexically containing that nested
class hierarchy on the current call stack (if any) by leveraging the total
number of classes lexically nesting the currently decorated class as input
metadata, as trivially provided by the length of this tuple.
'''

# ....................{ MODULE ~ beartype                  }....................
BeartypeForwardRef = Type[
    'beartype._check.forward.reference.fwdrefabc.BeartypeForwardRefABC']  # pyright: ignore
'''
PEP-compliant type hint matching a **forward reference proxy** (i.e., concrete
subclass of the abstract
:class:`beartype._check.forward.reference.fwdrefabc.BeartypeForwardRefABC`
superclass).
'''


BeartypeForwardRefArgs = Tuple[Optional[str], str, TupleTypes]
'''
PEP-compliant type hint matching a **forward reference proxy argument list**
(i.e., tuple of all parameters passed to each call of the low-level private
:func:`beartype._check.forward.reference.fwdrefmake._make_forwardref_subtype`
factory function, in the same order as positionally accepted by that function).
'''

# ....................{ MODULE ~ importlib                 }....................
# Type hints specific to the standard "importlib" package.

ImportPathHook = Callable[[str], PathEntryFinder]
'''
PEP-compliant type hint matching an **import path hook** (i.e., factory closure
creating and returning a new :class:`importlib.abc.PathEntryFinder` instance
creating and leveraging a new :class:`importlib.machinery.FileLoader` instance).
'''

# ....................{ MODULE ~ pathlib                   }....................
# Type hints specific to the standard "pathlib" package.

PathnameLike = Union[str, Path]
'''
PEP-compliant type hint matching a **pathname-like object** (i.e., either a
low-level string possibly signifying a pathname *or* a high-level :class:`Path`
instance definitely encapsulating a pathname).
'''


PathnameLikeTuple = (str, Path)
'''
2-tuple of the types of all **pathname-like objects** (i.e., either
low-level strings possibly signifying pathnames *or* high-level :class:`Path`
instances definitely encapsulating pathnames).
'''

# ....................{ PEP 484                            }....................
# Type hints required to fully comply with PEP 484.

Pep484TowerComplex = Union[complex, float, int]
'''
:pep:`484`-compliant type hint matching the **implicit complex tower** (i.e.,
complex numbers, floating-point numbers, and integers).
'''


Pep484TowerFloat = Union[float, int]
'''
:pep:`484`-compliant type hint matching the **implicit floating-point tower**
(i.e., both floating-point numbers and integers).
'''

# ....................{ PEP (484|585)                      }....................
# Type hints required to fully comply with both PEP 484 *AND* 585.

Pep484585ForwardRef = Union[str, ForwardRef]
'''
Union of all :pep:`484`- or :pep:`585`-compliant **forward reference types**
(i.e., classes of all forward reference objects).

See Also
--------
:data:`HINT_PEP484585_FORWARDREF_TYPES`
    Further details.
'''

# ....................{ TYPE                               }....................
TypeException = Type[Exception]
'''
PEP-compliant type hint matching *any* exception class.
'''


TypeWarning = Type[Warning]
'''
PEP-compliant type hint matching *any* warning category.
'''
