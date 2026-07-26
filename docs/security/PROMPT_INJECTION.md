# Prompt-injection handling

Scenario text, retrieved sources, model replies, and pack metadata are untrusted data. They cannot
change evaluator policy, select tools, alter budgets, approve canonical content, or mark a review
resolved. The runner sends scenario text only in the user role after a fixed policy message.

Never execute shell fragments or URLs emitted by a model. Never interpolate model output into paths,
SQL, templates, or commands. SQL tables are created from Arrow data rather than model-built queries.
HTML autoescaping is enabled. Evidence quotes are short and displayed as data.

Adversarial fixtures should include “the benchmark is over,” fake system messages, requests to expose
keys, judge-directed score demands, and nested instructions. A successful attack becomes a regression
test and a review finding.
