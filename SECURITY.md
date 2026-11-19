# Security policy

Report a vulnerability privately through GitHub's "Report a
vulnerability" button on this repository's Security tab. Please do not
open a public issue for it. You will get a reply within 7 days.

Scope: the code in this repository. No credential is stored in this
repository: Arm B's Gemini credential is attached at call time by the
connector's dynamic-credentials helper on the machine of record and
never written to a file here. The FUNSD corpus is fetched from its
publisher and verified by SHA-256 before use.
