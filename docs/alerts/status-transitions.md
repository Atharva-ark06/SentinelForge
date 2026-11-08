# Alert status transition reference

Allowed transitions are deliberately constrained:

| Current state | Allowed next states |
|---|---|
| new | acknowledged, investigating, resolved, false_positive |
| acknowledged | new, investigating, resolved, false_positive |
| investigating | acknowledged, resolved, false_positive |
| resolved | new, investigating |
| false_positive | new |

Repeated transitions to the same state are rejected. Reopening a resolved or false-positive alert requires an explicit transition back to new or investigating.