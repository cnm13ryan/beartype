#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright (c) 2014-2021 Beartype authors.
# See "LICENSE" for further details.

'''
**Beartype decorator type hint code generation unit tests.**

This submodule unit tests the :func:`beartype.beartype` decorator with respect
to type-checking code dynamically generated by the
:mod:`beartype._decor._code.codemain` submodule.
'''

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable test errors, avoid importing from
# package-specific submodules at module scope.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# import pytest
from beartype.roar import BeartypeDecorHintPepDeprecatedWarning
from beartype_test.util.mark.pytmark import ignore_warnings
from beartype_test.util.pyterror import raises_uncached
from re import search

# ....................{ TESTS                             }....................
# Prevent pytest from capturing and displaying all expected non-fatal
# beartype-specific warnings emitted by the @beartype decorator below. Urgh!
@ignore_warnings(BeartypeDecorHintPepDeprecatedWarning)
def test_codemain() -> None:
    '''
    Test the :func:`beartype.beartype` decorator with respect to type-checking
    code dynamically generated by the :mod:`beartype._decor._code.codemain`
    submodule.

    This unit test effectively acts as a functional test and is thus the core
    test exercising decorator functionality from the end user perspective --
    the only perspective that matters in the end. Unsurprisingly, this test is
    mildly more involved than most. *Whatevah.*

    This test additionally attempts to avoid similar issues to a `prior issue
    <issue #5_>`__ of this decorator induced by repeated
    :func:`beartype.beartype` decorations of different callables annotated by
    one or more of the same PEP-compliant type hints.

    .. _issue #5:
       https://github.com/beartype/beartype/issues/5
    '''

    # Defer heavyweight imports.
    from beartype import beartype
    from beartype.roar import (
        BeartypeCallHintPepException,
        # BeartypeDecorHintPepDeprecatedWarning,
    )
    from beartype._util.utilobject import is_object_context_manager
    from beartype_test.a00_unit.data.hint.util.data_hintmetacls import (
        HintPithSatisfiedMetadata,
        HintPithUnsatisfiedMetadata,
    )
    from beartype_test.a00_unit.data.hint.nonpep.data_nonpep import (
        HINTS_NONPEP_META)
    from beartype_test.a00_unit.data.hint.pep.data_pep import HINTS_PEP_META

    # Tuple of all PEP-compliant type hint metadata to be tested -- regardless
    # of whether those hints are uniquely identifiable by a sign or not.
    HINTS_META = HINTS_PEP_META + HINTS_NONPEP_META

    # Tuple of two arbitrary values used to trivially iterate twice below.
    RANGE_2 = (None, None)

    # For each predefined PEP-compliant type hint and associated metadata...
    for hint_meta in HINTS_META:
        # If this hint is currently unsupported, continue to the next.
        if not hint_meta.is_supported:
            continue
        # Else, this hint is currently supported.

        # Repeat the following logic twice. Why? To exercise memoization across
        # repeated @beartype decorations on different callables annotated by
        # the same PEP hints.
        for _ in RANGE_2:
            # Undecorated callable both accepting a single parameter and
            # returning a value annotated by this hint whose implementation
            # trivially reduces to the identity function.
            def func_untyped(hint_param: hint_meta.hint) -> hint_meta.hint:
                return hint_param

            # Decorated callable declared below.
            func_typed = None

            #FIXME: For unknown and probably uninteresting reasons, the
            #pytest.warns() context manager appears to be broken on our
            #local machine. We have no recourse but to unconditionally
            #ignore this warning at the module level. So much rage!
            #FIXME: It's likely this has something to do with the fact that
            #Python filters deprecation warnings by default. This is almost
            #certainly a pytest issue. Since this has become fairly
            #unctuous, we should probably submit a pytest issue report.
            #FIXME: Actually, pytest now appears to have explicit support for
            #testing that a code block emits a deprecation warning:
            #    with pytest.deprecated_call():
            #        myfunction(17)
            #See also: https://docs.pytest.org/en/6.2.x/warnings.html#ensuring-code-triggers-a-deprecation-warning

            # # If this is a deprecated PEP-compliant type hint, declare this
            # # decorated callable under a context manager asserting this
            # # declaration to emit non-fatal deprecation warnings.
            # if (
            #     isinstance(hint_meta, HintPepMetadata) and
            #     hint_meta.pep_sign in HINT_PEP_ATTRS_DEPRECATED
            # ):
            #     with pytest.warns(BeartypeDecorHintPepDeprecatedWarning):
            #         func_typed = beartype(func_untyped)
            # # Else, this is *NOT* a deprecated PEP-compliant type hint. In this
            # # case, declare this decorated callable as is.
            # else:
            #     func_typed = beartype(func_untyped)

            # @beartype-generated wrapper function type-checking this callable.
            func_typed = beartype(func_untyped)

            # For each pith satisfying this hint...
            for pith_satisfied_meta in hint_meta.piths_satisfied_meta:
                # Assert this metadata is an instance of the desired dataclass.
                assert isinstance(
                    pith_satisfied_meta, HintPithSatisfiedMetadata)
                # print('PEP-testing {!r} against {!r}...'.format(hint_pep, pith_satisfied))

                # Pith to be type-checked against this hint, defined as...
                pith = (
                    # If this pith is actually a pith factory (i.e., callable
                    # accepting *NO* parameters and dynamically creating and
                    # returning the value to be used as the desired pith), call
                    # this factory and localize its return value.
                    pith_satisfied_meta.pith()
                    if pith_satisfied_meta.is_pith_factory else
                    # Else, localize this pith as is.
                    pith_satisfied_meta.pith
                )

                # If...
                if (
                    # This pith is a context manager *AND*...
                    is_object_context_manager(pith) and
                    # This pith should be safely opened and closed as a
                    # context rather than preserved as a context manager...
                    not pith_satisfied_meta.is_context_manager
                # Then with this pith safely opened and closed as a context...
                ):
                    with pith as pith_context:
                        # Assert this wrapper function successfully type-checks
                        # this context against this hint *WITHOUT* modifying
                        # this context.
                        assert func_typed(pith_context) is pith_context
                # Else, this object is *NOT* a context manager and thus safely
                # passable and returnable as is.
                else:
                    # Assert this wrapper function successfully type-checks
                    # this object against this hint *WITHOUT* modifying this
                    # object.
                    assert func_typed(pith) is pith

            # For each pith *NOT* satisfying this hint...
            for pith_unsatisfied_meta in hint_meta.piths_unsatisfied_meta:
                # Assert this metadata is an instance of the desired dataclass.
                assert isinstance(
                    pith_unsatisfied_meta, HintPithUnsatisfiedMetadata)

                # Assert that iterables of uncompiled regular expression
                # expected to match and *NOT* match this message are *NOT*
                # strings, as commonly occurs when accidentally omitting a
                # trailing comma in tuples containing only one string: e.g.,
                # * "('This is a tuple, yo.',)" is a 1-tuple containing one
                #   string.
                # * "('This is a string, bro.')" is a string *NOT* contained in
                #   a 1-tuple.
                assert not isinstance(
                    pith_unsatisfied_meta.exception_str_match_regexes, str)
                assert not isinstance(
                    pith_unsatisfied_meta.exception_str_not_match_regexes, str)

                # Assert this wrapper function raises the expected exception
                # when type-checking this pith against this hint.
                with raises_uncached(BeartypeCallHintPepException) as (
                    exception_info):
                    func_typed(pith_unsatisfied_meta.pith)

                # Exception message raised by this wrapper function.
                exception_str = str(exception_info.value)
                # print('exception message: {}'.format(exception_str))

                # Exception type localized for debuggability. Sadly, the
                # pytest.ExceptionInfo.__repr__() dunder method fails to
                # usefully describe its exception metadata.
                exception_type = exception_info.type

                # Assert this exception metadata describes the expected
                # exception as a sanity check against upstream pytest issues
                # and/or issues with our raises_uncached() context manager.
                assert issubclass(exception_type, BeartypeCallHintPepException)

                # For each uncompiled regular expression expected to match this
                # message, assert this expression actually does so.
                #
                # Note that the re.search() rather than re.match() function is
                # called. The latter is rooted at the start of the string and
                # thus *ONLY* matches prefixes, while the former is *NOT*
                # rooted at any string position and thus matches arbitrary
                # substrings as desired.
                for exception_str_match_regex in (
                    pith_unsatisfied_meta.exception_str_match_regexes):
                    assert search(
                        exception_str_match_regex, exception_str) is not None

                # For each uncompiled regular expression expected to *NOT*
                # match this message, assert this expression actually does so.
                for exception_str_not_match_regex in (
                    pith_unsatisfied_meta.exception_str_not_match_regexes):
                    assert search(
                        exception_str_not_match_regex, exception_str) is None

            # assert False is True
