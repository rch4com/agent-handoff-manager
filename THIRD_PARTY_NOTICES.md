# Third-party notices

Status as of 2026-11-06: **no upstream source file is copied or vendored into this repository** (see `docs/ADR-0003.md`). This product re-implements handoff concepts with its own code. The notices below are retained because the design references the following MIT-licensed projects, and they MUST stay with any future redistributed upstream source.

| Upstream | Reviewed SHA (`upstreams.lock.json`) | License blob SHA | Use |
|---|---|---|---|
| https://github.com/WeirdSky924/agent-handoff-skill | `ef01fa9db0ea0aab19141954644a1049da4da795` | `bbf0adc0f98e1716d354e30cf601873f3fc5b0b2` | design reference (durable state layout, compaction ideas) |
| https://github.com/aploe/claude-handoff-skill | `b6ad33e52c8c72f95cbafb006b7c7347c34f3ec8` | `a0a2e818e69cd129bc3e49e7f9af9c1f6701e985` | design reference (write/resume/list/archive semantics) |

Both license texts below were fetched verbatim from the reviewed SHA on 2026-11-06 (bodies are identical; only the copyright line differs).

## WeirdSky924/agent-handoff-skill

```text
MIT License

Copyright (c) 2026 WeirdSky924

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## aploe/claude-handoff-skill

```text
MIT License

Copyright (c) 2026 aploe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
