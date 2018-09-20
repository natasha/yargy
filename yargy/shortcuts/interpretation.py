from __future__ import unicode_literals

import six

import sys

from yargy.interpretation.fact import Fact, fact

_PY36 = sys.version_info[:2] >= (3, 6)


# TODO CONSIDER: research ability to use directly with Fact class with backward compatibility saving
class FactDefinitionMeta(type):
    BASE_FACT_DEFINITION_CLS = None

    def __new__(mcs, typename, base_classes, class_attr):
        if class_attr.get('_ROOT_FACT_DEFINITION', False):
            # Checking for attempt to redeclare base definition class
            if mcs.BASE_FACT_DEFINITION_CLS is not None:
                raise TypeError(
                    "Attempt to redeclare base fact definition class"
                    " '{current_base_cls_name}' by '{new_base_cls_name}'".format(
                        current_base_cls_name=mcs.BASE_FACT_DEFINITION_CLS.__name__,
                        new_base_cls_name=typename
                    )
                )

            # Saving root class to metaclass attributes
            mcs.BASE_FACT_DEFINITION_CLS = super(FactDefinitionMeta, mcs).__new__(mcs, typename, base_classes,
                                                                                  class_attr)
            return mcs.BASE_FACT_DEFINITION_CLS

        if not _PY36:
            raise TypeError("Class-bases fact definition syntax is only supported in Python 3.6+")

        # TODO CONSIDER: research ability of mixins support
        # TODO CONSIDER: research ability of transitive inheritance from base class
        if base_classes != (mcs.BASE_FACT_DEFINITION_CLS,):
            raise TypeError("Class '{}' must be inherited directly from FactDefinition only."
                            " Mixins and transitive inheritance are not currently supported".format(typename))

        annotations = class_attr.get("__annotations__")

        if not annotations:
            raise TypeError("No annotations declared in fact definition class '{}'".format(typename))

        generated_fact_cls = fact("{}AutoGen".format(typename), list(annotations))

        new_base_classes = (generated_fact_cls,)

        return super(FactDefinitionMeta, mcs).__new__(mcs, typename, new_base_classes, class_attr)


class FactDefinition(six.with_metaclass(FactDefinitionMeta, Fact)):
    _ROOT_FACT_DEFINITION = True
