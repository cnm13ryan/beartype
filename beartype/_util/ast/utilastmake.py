#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright (c) 2014-2024 Beartype authors.
# See "LICENSE" for further details.

'''
Beartype **abstract syntax tree (AST) factories** (i.e., low-level callables
creating and returning various types of nodes, typically for inclusion in the
currently visited AST).

This private submodule is *not* intended for importation by downstream callers.
'''

# ....................{ IMPORTS                            }....................
from ast import (
    AST,
    Attribute,
    Call,
    Constant,
    Expr,
    FormattedValue,
    ImportFrom,
    Name,
    alias,
    keyword,
)
from beartype.typing import (
    List,
    Optional,
)
from beartype._cave._cavemap import NoneTypeOr
from beartype._data.ast.dataast import (
    NODE_CONTEXT_LOAD,
    NODE_CONTEXT_STORE,
)
from beartype._data.hint.datahinttyping import ListNodes
from beartype._data.kind.datakindsequence import LIST_EMPTY
from beartype._util.ast.utilastmunge import copy_node_metadata

# ....................{ FACTORIES                          }....................
#FIXME: Unit test us up, please.
def make_node_importfrom(
    # Mandatory parameters.
    module_name: str,
    source_attr_name: str,
    node_sibling: AST,

    # Optional parameters.
    target_attr_name: Optional[str] = None,
) -> ImportFrom:
    '''
    Create and return a new **import-from abstract syntax tree (AST) node**
    (i.e., node encapsulating an import statement of the alias-style format
    ``from {module_name} import {attr_name}``) importing the attribute with the
    passed source name from the module with the passed name into the currently
    visited module as a new attribute with the passed target name.

    Parameters
    ----------
    module_name : str
        Fully-qualified name of the module to import this attribute from.
    source_attr_name : str
        Unqualified basename of the attribute to import from this module.
    target_attr_name : Optional[str]
        Either:

        * If this attribute is to be imported into the currently visited module
          under a different unqualified basename, that basename.
        * If this attribute is to be imported into the currently visited module
          under the same unqualified basename as ``source_attr_name``,
          :data:`None`.

        Defaults to :data:`None`.
    node_sibling : AST
        Sibling node to copy source code metadata from.

    Returns
    -------
    ImportFrom
        Import-from node importing this attribute from this module.
    '''
    assert isinstance(module_name, str), f'{repr(module_name)} not string.'
    assert isinstance(source_attr_name, str), (
        f'{repr(source_attr_name)} not string.')
    assert isinstance(target_attr_name, NoneTypeOr[str]), (
        f'{repr(target_attr_name)} neither string nor "None".')

    # Node encapsulating the name of the attribute to import from this module,
    # defined as either...
    node_importfrom_name = (
        # If this attribute is to be imported into the currently visited module
        # under a different basename, do so;
        alias(name=source_attr_name, asname=target_attr_name)
        if target_attr_name else
        # Else, this attribute is to be imported into the currently visited
        # module under the same basename. In this case, do so.
        alias(name=source_attr_name)
    )

    # Node encapsulating the name of the module to import this attribute from.
    node_importfrom = ImportFrom(
        module=module_name,
        names=[node_importfrom_name],
        # Force an absolute import for safety (i.e., prohibit relative imports).
        level=0,
    )

    # Copy all source code metadata (e.g., line numbers) from this sibling node
    # onto these new nodes.
    copy_node_metadata(
        node_src=node_sibling, node_trg=(node_importfrom, node_importfrom_name))

    # Return this import-from node.
    return node_importfrom

# ....................{ FACTORIES ~ attribute              }....................
#FIXME: Unit test us up, please.
def make_node_attribute_load(
    # Mandatory parameters.
    node_name_load: AST,
    attr_name: str,
    node_sibling: AST,
) -> Attribute:
    '''
    Create and return a new **object attribute access abstract syntax tree (AST)
    node** (i.e., node encapsulating an access of an object attribute) of the
    passed object with the passed attribute name.

    Parameters
    ----------
    node_name_load : AST
        Name node accessing the parent object to access this attribute from.
    attr_name : str
        Unqualified basename of the attribute of this object to be accessed.
    node_sibling : AST
        Sibling node to copy source code metadata from.

    Returns
    -------
    Attribute
        Object attribute node accessing this attribute of this object.
    '''
    assert isinstance(node_name_load, AST), (
        f'{repr(node_name_load)} not AST node.')
    assert isinstance(attr_name, str), f'{repr(attr_name)} not string.'

    # Object attribute node accessing this attribute of this object.
    node_attribute_load = Attribute(
        value=node_name_load, attr=attr_name, ctx=NODE_CONTEXT_LOAD)

    # Copy source code metadata from this sibling node onto this new node.
    copy_node_metadata(node_src=node_sibling, node_trg=node_attribute_load)

    # Return this node.
    return node_attribute_load

