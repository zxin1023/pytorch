import torch
import sys
from collections import OrderedDict

# pattern for conv bn fusion
FUSION_PATTERNS = OrderedDict()
def register_fusion_pattern(pattern):
    def insert(fn):
        FUSION_PATTERNS[pattern] = fn
        return fn
    return insert

def get_fusion_patterns():
    return FUSION_PATTERNS

# pattern for both static quantization and qat
QUANTIZATION_PATTERNS = OrderedDict()
def register_quant_pattern(pattern):
    def insert(fn):
        QUANTIZATION_PATTERNS[pattern] = fn
        return fn
    return insert

def get_quant_patterns():
    return QUANTIZATION_PATTERNS

# pattern for dynamic quantization
DYNAMIC_QUANTIZATION_PATTERNS = OrderedDict()
def register_dynamic_pattern(pattern):
    def insert(fn):
        DYNAMIC_QUANTIZATION_PATTERNS[pattern] = fn
        return fn
    return insert

def get_dynamic_quant_patterns():
    return DYNAMIC_QUANTIZATION_PATTERNS

def matches(modules, node, pattern, max_uses=sys.maxsize):
    if isinstance(pattern, tuple):
        self_match, *arg_matches = pattern
        if self_match is getattr:
            assert len(pattern) == 2, 'Expecting getattr pattern to have two elements'
            arg_matches = None
    else:
        self_match = pattern
        arg_matches = None

    if node.uses > max_uses:
        return False

    if isinstance(self_match, type) and issubclass(self_match, torch.nn.Module):
        if node.op != 'call_module':
            return False
        if not type(modules[node.target]) == self_match:
            return False
    elif callable(self_match):
        if node.op != 'call_function' or node.target is not self_match:
            return False
        elif node.target is getattr:
            if node.args[1] != pattern[1]:
                return False
    elif node.target != self_match:
        return False

    if not arg_matches:
        return True

    if len(arg_matches) != len(node.args):
        return False

    return all(matches(modules, node, arg_match, max_uses=1) for node, arg_match in zip(node.args, arg_matches))