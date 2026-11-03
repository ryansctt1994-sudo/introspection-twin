/-!
# Fresh-replay root for the independent kernel-checking experiment

The lean4checker v4.22.0 CLI selects *prefixes*. Calling --fresh
IntrospectionTwin matches several library modules and is therefore rejected.
This leaf name matches exactly one .olean, while importing the complete
IntrospectionTwin root and its transitive Lean/Init dependencies.

This adds no theorem and proves nothing by itself. The checker must
independently replay the imported declarations under --fresh and return 0.
-/
import IntrospectionTwin