# ....................{ FACTORIES ~ call                   }....................
#FIXME: Unit test us up, please.
def make_node_call_expr(
    *args,
    node_sibling: AST,
    **kwargs
) -> Expr:
    '''
    Create and return a new **callable call expression abstract syntax tree
    (AST) node** (i.e., node encapsulating a Python expression expressing a call
    to an arbitrary function or method) calling the function or method with the
    passed name, positional arguments, and keyword arguments.

    Parameters
    ----------
    node_sibling : AST
        Sibling node to copy source code metadata from.

    All remaining passed positional and keyword parameters are passed to the
    lower-level :func:`.make_node_call` factory function as is.

    Returns
    -------
    Expr
        Expression node calling this callable with these parameters.
    '''

    # Child node calling this callable.
    node_func_call = make_node_call(*args, node_sibling=node_sibling, **kwargs)  # type: ignore[misc]

    # Child node expressing this call as a Python expression.
    node_func = Expr(node_func_call)

    # Copy source code metadata from this sibling node onto this new node.
    copy_node_metadata(node_src=node_sibling, node_trg=node_func)

    # Return this expression node.
    return node_func


#FIXME: Unit test us up, please.
def make_node_call(
    # Mandatory parameters.
    func_name: str,
    node_sibling: AST,

    # Optional parameters.
    nodes_args: ListNodes = LIST_EMPTY,
    nodes_kwargs: List[keyword] = LIST_EMPTY,
) -> Call:
    '''
    Create and return a new **callable call abstract syntax tree (AST) node**
    (i.e., node encapsulating a call to an arbitrary function or method)
    calling the function or method with the passed name, positional arguments,
    and keyword arguments.

    Parameters
    ----------
    func_name : str
        Fully-qualified name of the module to import this attribute from.
    node_sibling : AST
        Sibling node to copy source code metadata from.
    nodes_args : ListNodes, optional
        List of zero or more **positional parameter AST nodes** comprising the
        tuple of all positional parameters to be passed to this call. Defaults
        to the empty list.
    nodes_kwargs : ListNodes, optional
        List of zero or more **keyword parameter AST nodes** comprising the
        dictionary of all keyword parameters to be passed to this call. Defaults
        to the empty list.

    Returns
    -------
    Call
        Callable call node calling this callable with these parameters.
    '''
    assert isinstance(nodes_args, list), f'{repr(nodes_args)} not list.'
    assert isinstance(nodes_kwargs, list), f'{repr(nodes_kwargs)} not list.'
    assert all(
        isinstance(node_args, AST) for node_args in nodes_args), (
        f'{repr(nodes_args)} not list of AST nodes.')
    assert all(
        isinstance(node_kwargs, keyword) for node_kwargs in nodes_kwargs), (
        f'{repr(nodes_kwargs)} not list of keyword nodes.')

    # Child node referencing the callable to be called.
    node_func_name = make_node_name_load(
        name=func_name, node_sibling=node_sibling)

    # Child node calling this callable.
    node_func_call = Call(
        func=node_func_name,
        args=nodes_args,
        keywords=nodes_kwargs,
    )

    # Copy source code metadata from this sibling node onto this new node.
    copy_node_metadata(node_src=node_sibling, node_trg=node_func_call)

    # Return this call node.
    return node_func_call

