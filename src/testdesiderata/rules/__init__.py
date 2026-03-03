from testdesiderata.models import Rule
from testdesiderata.rules.automated import AutomatedRule
from testdesiderata.rules.behavioral import BehavioralRule
from testdesiderata.rules.composable import ComposableRule
from testdesiderata.rules.deterministic import DeterministicRule
from testdesiderata.rules.fast import FastRule
from testdesiderata.rules.isolated import IsolatedRule
from testdesiderata.rules.predictive import PredictiveRule
from testdesiderata.rules.readable import ReadableRule
from testdesiderata.rules.specific import SpecificRule
from testdesiderata.rules.structure_insensitive import StructureInsensitiveRule

ALL_RULES: list[Rule] = [
    DeterministicRule(),
    IsolatedRule(),
    FastRule(),
    AutomatedRule(),
    BehavioralRule(),
    StructureInsensitiveRule(),
    SpecificRule(),
    PredictiveRule(),
    ComposableRule(),
    ReadableRule(),
]