# ....................{ FACTORIES ~ literal : string       }....................
#FIXME: Unit test us up, please.
def make_node_str(text: str, node_sibling: AST) -> Constant:
    '''
    Create and return a new **string literal abstract syntax tree
    (AST) node** (i.e., node encapsulating the passed string).

    Parameters
    ----------
    text : str
        String literal to be encapsulated in a new node.
    node_sibling : AST
        Sibling node to copy source code metadata from.

    Returns
    -------
    Constant
        String literal node encapsulating this string.
    '''
    assert isinstance(text, str), f'{repr(text)} not string.'

    # Child node encapsulating this string.
    node_str = Constant(value=text)

    # Copy source code metadata from this sibling node onto this new node.
    copy_node_metadata(node_src=node_sibling, node_trg=node_str)

    # Return this string literal node.
    return node_str

# ....................{ FACTORIES ~ literal : f-string     }....................
#FIXME: Unit test us up, please.
def make_node_fstr_field(node_expr: AST, node_sibling: AST) -> FormattedValue:
    '''
    Create and return a new **f-string formatting field abstract syntax tree
    (AST) node** (i.e., node embedding the substring created and returned by the
    evaluation of the passed arbitrary expression in some parent node
    encapsulating an f-string embedding this field).

    This factory function creates substrings resembling ``{some_fstr_field}`` in
    larger f-strings resembling ``f'This is {some_fstr_field}, isn't it?'``.

    Caveats
    -------
    This field assumes *no* suffixing ``!``-prefixed conversion (e.g., "!a",
    "!r", "!s"). Thankfully, those conversions are only syntactic sugar for more
    human-readable builtins (e.g., ``repr()``, ``str()``). Ergo, this caveat
    does *not* actually constitute a hard constraint. Just prefer the builtins.

    Parameters
    ----------
    node_expr : AST
        Formatting field to be embedded in some parent f-string node.
    node_sibling : AST
        Sibling node to copy source code metadata from.

    Returns
    -------
    Name
        Name node accessing this attribute in the current lexical scope.
    '''
    assert isinstance(node_expr, AST), f'{repr(node_expr)} not AST node.'

    # Child node encapsulating a formatting field "{node_expr.value}" in some
    # parent node encapsulating an f-string embedding this field. For unknown
    # reasons, the standard "ast" module requires that the "conversion"
    # parameter be passed as a non-standard magic integer constant. Whatevahs!
    node_fstr_field = FormattedValue(value=node_expr, conversion=-1)

    # Copy source code metadata from this sibling node onto this new node.
    copy_node_metadata(node_src=node_sibling, node_trg=node_fstr_field)

    # Return this f-string field node.
    return node_fstr_field

# ....................{ FACTORIES ~ name                   }....................
#FIXME: Unit test us up.
def make_node_name_load(name: str, node_sibling: AST) -> Name:
    '''
    Create and return a new **attribute access abstract syntax tree (AST) node**
    (i.e., node encapsulating an access of an attribute) in the current lexical
    scope with the passed name.

    Parameters
    ----------
    name : str
        Fully-qualified name of the attribute to be accessed.
    node_sibling : AST
        Sibling node to copy source code metadata from.

    Returns
    -------
    Name
        Name node accessing this attribute in the current lexical scope.
    '''
    assert isinstance(name, str), f'{repr(name)} not string.'

    # Child node accessing this attribute in the current lexical scope.
    node_name = Name(name, ctx=NODE_CONTEXT_LOAD)

    # Copy source code metadata from this sibling node onto this new node.
    copy_node_metadata(node_src=node_sibling, node_trg=node_name)

    # Return this child node.
    return node_name


#FIXME: Unit test us up.
def make_node_name_store(name: str, node_sibling: AST) -> Name:
    '''
    Create and return a new **attribute assignment abstract syntax tree (AST)
    node** (i.e., node encapsulating an assignment of an attribute) in the
    current lexical scope with the passed name.

    Parameters
    ----------
    name : str
        Fully-qualified name of the attribute to be assigned.
    node_sibling : AST
        Sibling node to copy source code metadata from.

    Returns
    -------
    Name
        Name node assigning this attribute in the current lexical scope.
    '''
    assert isinstance(name, str), f'{repr(name)} not string.'

    # Child node assigning this attribute in the current lexical scope.
    node_name = Name(name, ctx=NODE_CONTEXT_STORE)

    # Copy source code metadata from this sibling node onto this new node.
    copy_node_metadata(node_src=node_sibling, node_trg=node_name)

    # Return this child node.
    return node_name
